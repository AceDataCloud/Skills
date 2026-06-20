---
name: onepage-pdf
description: Convert an HTML page into a single continuous-page PDF (one tall page, no pagination breaks), preserving desktop layout, backgrounds and selectable text. Use when the user asks to turn an HTML file/report/proposal into a "single-page PDF", "long PDF", "不分页 PDF", "单页 PDF", "长图式 PDF", or complains that an HTML-to-PDF export breaks into pages or cuts content. Supports optional string redaction with leak verification.
license: MIT
metadata:
  author: xntj-ai
  version: "1.0"
  source: https://github.com/xntj-ai/onepage-pdf
compatibility: No API token required. Requires Python 3.10+ with `pymupdf` (`pip install pymupdf`) and a local Chrome or Edge browser. Runs fully offline against local HTML — does not call api.acedata.cloud.
---

# onepage-pdf

> Vendored from [github.com/xntj-ai/onepage-pdf](https://github.com/xntj-ai/onepage-pdf)
> by 张拼拼 · XNTJ, under the MIT License. See [LICENSE](LICENSE).

Render HTML to one tall PDF page via headless Chrome, then crop the page to the
real content height with PyMuPDF. Height is never predicted (print layout is
not screen layout); it is measured after rendering, which is exact.

**Requires:** Python with `pymupdf`, plus a local Chrome or Edge. No API token.

## Workflow

### 1. Inspect the source HTML first

Read the HTML and check four things; they decide whether `--extra-css` is needed:

1. **Responsive breakpoints.** Print media queries evaluate against the default
   paper width (~741px), NOT the `@page` size. Any `@media (max-width: N)` with
   N ≥ 741 will fire during print and collapse the desktop layout. For each such
   rule, write an override locking the desktop value with `!important`
   (e.g. `.grid{grid-template-columns:repeat(3,1fr)!important}`).
2. **Glassmorphism.** `backdrop-filter` blur is silently dropped in PDF output.
   If glass elements sit on busy backgrounds, add a print fallback:
   `.glass{backdrop-filter:none!important;background:rgba(255,255,255,.88)!important}`.
3. **Scroll-reveal animations.** Common class patterns (`fade*`, `reveal*`,
   `animate*`, `aos`) are forced visible automatically. Anything else that
   starts at `opacity:0` needs an explicit `opacity:1!important` override.
4. **vh/vw sizing.** Viewport units resolve against the page area in print and
   drift ~1%; a `min-height:100vh` hero becomes ~187in tall on the bedrock
   page. Override such rules with fixed px values.

Put all overrides in one CSS file and pass it via `--extra-css`.

### 2. Convert

Paths below are relative to this skill directory.

```bash
python scripts/onepage_pdf.py input.html -o output.pdf --width 1280 \
    [--extra-css fixes.css] [--replace subs.json --forbid words.txt]
```

- `--width`: match the design width of the page (snapped to 8px; non-8px
  page sizes hit MediaBox rounding bugs that spawn phantom pages).
- `--replace`: JSON `[["old","new"], ...]`, applied in order — put longer /
  more specific strings first. Use for redaction before publishing.
- `--forbid`: one word per line; the script aborts if any survives in the
  HTML or in the final PDF text layer. Always pair with `--replace`.
- `--crop pixel`: switch to raster row-scanning if the vector crop misjudges
  (e.g. a decorative element painted taller than the real content).

The script self-handles: oversized-bedrock rendering with auto-retry on
overflow, content cropping (MediaBox + CropBox rewritten identically for
viewer compatibility), CJK-safe output paths, single-page assertion.

A bundled example lives in `examples/` — try it end to end:

```bash
python scripts/onepage_pdf.py examples/demo.html -o /tmp/demo.pdf \
    --width 1280 --extra-css examples/demo-fixes.css
```

### 3. Verify

The script prints `OK 1 page, WxHpt`. Then:

1. Render a thumbnail and eyeball it (layout intact, no collapsed grids,
   backgrounds present, nothing cut at the bottom):
   ```python
   import pymupdf
   doc = pymupdf.open("output.pdf")
   doc[0].get_pixmap(dpi=40).save("check.png")
   ```
2. If redaction was used, the forbid check already ran against the PDF text;
   still spot-check the rendered image for sensitive content in raster form.
3. Heed the script warnings: heights above 14400pt break Acrobat (Chrome,
   Firefox and WeChat preview are fine); "content nearly fills the bedrock"
   means inspect the tail for truncation.

## Troubleshooting and mechanics

Read [references/mechanics.md](references/mechanics.md) when output looks wrong
(collapsed layout, missing backgrounds, blank page, phantom second page, blurry
or missing CJK glyphs) — it documents the Chrome print-rendering rules this
tool is built around, plus the CDP-based alternative route.
