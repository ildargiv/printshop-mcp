"""Windows printing: winspool/GDI via ctypes (ported from PhotoCrop).

A sheet image always covers the whole physical paper; the driver's unprintable margins are clipped
by the printer itself, so millimetres on the image are millimetres on paper.
"""
import ctypes
import json
import os
import struct
import subprocess
import sys

DM_ORIENTATION, DM_PAPERSIZE, DM_PAPERLENGTH, DM_PAPERWIDTH = 0x1, 0x2, 0x4, 0x8
DM_COPIES, DM_DEFAULTSOURCE, DM_PRINTQUALITY, DM_COLOR, DM_DUPLEX = 0x100, 0x200, 0x400, 0x800, 0x1000
DM_FORMNAME, DM_ICMMETHOD, DM_MEDIATYPE = 0x10000, 0x800000, 0x2000000
DM_OUT_BUFFER, DM_IN_PROMPT, DM_IN_BUFFER = 2, 4, 8
DMPAPER_USER, DMICMMETHOD_NONE = 256, 1

# Windows paper codes for common sizes (short side, long side in mm)
PAPER_CODES = {(210, 297): 9, (297, 420): 8, (148, 210): 11, (105, 148): 70, (216, 279): 1, (216, 356): 5,
               (182, 257): 13, (102, 152): 0}
QUALITY = {"draft": -1, "low": -2, "medium": -3, "high": -4}
COLOR = {"mono": 1, "color": 2}
DUPLEX = {"simplex": 1, "long_edge": 2, "short_edge": 3}

DC = {"papers": 2, "papersize": 3, "bins": 6, "duplex": 7, "binnames": 12, "resolutions": 13, "papernames": 16,
      "copies": 18, "mediaready": 29, "colordevice": 32, "mediatypenames": 34, "mediatypes": 35}


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_uint16 * 32), ("dmSpecVersion", ctypes.c_ushort), ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort), ("dmDriverExtra", ctypes.c_ushort), ("dmFields", ctypes.c_uint32),
        ("dmOrientation", ctypes.c_short), ("dmPaperSize", ctypes.c_short), ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short), ("dmScale", ctypes.c_short), ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short), ("dmPrintQuality", ctypes.c_short), ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short), ("dmYResolution", ctypes.c_short), ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short), ("dmFormName", ctypes.c_uint16 * 32), ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_uint32), ("dmPelsWidth", ctypes.c_uint32), ("dmPelsHeight", ctypes.c_uint32),
        ("dmDisplayFlags", ctypes.c_uint32), ("dmDisplayFrequency", ctypes.c_uint32), ("dmICMMethod", ctypes.c_uint32),
        ("dmICMIntent", ctypes.c_uint32), ("dmMediaType", ctypes.c_uint32), ("dmDitherType", ctypes.c_uint32),
        ("dmReserved1", ctypes.c_uint32), ("dmReserved2", ctypes.c_uint32), ("dmPanningWidth", ctypes.c_uint32),
        ("dmPanningHeight", ctypes.c_uint32),
    ]


class DOCINFOW(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_int), ("lpszDocName", ctypes.c_wchar_p), ("lpszOutput", ctypes.c_wchar_p),
                ("lpszDatatype", ctypes.c_wchar_p), ("fwType", ctypes.c_uint32)]


class PRINTER_INFO_4(ctypes.Structure):
    _fields_ = [("pPrinterName", ctypes.c_wchar_p), ("pServerName", ctypes.c_wchar_p), ("Attributes", ctypes.c_uint32)]


class PrintError(Exception):
    def __init__(self, message, code="error"):
        super().__init__(message)
        self.code = code


_WIN = None


