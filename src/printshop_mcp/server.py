"""MCP server: the print shop inside your agent."""
import json

import anyio
try:                                   # mcp 2.x
    from mcp.server.mcpserver import Image, MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:                    # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer, Image
    from mcp.server.fastmcp.exceptions import ToolError

from . import impose, jobs, win
from .profiles import ProfileStore, public

GUIDE = """# printshop-mcp: how to write printable HTML

Every physical sheet is one element with class `ps-sheet` and an explicit size in mm:

    <section class="ps-sheet" style="width:210mm;height:297mm"> ... </section>

* Use mm for all layout (`position:absolute; left:10mm; top:12mm; width:90mm`). 1 mm in CSS = 1 mm on paper.
* Landscape sheet = width > height (e.g. 297mm x 210mm). The driver orientation is set automatically.
* Optional `data-name="Badges"` labels a sheet in proofs and reports.
* Images: paths relative to the HTML file (or to PRINTSHOP_ASSETS for inline html). Aim for >= 250 dpi.
* Keep important content inside the printable area reported by describe_printer / proof (grey zone on proofs).
* Text that may be long (names!) should shrink to fit: give boxes fixed size and `overflow:hidden` - the proof
  then reports clipped boxes so you can fix font sizes before printing.
* Crop marks, gaps for cutting and bleed are plain HTML/CSS for now (automatic mixed layout is coming).
"""

INSTRUCTIONS = """printshop-mcp prints HTML to real printers with millimetre accuracy and REMEMBERS the user's print profiles.

Workflow:
1. Start with list_profiles: profiles hold everything about a printer + paper setup (driver settings incl. vendor
   options, tray, media, quality, colour profile, calibration). Pick the one that fits the task (see tags/notes);
   ask the user when unsure. Read printshop://guide before writing HTML.
2. When the user mentions a new setup ("thick cardstock in the rear tray", "glossy photo paper"), save it with
   save_profile. If vendor-specific options matter, use open_driver_dialog=true so the user sets them once in the
   driver window - they are remembered forever.
   Many items (badges per guest, cards, flyers, PDFs from other tools)? Use layout: it packs them onto sheets.
3. proof -> look at the proof images and warnings -> fix the HTML or tell the user -> print_job(job_id).
   Never pass accept_warnings=true without telling the user what the warnings are.
4. After printing ask whether the result is right. Size or position off? Update the profile calibration
   (scale_x/scale_y, offset_x_mm/offset_y_mm) so every future job is corrected automatically."""

mcp = MCPServer("printshop", instructions=INSTRUCTIONS)
store = ProfileStore()


async def _run(fn, *a, **kw):
    """Runs blocking work (Playwright, printer driver) off the event loop; errors reach the agent as readable text."""
    try:
        return await anyio.to_thread.run_sync(lambda: fn(*a, **kw))
    except win.PrintError as e:
        raise ToolError(f"[{e.code}] {e}") from e
    except Exception as e:
        raise ToolError(f"[internal] {type(e).__name__}: {e}") from e


def _pick(options, value, what):
    """Driver option by code or by (part of) its name."""
    if value is None or value == "":
        return None
    if isinstance(value, int) or str(value).isdigit():
        return int(value)
    v = str(value).lower()
    hits = [o for o in options if v == o["name"].lower()] or [o for o in options if v in o["name"].lower()]
    if len(hits) != 1:
        names = ", ".join(o["name"] for o in options) or "none"
        raise win.PrintError(f"{what} '{value}' is {'ambiguous' if hits else 'unknown'}. Available: {names}", "bad_args")
    return hits[0]["code"]


@mcp.resource("printshop://guide")
def guide() -> str:
    """How to write printable HTML."""
    return GUIDE


@mcp.tool(structured_output=False)
async def list_printers() -> str:
    """Installed printers with their saved profiles. The first printer is the Windows default."""
    def go():
        db = store.all()
        out = []
        for i, n in enumerate(win.list_printers()):
            out.append({"name": n, "windows_default": i == 0,
                        "profiles": [k for k, p in db["profiles"].items() if p["printer"] == n],
                        "default_profile": db["defaults"].get(n)})
        return out
    return json.dumps(await _run(go), ensure_ascii=False)


