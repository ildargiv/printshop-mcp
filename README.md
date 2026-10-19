# printshop-mcp

**English** · [Русский](docs/i18n/README.ru.md) · [简体中文](docs/i18n/README.zh-CN.md) · [Español](docs/i18n/README.es.md) · [Português](docs/i18n/README.pt-BR.md) · [Deutsch](docs/i18n/README.de.md) · [日本語](docs/i18n/README.ja.md)

**The print shop inside your AI agent.** Ask for "badges for these 40 guests, business cards and a flyer" and the
agent designs them, packs them onto sheets, shows you an exact proof and prints them on **your real printer** -
millimetre-accurate. And it **remembers all your print profiles**: printer, paper, tray, media type, quality,
colour profile, calibration, even vendor-only driver options. Explain your printer once, never again.

<p align="center"><img src="docs/event-kit-a4-proof.png" width="420" alt="Proof of a mixed A4 sheet: flyer, badges and business cards with crop marks"></p>

*A mixed sheet (1 flyer + 3 badges + 4 business cards) as the agent sees it before printing: crop marks only where you cut,
long names shrunk to fit, grey border = what your printer can't print.*

> Status: v0.1, Windows. Coming next: PDF input (print any design skill's output), automatic mixed layout,
> self-learning from print defects, macOS/Linux.

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

**MCP tools:**

| Tool | |
|---|---|
| `list_printers`, `describe_printer` | Printers, papers, trays, media types, printable area, saved profiles |
| `list_profiles`, `save_profile`, `set_default_profile`, `delete_profile` | Remembered print setups; `open_driver_dialog=true` lets you set vendor options once in the driver window |
| `proof` | Render + preflight: proof images and a job id |
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
