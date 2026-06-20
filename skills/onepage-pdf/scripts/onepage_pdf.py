#!/usr/bin/env python3
"""onepage-pdf: render an HTML file into a single continuous-page PDF (no pagination).

Strategy: never *predict* the page height (screen layout != print layout, and the
px->inch->pt conversion chain rounds non-monotonically). Instead render onto an
oversized "bedrock" page, then measure the real content bottom with PyMuPDF's
render-level bbox log and shrink MediaBox + CropBox to fit. Height is cropped,
not calculated.

Dependencies: PyMuPDF (pip install pymupdf) + a local Chrome or Edge.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

try:
    import pymupdf
except ImportError:  # PyMuPDF < 1.24 exposes the legacy name only
    import fitz as pymupdf

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

# Injected before </head>. The @page rule is the only official channel for paper
# size in CLI headless mode (--print-to-pdf hardcodes preferCSSPageSize:true).
# Width/height must be multiples of 8px: 8px = 6pt exactly, anything else risks
# MediaBox rounding errors that spill content onto a phantom second page.
PRINT_CSS = """
<style data-onepage-pdf>
  @page {{ size: {width}px {bedrock}px; margin: 0; }}
  * {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    animation: none !important;
    transition: none !important;
    background-attachment: scroll !important; /* fixed bg paints only page 1 */
  }}
  /* scroll-reveal patterns start at opacity:0 and never "enter the viewport"
     during a headless print pass — force them visible */
  [class*="fade"], [class*="reveal"], [class*="animate"], [class*="aos"],
  [data-aos] {{
    opacity: 1 !important;
    transform: none !important;
    visibility: visible !important;
  }}
{extra}
</style>
</head>"""

ACROBAT_LIMIT_PT = 14400  # ISO 32000-1 Annex C; Chrome will exceed it happily


def find_browser(explicit):
    if explicit:
        if Path(explicit).exists():
            return explicit
        sys.exit(f"browser not found: {explicit}")
    for p in BROWSERS:
        if Path(p).exists():
            return p
    found = shutil.which("chrome") or shutil.which("chromium") or shutil.which("msedge")
    if found:
        return found
    sys.exit("no Chrome/Edge found; pass --chrome PATH")


def align8(px):
    return max(8, int(round(px / 8.0)) * 8)


def apply_replacements(html, replace_file):
    pairs = json.loads(Path(replace_file).read_text(encoding="utf-8"))
    for old, new in pairs:  # order matters: longest/most specific first
        html = html.replace(old, new)
    return html


def check_forbidden(text, forbid_file, where):
    words = [w.strip() for w in Path(forbid_file).read_text(encoding="utf-8").splitlines() if w.strip()]
    leaks = [w for w in words if w in text]
    if leaks:
        sys.exit(f"LEAK in {where}: {leaks}")
    return len(words)


def render(browser, html_path, pdf_path, width, virtual_time):
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--hide-scrollbars",
        f"--window-size={width},2000",
        f"--virtual-time-budget={virtual_time}",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    subprocess.run(cmd, check=True, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def content_bottom_vector(page):
    """Bottom edge (pt, from page top) via the render-level bbox log.

    get_bboxlog() covers text, images, vector paths and unrolls Form XObjects —
    the only single API that misses nothing. Full-page-height fills are the
    body background painted across the whole bedrock page; skip them or the
    union degenerates to the entire page.
    """
    page_h = page.rect.height
    bottom = None
    for kind, bbox in page.get_bboxlog():
        if kind == "ignore-text":  # invisible text, must not drive the crop
            continue
        r = pymupdf.Rect(bbox)
        if r.is_empty or r.is_infinite or r.height >= 0.97 * page_h:
            continue
        bottom = r.y1 if bottom is None else max(bottom, r.y1)
    try:
        for annot in page.annots():
            bottom = annot.rect.y1 if bottom is None else max(bottom, annot.rect.y1)
    except TypeError:
        pass
    return bottom


def content_bottom_pixel(page, dpi=24, stdev_threshold=3.0):
    """Fallback: rasterize and scan rows bottom-up for horizontal variance.

    A vertical gradient background is horizontally uniform (variance ~0);
    real content (text, cards, rules) breaks horizontal uniformity.
    """
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    w, h, buf = pix.width, pix.height, pix.samples
    threshold = stdev_threshold ** 2
    for row in range(h - 1, -1, -1):
        line = buf[row * w:(row + 1) * w]
        mean = sum(line) / w
        if sum((b - mean) ** 2 for b in line) / w > threshold:
            return (row + 1) / dpi * 72.0
    return None


def crop_to_content(doc, padding_px, crop_mode):
    page = doc[0]
    bottom = None
    if crop_mode != "pixel":
        bottom = content_bottom_vector(page)
    if bottom is None:
        bottom = content_bottom_pixel(page)
    if bottom is None:
        sys.exit("could not locate any content on the page")
    new_h = min(page.rect.height, bottom + padding_px * 0.75)  # px -> pt
    # Rewrite both boxes via xref in raw PDF coordinates (y-up) — sidesteps
    # PyMuPDF's top-left flip ambiguity and the set_mediabox side effect of
    # deleting CropBox. Some viewers read MediaBox, some CropBox ∩ MediaBox;
    # writing both identically removes the difference.
    mb = page.mediabox
    box = f"[{mb.x0:.2f} {mb.y1 - new_h:.2f} {mb.x1:.2f} {mb.y1:.2f}]"
    doc.xref_set_key(page.xref, "MediaBox", box)
    doc.xref_set_key(page.xref, "CropBox", box)
    return new_h


def main():
    ap = argparse.ArgumentParser(description="HTML -> single continuous-page PDF")
    ap.add_argument("input", help="source HTML file")
    ap.add_argument("-o", "--output", required=True, help="destination PDF")
    ap.add_argument("--width", type=int, default=1280,
                    help="page width in CSS px (default 1280, snapped to 8px)")
    ap.add_argument("--bedrock", type=int, default=18000,
                    help="initial oversized page height in px (default 18000)")
    ap.add_argument("--padding", type=int, default=32,
                    help="whitespace kept below content, px (default 32)")
    ap.add_argument("--extra-css", help="CSS file appended to the injected print styles "
                    "(breakpoint locks, glassmorphism fallbacks, ...)")
    ap.add_argument("--replace", help="JSON file [[old,new],...] applied to the HTML "
                    "before rendering (redaction / token substitution)")
    ap.add_argument("--forbid", help="text file, one word per line; abort if any "
                    "survives in the HTML or the final PDF text")
    ap.add_argument("--crop", choices=["vector", "pixel"], default="vector",
                    help="content-bottom detection (default vector, auto-falls back)")
    ap.add_argument("--chrome", help="explicit browser executable")
    ap.add_argument("--virtual-time", type=int, default=10000,
                    help="--virtual-time-budget ms (default 10000)")
    ap.add_argument("--max-retries", type=int, default=2,
                    help="bedrock doublings when content overflows (default 2)")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    src = Path(args.input)
    html = src.read_text(encoding="utf-8")
    if args.replace:
        html = apply_replacements(html, args.replace)
    if args.forbid:
        n = check_forbidden(html, args.forbid, "HTML after replacements")
        print(f"forbid check (html): {n} words, clean")

    width = align8(args.width)
    extra = ""
    if args.extra_css:
        extra = Path(args.extra_css).read_text(encoding="utf-8")
    if "</head>" not in html:
        sys.exit("input HTML has no </head>; cannot inject print CSS")

    browser = find_browser(args.chrome)
    # Chrome writes PDFs unreliably to non-ASCII paths; stage everything in TEMP
    workdir = Path(tempfile.gettempdir()) / f"onepage-pdf-{uuid.uuid4().hex[:8]}"
    workdir.mkdir()
    tmp_pdf = workdir / "out.pdf"

    try:
        bedrock = align8(args.bedrock)
        for attempt in range(args.max_retries + 1):
            injected = html.replace(
                "</head>",
                PRINT_CSS.format(width=width, bedrock=bedrock, extra=extra), 1)
            tmp_html = workdir / "in.html"
            tmp_html.write_text(injected, encoding="utf-8")
            render(browser, tmp_html, tmp_pdf, width, args.virtual_time)
            doc = pymupdf.open(tmp_pdf)
            if doc.page_count == 1:
                break
            print(f"content overflowed {bedrock}px bedrock "
                  f"({doc.page_count} pages); doubling")
            doc.close()
            bedrock = align8(bedrock * 2)
        else:
            sys.exit(f"still paginated after {args.max_retries} retries; "
                     f"raise --bedrock explicitly")

        new_h = crop_to_content(doc, args.padding, args.crop)
        final = workdir / "final.pdf"
        doc.save(final)
        doc.close()

        check = pymupdf.open(final)
        page = check[0]
        assert check.page_count == 1
        w_pt, h_pt = page.rect.width, page.rect.height
        if args.forbid:
            text = "".join(p.get_text() for p in check)
            check_forbidden(text, args.forbid, "final PDF text")
            print("forbid check (pdf): clean")
        check.close()

        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(final, dest)

        size_kb = dest.stat().st_size / 1024
        print(f"OK 1 page, {w_pt:.0f}x{h_pt:.0f}pt "
              f"({w_pt/72*96:.0f}x{h_pt/72*96:.0f}px), {size_kb:.0f} KB -> {dest}")
        if h_pt > ACROBAT_LIMIT_PT:
            print(f"warning: height {h_pt:.0f}pt exceeds the 14400pt Acrobat "
                  f"limit; fine in Chrome/Firefox/WeChat, may fail in Acrobat")
        if new_h >= bedrock * 0.75 * 0.985:
            print("note: content nearly fills the bedrock; check the PDF tail "
                  "for accidental truncation")
    finally:
        if args.keep_temp:
            print(f"temp kept: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
