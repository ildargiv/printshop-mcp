"""Job estimate: paper, ink coverage measured on the rendered pixels, and cost when the profile has prices.

Coverage uses a simple RGB -> CMYK split (K = 1 - max(R,G,B)), averaged over the whole sheet. It is an estimate,
not a colour-managed ink calculation, but it is measured on what will actually print rather than guessed.
"""
from PIL import Image

A4_MM2 = 210 * 297
ISO_PCT = 5.0              # ink yields on boxes are quoted for pages with 5% coverage (ISO/IEC 24711 / 19752)


def coverage(img):
    """Average ink coverage per channel, % of the sheet: {"c", "m", "y", "k", "total"}."""
    im = img.convert("RGB")
    w, h = im.size
    k = 220 / max(w, h)
    if k < 1:
        im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.Resampling.BOX)
    sc = sm = sy = sk = 0.0
    n = 0
    for r, g, b in im.getdata():
        n += 1
        mx = max(r, g, b)
        kk = 255 - mx
        if mx == 0:
            sk += 1.0
            continue
        sc += (mx - r) / mx
        sm += (mx - g) / mx
        sy += (mx - b) / mx
        sk += kk / 255
    out = {ch: round(100 * v / n, 1) for ch, v in (("c", sc), ("m", sm), ("y", sy), ("k", sk))}
    out["total"] = round(sum(out.values()), 1)
    return out


def job_estimate(sheets, copies, prof):
    """sheets: [{"size_mm": [w, h], "coverage_pct": {...}}]. Money only when the profile has prices."""
    paper_price = (prof or {}).get("paper_price")
    ink_price = (prof or {}).get("ink_price_5pct")
    cur = (prof or {}).get("currency") or ""
    ink_units = 0.0                       # ink in "A4 pages at 5% coverage"
    for s in sheets:
        area = s["size_mm"][0] * s["size_mm"][1] / A4_MM2
        ink_units += s["coverage_pct"]["total"] / ISO_PCT * area
    ink_units *= copies
    total_sheets = len(sheets) * copies
    est = {"sheets": total_sheets, "ink_equivalent_iso_pages": round(ink_units, 1),
           "avg_coverage_pct": round(sum(s["coverage_pct"]["total"] for s in sheets) / max(1, len(sheets)), 1)}
    if paper_price is not None or ink_price is not None:
        paper = total_sheets * float(paper_price or 0)
        ink = ink_units * float(ink_price or 0)
        est.update({"paper_cost": round(paper, 2), "ink_cost": round(ink, 2), "total_cost": round(paper + ink, 2),
                    "currency": cur})
        if paper_price is None or ink_price is None:
            est["note"] = "Partial: set both paper_price and ink_price_5pct in the profile for a full cost."
    else:
        est["note"] = ("No prices in the profile. Set paper_price (per sheet) and ink_price_5pct (ink cost of one A4 "
                       "page at 5% coverage of one colour = bottle/cartridge price / ISO page yield on the box) to get costs.")
    return est