def _win():
    global _WIN
    if _WIN is None:
        if sys.platform != "win32":
            raise PrintError("Printing is only supported on Windows for now (macOS/Linux via CUPS is planned).", "windows_only")
        from ctypes import wintypes as wt
        wp = ctypes.WinDLL("winspool.drv", use_last_error=True)
        gd = ctypes.WinDLL("gdi32", use_last_error=True)
        wp.OpenPrinterW.argtypes = [wt.LPWSTR, ctypes.POINTER(wt.HANDLE), ctypes.c_void_p]
        wp.OpenPrinterW.restype = wt.BOOL
        wp.ClosePrinter.argtypes = [wt.HANDLE]
        wp.DocumentPropertiesW.argtypes = [wt.HWND, wt.HANDLE, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wt.DWORD]
        wp.DocumentPropertiesW.restype = ctypes.c_long
        wp.EnumPrintersW.argtypes = [wt.DWORD, wt.LPWSTR, wt.DWORD, ctypes.c_void_p, wt.DWORD,
                                     ctypes.POINTER(wt.DWORD), ctypes.POINTER(wt.DWORD)]
        wp.EnumPrintersW.restype = wt.BOOL
        wp.GetDefaultPrinterW.argtypes = [wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
        wp.GetDefaultPrinterW.restype = wt.BOOL
        wp.DeviceCapabilitiesW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, wt.WORD, ctypes.c_void_p, ctypes.c_void_p]
        wp.DeviceCapabilitiesW.restype = ctypes.c_int
        gd.CreateDCW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p]
        gd.CreateDCW.restype = ctypes.c_void_p
        gd.DeleteDC.argtypes = [ctypes.c_void_p]
        gd.GetDeviceCaps.argtypes = [ctypes.c_void_p, ctypes.c_int]
        gd.GetDeviceCaps.restype = ctypes.c_int
        gd.StartDocW.argtypes = [ctypes.c_void_p, ctypes.POINTER(DOCINFOW)]
        gd.StartDocW.restype = ctypes.c_int
        for fn in ("StartPage", "EndPage", "EndDoc", "AbortDoc"):
            getattr(gd, fn).argtypes = [ctypes.c_void_p]
            getattr(gd, fn).restype = ctypes.c_int
        _WIN = (wp, gd, wt)
    return _WIN


def list_printers():
    """Installed printers, default printer first."""
    wp, gd, wt = _win()
    flags = 2 | 4   # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
    need, ret = wt.DWORD(0), wt.DWORD(0)
    wp.EnumPrintersW(flags, None, 4, None, 0, ctypes.byref(need), ctypes.byref(ret))
    if need.value == 0:
        return []
    buf = ctypes.create_string_buffer(need.value)
    if not wp.EnumPrintersW(flags, None, 4, buf, need.value, ctypes.byref(need), ctypes.byref(ret)):
        return []
    arr = ctypes.cast(buf, ctypes.POINTER(PRINTER_INFO_4))
    names = [arr[i].pPrinterName for i in range(ret.value)]
    d = default_printer()
    if d in names:
        names.remove(d)
        names.insert(0, d)
    return names


def default_printer():
    wp, gd, wt = _win()
    n = wt.DWORD(512)
    buf = ctypes.create_unicode_buffer(512)
    return buf.value if wp.GetDefaultPrinterW(buf, ctypes.byref(n)) else None


def check_printer(name):
    if name not in list_printers():
        raise PrintError(f"Printer '{name}' not found. Call list_printers.", "no_printer")


def _docprops(name, blob, mode, hwnd=None):
    wp, gd, wt = _win()
    h = wt.HANDLE()
    if not wp.OpenPrinterW(name, ctypes.byref(h), None):
        raise PrintError(f"Cannot open printer '{name}'.", "no_printer")
    try:
        size = wp.DocumentPropertiesW(None, h, name, None, None, 0)
        if size <= 0:
            raise PrintError("Printer driver returned no settings.", "driver_error")
        out = ctypes.create_string_buffer(size)
        if blob is not None and (mode & DM_IN_BUFFER):
            inb = ctypes.create_string_buffer(blob, max(len(blob), size))
            res = wp.DocumentPropertiesW(hwnd, h, name, out, inb, mode)
        else:
            res = wp.DocumentPropertiesW(hwnd, h, name, out, None, mode)
        return res, out.raw[:size]
    finally:
        wp.ClosePrinter(h)


