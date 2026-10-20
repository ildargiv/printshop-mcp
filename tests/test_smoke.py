"""Smoke test on Windows without a physical printer: renders the example and prints it to a PDF file."""
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ["PRINTSHOP_HOME"] = tempfile.mkdtemp()
import pytest                                            # noqa: E402

from printshop_mcp import jobs, win                      # noqa: E402
from printshop_mcp.profiles import ProfileStore          # noqa: E402

PDF = "Microsoft Print to PDF"
EX = Path(__file__).parent.parent / "examples" / "badges.html"


def need_pdf_printer():
    if PDF not in win.list_printers():
        pytest.skip("Microsoft Print to PDF is not installed")


def test_profile_and_print_to_pdf():
    need_pdf_printer()
    store = ProfileStore()
    store.save("pdf calibrated", devmode=win.default_devmode(PDF), printer=PDF, scale_x=1.01, offset_y_mm=-1.5,
               tags=["test"])
    store.set_default("pdf calibrated")
    job = jobs.preflight(path=str(EX))
    assert job["profile"] == "pdf calibrated" and job["printer"] == PDF
    assert job["sheets"][0]["size_mm"] == [210, 297]
    assert any("pixelated" in w for w in job["warnings"])
    assert any("Константинопольский" in w for w in job["warnings"])
    out = Path(os.environ["PRINTSHOP_HOME"]) / "out.pdf"
    res = jobs.print_job(job["job_id"], accept_warnings=True, output=str(out))
    assert res["status"] == "sent" and res["sheets_sent"] == 1
    box = re.search(rb"MediaBox\s*\[\s*0(?:\.0+)?\s+0(?:\.0+)?\s+([\d.]+)\s+([\d.]+)", out.read_bytes())
    assert abs(float(box[1]) - 595.28) < 1 and abs(float(box[2]) - 841.89) < 1   # A4 in points
    assert store.get("pdf calibrated")["uses"] == 1
    assert job["estimate"]["sheets"] == 1 and job["sheets"][0]["coverage_pct"]["total"] > 0
    try:
        jobs.print_job(job["job_id"], accept_warnings=True, output=str(out))
        raise AssertionError("printed twice")
    except win.PrintError as e:
        assert e.code == "already_printed"


def test_mirror_for_sublimation():
    need_pdf_printer()
    import pypdfium2 as pdfium
    home = Path(os.environ["PRINTSHOP_HOME"])
    (home / "m.html").write_text('<section class="ps-sheet" style="width:210mm;height:297mm"><div style="position:absolute;'
                                 'left:10mm;top:10mm;width:40mm;height:40mm;background:#000"></div></section>', "utf-8")
    ProfileStore().save("transfer", devmode=win.default_devmode(PDF), printer=PDF, mirror=True)
    job = jobs.preflight(path=str(home / "m.html"), profile="transfer")
    jobs.print_job(job["job_id"], output=str(home / "m.pdf"))
    img = pdfium.PdfDocument(str(home / "m.pdf"))[0].render(scale=1).to_pil().convert("L")
    W, H = img.size
    assert img.getpixel((int(W * .14), int(H * .1))) > 200 and img.getpixel((int(W * .86), int(H * .1))) < 50


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("Windows only")
    test_profile_and_print_to_pdf()
    test_mirror_for_sublimation()
    print("ok")
