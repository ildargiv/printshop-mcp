"""Automatic imposition: a list of items (badges, cards, flyers, PDFs, images, HTML snippets) -> packed sheets.

Items are packed into full-width shelves (rows), so every sheet can be cut with straight guillotine cuts.
Items of different paper groups never share a sheet: each group becomes its own HTML file / print job.
"""
import html as _html
import json
import os
import time
from pathlib import Path
from urllib.parse import quote

from .win import PrintError

SHEETS = {"A3": (297, 420), "A4": (210, 297), "A5": (148, 210), "A6": (105, 148), "Letter": (215.9, 279.4),
          "Legal": (215.9, 355.6), "Tabloid": (279.4, 431.8), "10x15": (101.6, 152.4)}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".pdf"}
MAX_UNITS = 2000


def _sheet_size(sheet, landscape=False):
    if isinstance(sheet, (list, tuple)) and len(sheet) == 2:
        w, h = float(sheet[0]), float(sheet[1])
    elif str(sheet) in SHEETS:
        w, h = SHEETS[str(sheet)]
    else:
        raise PrintError(f"Unknown sheet '{sheet}'. Use one of {', '.join(SHEETS)} or [width_mm, height_mm].", "bad_args")
    return (max(w, h), min(w, h)) if landscape else (w, h)


def pack(units, W, H, margin, gap, rotate=True):
    """Tries several orderings / orientation preferences and keeps the result with the fewest sheets
    (then the fullest first sheets)."""
    best = None
    flipped = [{**u, "w": u["h"], "h": u["w"]} for u in units]
    for columns in (False, True):            # rows (shelves) across the sheet, or columns down it
        for order in ("side", "area", "height"):
            for prefer in ("fill", "low", "tall"):
                if columns:                  # pack on the transposed sheet, then transpose back
                    res = [[{**p, "w": p["h"], "h": p["w"], "x": p["y"], "y": p["x"], "pw": p["ph"], "ph": p["pw"]}
                            for p in sh] for sh in _pack(flipped, H, W, margin, gap, rotate, order, prefer)]
                else:
                    res = _pack(units, W, H, margin, gap, rotate, order, prefer)
                key = (len(res), [-len(sh) for sh in res], sum(p["rotated"] for sh in res for p in sh))
                if best is None or key < best[0]:
                    best = (key, res)
    return best[1]


