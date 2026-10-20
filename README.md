# printshop-mcp

[![CI](https://github.com/ildargiv/printshop-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ildargiv/printshop-mcp/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**English** · [Русский](docs/i18n/README.ru.md) · [简体中文](docs/i18n/README.zh-CN.md) · [Español](docs/i18n/README.es.md) · [Português](docs/i18n/README.pt-BR.md) · [Deutsch](docs/i18n/README.de.md) · [Français](docs/i18n/README.fr.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md) · [Italiano](docs/i18n/README.it.md) · [Türkçe](docs/i18n/README.tr.md) · [Polski](docs/i18n/README.pl.md) · [Українська](docs/i18n/README.uk.md) · [العربية](docs/i18n/README.ar.md) · [हिन्दी](docs/i18n/README.hi.md)

🌐 **[ildargiv.github.io/printshop-mcp](https://ildargiv.github.io/printshop-mcp/)**

**The print shop inside your AI agent.** Ask for "badges for these 40 guests, business cards and a flyer" and the
agent designs them, packs them onto sheets, shows you an exact proof and prints them on **your real printer** -
millimetre-accurate. And it **remembers all your print profiles**: printer, paper, tray, media type, quality,
colour profile, calibration, even vendor-only driver options. Explain your printer once, never again.

<p align="center"><img src="docs/event-kit-a4-proof.png" width="420" alt="Proof of a mixed A4 sheet: flyer, badges and business cards with crop marks"></p>

*A mixed sheet (1 flyer + 3 badges + 4 business cards) as the agent sees it before printing: crop marks only where you cut,
long names shrunk to fit, grey border = what your printer can't print.*

> Status: v0.2, Windows. New: print any PDF (e.g. from other design skills) and automatic layout of many items.
> Next: self-learning from print defects, macOS/Linux.

## Printer compatibility

**For paper printers: inkjet, laser, photo, sublimation (souvenir transfer printing) and label printers. Not for 3D printers.**

Works with any printer that has a Windows driver, whatever the brand: printing goes through the standard Windows print system, and vendor-only options (paper types, borderless, print quality) are kept in profiles through the driver's own settings window.

| Printer type | Brands |
|---|---|
| Inkjet | Epson · Canon · HP · Brother |
| Laser and MFP | HP · Brother · Canon · Kyocera · Xerox · Ricoh · Konica Minolta · Sharp · Lexmark · OKI · Pantum · Samsung |
| Photo (inkjet and dye-sub photo) | Epson · Canon · HP · DNP · Mitsubishi · Citizen · Canon Selphy |
| Sublimation (souvenirs: mugs, T-shirts, puzzles) | Epson EcoTank / SureColor F (with sublimation ink) · Sawgrass · Ricoh |
| Label / thermal | Zebra · TSC · Brother QL · Dymo · Xprinter |

Verified so far:

| Printer | Type | Status |
|---|---|---|
| Microsoft Print to PDF | virtual | ✅ full test suite |
| Epson L8050 | inkjet, photo | ✅ trays, media types, margins detected · test print pending |

Printed with another model? [Report it](https://github.com/ildargiv/printshop-mcp/issues/new?template=printer-report.yml) and it gets added here. macOS and Linux (CUPS) are planned.

## Install

**Claude Code** (skill + MCP server in one plugin):

```
/plugin marketplace add ildargiv/printshop-mcp
/plugin install printshop@printshop-mcp
```

**Any MCP client** (Claude Desktop, Cursor, Codex, ...):

```json
{ "mcpServers": { "printshop": { "command": "uvx",
    "args": ["--from", "git+https://github.com/ildargiv/printshop-mcp", "printshop-mcp"] } } }
```

Pin a release instead of the latest code: `git+https://github.com/ildargiv/printshop-mcp@v0.3.0`
(see [Releases](https://github.com/ildargiv/printshop-mcp/releases); each release also has a wheel for `pip install`).

Needs [uv](https://docs.astral.sh/uv/) and Edge or Chrome (used for rendering).

## Why not just Ctrl+P?

| Ctrl+P | printshop-mcp |
|---|---|
| "Fit to page" silently scales: 90 mm becomes 88.7 mm | Rendered straight to device pixels: 1 mm in CSS = 1 mm on paper |
| Content falls into the unprintable margin | Proof shows the printer's real unprintable zone; preflight warns |
| The agent can't see the result | Proof images + JSON report: clipped text, low-dpi images, wrong paper |
| Settings forgotten every time | Named profiles with the full driver state, calibration and ICC |
| One kind of item per print | Badges, cards and flyers packed on shared sheets with crop marks |

## What the agent gets

**Skill** (`skills/printshop`): the workflow (profiles -> design -> proof -> print -> fix the profile), HTML rules,
a layout reference (what fits on A4/Letter) and templates:

| Template | |
|---|---|
| `badges-a4.html` | Event badges 90x55, 10 per A4 |
| `business-cards-a4.html` | Business cards 90x50, 10 per A4 |
| `flyers-a6.html` | A6 flyers, 4 per A4 |
| `table-tent-a4.html` | Folded table tent / name card |
| `event-kit-a4.html` | Mixed: flyer + badges + business cards on one sheet |
| `mug-wrap-a4.html` | Sublimation mug wraps 200x95 (11 oz), printed mirrored |

**MCP tools:**

| Tool | |
|---|---|
| `list_printers`, `describe_printer` | Printers, papers, trays, media types, printable area, saved profiles |
| `list_profiles`, `save_profile`, `set_default_profile`, `delete_profile` | Remembered print setups; `open_driver_dialog=true` lets you set vendor options once in the driver window; `mirror=true` for sublimation transfer paper |
| `layout` | Pack many items (HTML designs, PDFs, images) onto sheets, grouped by paper, with crop marks |
| `proof` | Render + preflight an HTML file or **any PDF**: proof images, a job id and a **cost estimate** (sheets, ink coverage measured on the pixels, money if the profile has prices) |
| `print_job` | Print a proofed job (warnings need explicit confirmation) |
| `printer_status` | Offline / out of paper / jammed, and the queue |

**HTML conventions:** each sheet is `<section class="ps-sheet" style="width:210mm;height:297mm">`, layout in mm.
`data-fit="9pt"` shrinks text to fit its box; `data-cut` adds crop marks.

## Safety

- Printing only after `proof` (the job id is the token); jobs expire after 1 hour and print once.
- `PRINTSHOP_MAX_SHEETS` (default 50) caps paper use; `PRINTSHOP_DRYRUN=1` never touches the printer.
- HTML can only load local files from its own folder.

## CLI

```
printshop-mcp printers
printshop-mcp proof badges.html --printer "My Printer"
printshop-mcp print <job_id> [--accept-warnings]
```

## License

MIT
