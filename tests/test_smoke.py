"""Smoke test on Windows without a physical printer: renders the example and prints it to a PDF file."""
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ["PRINTSHOP_HOME"] = tempfile.mkdtemp()
from printshop_mcp import jobs, win                      # noqa: E402
from printshop_mcp.profiles import ProfileStore          # noqa: E402

PDF = "Microsoft Print to PDF"
EX = Path(__file__).parent.parent / "examples" / "badges.html"


def test_profile_and_print_to_pdf():
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
    try:
        jobs.print_job(job["job_id"], accept_warnings=True, output=str(out))
        raise AssertionError("printed twice")
    except win.PrintError as e:
        assert e.code == "already_printed"


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("Windows only")
    test_profile_and_print_to_pdf()
    print("ok")
