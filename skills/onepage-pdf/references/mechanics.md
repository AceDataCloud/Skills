# Chrome print-rendering mechanics

Why this tool crops instead of calculating, and what to do when output looks
wrong. Findings verified against Chromium source / specs / production code
(Gotenberg), June 2026.

## Contents

- [Why height cannot be predicted](#why-height-cannot-be-predicted)
- [Media queries vs @page — two viewports](#media-queries-vs-page--two-viewports)
- [The 1.5x hidden shrink](#the-15x-hidden-shrink)
- [Unit rounding and the phantom page](#unit-rounding-and-the-phantom-page)
- [PDF size limits](#pdf-size-limits)
- [Fidelity losses in PDF output](#fidelity-losses-in-pdf-output)
- [Resource readiness](#resource-readiness)
- [CJK pitfalls](#cjk-pitfalls)
- [Crop internals](#crop-internals)
- [Alternative route: CDP measured height](#alternative-route-cdp-measured-height)

## Why height cannot be predicted

Screen-measured `scrollHeight` does not match the printed layout height:

- `page.pdf()` / `--print-to-pdf` render with **print** media CSS; measuring on
  screen measures a different layout.
- Print media queries evaluate against a different width than the layout width
  (next section), shifting breakpoints.
- Web fonts arriving after measurement change line heights.
- The px→inch→pt conversion chain rounds non-monotonically (puppeteer#2278).

Hence: render onto an oversized bedrock page, measure the result, crop.

## Media queries vs @page — two viewports

Per css-page-3 §7.1, media queries **must ignore `@page size`** (anti-cycle
rule) and evaluate against the default paper. Measured in Chrome: MQ width is
the default paper's page area, **~741px** (US Letter minus default margins),
regardless of any `@page` declaration.

Meanwhile vw/vh resolve against the **first page area** — which DOES honor
`@page size` — with ~1% drift from device-unit rounding. So one document
evaluates MQ at 741px and vw at the @page width simultaneously. Container
queries follow the laid-out container and are the only reliable responsive
mechanism in print.

Practical rule: lock every breakpoint ≥741px to its desktop value via
`--extra-css`, and replace vh/vw sizing with px.

## The 1.5x hidden shrink

`printingMaximumShrinkFactor = 1.5` in Blink: if the widest unbreakable content
exceeds the page width, Chrome relayouts and **scales the whole document down
by up to 1.5x** to fit (beyond that it clips). One overflowing element changes
the scale of everything. Keep actual content width ≤ `--width`.

## Unit rounding and the phantom page

Chrome converts px → inches → pt with rounding errors up to ~0.2% (MediaBox
73pt becomes 72.959999). A height short by a fraction of a pt spills one line
onto a second page. Mitigations used here:

- widths/heights snapped to 8px (8px = 6pt exactly);
- the bedrock is intentionally huge, so rounding never matters at render time;
- Gotenberg's equivalent trick for the CDP route is `pageRanges: "1"`.

## PDF size limits

- 14400pt (200in, ≈19200px) is the **Acrobat implementation limit** from ISO
  32000-1 Annex C — not a format limit. PDF 2.0 drops it.
- Chrome happily writes larger pages (verified: 22500pt, no clamp, no
  UserUnit). Chrome/Firefox/PDFium/WeChat render them; old Acrobat may refuse.
- The script warns when output exceeds 14400pt; that's a compatibility note,
  not an error.

## Fidelity losses in PDF output

| Feature | Behavior in PDF | Fix |
|---|---|---|
| `backdrop-filter` blur | **Silently dropped** (crbug 40895818); translucent bg layer survives | Print fallback: `backdrop-filter:none` + near-opaque `background` |
| `background-attachment: fixed` | Painted on page 1 only, off-spec | Injected CSS forces `scroll` |
| `box-shadow` | Fine, stays vector | — |
| Perspective transforms | Rendered as identity (SkPDF) | Avoid in print |
| Element behind CSS `filter`/image filter | Rasterized; text loses selectability | Avoid filters on text containers |
| Backgrounds in general | Need `print-color-adjust: exact` (injected) | — |

## Resource readiness

CLI `--print-to-pdf` waits for the `load` event only — not fonts, not
JS-injected content. The script passes:

- `--virtual-time-budget=10000`: fast-forwards timer-driven JS (experimental;
  does not wait for slow networks or CPU);
- `--run-all-compositor-stages-before-draw`: ensures rasterization completes
  before capture.

If fonts or late-loading images still miss: raise `--virtual-time`, inline
resources as data URLs, or preload fonts in `<head>`. Note headless
`--print-to-pdf` silently refuses external resources referenced from inside
`@page` margin-box CSS — inline those as data URLs.

`loading="lazy"` images render fine in current headless print (verified Chrome
149); for older Chrome force `loading="eager"` via `--replace`.

## CJK pitfalls

- Set `<html lang="zh-CN">` — without it, fontconfig on Linux may pick the
  Thin weight of Noto CJK for body text.
- Docker/CI images need `fonts-noto-cjk` installed or all CJK renders as tofu.
- CJK fonts often ship Regular only; `font-weight:600+` triggers synthetic
  bold that looks smeared in PDF. Load real weight files (e.g. Noto Sans SC
  500/700).
- Webfonts without CJK glyphs fall back to system fonts on screen but may
  embed nothing in the PDF — Acrobat shows missing glyphs. Declare a CJK
  fallback explicitly in `font-family`.

## Crop internals

- Content bottom comes from `page.get_bboxlog()` — a render-level command log
  covering text, images, vector paths, and contents of Form XObjects (the
  APIs `get_text('blocks')` + `get_drawings()` miss XObject internals and
  inline images). `ignore-text` (invisible text) entries are skipped, as are
  fills taller than 97% of the page (the body background painted across the
  whole bedrock).
- Pixel mode (`--crop pixel`) rasterizes at 24dpi and scans rows bottom-up for
  horizontal variance > threshold; vertical gradients are horizontally uniform
  so they don't count as content. Use it when vector mode keeps decorative
  geometry that extends below the real content.
- Both MediaBox and CropBox are rewritten to the same rect via `xref_set_key`
  in raw PDF (y-up) coordinates. This avoids PyMuPDF's `set_mediabox` side
  effect (it deletes CropBox) and the viewer ambiguity between viewers that
  honor MediaBox (some mobile/embedded viewers) vs CropBox (Acrobat, pdf.js).

## Alternative route: CDP measured height

Gotenberg 8's production `singlePage=true` implementation (tasks.go):

```
Emulation.setEmulatedMedia(media="print")
m = Page.getLayoutMetrics()              # cssContentSize is the authoritative height
Page.printToPDF(paperWidth = W/96,
                paperHeight = m.cssContentSize.height/96,
                marginTop=0, ..., pageRanges="1")   # "1" discards rounding spill
```

Pros: no bedrock, no crop, exact MediaBox at render time. Cons: requires a CDP
client (websocket) instead of a bare CLI call; lazy-load / viewport-relative
layouts can still mismeasure (gotenberg#1046). This tool deliberately stays on
the CLI+crop route for zero runtime dependencies beyond PyMuPDF; switch to CDP
only if a page class consistently defeats the crop heuristics.
