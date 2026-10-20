"""Print profiles: the agent remembers every printer + paper setup you ever used.

A profile stores the complete driver settings (including vendor-private options such as Epson's
"Premium Glossy / Best Photo"), colour management and per-printer calibration. Configure once, reuse forever.
Stored as plain JSON in the data dir, so it is easy to read, back up or edit by hand.
"""
import base64
import json
import os
import time
from pathlib import Path

from .win import PrintError


def data_dir():
    d = os.environ.get("PRINTSHOP_HOME")
    if d:
        p = Path(d)
    elif os.environ.get("APPDATA"):
        p = Path(os.environ["APPDATA"]) / "printshop-mcp"
    else:
        p = Path.home() / ".printshop-mcp"
    p.mkdir(parents=True, exist_ok=True)
    return p


FIELDS = ("printer", "paper", "tray", "media", "quality", "color", "duplex", "icc", "intent", "dpi",
          "scale_x", "scale_y", "offset_x_mm", "offset_y_mm", "mirror", "paper_price", "ink_price_5pct", "currency", "tags", "notes")
CAL_LIMITS = {"scale_x": (0.97, 1.03), "scale_y": (0.97, 1.03), "offset_x_mm": (-5, 5), "offset_y_mm": (-5, 5)}


class ProfileStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_dir() / "profiles.json"

    def _load(self):
        if self.path.is_file():
            return json.loads(self.path.read_text("utf-8"))
        return {"profiles": {}, "defaults": {}, "default_printer": None}

    def _save(self, db):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(db, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(self.path)

    def all(self):
        return self._load()

    def get(self, name):
        p = self._load()["profiles"].get(name)
        if not p:
            raise PrintError(f"Profile '{name}' not found. Call list_profiles.", "no_profile")
        return p

    def devmode(self, name):
        p = self.get(name)
        return base64.b64decode(p["devmode"]) if p.get("devmode") else None

    def save(self, name, devmode=None, **fields):
        """Creates or updates a profile; only given fields change."""
        if not name or len(name) > 80:
            raise PrintError("Profile name must be 1-80 characters.", "bad_args")
        db = self._load()
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        p = db["profiles"].get(name) or {"name": name, "created": now, "uses": 0, "last_used": None,
                                          "scale_x": 1.0, "scale_y": 1.0, "offset_x_mm": 0.0, "offset_y_mm": 0.0,
                                          "tags": [], "notes": ""}
        for k, v in fields.items():
            if k not in FIELDS:
                raise PrintError(f"Unknown profile field '{k}'.", "bad_args")
            if v is None:
                continue
            if k in CAL_LIMITS:
                lo, hi = CAL_LIMITS[k]
                if not lo <= float(v) <= hi:
                    raise PrintError(f"{k}={v} is outside the safe range [{lo}, {hi}].", "bad_args")
                v = float(v)
            p[k] = v
        if not p.get("printer"):
            raise PrintError("A profile needs a printer.", "bad_args")
        if devmode is not None:
            p["devmode"] = base64.b64encode(devmode).decode()
        p["updated"] = now
        db["profiles"][name] = p
        db["defaults"].setdefault(p["printer"], name)
        self._save(db)
        return p

    def delete(self, name):
        db = self._load()
        p = db["profiles"].pop(name, None)
        if not p:
            raise PrintError(f"Profile '{name}' not found.", "no_profile")
        if db["defaults"].get(p["printer"]) == name:
            rest = [n for n, q in db["profiles"].items() if q["printer"] == p["printer"]]
            if rest:
                db["defaults"][p["printer"]] = rest[0]
            else:
                db["defaults"].pop(p["printer"])
        self._save(db)

    def set_default(self, name):
        db = self._load()
        p = db["profiles"].get(name)
        if not p:
            raise PrintError(f"Profile '{name}' not found.", "no_profile")
        db["defaults"][p["printer"]] = name
        db["default_printer"] = p["printer"]
        self._save(db)

    def resolve(self, profile=None, printer=None):
        """Explicit profile > printer's default profile > last-used printer's default profile > None."""
        db = self._load()
        if profile:
            return self.get(profile)
        if printer:
            n = db["defaults"].get(printer)
            return db["profiles"].get(n) if n else None
        dp = db.get("default_printer")
        n = db["defaults"].get(dp) if dp else None
        return db["profiles"].get(n) if n else None

    def mark_used(self, name, printer):
        db = self._load()
        p = db["profiles"].get(name)
        if p:
            p["uses"] = p.get("uses", 0) + 1
            p["last_used"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        db["default_printer"] = printer
        self._save(db)


def public(p):
    """Profile as shown to the agent (driver blob hidden)."""
    q = {k: v for k, v in p.items() if k != "devmode"}
    q["has_driver_settings"] = bool(p.get("devmode"))
    return q
