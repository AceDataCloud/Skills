---
name: gpt-image-2
description: Generate and EDIT images with OpenAI gpt-image-2 via AceDataCloud API. Use when you need high-fidelity images from a prompt, or to edit/composite existing images (e.g. fuse a real logo/QR/screenshot into a scene, keep characters consistent, restyle). Strong at legible text and faithful editing.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# gpt-image-2 — Image Generation & Editing

OpenAI `gpt-image-2` through AceDataCloud. Two endpoints, both **synchronous** (return image url(s) directly). Its standout is **editing**: feed real images (logos, QR codes, product shots, screenshots) and it composites/restyles them faithfully — great for on-brand video assets and character consistency.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

Model variants: use `gpt-image-2` by default, `gpt-image-2:official` for the official stable channel with true 2K / 4K output at 2× price, or `gpt-image-2:reverse` for the cost-optimized equivalent route.

## 1. Generate (text → image)

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"a clean dark tech hero background with a glowing API hub, lots of negative space","size":"1792x1024","n":1}'
```

## 2. Edit / composite (images + prompt → image)  ← the powerful one

Multipart. Pass one or more source images via repeated `image[]` (local files with
`@`, or URLs). JSON requests can also pass `image` as a URL, base64 string, or an
array of up to 16 images. Use it to **fuse a real logo/QR into a generated scene**,
keep a subject consistent across scenes, or restyle a screenshot.

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -F "model=gpt-image-2" \
  -F "prompt=Place this logo crisply in the top-left on the tech background; keep the logo's exact colors and shape." \
  -F "image[]=@background.png" \
  -F "image[]=@logo.png" \
  -F "size=1792x1024" \
  -F "n=1"
```

Response (both endpoints): `{"data":[{"url":"https://...png"}]}` → download `data[0].url`.

## Sizes

`size` is `WIDTHxHEIGHT` or `"auto"`. Common presets:

| Aspect | Sizes |
|---|---|
| 16:9 | `1792x1024` (HD), `2048x1152`, `3840x2160` (4K) |
| 9:16 | `1024x1792`, `1152x2048`, `2160x3840` |
| 1:1 | `1024x1024`, `2048x2048`, `2880x2880` (4K) |
| 4:3 | `1536x1024`, `2048x1536`, `3264x2448` |
| 3:4 | `1024x1536`, `1536x2048`, `2448x3264` |

For generation, `size: "auto"` plans the canvas from explicit size/ratio hints in
the prompt; omitting `size` uses the model default aspect ratio. For edits, omitting
`size` is equivalent to `"auto"`: `gpt-image-2` first honors explicit prompt size
intent, then falls back to the first reference image size if no usable size intent is
found. Custom sizes must have both sides as multiples of 16, long side ≤ 3840, and
total pixels ≤ 8,294,400 — otherwise 400. Pass an explicit `WIDTHxHEIGHT` when you
need exact control; completed generations are not retried automatically for output
pixel differences, avoiding duplicate generation charges.

## Tips

- **Editing keeps things faithful** — to place a logo/QR exactly, pass it as one of the
  `image[]` and say "keep its exact colors/shape, do not redraw it".
- For **character/scene consistency** across video beats, generate one hero image, then
  `edits` it per beat instead of regenerating from scratch.
- Text in images renders legibly — good for titles/labels you don't want to overlay in HTML.
- `n` accepts **1–10** and you are billed **per image returned**, not per request — `n: 4`
  costs 4×. (`response_format: "b64_json"` still requires `n: 1`.)
- Both endpoints are synchronous by default. For long 4K jobs pass `callback_url` (optionally
  with `async: true`) and poll `POST /openai/tasks` with `{"id": "<task_id>"}`.
