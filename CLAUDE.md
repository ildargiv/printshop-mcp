# printshop-mcp

MCP server + Claude Code plugin/skill: "the print shop inside your agent". The agent writes HTML in mm,
printshop-mcp renders it exactly as the printer will print it, proofs it, prints it, and **remembers the user's print
profiles** (full driver settings incl. vendor options, tray, media, quality, ICC, calibration).

## Layout

| Path | Role |
|---|---|
| `src/printshop_mcp/win.py` | winspool/GDI via ctypes: printers, DEVMODE, geometry, capabilities, PrinterJob, spooler status |
| `src/printshop_mcp/render.py` | HTML -> raster at exact dpi via Playwright (Edge/Chrome); `.ps-sheet` sheets in mm; `data-fit`, `data-cut` helpers; checks |
| `src/printshop_mcp/profiles.py` | Profile store (`%APPDATA%\printshop-mcp\profiles.json`, override with `PRINTSHOP_HOME`) |
| `src/printshop_mcp/pdf.py` | PDF pages -> sheets or images inside layouts (pypdfium2) |
| `src/printshop_mcp/impose.py` | `layout`: shelf/column guillotine packing of many items, grouped by paper |
| `src/printshop_mcp/jobs.py` | preflight/proof -> print_job (job id is the token, TTL 1 h, prints once) |
| `src/printshop_mcp/server.py` | MCP tools, instructions, `printshop://guide` (mcp 2.x `MCPServer`, falls back to 1.x `FastMCP`) |
| `src/printshop_mcp/cli.py` | `printshop-mcp` (stdio server) and `printers / profiles / proof / print` subcommands |
| `skills/printshop/` | Agent skill: `SKILL.md`, HTML templates, layout reference |
| `.claude-plugin/`, `.mcp.json` | Claude Code plugin + marketplace manifests; the plugin starts the server via `uvx` from this repo |

## Dev

```bash
uv venv .venv && uv pip install --python .venv/Scripts/python.exe -e .
.venv/Scripts/python.exe tests/test_smoke.py
```

Test with the virtual "Microsoft Print to PDF" printer (`printshop-mcp print JOB --to-file out.pdf`).
Never send test jobs to a real printer without asking. `PRINTSHOP_DRYRUN=1` blocks real printing.
Every template in `skills/printshop/templates/` must proof with status `ready` (no warnings) on a typical inkjet.

## Roadmap

1. ~~Core: render, proof, preflight, print, profiles, MCP~~
2. ~~Skill + templates + plugin~~
3. ~~PDF input (pypdfium2)~~
4. ~~Automatic mixed imposition (`impose.py`, `layout` tool)~~; still to do: cutting map sheet, duplex
5. Self-learning: defect catalogue -> typed fix -> test strip -> confirm -> lesson per printer/paper/template, rollback, `LESSONS.md`
- v1.1: CUPS (macOS/Linux), photo-of-sheet calibration marks
- v2: thermal label printers (ZPL/TSPL), remote printing, community printer profiles
