"""PDF input: pages become sheets, or images inside a layout (any design tool's PDF can be proofed and printed)."""
import io
from pathlib import Path
from urllib.parse import quote

from .win import PrintError

PDF_DPI = 400                 # raster resolution for PDF pages placed into sheets
MAX_PIXELS = 80_000_000
_cache = {}


def _doc(path):
    import pypdfium2 as pdfium
    try:
        return pdfium.PdfDocument(str(path))
    except Exception as e:
        raise PrintError(f"Cannot open PDF {Path(path).name}: {e}", "bad_pdf")


def page_sizes_mm(path):
    """[(width_mm, height_mm), ...] for every page (CropBox, as viewers show it)."""
    doc = _doc(path)
    try:
        return [tuple(round(v * 25.4 / 72, 2) for v in doc[i].get_size()) for i in range(len(doc))]
    finally:
        doc.close()


def page_png(path, page=1, dpi=PDF_DPI):
    """PNG bytes of one page (1-based) on white, cached by file and modification time."""
    path = Path(path)
    key = (str(path), path.stat().st_mtime, page, dpi)
    if key in _cache:
        return _cache[key]
    doc = _doc(path)
    try:
        if not 1 <= page <= len(doc):
            raise PrintError(f"{path.name} has {len(doc)} page(s); page {page} does not exist.", "bad_pdf")
        pg = doc[page - 1]
        w, h = pg.get_size()
        scale = dpi / 72
        if w * h * scale * scale > MAX_PIXELS:
            scale = (MAX_PIXELS / (w * h)) ** 0.5
        img = pg.render(scale=scale, fill_color=(255, 255, 255, 255)).to_pil().convert("RGB")
    finally:
        doc.close()
    buf = io.BytesIO()
    img.save(buf, "PNG", compress_level=1)
    if len(_cache) > 32:
        _cache.clear()
    _cache[key] = buf.getvalue()
    return _cache[key]


def sheets_html(path):
    """HTML with one .ps-sheet per PDF page, page size = sheet size."""
    name = quote(Path(path).name)
    parts = []
    for i, (w, h) in enumerate(page_sizes_mm(path), 1):
        parts.append(f'<section class="ps-sheet" data-name="page {i}" style="width:{w}mm;height:{h}mm">'
                     f'<img src="{name}?page={i}" style="position:absolute;left:0;top:0;width:100%;height:100%"></section>')
    return "<!doctype html><html><head><meta charset='utf-8'></head><body>" + "".join(parts) + "</body></html>"