def default_devmode(name):
    res, blob = _docprops(name, None, DM_OUT_BUFFER)
    if res != 1:
        raise PrintError("Cannot read printer default settings.", "driver_error")
    return blob


def merge_devmode(name, blob):
    """Lets the driver validate and reconcile the settings."""
    res, out = _docprops(name, blob, DM_IN_BUFFER | DM_OUT_BUFFER)
    return out if res == 1 else blob


def driver_dialog(name, blob):
    """Opens the driver's own Properties dialog (all vendor options). Returns new settings or None if cancelled."""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    res, out = _docprops(name, blob, DM_IN_BUFFER | DM_OUT_BUFFER | DM_IN_PROMPT, hwnd)
    return out if res == 1 else None


def paper_code(w_mm, h_mm):
    s, l = sorted((round(w_mm), round(h_mm)))
    for (a, b), code in PAPER_CODES.items():
        if abs(a - s) <= 1 and abs(b - l) <= 1:
            return code
    return 0


def patch_devmode(blob, orientation=None, paper=None, icm_off=None, source=None, media=None, quality=None,
                  color=None, duplex=None):
    """Changes public DEVMODE fields; vendor-private driver data is kept as is.
    paper = (width_mm, height_mm); orientation = 'portrait' | 'landscape'."""
    ba = bytearray(blob)
    need = ctypes.sizeof(DEVMODEW)
    if len(ba) < need:
        ba += bytearray(need - len(ba))
    dm = DEVMODEW.from_buffer(ba)
    if orientation:
        dm.dmOrientation = 1 if orientation == "portrait" else 2
        dm.dmFields |= DM_ORIENTATION
    dm.dmCopies = 1
    dm.dmFields |= DM_COPIES
    if paper:
        w, h = sorted(paper)
        code = paper_code(w, h)
        dm.dmFields &= ~DM_FORMNAME
        if code:
            dm.dmPaperSize = code
            dm.dmFields = (dm.dmFields | DM_PAPERSIZE) & ~(DM_PAPERLENGTH | DM_PAPERWIDTH)
        else:
            dm.dmPaperSize = DMPAPER_USER
            dm.dmPaperWidth, dm.dmPaperLength = int(round(w * 10)), int(round(h * 10))
            dm.dmFields |= DM_PAPERSIZE | DM_PAPERLENGTH | DM_PAPERWIDTH
    if icm_off:
        dm.dmICMMethod = DMICMMETHOD_NONE
        dm.dmFields |= DM_ICMMETHOD
    if source is not None:
        dm.dmDefaultSource = int(source)
        dm.dmFields |= DM_DEFAULTSOURCE
    if media is not None:
        dm.dmMediaType = int(media)
        dm.dmFields |= DM_MEDIATYPE
    if quality is not None:
        dm.dmPrintQuality = QUALITY.get(quality, quality) if isinstance(quality, str) else int(quality)
        dm.dmFields |= DM_PRINTQUALITY
    if color is not None:
        dm.dmColor = COLOR[color]
        dm.dmFields |= DM_COLOR
    if duplex is not None:
        dm.dmDuplex = DUPLEX[duplex]
        dm.dmFields |= DM_DUPLEX
    return bytes(ba[:len(blob)])