def _pack(units, W, H, margin, gap, rotate, order_by, prefer):
    """Shelf packing. units: [{"w","h","rot_ok",...}] -> list of sheets, each a list of placed units
    {"x","y","w","h","rotated"} in mm relative to the sheet (centred on the sheet)."""
    uw, uh = W - 2 * margin, H - 2 * margin
    for u in units:
        fits = (u["w"] <= uw + 1e-6 and u["h"] <= uh + 1e-6) or (u["rot_ok"] and rotate and u["h"] <= uw + 1e-6 and u["w"] <= uh + 1e-6)
        if not fits:
            raise PrintError(f"Item '{u['name']}' ({u['w']}x{u['h']} mm) does not fit on a {W}x{H} mm sheet with "
                             f"{margin} mm margins.", "too_big")

    def options(u):
        o = [(u["w"], u["h"], False)]
        if rotate and u["rot_ok"] and abs(u["w"] - u["h"]) > 1e-6:
            o.append((u["h"], u["w"], True))
        return [x for x in o if x[0] <= uw + 1e-6 and x[1] <= uh + 1e-6]

    # big first: by the larger side, then by area
    keys = {"side": lambda u: (-max(u["w"], u["h"]), -u["w"] * u["h"]),
            "area": lambda u: (-u["w"] * u["h"], -max(u["w"], u["h"])),
            "height": lambda u: (-min(u["w"], u["h"]), -u["w"] * u["h"])}
    order = sorted(units, key=keys[order_by])
    sheets = []
    cur, shelves, y_next = None, [], 0.0

    def new_sheet():
        nonlocal cur, shelves, y_next
        cur, shelves, y_next = [], [], 0.0
        sheets.append(cur)

    new_sheet()
    for u in order:
        placed = False
        # 1) fill a hole: stack under an existing column of a shelf, or open a new column at the shelf's end.
        #    Pick the spot that leaves the least height unused in that column.
        best = None
        for s in shelves:
            for w, h, r in options(u):
                for c in s["cols"]:
                    y = c["used"] + gap
                    if w <= c["w"] + 1e-6 and y + h <= s["h"] + 1e-6:
                        cand = (s["h"] - (y + h), 0, s, c, c["x"], s["y"] + y, w, h, r)
                        if best is None or cand[:2] < best[:2]:
                            best = cand
                x = s["x"] + gap
                if h <= s["h"] + 1e-6 and x + w <= uw + 1e-6:
                    cand = (s["h"] - h, 1, s, None, x, s["y"], w, h, r)
                    if best is None or cand[:2] < best[:2]:
                        best = cand
        if best:
            _, _, s, c, x, y, w, h, r = best
            cur.append({**u, "x": x, "y": y, "pw": w, "ph": h, "rotated": r})
            if c is not None:
                c["used"] = y - s["y"] + h
            else:
                s["cols"].append({"x": x, "w": w, "used": h})
                s["x"] = x + w
            placed = True
        if not placed:
            # 2) a new shelf: orientation that fills the row best, then the lower one
            def score(o):
                w, h, r = o
                n = max(1, int((uw + gap + 1e-6) // (w + gap)))
                fill = -(n * w) / uw
                return {"fill": (fill, h), "low": (h, fill), "tall": (-h, fill)}[prefer]
            for attempt in range(2):
                y = y_next + (gap if shelves else 0)
                opts = [o for o in options(u) if y + o[1] <= uh + 1e-6]
                if opts:
                    w, h, r = min(opts, key=score)
                    s = {"y": y, "h": h, "x": w, "cols": [{"x": 0.0, "w": w, "used": h}]}
                    shelves.append(s)
                    y_next = y + h
                    cur.append({**u, "x": 0.0, "y": y, "pw": w, "ph": h, "rotated": r})
                    placed = True
                    break
                new_sheet()
        if not placed:
            raise PrintError(f"Cannot place item '{u['name']}'.", "too_big")

    # centre each sheet's block so the margins are even
    out = []
    for sh in sheets:
        if not sh:
            continue
        bw = max(p["x"] + p["pw"] for p in sh)
        bh = max(p["y"] + p["ph"] for p in sh)
        ox, oy = (W - bw) / 2, (H - bh) / 2
        out.append([{**p, "x": round(p["x"] + ox, 3), "y": round(p["y"] + oy, 3)} for p in sh])
    return out


def _content(item, base):
    """Inner HTML for one item, sized to its unrotated box (100% x 100%)."""
    if item.get("html"):
        return item["html"]
    src = Path(item["src"])
    if not src.is_absolute():
        src = (base / src)
    src = src.resolve()
    if not src.is_file():
        raise PrintError(f"File not found: {src}", "bad_args")
    if src.suffix.lower() not in IMAGE_EXT:
        raise PrintError(f"Unsupported file type {src.suffix}; use PDF, PNG, JPG, WEBP, SVG or html.", "bad_args")
    rel = os.path.relpath(src, base).replace(os.sep, "/")
    if rel.startswith(".."):
        raise PrintError(f"{src} must be inside the layout folder {base}. Pass out= in a folder that contains all files.",
                         "bad_args")
    url = quote(rel)
    if src.suffix.lower() == ".pdf":
        url += f"?page={int(item.get('page') or 1)}"
    fit = "contain" if item.get("fit") == "contain" else "fill"
    return f'<img src="{url}" style="display:block;width:100%;height:100%;object-fit:{fit}">'


def layout(items, sheet="A4", landscape=False, margin_mm=5, gap_mm=0, crop_marks=True, css="", out=None, title="layout"):
    """Packs items onto sheets and writes one HTML file per paper group. Returns the plan."""
    if not items:
        raise PrintError("No items.", "bad_args")
    W, H = _sheet_size(sheet, landscape)
    margin, gap = float(margin_mm), float(gap_mm)
    if out:
        out = Path(out).resolve()
        if out.suffix.lower() != ".html":
            out = out / f"{title}.html"
    else:
        from .profiles import data_dir
        d = data_dir() / "layouts"
        d.mkdir(exist_ok=True)
        out = d / f"{time.strftime('%m%d-%H%M%S')}-{title}.html"
    base = out.parent
    base.mkdir(parents=True, exist_ok=True)

    groups, units = {}, 0
    for i, it in enumerate(items):
        if not (it.get("html") or it.get("src")):
            raise PrintError(f"Item {i} needs 'src' (pdf/image file) or 'html'.", "bad_args")
        try:
            w, h = float(it["width_mm"]), float(it["height_mm"])
        except (KeyError, TypeError, ValueError):
            raise PrintError(f"Item {i} needs width_mm and height_mm.", "bad_args")
        copies = max(1, int(it.get("copies") or 1))
        units += copies
        if units > MAX_UNITS:
            raise PrintError(f"More than {MAX_UNITS} items in one layout.", "bad_args")
        g = str(it.get("group") or "default")
        name = str(it.get("name") or f"item {i + 1}")
        inner = _content(it, base)
        for c in range(copies):
            groups.setdefault(g, []).append({"name": name, "w": w, "h": h, "inner": inner,
                                             "rot_ok": it.get("rotate", True) is not False})

    files = []
    for g, us in groups.items():
        sheets = pack(us, W, H, margin, gap)
        parts = []
        for si, sh in enumerate(sheets, 1):
            boxes = []
            for p in sh:
                cut = " data-cut" if crop_marks else ""
                if p["rotated"]:
                    inner = (f'<div style="position:absolute;left:0;top:0;width:{p["w"]}mm;height:{p["h"]}mm;'
                             f'transform-origin:0 0;transform:translate({p["pw"]}mm,0) rotate(90deg)">{p["inner"]}</div>')
                else:
                    inner = p["inner"]
                boxes.append(f'<div class="ps-item"{cut} data-item="{_html.escape(p["name"])}" style="left:{p["x"]}mm;'
                             f'top:{p["y"]}mm;width:{p["pw"]}mm;height:{p["ph"]}mm">{inner}</div>')
            parts.append(f'<section class="ps-sheet" data-name="{_html.escape(g)} {si}/{len(sheets)}" '
                         f'style="width:{W}mm;height:{H}mm">\n' + "\n".join(boxes) + "\n</section>")
        f = out if len(groups) == 1 else out.with_name(f"{out.stem}-{_safe(g)}{out.suffix}")
        doc = ("<!doctype html><html><head><meta charset='utf-8'><style>"
               ".ps-item{position:absolute;overflow:hidden;background:#fff}" + (css or "") + "</style></head><body>\n"
               + "\n".join(parts) + "\n</body></html>")
        f.write_text(doc, "utf-8")
        area = sum(p["pw"] * p["ph"] for sh in sheets for p in sh)
        counts = {}
        for sh in sheets:
            for p in sh:
                counts[p["name"]] = counts.get(p["name"], 0) + 1
        files.append({"group": g, "path": str(f), "sheets": len(sheets), "items": counts,
                      "paper_used_pct": round(100 * area / (len(sheets) * W * H), 1),
                      "per_sheet": [len(sh) for sh in sheets]})
    return {"sheet_mm": [W, H], "groups": files,
            "next": "Run proof on each file with the profile for that paper group, then print_job."}


def _safe(s):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:40] or "group"
