"""Proof -> preflight -> print. Printing is only possible for a job that passed preflight (the job id is the token)."""
import io
import json
import os
import time
import uuid
from pathlib import Path

from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps

from . import win
from .profiles import ProfileStore, data_dir
from .render import render_sheets
from .win import PrintError

JOB_TTL = 3600          # seconds a proofed job stays printable
LOW_DPI, BAD_DPI = 200, 120
INTENTS = {"perceptual": 0, "relative": 1, "saturation": 2, "absolute": 3}


def max_sheets():
    return int(os.environ.get("PRINTSHOP_MAX_SHEETS", "50"))


def _jobs_dir():
    d = data_dir() / "jobs"
    d.mkdir(exist_ok=True)
    return d


def _cleanup():
    now = time.time()
    for j in _jobs_dir().iterdir():
        try:
            if now - j.stat().st_mtime > 7 * 86400:
                for f in j.iterdir():
                    f.unlink()
                j.rmdir()
        except OSError:
            pass


def _content_bbox_mm(img, dpi):
    """Bounding box of non-white pixels, mm."""
    g = ImageOps.invert(img.convert("L")).point(lambda v: 255 if v > 6 else 0)
    b = g.getbbox()
    return None if b is None else [round(v * 25.4 / dpi, 1) for v in b]


def _driver_blob(printer, prof, w, h):
    store = ProfileStore()
    base = store.devmode(prof["name"]) if prof and prof.get("devmode") else win.default_devmode(printer)
    p = prof or {}
    blob = win.patch_devmode(
        base, orientation="landscape" if w > h else "portrait",
        paper=None if p.get("paper") == "driver" else (w, h),
        icm_off=bool(p.get("icc")), source=p.get("tray"), media=p.get("media"), quality=p.get("quality"),
        color=p.get("color"), duplex=p.get("duplex"))
    return win.merge_devmode(printer, blob)


def _label_font():
    """A TrueType font with Cyrillic and other scripts; Pillow's built-in bitmap font is ASCII-only."""
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf", "Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            return ImageFont.truetype(name, 13)
        except OSError:
            pass
    return ImageFont.load_default()


