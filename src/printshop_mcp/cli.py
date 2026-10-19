"""printshop-mcp            -> MCP server (stdio)
printshop-mcp printers   -> list printers
printshop-mcp profiles   -> list remembered profiles
printshop-mcp proof FILE [--printer P] [--profile N] [--copies K] [--dpi D]
printshop-mcp print JOB_ID [--accept-warnings] [--to-file OUT.pdf]
"""
import argparse
import json
import sys


def main():
    if len(sys.argv) == 1 or sys.argv[1] == "mcp":
        from .server import main as serve
        return serve()
    from . import jobs, win
    from .profiles import ProfileStore, public
    ap = argparse.ArgumentParser(prog="printshop-mcp")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("printers")
    sub.add_parser("profiles")
    p = sub.add_parser("proof")
    p.add_argument("file")
    p.add_argument("--printer")
    p.add_argument("--profile")
    p.add_argument("--copies", type=int, default=1)
    p.add_argument("--dpi", type=int)
    p = sub.add_parser("print")
    p.add_argument("job_id")
    p.add_argument("--accept-warnings", action="store_true")
    p.add_argument("--to-file", help="write the spooler output to a file (e.g. with 'Microsoft Print to PDF')")
    a = ap.parse_args()
    try:
        if a.cmd == "printers":
            res = win.list_printers()
        elif a.cmd == "profiles":
            res = [public(x) for x in ProfileStore().all()["profiles"].values()]
        elif a.cmd == "proof":
            res = jobs.preflight(path=a.file, printer=a.printer, profile=a.profile, copies=a.copies, dpi=a.dpi)
        else:
            res = jobs.print_job(a.job_id, a.accept_warnings, output=a.to_file)
    except win.PrintError as e:
        res = {"error": str(e), "code": e.code}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 1 if isinstance(res, dict) and "error" in res else 0


if __name__ == "__main__":
    sys.exit(main())
