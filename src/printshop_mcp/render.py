"""HTML -> exact-size raster sheets via headless Chromium.

Convention: every physical sheet is an element with class "ps-sheet" and a size in mm, e.g.
    <section class="ps-sheet" style="width:210mm;height:297mm"> ... </section>
The page is rendered straight to pixels at the target dpi (no PDF, no "fit to page"), so 1 mm in CSS is 1 mm on paper.
Files are served from base_dir only: the page cannot read anything outside it.
"""
import io
import mimetypes
from pathlib import Path

from PIL import Image

from .win import PrintError

CSS_DPI = 96.0
ORIGIN = "http://printshop.local/"

BASE_CSS = """
html, body { margin: 0; padding: 0; background: #888; }
.ps-sheet { position: relative; overflow: hidden; background: #fff; box-sizing: border-box;
            margin: 0 0 10px 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
"""

# Built-in helpers, run after fonts are loaded:
#   data-fit="7pt"  shrink the element's font size until its text fits the box (not below the given minimum);
#   data-cut        draw crop marks at the element's corners, skipping marks that would land on a neighbouring item
#                   or in the outer 4 mm of the sheet.
HELPERS_JS = r"""
() => {
  const toPx = v => {
    const m = String(v || '').match(/([\d.]+)\s*(pt|px|mm)?/);
    if (!m) return 6;
    const n = parseFloat(m[1]);
    return m[2] === 'pt' ? n * 96 / 72 : m[2] === 'mm' ? n * 96 / 25.4 : n;
  };
  for (const el of document.querySelectorAll('[data-fit]')) {
    const min = toPx(el.dataset.fit);
    let s = parseFloat(getComputedStyle(el).fontSize);
    while ((el.scrollWidth > el.clientWidth + 0.5 || el.scrollHeight > el.clientHeight + 0.5) && s > min) {
      s = Math.max(min, s - 0.25);
      el.style.fontSize = s + 'px';
    }
  }
  const MM = 96 / 25.4, OFF = 1 * MM, LEN = 3 * MM, W = 0.15 * MM;
  for (const sh of document.querySelectorAll('.ps-sheet')) {
    const r = sh.getBoundingClientRect();
    const items = [...sh.querySelectorAll('[data-cut]')].map(e => e.getBoundingClientRect());
    const covered = (x0, y0, x1, y1, self) => items.some(b => b !== self &&
      x0 < b.right - 0.5 && x1 > b.left + 0.5 && y0 < b.bottom - 0.5 && y1 > b.top + 0.5);
    const EDGE = 4 * MM;                       // printers cannot print the outer few mm anyway
    const add = (x0, y0, x1, y1) => {
      x0 = Math.max(x0, r.left + EDGE); x1 = Math.min(x1, r.right - EDGE);
      y0 = Math.max(y0, r.top + EDGE); y1 = Math.min(y1, r.bottom - EDGE);
      if (x1 - x0 < W / 2 || y1 - y0 < W / 2 || Math.max(x1 - x0, y1 - y0) < 1 * MM) return;
      const d = document.createElement('div');
      d.className = 'ps-mark';
      Object.assign(d.style, {position: 'absolute', left: (x0 - r.left) + 'px', top: (y0 - r.top) + 'px',
        width: (x1 - x0) + 'px', height: (y1 - y0) + 'px', background: '#000', zIndex: 9999, pointerEvents: 'none'});
      sh.appendChild(d);
    };
    for (const b of items) {
      for (const [cx, cy] of [[b.left, b.top], [b.right, b.top], [b.left, b.bottom], [b.right, b.bottom]]) {
        const hx0 = cx === b.left ? cx - OFF - LEN : cx + OFF;
        if (!covered(hx0, cy - W / 2, hx0 + LEN, cy + W / 2, b)) add(hx0, cy - W / 2, hx0 + LEN, cy + W / 2);
        const vy0 = cy === b.top ? cy - OFF - LEN : cy + OFF;
        if (!covered(cx - W / 2, vy0, cx + W / 2, vy0 + LEN, b)) add(cx - W / 2, vy0, cx + W / 2, vy0 + LEN);
      }
    }
  }
}
"""

