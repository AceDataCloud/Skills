---
name: gpt-image-2-5
description: Generate or edit GPT Image 2.5 and 2.6 images through Ace Data Cloud using Flare or Sunburst, including reverse and official variants. Use for image generation, reference-image editing, 2.6 animated GIFs and annotation-guided static edits.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# GPT Image by Ace Data Cloud

Requires ACEDATACLOUD_API_TOKEN in the agent process environment and HTTPS access to api.acedata.cloud. See README.md for installation and key setup.

Use one exact model ID for every request:

- `gpt-image-2.5-flare` — faster generation.
- `gpt-image-2.6-flare` — faster generation.
- `gpt-image-2.5-flare:reverse` — explicit reverse alias, equivalent to `gpt-image-2.5-flare`.
- `gpt-image-2.6-flare:reverse` — explicit reverse alias, equivalent to `gpt-image-2.6-flare`.
- `gpt-image-2.5-sunburst` — higher-fidelity output and editing control.
- `gpt-image-2.6-sunburst` — higher-fidelity output and editing control.
- `gpt-image-2.5-sunburst:reverse` — explicit reverse alias, equivalent to `gpt-image-2.5-sunburst`.
- `gpt-image-2.6-sunburst:reverse` — explicit reverse alias, equivalent to `gpt-image-2.6-sunburst`.
- `gpt-image-2.5-flare:official` — Flare using the official, token-billed variant.
- `gpt-image-2.6-flare:official` — Flare using the official, token-billed variant.
- `gpt-image-2.5-sunburst:official` — Sunburst using the official, token-billed variant.
- `gpt-image-2.6-sunburst:official` — Sunburst using the official, token-billed variant.

Do not send `gpt-image-2.5` or `gpt-image-2.5:reverse`; they are not model IDs. To explicitly select a reverse variant, replace `model` in Generate or Edit with the complete `:reverse` alias above; preserve the suffix. Both aliases support generation JSON, URL-edit JSON and multipart file edits with the same parameter limits as their unsuffixed names.

## Install and connect from skills.sh

