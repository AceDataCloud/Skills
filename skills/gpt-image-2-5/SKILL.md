---
name: gpt-image-2-5
description: GPT Image 2.5 by Ace Data Cloud. Generate and edit images using Flare for speed or Sunburst for higher-fidelity control. Use when the user asks for GPT Image, gpt-image-2.5-flare or gpt-image-2.5-sunburst image generation or editing.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in the agent process environment and HTTPS access to api.acedata.cloud. See README.md for installation and key setup.
---

# GPT Image by Ace Data Cloud

Use one exact model ID for every request:

- `gpt-image-2.5-flare` — faster generation.
- `gpt-image-2.5-sunburst` — higher-fidelity output and editing control.
- `gpt-image-2.5-flare:official` — Flare using the official, token-billed variant.
- `gpt-image-2.5-sunburst:official` — Sunburst using the official, token-billed variant.

Do not send `gpt-image-2.5` or `gpt-image-2.5:reverse`; they are not model IDs.

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
- For generation and editing, `quality` accepts `auto` (default), `low`, `medium`, or `high`. Only `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst` (including their `:official` variants) additionally support `xhigh` and `max`; do not use those extra levels with other GPT Image models.
- Pass `quality` in generation JSON, URL-edit JSON, or multipart file edits (for example, `"quality":"xhigh"` in JSON or `-F "quality=max"` in multipart). On `:official` variants, quality affects token usage; the displayed pre-request price is an estimate, not the final charge.
- `n` accepts 1–10 and billing uses the number of images returned. Use URL output for `n>1`; `b64_json` requires `n=1`.
- The `:official` variants bill for actual text, reference-image, and output-image tokens; use returned usage records for final cost.
- For long jobs, pass `async: true` or `callback_url`, then poll `POST /openai/tasks` with `{"id":"<task_id>"}`.
- Image editing accepts URL input in JSON or local files with multipart form data.