# Collects sheet sizes, image resolution and clipped / overflowing content, in mm relative to each sheet.
INSPECT_JS = """
() => {
  const mm = px => px * 25.4 / 96;
  const label = el => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].join('.');
    const t = (el.innerText || el.getAttribute('src') || '').trim().slice(0, 40);
    return t ? s + ' "' + t + '"' : s;
  };
  return [...document.querySelectorAll('.ps-sheet')].map((sh, i) => {
    const r = sh.getBoundingClientRect();
    const rel = b => [mm(b.left - r.left), mm(b.top - r.top), mm(b.right - r.left), mm(b.bottom - r.top)].map(v => Math.round(v * 10) / 10);
    const images = [], clipped = [], outside = [];
    for (const el of sh.querySelectorAll('*')) {
      if (el.classList.contains('ps-mark')) continue;
      const b = el.getBoundingClientRect();
      if (b.width === 0 || b.height === 0) continue;
      if (el.tagName === 'IMG') {
        const wmm = mm(b.width), hmm = mm(b.height);
        const dpi = el.naturalWidth ? Math.min(el.naturalWidth / (wmm / 25.4), el.naturalHeight / (hmm / 25.4)) : 0;
        images.push({element: label(el), box_mm: rel(b), dpi: Math.round(dpi), loaded: el.complete && el.naturalWidth > 0});
      }
      const cs = getComputedStyle(el);
      if (cs.overflow !== 'visible' && (el.scrollWidth - el.clientWidth >= 4 || el.scrollHeight - el.clientHeight >= 4))
        clipped.push({element: label(el), box_mm: rel(b)});
      if (b.left < r.left - 0.5 || b.top < r.top - 0.5 || b.right > r.right + 0.5 || b.bottom > r.bottom + 0.5)
        outside.push({element: label(el), box_mm: rel(b)});
    }
    return {index: i, size_mm: [Math.round(mm(r.width) * 100) / 100, Math.round(mm(r.height) * 100) / 100],
            name: sh.dataset.name || null, paper: sh.dataset.paper || null, images, clipped, outside};
  });
}
"""


def _launch(p):
    errors = []
    for kw in ({"channel": "msedge"}, {"channel": "chrome"}, {}):
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            errors.append(str(e).splitlines()[0])
    raise PrintError("No Chromium browser found. Install Edge/Chrome or run: playwright install chromium. " + "; ".join(errors),
                     "no_browser")


def render_sheets(html, base_dir, dpi):
    """Returns (list of PIL RGB images, list of sheet info dicts)."""
    from playwright.sync_api import sync_playwright
    base = Path(base_dir).resolve()
    if "<head>" in html:
        html = html.replace("<head>", "<head><style>" + BASE_CSS + "</style>", 1)
    else:
        html = "<style>" + BASE_CSS + "</style>" + html

    def route(r):
        url = r.request.url
        if not url.startswith(ORIGIN):
            return r.abort() if url.startswith("file:") else r.continue_()   # web fonts / CDN images are allowed
        rel = url[len(ORIGIN):].split("?")[0].split("#")[0]
        if rel in ("", "index.html"):
            return r.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
        from urllib.parse import unquote
        f = (base / unquote(rel)).resolve()
        if base not in f.parents or not f.is_file():
            return r.fulfill(status=404, body="")
        r.fulfill(status=200, content_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream", body=f.read_bytes())

    with sync_playwright() as p:
        browser = _launch(p)
        try:
            page = browser.new_page(viewport={"width": 1200, "height": 1000}, device_scale_factor=dpi / CSS_DPI)
            page.route("**/*", route)
            page.goto(ORIGIN + "index.html", wait_until="networkidle", timeout=60000)
            page.evaluate("document.fonts.ready")
            page.evaluate(HELPERS_JS)
            info = page.evaluate(INSPECT_JS)
            if not info:
                raise PrintError('No sheets found. Wrap each physical sheet in <section class="ps-sheet" '
                                 'style="width:210mm;height:297mm">...</section>.', "no_sheets")
            images = []
            for el, sh in zip(page.query_selector_all(".ps-sheet"), info):
                png = el.screenshot(type="png", scale="device", animations="disabled")
                img = Image.open(io.BytesIO(png)).convert("RGB")
                want = (round(sh["size_mm"][0] / 25.4 * dpi), round(sh["size_mm"][1] / 25.4 * dpi))
                if img.size != want:                      # sub-pixel rounding of the element box
                    img = img.resize(want, Image.Resampling.LANCZOS)
                images.append(img)
            return images, info
        finally:
            browser.close()
