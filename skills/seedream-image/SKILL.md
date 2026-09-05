---
name: seedream-image
description: Generate and edit AI images with Seedream (ByteDance) via AceDataCloud API. Use when creating images from text prompts, editing existing images, or working with high-resolution outputs. Supports Seedream 4.0, 4.5, and 5.0 models.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-seedream for tool-use.
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
| `doubao-seedream-5-0-260128` | Seedream 5.0 Lite | Current standard 5.0 model |
| `doubao-seedream-5-0-pro-260628` | Seedream 5.0 Pro | Highest-quality Seedream 5.0 model |
| `doubao-seedream-5-0-lite-260128` | Seedream 5.0 Lite | Lite 5.0 variant |
| `doubao-seedream-4-5-251128` | Seedream 4.5 | High quality, balanced |
| `doubao-seedream-4-0-250828` | Seedream 4.0 | Reliable generation |

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

Edit an existing image by providing the source image URL(s) and a descriptive prompt. Seedream 5.0 Pro, 5.0 Lite, 4.5, and 4.0 all support image input.

```json
POST /seedream/images
{
  "prompt": "change the sky to a golden sunset",
  "model": "doubao-seedream-5-0-260128",
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
{"action": "retrieve", "id": "<task_id>"}
```

Batch poll multiple tasks with `{"action":"retrieve_batch","ids":["<task_id>"]}`. `action` defaults to `"retrieve"`.

## Output

`/seedream/images` returns JSON with `success`, `task_id`, `trace_id`, `data[]` (`image_url` or `b64_json`, `prompt`, `size`, `output_format`, optional `error`; layer decomposition may include `z_index`, `name`, `description`, `bounding_box`), plus optional `usage` and `tools`. With `stream: true`, request `Accept: application/x-ndjson` and process events such as `image_generation.partial_succeeded`.

## Parameters

### Generation

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | see Models table | Model to use (required) |
| `prompt` | string | Image description (required except for 5.0 Pro layer decomposition) |
| `size` | `"1K"`, `"1.5K"`, `"2K"`, `"3K"`, `"4K"`, `"auto"`, or custom `"WIDTHxHEIGHT"` | Output resolution; model-specific constraints apply |
| `sequential_image_generation` | `"auto"`, `"disabled"` | Generate related images in sequence (5.0, 4.5, 4.0 only) |
| `sequential_image_generation_options` | object | Options for sequential generation, e.g. `{"max_images": 1..15}` |
| `stream` | boolean | Stream images as they're generated (5.0, 4.5, 4.0 only) |
| `watermark` | boolean | Add AI-generated watermark (default: true) |
| `output_format` | `"jpeg"`, `"png"` | Output file format (Seedream 5.0 only; default: jpeg) |
| `response_format` | `"url"`, `"b64_json"` | Response format (default: url) |
| `tools` | array | Enable tools, e.g. `[{"type": "web_search"}]` (Seedream 5.0 only) |
| `optimize_prompt_options` | object | Prompt optimization, e.g. `{"mode":"standard"}` or `{"mode":"fast"}`; Lite allows `standard` only |
| `async` | boolean | Force async task behavior |
| `layer_decomposition` | boolean | Seedream 5.0 Pro only; requires `image` and `layer_decomposition: true` |
| `background` | `"transparent"`, `"opaque"` | Background mode |
| `callback_url` | string | Webhook URL for async delivery; returns `task_id` immediately |

### Editing

| Parameter | Required | Description |
|-----------|----------|-------------|
| `image` | Yes for editing/layer decomposition | Image URL/base64 string or array; arrays allow up to 14 images generally, but Seedream 5.0 Pro generation/editing allows up to 10 |
| `prompt` | Yes | Describe the desired edit |

## Gotchas

- Model names now use the `doubao-*` naming convention (e.g. `doubao-seedream-5-0-260128`)
- Image editing uses the same `/seedream/images` endpoint with the `image` array parameter (no separate edit endpoint)
- `size` replaces separate `width`/`height` params; it supports `"1K"`, `"1.5K"`, `"2K"`, `"3K"`, `"4K"`, `"auto"`, and custom `"WIDTHxHEIGHT"`; use `auto`, not `adaptive`
- Seedream 5.0 Pro generation/editing supports `1K`/`1.5K`/`2K`/custom sizes; Pro layer decomposition supports `auto`/`1K`/`1.5K`/`2K`
- `doubao-seedream-5-0-260128` and `doubao-seedream-5-0-lite-260128` support `2K`/`3K`/`4K`/custom sizes
- Seedream 4.x does not support `layer_decomposition`, `background`, `output_format`, or `tools`
- Seedream 5.0 Pro does not support `stream`, `sequential_image_generation`, or `tools`; Pro layer decomposition also does not support `background`
- `stream` and `sequential_image_generation` are only available for Seedream 5.0, 4.5, and 4.0
- Pass `callback_url` or `"async": true` to get a `task_id` immediately and avoid blocking; poll `/seedream/tasks` for the result — use `"https://api.acedata.cloud/health"` as a placeholder callback if a webhook URL is required by your client

> **MCP:** `pip install mcp-seedream` | Hosted: `https://seedream.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
