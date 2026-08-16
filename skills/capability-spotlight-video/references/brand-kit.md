# Ace Data Cloud video brand kit

## Canonical source

Use only:

`https://cdn.acedata.cloud/logo.png`

It is the stable transparent 885×282 RGBA source. Its visible content is approximately x=50–828, y=47–230.

Never use the retired 1600×900 upload `36066a80-7a14-4fd9-a7bc-7722f3be8285`, screenshots, color-key extraction, generated/redrawn logos, or the bitmap `AceData/ceData` wordmark.

## Construct the lockup

The source contains an A symbol plus a legacy wordmark. Crop the **A symbol only** from the transparent source, preserving its pixels and aspect ratio. For the canonical 885×282 file, the symbol occupies alpha columns `x=50…250` and the legacy wordmark begins at `x=264`; use crop box `(50, 47, 251, 231)` (right/bottom exclusive), then trim only transparent padding. Verify the derivative contains exactly the first occupied column run and no non-transparent pixel originating at source `x>=264`. A width-ratio crop is forbidden because it can retain `ceData`. Author the formal name as live HTML text:

`ACE DATA CLOUD`

Use a flex/grid lockup with separate controllable elements:

- symbol optical box: square; object-fit contain; no CSS distortion;
- wordmark: uppercase, 600–700 weight, tracking 0.08–0.14em;
- gap: 0.28–0.38× the symbol's visible width;
- align optical vertical centers, then adjust the wordmark baseline independently;
- minimum visible opening symbol width at 1920×1080: 170px;
- minimum authored wordmark cap height: 72px;
- lockup clear space: at least 0.5× symbol width on every edge;
- no black/white rectangular source canvas around the symbol.

Do not place the symbol inline as the letter A inside another bitmap wordmark. The formal name must read exactly `ACE DATA CLOUD`.

## Usage

- Full lockup exactly twice: decoded frame 0/open and final CTA.
- Middle scenes: authored eyebrow `ACE DATA CLOUD / <CAPABILITY>` only; no logo watermark.
- Dark background: preserve cyan/blue symbol; wordmark #F8FAFC.
- Light background: place lockup on a deliberate dark brand field; do not recolor the source symbol.
- URLs: `https://platform.acedata.cloud` and `https://studio.acedata.cloud` as live HTML text.
- Final CTA must include one readable action phrase such as `EXPLORE THE API`, `BUILD WITH ACE DATA CLOUD`, or `OPEN THE STUDIO`; an abstract symbol, endpoint, or decorative target alone is not a CTA.

## Reviewer geometry checks

At frame 0 and CTA verify:

1. the A symbol is the canonical source crop, not a redraw;
2. no legacy `AceData` or `ceData` bitmap appears;
3. symbol and authored wordmark share a convincing optical center and baseline;
4. gap and clear space are balanced at full resolution;
5. neither element is stretched, cropped, blurred, or inside a source rectangle;
6. the lockup is readable before any entrance animation; decoded frame 0 is authoritative.