This integration is maintained by **Ace Data Cloud**; it is not an official GPT Image publisher listing. Install only this Skill with `npx skills add acedatacloud/skills --skill gpt-image-2-5 --yes`, or use the [public skills.sh page](https://skills.sh/acedatacloud/skills/gpt-image-2-5). Keep the slug `gpt-image-2-5` when selecting it.

Read the [illustrated first-run guide](README.md) ([简体中文](readme.zh-CN.md)) for registration, **Applications → General application**, API key access and price checks, and the environment variable location for your coding agent. For skills.sh installations, use this guide; any ClawHub-specific setup applies only to OpenClaw. The shared references linked here are online because focused installs do not include sibling `_shared/` folders.

> **Setup:** See [authentication](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md) for token setup.

## Regional catalog check

Before recommending GPT Image, inspect the OpenAI service's current public `image_unavailable_regions` and the image API/guide `unavailable_regions` from the caller's environment. The service record is available at `GET https://platform.acedata.cloud/api/v1/services/?id=06f2acb7-e4d4-43de-9909-76e27b4e2355`.

Mainland-China catalog views hide OpenAI image generation/editing and companion guides. Raw REST results may still contain marked rows; honor the metadata rather than treating presence as publication. Visibility follows the requesting visitor's IP, not the display language or a `?country=` override. Do not recommend region-hidden images from a cached global catalog or hide unrelated OpenAI capabilities. This presentation filtering does not change API routing or billing and is not proof of retirement or revoked API access. For a user-selected model, report any discovery limitation and check actual account access, key restrictions and pricing before submitting; do not silently substitute another model.

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
  -F "model=gpt-image-2.5-sunburst:reverse" \
  -F "prompt=Keep the subject and composition; change only the background to dark navy." \
  -F "image=@input.png" \
  -F "size=1024x1024" \
  -F "n=1"
```

The result is in `data[].url`.

## Shared contract

- `size` may be `auto` or `WIDTHxHEIGHT`.
- Static PNG/JPEG/WebP custom dimensions use multiples of 16, max side 3840, 655,360–8,294,400 pixels, and aspect ratio at most 3:1.
- For generation and editing, `quality` accepts `auto` (default), `low`, `medium`, or `high`. GPT Image 2.5 and 2.6 Flare/Sunburst (including their `:reverse` and `:official` variants) additionally support `xhigh` and `max`; do not use those extra levels with other GPT Image models.
- Pass `quality` in generation JSON, URL-edit JSON, or multipart file edits (for example, `"quality":"xhigh"` in JSON or `-F "quality=max"` in multipart). On `:official` variants, quality affects token usage; the displayed pre-request price is an estimate, not the final charge.
- `n` accepts 1–10. Use URL output for `n>1`; `b64_json` requires `n=1`.
- Unsuffixed 2.5 Flare/Sunburst and their `:reverse` aliases bill per successful image, with a base price of 0.19 Credits per image for generation and editing. The corresponding 2.6 models bill 0.22 Credits per image for generation and editing. Check current account pricing and final usage records; token statistics in a reverse response do not change its billing mode.
- During automatic recovery, 2.5 reverse models (including `:reverse` aliases) may be fulfilled using GPT Image 2.5 Flare; the requested model and per-successful-image billing remain unchanged. Do not resubmit to force recovery or silently change the user's requested model.
- The `:official` variants bill for actual text, reference-image, and output-image tokens; use returned usage records for final cost.
- For long jobs, pass `async: true` or `callback_url`, then poll `POST /openai/tasks` with `{"id":"<task_id>"}`.
- Image editing accepts URL input in JSON or local files with multipart form data.

For 2.6, use the complete Flare/Sunburst ID; `gpt-image-2.6` is not valid. No cross-model fallback is configured for 2.6. Static generation and editing support PNG/JPEG/WebP, including 4K `3840x2160` or `2160x3840`; pass concrete pixels, not `size: "4K"`. `4096x4096` exceeds the pixel limit. SVG is not exposed. Official 2.6 variants use the same token rates as 2.5.


## Animated GIF (GPT Image 2.6)

GIF generation and editing support `gpt-image-2.6-flare`, `gpt-image-2.6-flare:reverse`, `gpt-image-2.6-flare:official`, `gpt-image-2.6-sunburst`, `gpt-image-2.6-sunburst:reverse`, and `gpt-image-2.6-sunburst:official`. Do not silently change the requested model.

Set `output_format: "gif"` in generation JSON, URL-edit JSON, or multipart file edits. GIF defaults to a `512x512` preview, `frame_count: 9`, and `frame_duration_ms: 200`; omitted size or `size: "auto"` uses the GIF preview default. The returned GIF can have different actual dimensions. GIF frame counts must be integers from 2 to 16. Frame duration must be an integer from 20 to 655350 ms, rounded to the nearest 10ms when encoded. Frame controls apply only to GIF. Native animation, frame timing, and looping are preserved in both URL and Base64 output. Static 4K sizes do not apply to GIF.

```json
{"model":"gpt-image-2.6-flare","prompt":"A red ball bouncing in a seamless loop","output_format":"gif","size":"512x512","frame_count":9,"frame_duration_ms":200,"n":1,"async":true}
```

For image-to-GIF, send the same GIF controls to `/openai/images/edits` with `image` and a prompt describing the motion and what to preserve. Use an image URL in JSON or `-F "image=@input.png"` with multipart; pass GIF controls as form fields for multipart.

Keep the original task ID and poll it to completion; do not resubmit a pending job. `n` counts returned GIF files, not animation frames. The normal per-successful-file or official token billing for the requested model still applies; inspect actual usage for the final charge.

Do not combine GIF with `mask`, `markup`, `output_compression`, `prompt_rewriter` or partial-image streaming. Incompatible combinations are rejected before generation. Size, frame count and `n` share a model pixel budget: ordinary Flare has a verified `1024x1024`, 2-frame combination, not blanket support for every 1K combination or 4K GIF. Start with the recommended `512x512`, 9-frame, 200ms settings.

## Planning complexity (GPT Image 2.6 only)

For generation or editing, pass `complexity: "low"`, `"medium"` or `"high"` in JSON, or `-F "complexity=medium"` in multipart. Omission uses the model default `high`. Complexity controls composition planning independently of rendering `quality`; it has no separate per-request surcharge, while official variants still bill actual token usage. Do not send it to other models.

## Annotation-guided static editing (GPT Image 2.6 only)

1. Prepare a PNG annotation layer with transparent pixels and the same dimensions as the first reference image after orientation correction. Mark the areas to change and explain the intended changes in `prompt`. Each image must be at most 16,777,216 pixels; the annotation must be at most 40MB.
2. Submit `image`, `prompt` and `markup` to `/openai/images/edits` with the user's exact 2.6 model. JSON `markup` accepts an HTTPS URL, PNG base64 data URL or an object containing only `image_url`; multipart accepts an annotation file or HTTPS URL. `file_id` is not supported.
3. Use static PNG/JPEG/WebP output. Do not combine `markup` with `mask`, GIF or `prompt_rewriter`. Omit `input_fidelity` for GPT Image 2.6; it is not applicable.
4. Poll the same task ID to its terminal result and use the returned media URL.

```bash
curl -X POST https://api.acedata.cloud/openai/images/edits \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -F "model=gpt-image-2.6-sunburst:reverse" \
  -F "image=@input.png" \
  -F "markup=@annotation.png" \
  -F "prompt=Change only the circled background area to dark navy; preserve the subject." \
  -F "output_format=png" \
  -F "complexity=medium" \
  -F "n=1" \
  -F "async=true"
```