@mcp.tool(structured_output=False)
async def describe_printer(printer: str) -> str:
    """Papers, trays, media types, resolutions and printable area (A4) of a printer, plus its saved profiles."""
    def go():
        win.check_printer(printer)
        caps = win.printer_capabilities(printer)
        blob = win.merge_devmode(printer, win.patch_devmode(win.default_devmode(printer), "portrait", (210, 297)))
        caps["a4_geometry"] = win.printer_geometry(printer, blob)
        caps["profiles"] = [public(p) for p in store.all()["profiles"].values() if p["printer"] == printer]
        return caps
    return json.dumps(await _run(go), ensure_ascii=False)


@mcp.tool(structured_output=False)
async def list_profiles(printer: str | None = None) -> str:
    """All remembered print profiles (optionally for one printer) and the default profile of each printer."""
    db = await _run(store.all)
    profs = [public(p) for p in db["profiles"].values() if not printer or p["printer"] == printer]
    return json.dumps({"profiles": profs, "default_profile_per_printer": db["defaults"],
                       "last_printer": db.get("default_printer")}, ensure_ascii=False)


@mcp.tool(structured_output=False)
async def save_profile(name: str, printer: str | None = None, paper: str | None = None, tray: str | None = None,
                       media: str | None = None, quality: str | None = None, color: str | None = None,
                       duplex: str | None = None, icc: str | None = None, intent: str | None = None,
                       dpi: int | None = None, scale_x: float | None = None, scale_y: float | None = None,
                       offset_x_mm: float | None = None, offset_y_mm: float | None = None,
                       tags: list[str] | None = None, notes: str | None = None,
                       mirror: bool | None = None, open_driver_dialog: bool = False, make_default: bool = False) -> str:
    """Create or update a remembered print profile. Only the given fields change.

    paper: "sheet" (paper size follows the HTML sheet, default) or "driver" (keep the paper set in the driver).
    tray / media: name (or part of it) or code from describe_printer. quality: draft|low|medium|high.
    color: color|mono. duplex: simplex|long_edge|short_edge. icc: path to a printer ICC profile, intent:
    perceptual|relative|saturation|absolute. dpi: render resolution (default 300).
    scale_x/scale_y (0.97-1.03) and offset_x_mm/offset_y_mm (-5..5): calibration applied to every job.
    mirror: print every sheet mirrored (sublimation / heat-transfer paper for mugs, T-shirts). Proofs stay readable.
    tags/notes: what this profile is for ("business cards", "cardstock 300g") so it can be found later.
    open_driver_dialog: shows the printer driver's own settings window to the user; everything they choose there,
    including vendor-only options, is stored in the profile.
    """
    def go():
        try:
            existing = store.get(name)
        except win.PrintError:
            existing = None
        prn = printer or (existing or {}).get("printer") or win.default_printer()
        win.check_printer(prn)
        if existing and existing["printer"] != prn:
            raise win.PrintError(f"Profile '{name}' belongs to '{existing['printer']}'. Use another name.", "bad_args")
        caps = win.printer_capabilities(prn) if (tray or media) else None
        devmode = None
        if open_driver_dialog:
            base = store.devmode(name) if existing and existing.get("devmode") else win.default_devmode(prn)
            devmode = win.driver_dialog(prn, base)
            if devmode is None:
                raise win.PrintError("The user cancelled the driver settings window; nothing saved.", "cancelled")
        elif not existing:
            devmode = win.default_devmode(prn)          # snapshot today's driver settings
        if paper not in (None, "sheet", "driver"):
            raise win.PrintError("paper must be 'sheet' or 'driver'.", "bad_args")
        p = store.save(name, devmode=devmode, printer=prn, paper=paper,
                       tray=_pick(caps["trays"], tray, "tray") if tray else None,
                       media=_pick(caps["media_types"], media, "media") if media else None,
                       quality=quality, color=color, duplex=duplex, icc=icc, intent=intent, dpi=dpi,
                       scale_x=scale_x, scale_y=scale_y, offset_x_mm=offset_x_mm, offset_y_mm=offset_y_mm,
                       mirror=mirror, tags=tags, notes=notes)
        if make_default:
            store.set_default(name)
        q = public(p)
        if p.get("devmode"):
            q["driver"] = win.devmode_summary(store.devmode(name))
        return q
    return json.dumps(await _run(go), ensure_ascii=False)