def devmode_summary(blob):
    """Readable public fields of saved driver settings."""
    ba = bytearray(blob)
    if len(ba) < ctypes.sizeof(DEVMODEW):
        ba += bytearray(ctypes.sizeof(DEVMODEW) - len(ba))
    dm = DEVMODEW.from_buffer(ba)
    q = {v: k for k, v in QUALITY.items()}
    return {"orientation": {1: "portrait", 2: "landscape"}.get(dm.dmOrientation),
            "paper_code": dm.dmPaperSize, "source_code": dm.dmDefaultSource, "media_code": dm.dmMediaType,
            "quality": q.get(dm.dmPrintQuality, dm.dmPrintQuality),
            "color": {1: "mono", 2: "color"}.get(dm.dmColor), "duplex": {1: "simplex", 2: "long_edge", 3: "short_edge"}.get(dm.dmDuplex),
            "driver_private_bytes": dm.dmDriverExtra}


def _create_dc(name, blob):
    wp, gd, wt = _win()
    buf = ctypes.create_string_buffer(blob, len(blob))
    dc = gd.CreateDCW("WINSPOOL", name, None, ctypes.cast(buf, ctypes.c_void_p))
    if not dc:
        raise PrintError(f"Cannot connect to printer '{name}'.", "no_printer")
    return dc, buf


def printer_geometry(name, blob):
    """Paper size, printable area (mm) and device dpi for these driver settings."""
    wp, gd, wt = _win()
    dc, _keep = _create_dc(name, blob)
    try:
        cap = lambda i: gd.GetDeviceCaps(dc, i)
        dpx, dpy = cap(88), cap(90)
        pw, ph, ox, oy = cap(110), cap(111), cap(112), cap(113)
        hr, vr = cap(8), cap(10)
        if dpx <= 0 or dpy <= 0 or pw <= 0 or ph <= 0:
            raise PrintError("Driver returned invalid paper geometry.", "driver_error")
        mx, my = 25.4 / dpx, 25.4 / dpy
        return {"paper_mm": [round(pw * mx, 2), round(ph * my, 2)],
                "printable_mm": [round(ox * mx, 2), round(oy * my, 2), round((ox + hr) * mx, 2), round((oy + vr) * my, 2)],
                "dpi": [dpx, dpy]}
    finally:
        gd.DeleteDC(dc)


def printer_capabilities(name):
    wp, gd, wt = _win()
    fn = wp.DeviceCapabilitiesW

    def items(cap, size):
        n = fn(name, None, DC[cap], None, None)
        if n <= 0:
            return []
        buf = ctypes.create_string_buffer(n * size)
        fn(name, None, DC[cap], buf, None)
        return [buf.raw[i * size:(i + 1) * size] for i in range(n)]

    txt = lambda b: b.decode("utf-16le", "ignore").split("\0")[0]
    codes = [struct.unpack("<H", b)[0] for b in items("papers", 2)]
    names = [txt(b) for b in items("papernames", 128)]
    sizes = [struct.unpack("<ii", b) for b in items("papersize", 8)]
    papers = [{"code": c, "name": names[i] if i < len(names) else "",
               "mm": [sizes[i][0] / 10, sizes[i][1] / 10] if i < len(sizes) else None} for i, c in enumerate(codes)]
    trays = [{"code": struct.unpack("<H", b)[0], "name": n}
             for b, n in zip(items("bins", 2), [txt(b) for b in items("binnames", 48)])]
    mt_codes = [struct.unpack("<I", b)[0] for b in items("mediatypes", 4)]
    mt_names = [txt(b) for b in items("mediatypenames", 128)]
    media = [{"code": c, "name": mt_names[i] if i < len(mt_names) else ""} for i, c in enumerate(mt_codes)]
    return {"papers": papers, "trays": trays, "media_types": media,
            "resolutions_dpi": [list(struct.unpack("<ii", b)) for b in items("resolutions", 8)],
            "color": fn(name, None, DC["colordevice"], None, None) == 1,
            "duplex": fn(name, None, DC["duplex"], None, None) == 1}


