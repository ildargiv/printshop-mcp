"""Imposition and PDF input. Packing tests are pure Python; render tests need Windows + Edge/Chrome."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("PRINTSHOP_HOME", tempfile.mkdtemp())
from PIL import Image, ImageDraw                         # noqa: E402

from printshop_mcp import impose, jobs                    # noqa: E402
from printshop_mcp.win import PrintError                  # noqa: E402

PDF = "Microsoft Print to PDF"


def units(name, w, h, n):
    return [{"name": name, "w": w, "h": h, "rot_ok": True} for _ in range(n)]


def check(sheets, W=210, H=297, m=5):
    for sh in sheets:
        for i, a in enumerate(sh):
            assert a["x"] >= m - 0.01 and a["y"] >= m - 0.01
            assert a["x"] + a["pw"] <= W - m + 0.01 and a["y"] + a["ph"] <= H - m + 0.01
            for b in sh[i + 1:]:
                assert (a["x"] + a["pw"] <= b["x"] + 1e-6 or b["x"] + b["pw"] <= a["x"] + 1e-6 or
                        a["y"] + a["ph"] <= b["y"] + 1e-6 or b["y"] + b["ph"] <= a["y"] + 1e-6), "overlap"


def test_pack_counts():
    s = impose.pack(units("badge", 90, 55, 40), 210, 297, 5, 0)
    check(s)
    assert [len(x) for x in s] == [10, 10, 10, 10]
    s = impose.pack(units("card", 90, 50, 10), 210, 297, 5, 0)
    check(s)
    assert len(s) == 1 and not any(p["rotated"] for p in s[0])
    s = impose.pack(units("flyer", 105, 148, 1) + units("badge", 90, 55, 3) + units("card", 90, 50, 4), 210, 297, 5, 0)
    check(s)
    assert len(s) == 1
    s = impose.pack(units("card", 90, 50, 37) + units("badge", 90, 55, 23), 210, 297, 5, 3)
    check(s)


def test_too_big():
    try:
        impose.pack(units("poster", 300, 400, 1), 210, 297, 5, 0)
        raise AssertionError("should not fit")
    except PrintError as e:
        assert e.code == "too_big"


def test_layout_and_pdf_render():
    d = Path(tempfile.mkdtemp())
    w, h = round(105 / 25.4 * 300), round(148 / 25.4 * 300)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).rectangle((60, 60, w - 60, h // 2), fill=(30, 80, 160))
    im.save(d / "flyer.pdf", resolution=300)
    from printshop_mcp import pdf
    w_mm, h_mm = pdf.page_sizes_mm(d / "flyer.pdf")[0]
    assert abs(w_mm - 105) < 0.2 and abs(h_mm - 148) < 0.2
    items = [{"name": "badge", "width_mm": 90, "height_mm": 55, "group": "plain",
              "html": f'<div style="position:absolute;inset:0;font:20pt Arial"><b data-fit="9pt" '
                      f'style="position:absolute;left:4mm;right:4mm;top:15mm;white-space:nowrap;overflow:hidden">{n}</b></div>'}
             for n in ["Anna", "Konstantin Konstantinopolsky", "王小明"]]
    items.append({"name": "flyer", "width_mm": 105, "height_mm": 148, "group": "plain", "src": "flyer.pdf"})
    items.append({"name": "card", "width_mm": 90, "height_mm": 50, "copies": 10, "group": "card",
                  "html": '<div style="position:absolute;inset:0;border-left:6mm solid #034">Card</div>'})
    plan = impose.layout(items, out=str(d / "kit.html"))
    assert {g["group"] for g in plan["groups"]} == {"plain", "card"}
    for g in plan["groups"]:
        j = jobs.preflight(path=g["path"], printer=PDF)
        assert j["status"] == "ready", j["warnings"] + j["errors"]


if __name__ == "__main__":
    test_pack_counts()
    test_too_big()
    if sys.platform == "win32":
        test_layout_and_pdf_render()
    print("ok")
