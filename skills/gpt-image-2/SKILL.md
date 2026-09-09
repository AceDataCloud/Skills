---
name: gpt-image-2
description: Generate and EDIT images with OpenAI gpt-image-2, gpt-image-2.5-flare, and gpt-image-2.5-sunburst via AceDataCloud API. Use when you need high-fidelity images from a prompt, or to edit/composite existing images (e.g. fuse a real logo/QR/screenshot into a scene, keep characters consistent, restyle). Strong at legible text and faithful editing.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# gpt-image-2 — Image Generation & Editing

OpenAI `gpt-image-2`, `gpt-image-2.5-flare`, and `gpt-image-2.5-sunburst` through AceDataCloud. Both endpoints are synchronous by default and also support asynchronous task responses. Their standout is **editing**: feed real images (logos, QR codes, product shots, screenshots) and they composite/restyle them faithfully — great for on-brand video assets and character consistency.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## 1. Generate (text → image)

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2","prompt":"a clean dark tech hero background with a glowing API hub, lots of negative space","size":"1792x1024","n":1}'
```

## 2. Edit / composite (images + prompt → image)  ← the powerful one

Multipart. Pass one or more source images via repeated `image[]` (local files with
`@`, or URLs). Use it to **fuse a real logo/QR into a generated scene**, keep a subject
consistent across scenes, or restyle a screenshot.

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

Response (both endpoints): synchronous requests return `{"created":0,"data":[{"url":"https://...png"}]}`; asynchronous requests return `{"task_id":"..."}`.

## Sizes

`size` is `WxH` (a preset) or `"auto"`. Common presets:

| Aspect | Sizes |
|---|---|
| 16:9 | `1792x1024` (HD), `2048x1152`, `3840x2160` (4K) |
| 9:16 | `1024x1792`, `1152x2048`, `2160x3840` |
| 1:1 | `1024x1024`, `2048x2048`, `2880x2880` (4K) |

(Omit `size` or use `"auto"` to let the model pick. Custom sizes must have both sides a
multiple of 16, each side ≤ 3840, total pixels between 655,360 and 8,294,400, and an aspect
ratio ≤ 3:1 — otherwise 400.)

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