class PrinterJob:
    """One spooler document. output= writes to a file instead of the device (used for tests with 'Microsoft Print to PDF')."""

    def __init__(self, name, blob, title, output=None):
        self.name, self.blob, self.title, self.output = name, blob, title, output
        self.dc = None
        self.started = False

    def __enter__(self):
        wp, gd, wt = _win()
        self.dc, self._keep = _create_dc(self.name, self.blob)
        cap = lambda i: gd.GetDeviceCaps(self.dc, i)
        self.physw, self.physh, self.offx, self.offy = cap(110), cap(111), cap(112), cap(113)
        di = DOCINFOW(ctypes.sizeof(DOCINFOW), self.title, self.output, None, 0)
        if gd.StartDocW(self.dc, ctypes.byref(di)) <= 0:
            gd.DeleteDC(self.dc)
            self.dc = None
            raise PrintError("Printer did not accept the job.", "spooler_error")
        self.started = True
        return self

    def page(self, img, band=512):
        """Prints one sheet; img covers the whole physical paper. Sent in bands to save memory."""
        from PIL import ImageWin
        wp, gd, wt = _win()
        gd.StartPage(self.dc)
        W, H = img.size
        x0, y0 = -self.offx, -self.offy
        for a in range(0, H, band):
            b = min(H, a + band)
            top = y0 + round(a * self.physh / H)
            bot = y0 + round(b * self.physh / H)
            ImageWin.Dib(img.crop((0, a, W, b))).draw(int(self.dc), (x0, top, x0 + self.physw, bot))
        gd.EndPage(self.dc)

    def finish(self):
        if self.dc and self.started:
            _win()[1].EndDoc(self.dc)
            self.started = False

    def __exit__(self, et, ev, tb):
        if self.dc:
            if self.started:
                _win()[1].AbortDoc(self.dc)
            _win()[1].DeleteDC(self.dc)
            self.dc = None
        return False


# ---- spooler status (PowerShell)

PRINTER_STATUS = {1: "other", 2: "unknown", 3: "idle", 4: "printing", 5: "warmup", 6: "stopped", 7: "offline"}
PRINTER_ERROR = {0: "unknown", 1: "other", 2: "no_error", 3: "low_paper", 4: "no_paper", 5: "low_toner", 6: "no_toner",
                 7: "door_open", 8: "jammed", 9: "offline", 10: "service_requested", 11: "output_bin_full"}


def _ps(script, env):
    e = dict(os.environ)
    e.update(env)
    pre = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $ErrorActionPreference='Stop'; "
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", pre + script],
                       capture_output=True, timeout=40, env=e, creationflags=0x08000000)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise PrintError("Spooler error: " + (r.stderr.decode("utf-8", "replace").strip() or out)[:400], "spooler_error")
    return json.loads(out) if out else None


def spooler_status(name):
    d = _ps("$p = Get-CimInstance Win32_Printer | Where-Object Name -eq $env:PS_PRINTER; "
            "$j = @(Get-PrintJob -PrinterName $env:PS_PRINTER | Select-Object Id,DocumentName,TotalPages,PagesPrinted,"
            "@{n='Status';e={$_.JobStatus.ToString()}}); "
            "@{printer=($p | Select-Object WorkOffline,PrinterStatus,DetectedErrorState); jobs=$j} | ConvertTo-Json -Compress -Depth 4",
            {"PS_PRINTER": name})
    p = (d or {}).get("printer") or {}
    jobs = d.get("jobs") or []
    if isinstance(jobs, dict):
        jobs = [jobs]
    return {"printer": name, "offline": bool(p.get("WorkOffline")),
            "status": PRINTER_STATUS.get(p.get("PrinterStatus"), str(p.get("PrinterStatus"))),
            "error": PRINTER_ERROR.get(p.get("DetectedErrorState"), str(p.get("DetectedErrorState"))),
            "queue": [{"id": j.get("Id"), "document": j.get("DocumentName"), "status": j.get("Status"),
                       "pages": j.get("TotalPages"), "pages_printed": j.get("PagesPrinted")} for j in jobs]}
