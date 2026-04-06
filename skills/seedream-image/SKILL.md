---
name: seedream-image
description: Generate and edit AI images with Seedream (ByteDance) via AceDataCloud API. Use when creating images from text prompts, editing existing images, or working with high-resolution outputs. Supports Seedream 3.0 T2I, 4.0, 4.5, 5.0, and SeedEdit 3.0 models.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-seedream for tool-use.
---

# Seedream Image Generation

Generate and edit AI images through AceDataCloud's Seedream (ByteDance) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/seedream/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cyberpunk cat wearing VR goggles in a neon city", "model": "doubao-seedream-5-0-260128"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /seedream/tasks` with `{"id": "..."}`.
## Models

| Model | Version | Best For |
|-------|---------|----------|
| `doubao-seedream-5-0-260128` | Seedream 5.0 | Latest, highest quality (default) |
| `doubao-seedream-4-5-251128` | Seedream 4.5 | High quality, balanced |
| `doubao-seedream-4-0-250828` | Seedream 4.0 | Reliable generation |
| `doubao-seedream-3-0-t2i-250415` | Seedream 3.0 T2I | Text-to-image, precise prompt following |
| `doubao-seededit-3-0-i2i-250628` | SeedEdit 3.0 | Image-to-image editing |

## Workflows

### 1. Text-to-Image

```json
POST /seedream/images
{
  "prompt": "a serene Japanese garden with cherry blossoms and a red bridge",
  "model": "doubao-seedream-5-0-260128",
  "size": "1K"
}
```

### 2. Image Editing (Image-to-Image)

Edit an existing image by providing the source image URL(s) and a descriptive prompt. Use the `doubao-seededit-3-0-i2i-250628` model for best editing results.

```json
POST /seedream/images
{
  "prompt": "change the sky to a golden sunset",
  "model": "doubao-seededit-3-0-i2i-250628",
  "image": ["https://example.com/photo.jpg"]
}
```

### 3. Async Generation with Task Polling

Pass a `callback_url` to receive results asynchronously via webhook, or poll `/seedream/tasks` for the result:

```json
POST /seedream/images
{
  "prompt": "an epic fantasy landscape",
  "model": "doubao-seedream-5-0-260128",
  "callback_url": "https://api.acedata.cloud/health"
}
```

Poll the returned `task_id`:

```json
POST /seedream/tasks
{"id": "<task_id>"}
```

## Parameters

### Generation

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | see Models table | Model to use (required) |
| `prompt` | string | Image description (required) |
| `size` | `"1K"`, `"2K"`, `"3K"`, `"4K"`, `"adaptive"` | Output resolution (e.g. `1K`=1024px, `2K`=2048px); `3K` only for Seedream 5.0 |
| `seed` | integer [-1, 2147483647] | Seed for reproducibility (Seedream 3.0 T2I / SeedEdit 3.0 only) |
| `guidance_scale` | number [1, 10] | Prompt adherence strength (3.0 models only; T2I default 2.5, edit default 5.5) |
| `sequential_image_generation` | `"auto"`, `"disabled"` | Generate related images in sequence (5.0, 4.5, 4.0 only) |
| `stream` | boolean | Stream images as they're generated (5.0, 4.5, 4.0 only) |
| `watermark` | boolean | Add AI-generated watermark (default: true) |
| `output_format` | `"jpeg"`, `"png"` | Output file format (Seedream 5.0 only; default: jpeg) |
| `response_format` | `"url"`, `"b64_json"` | Response format (default: url) |
| `tools` | array | Enable tools, e.g. `[{"type": "web_search"}]` (Seedream 5.0 only) |
| `callback_url` | string | Webhook URL for async delivery; returns `task_id` immediately |

### Editing

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image` | Yes (for editing) | Array of image URLs or base64 strings (max 10MB each) |
| `prompt` | Yes | Describe the desired edit |

## Gotchas

- Model names now use the `doubao-*` naming convention (e.g. `doubao-seedream-5-0-260128`)
- Image editing uses the same `/seedream/images` endpoint with the `image` array parameter (no separate edit endpoint)
- `size` replaces separate `width`/`height` params; use `"1K"` for 1024×1024, `"2K"` for 2048×2048, etc.
- `3K` size is only supported by Seedream 5.0; `adaptive` selects the best aspect ratio automatically
- `seed` only works with `doubao-seedream-3-0-t2i-250415` and `doubao-seededit-3-0-i2i-250628`
- `guidance_scale` is only available for the 3.0-series models
- `stream` and `sequential_image_generation` are only available for Seedream 5.0, 4.5, and 4.0
- Pass `callback_url` to get a `task_id` immediately and avoid blocking; poll `/seedream/tasks` for the result — use `"https://api.acedata.cloud/health"` as a placeholder to force async mode without a real webhook

> **MCP:** `pip install mcp-seedream` | Hosted: `https://seedream.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