def _proof_image(img, sheet, geom, issues, dpi, label):
    W, H = img.size
    k = min(1.0, 1100 / max(W, H))
    pv = img.resize((max(1, round(W * k)), max(1, round(H * k))), Image.Resampling.LANCZOS).convert("RGBA")
    ov = Image.new("RGBA", pv.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    px = lambda mm: mm / 25.4 * dpi * k
    if geom:
        l, t, r, b = geom["printable_mm"]
        pw, ph = pv.size
        for box in ((0, 0, pw, px(t)), (0, px(b), pw, ph), (0, 0, px(l), ph), (px(r), 0, pw, ph)):
            if box[2] > box[0] and box[3] > box[1]:
                d.rectangle(box, fill=(90, 90, 90, 110))
    for it in issues:
        if it.get("box_mm"):
            x0, y0, x1, y1 = it["box_mm"]
            col = (220, 30, 30, 255) if it["level"] == "error" else (240, 140, 0, 255)
            d.rectangle((px(x0), px(y0), px(x1), px(y1)), outline=col, width=3)
    out = Image.alpha_composite(pv, ov).convert("RGB")
    bar = Image.new("RGB", (out.width, 24), (30, 30, 30))
    ImageDraw.Draw(bar).text((6, 4), label, fill=(255, 255, 255), font=_label_font())
    canvas = Image.new("RGB", (out.width, out.height + 24), "white")
    canvas.paste(bar, (0, 0))
    canvas.paste(out, (0, 24))
    return canvas


def preflight(html=None, path=None, printer=None, profile=None, copies=1, dpi=None):
    """Renders the HTML, checks it against the printer/profile and returns a printable job with proofs."""
    _cleanup()
    if bool(html) == bool(path):
        raise PrintError("Pass either html or path.", "bad_args")
    if path:
        f = Path(path).resolve()
        if not f.is_file():
            raise PrintError(f"File not found: {f}", "bad_args")
        html, base_dir = f.read_text("utf-8"), f.parent
    else:
        base_dir = Path(os.environ.get("PRINTSHOP_ASSETS", os.getcwd()))
    copies = max(1, int(copies or 1))

    store = ProfileStore()
    prof = store.resolve(profile, printer)
    if prof and printer and prof["printer"] != printer:
        raise PrintError(f"Profile '{prof['name']}' belongs to printer '{prof['printer']}', not '{printer}'.", "bad_args")
    printer = printer or (prof and prof["printer"]) or win.default_printer()
    win.check_printer(printer)
    dpi = int(dpi or (prof or {}).get("dpi") or 300)
    dpi = max(150, min(720, dpi))

    images, info = render_sheets(html, base_dir, dpi)
    job_id = time.strftime("%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    jdir = _jobs_dir() / job_id
    jdir.mkdir()

    sheets, errors, warnings, proofs, geoms = [], [], [], [], {}
    for img, sh in zip(images, info):
        n = sh["index"] + 1
        w, h = sh["size_mm"]
        issues = []
        key = (round(w), round(h))
        if key not in geoms:
            blob = _driver_blob(printer, prof, w, h)
            geoms[key] = (blob, win.printer_geometry(printer, blob))
        blob, geom = geoms[key]
        pw, ph = geom["paper_mm"]
        if abs(pw - w) > 1.5 or abs(ph - h) > 1.5:
            issues.append({"level": "error", "msg": f"sheet is {w}x{h} mm but the printer paper is {pw}x{ph} mm "
                                                    f"(set the sheet size or the profile paper)"})
        l, t, r, b = geom["printable_mm"]
        cb = _content_bbox_mm(img, dpi)
        if cb:
            cut = {"left": l - cb[0], "top": t - cb[1], "right": cb[2] - r, "bottom": cb[3] - b}
            cut = {k: round(v, 1) for k, v in cut.items() if v > 0.2}
            if cut:
                issues.append({"level": "warning", "msg": "content reaches the unprintable margin and will be cut: " +
                               ", ".join(f"{k} {v} mm" for k, v in cut.items())})
        for im in sh["images"]:
            if not im["loaded"]:
                issues.append({"level": "error", "msg": f"image not loaded: {im['element']}", "box_mm": im["box_mm"]})
            elif im["dpi"] < BAD_DPI:
                issues.append({"level": "warning", "msg": f"image will look pixelated ({im['dpi']} dpi): {im['element']}",
                               "box_mm": im["box_mm"]})
            elif im["dpi"] < LOW_DPI:
                issues.append({"level": "warning", "msg": f"low image resolution ({im['dpi']} dpi): {im['element']}",
                               "box_mm": im["box_mm"]})
        for c in sh["clipped"]:
            issues.append({"level": "warning", "msg": f"content does not fit its box and is clipped: {c['element']}",
                           "box_mm": c["box_mm"]})
        for c in sh["outside"][:10]:
            issues.append({"level": "warning", "msg": f"element sticks out of the sheet: {c['element']}", "box_mm": c["box_mm"]})

        img.save(jdir / f"sheet-{n}.png")
        label = f"sheet {n}/{len(images)}  {w}x{h} mm  {printer}" + (f"  [{prof['name']}]" if prof else "")
        pv = _proof_image(img, sh, geom, issues, dpi, label)
        pv.save(jdir / f"proof-{n}.png")
        proofs.append(str(jdir / f"proof-{n}.png"))
        for it in issues:
            (errors if it["level"] == "error" else warnings).append(f"sheet {n}: {it['msg']}")
        sheets.append({"sheet": n, "name": sh["name"], "size_mm": [w, h], "orientation": "landscape" if w > h else "portrait",
                       "printable_mm": geom["printable_mm"], "device_dpi": geom["dpi"], "content_mm": cb,
                       "images": len(sh["images"]), "issues": len(issues)})

    total = len(images) * copies
    if total > max_sheets():
        errors.append(f"{total} sheets exceeds the limit of {max_sheets()} (env PRINTSHOP_MAX_SHEETS).")
    job = {"job_id": job_id, "created": time.time(), "printer": printer, "profile": prof["name"] if prof else None,
           "dpi": dpi, "copies": copies, "total_sheets": total, "sheets": sheets, "errors": errors, "warnings": warnings,
           "status": "blocked" if errors else ("needs_confirmation" if warnings else "ready"), "proofs": proofs}
    (jdir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), "utf-8")
    if not prof:
        job["tip"] = ("No saved profile for this printer: default driver settings are used. "
                      "Use save_profile to remember paper, tray, media and quality.")
    return job


def _calibrate(img, prof, dpi):
    sx, sy = prof.get("scale_x", 1.0), prof.get("scale_y", 1.0)
    ox, oy = prof.get("offset_x_mm", 0.0), prof.get("offset_y_mm", 0.0)
    if abs(sx - 1) < 1e-4 and abs(sy - 1) < 1e-4 and abs(ox) < 0.01 and abs(oy) < 0.01:
        return img
    W, H = img.size
    nw, nh = round(W * sx), round(H * sy)
    src = img.resize((nw, nh), Image.Resampling.LANCZOS) if (nw, nh) != (W, H) else img
    out = Image.new("RGB", (W, H), "white")
    out.paste(src, (round((W - nw) / 2 + ox / 25.4 * dpi), round((H - nh) / 2 + oy / 25.4 * dpi)))
    return out


def _color(img, prof):
    icc = prof.get("icc")
    if not icc:
        return img
    if not Path(icc).is_file():
        raise PrintError(f"ICC profile not found: {icc}", "bad_profile")
    t = ImageCms.buildTransform(ImageCms.createProfile("sRGB"), ImageCms.ImageCmsProfile(icc), "RGB", "RGB",
                                renderingIntent=INTENTS.get(prof.get("intent") or "relative", 1), flags=0x2000)
    return ImageCms.applyTransform(img, t)


def print_job(job_id, accept_warnings=False, output=None):
    jdir = _jobs_dir() / str(job_id)
    if not (jdir / "job.json").is_file():
        raise PrintError(f"Unknown job '{job_id}'. Run proof first.", "no_job")
    job = json.loads((jdir / "job.json").read_text("utf-8"))
    if time.time() - job["created"] > JOB_TTL:
        raise PrintError("Job expired. Run proof again.", "expired")
    if job["errors"]:
        raise PrintError("Job has errors and cannot be printed: " + "; ".join(job["errors"]), "blocked")
    if job["warnings"] and not accept_warnings:
        raise PrintError("Job has warnings. Show them to the user; to print anyway pass accept_warnings=true: "
                         + "; ".join(job["warnings"]), "needs_confirmation")
    if job.get("printed"):
        raise PrintError("Job already printed. Run proof again to print once more.", "already_printed")
    if os.environ.get("PRINTSHOP_DRYRUN") == "1":
        return {"job_id": job_id, "status": "dry_run", "would_print_sheets": job["total_sheets"]}

    store = ProfileStore()
    prof = store.get(job["profile"]) if job["profile"] else {}
    printer, dpi = job["printer"], job["dpi"]
    # consecutive sheets with the same paper/orientation go into one spooler document
    seq = [sh for _ in range(job["copies"]) for sh in job["sheets"]]
    groups = []
    for sh in seq:
        key = tuple(round(v) for v in sh["size_mm"])
        if groups and groups[-1][0] == key:
            groups[-1][1].append(sh)
        else:
            groups.append((key, [sh]))
    blobs, sent = {}, 0
    for gi, (key, group) in enumerate(groups, 1):
        if key not in blobs:
            blobs[key] = _driver_blob(printer, prof or None, *group[0]["size_mm"])
        out = None
        if output:
            o = Path(output)
            out = str(o if len(groups) == 1 else o.with_name(f"{o.stem}-{gi}{o.suffix}"))
        with win.PrinterJob(printer, blobs[key], f"printshop {job_id}", output=out) as pj:
            for sh in group:
                img = Image.open(jdir / f"sheet-{sh['sheet']}.png").convert("RGB")
                pj.page(_calibrate(_color(img, prof), prof, dpi))
                sent += 1
            pj.finish()
    job["printed"] = time.time()
    (jdir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1), "utf-8")
    store.mark_used(job["profile"], printer)
    res = {"job_id": job_id, "status": "sent", "printer": printer, "profile": job["profile"], "sheets_sent": sent}
    if not job["profile"]:
        res["tip"] = "Ask the user if the result looks right, then save_profile so these settings are remembered."
    else:
        res["tip"] = "Ask the user if the result looks right. If not, adjust the profile (calibration/paper/media)."
    return res
