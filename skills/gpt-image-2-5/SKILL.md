---
name: gpt-image-2-5
description: Generate or edit images with GPT Image 2.5 Flare or Sunburst through AceDataCloud. Choose Flare for speed or Sunburst for high-fidelity control; never use the unsupported bare gpt-image-2.5 name.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# GPT Image 2.5

Use one exact model ID for every request:

- `gpt-image-2.5-flare` — faster generation.
- `gpt-image-2.5-sunburst` — higher-fidelity output and editing control.

Do not send `gpt-image-2.5`; it is not a model ID.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Generate

```bash
curl -X POST https://api.acedata.cloud/openai/images/generations \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-image-2.5-flare","prompt":"A clean product photograph on a pale studio background, no text","size":"1024x1024","n":1}'
```

## Edit

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -F "model=gpt-image-2.5-sunburst" \
  -F "prompt=Keep the subject and composition; change only the background to dark navy." \
  -F "image=@input.png" \
  -F "size=1024x1024" \
  -F "n=1"
```

The result is in `data[].url`.

## Shared contract

- `size` may be `auto` or `WIDTHxHEIGHT`.
- Custom dimensions use multiples of 16, max side 3840, 655,360–8,294,400 pixels, and aspect ratio at most 3:1.
- `quality` accepts `auto`, `low`, `medium`, or `high`.
- `n` accepts 1–10 and billing uses the number of images returned. Use URL output for `n>1`; `b64_json` requires `n=1`.
- For long jobs, pass `async: true` or `callback_url`, then poll `POST /openai/tasks` with `{"id":"<task_id>"}`.
- Image editing JSON accepts one URL or an array of up to 16 URLs; multipart accepts repeated `image` fields for local files.