@mcp.tool(structured_output=False)
async def delete_profile(name: str) -> str:
    """Forget a print profile."""
    await _run(store.delete, name)
    return json.dumps({"deleted": name})


@mcp.tool(structured_output=False)
async def set_default_profile(name: str) -> str:
    """Make a profile the default for its printer (and that printer the default for printing)."""
    await _run(store.set_default, name)
    return json.dumps({"default": name})


@mcp.tool(structured_output=False)
async def proof(html: str | None = None, path: str | None = None, printer: str | None = None,
                profile: str | None = None, copies: int = 1, dpi: int | None = None) -> list:
    """Render printable HTML exactly as it will print and check it. Returns a job (job_id, errors, warnings,
    per-sheet geometry) and proof images: grey = area the printer cannot print, red/orange frames = problems.
    Give either html (a string) or path: an .html file (images resolve relative to it) or a .pdf
    (every page becomes a sheet of the page's size - use this to print PDFs made by other tools).
    Without printer/profile the default profile of the last used printer is taken."""
    job = await _run(jobs.preflight, html=html, path=path, printer=printer, profile=profile, copies=copies, dpi=dpi)
    out = [json.dumps({k: v for k, v in job.items() if k != "proofs"}, ensure_ascii=False)]
    for pth in job["proofs"][:4]:
        out.append(Image(path=pth))
    if len(job["proofs"]) > 4:
        out.append(f"{len(job['proofs']) - 4} more proof images on disk: " + ", ".join(job["proofs"][4:]))
    return out


@mcp.tool(structured_output=False)
async def layout(items: list[dict], sheet: str | list[float] = "A4", landscape: bool = False, margin_mm: float = 5,
                 gap_mm: float = 0, crop_marks: bool = True, css: str = "", out: str | None = None,
                 title: str = "layout") -> str:
    """Automatically pack many items onto sheets (imposition) and write printable HTML, one file per paper group.

    items: [{"name": "badge", "width_mm": 90, "height_mm": 55, "copies": 1, "group": "plain",
             "html": "<div ...>...</div>"  OR  "src": "card.pdf" | "photo.jpg", "page": 1,
             "rotate": true, "fit": "fill"|"contain"}]
      - html: the item's design, filling its box (use position:absolute children, mm units, data-fit). Shared
        styles go into css. One entry per distinct item (e.g. one per guest), copies for identical ones.
      - src: a PDF page or image (e.g. a business card PDF from another tool), path relative to out's folder.
      - group: items that need different paper (cardstock vs plain) must have different groups; each group
        becomes its own file to proof and print with its own profile.
    sheet: A4, A3, A5, Letter, Legal, Tabloid or [width_mm, height_mm]. margin_mm: keep >= printer margin (~4).
    gap_mm: space between items (0 = shared cut lines). Items rotate automatically when that saves paper.
    out: .html path (or folder) for the result; must contain any src files. Returns files, sheet counts, paper use."""
    res = await _run(impose.layout, items, sheet=sheet, landscape=landscape, margin_mm=margin_mm, gap_mm=gap_mm,
                     crop_marks=crop_marks, css=css, out=out, title=title)
    return json.dumps(res, ensure_ascii=False)


@mcp.tool(structured_output=False)
async def print_job(job_id: str, accept_warnings: bool = False) -> str:
    """Send a proofed job to the printer. Requires a job_id from proof. If the proof had warnings, tell the user
    first and pass accept_warnings=true only after they agree."""
    return json.dumps(await _run(jobs.print_job, job_id, accept_warnings), ensure_ascii=False)


@mcp.tool(structured_output=False)
async def printer_status(printer: str) -> str:
    """Printer state (offline, out of paper, jammed...) and its print queue."""
    return json.dumps(await _run(win.spooler_status, printer), ensure_ascii=False)


def main():
    mcp.run()
