---
name: qwen-image
description: Generate and edit images with Qwen Image 3 via AceDataCloud API. Use for text-to-image generation and image-guided editing with Qwen Image 3 and Qwen Image 3 Pro.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Qwen Image 3

Generate and edit AI images through AceDataCloud's Qwen Image API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/qwen-image/images \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-image-3.0","prompt":"a watercolor fox in a moonlit forest","size":"1024x1024"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /qwen-image/tasks` with `{"id":"..."}` or `{"ids":["..."],"action":"retrieve_batch"}`.

## Models

| Model | Best For |
|-------|----------|
| `qwen-image-3.0` | General text/image generation and editing |
| `qwen-image-3.0-pro` | Higher quality / premium generation |

## Endpoints

- `POST /qwen-image/images` — Create images (text-to-image and image-guided editing)
- `POST /qwen-image/tasks` — Retrieve one or more async task results

## Parameters (`POST /qwen-image/images`)

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | Yes | `qwen-image-3.0`, `qwen-image-3.0-pro` | Model name |
| `prompt` | Yes | string | Image prompt |
| `image_urls` | No | array of strings | Reference images for image-guided generation/editing |
| `n` | No | integer | Number of images to generate |
| `size` | No | string | Output size, e.g. `1024x1024` |
| `prompt_extend` | No | boolean | Enable prompt extension |
| `prompt_extend_mode` | No | `direct`, `agent` | Prompt extension strategy |
| `enable_thinking` | No | boolean | Enable model reasoning mode |
| `negative_prompt` | No | string | Content to avoid |
| `seed` | No | integer | Reproducibility seed |
| `watermark` | No | boolean | Add watermark |
| `callback_url` | No | string | Async webhook callback URL |
| `async` | No | boolean | Return immediately with task ID |

## Parameters (`POST /qwen-image/tasks`)

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `id` | For single lookup | string | Task ID for `retrieve` |
| `ids` | For batch lookup | array of strings | Task IDs for `retrieve_batch` |
| `action` | No | `retrieve`, `retrieve_batch` | Task query mode |

## Gotchas

- Use `/qwen-image/images` for both generation and editing; include `image_urls` when you want image-guided output.
- `model` and `prompt` are required for image creation requests.
- For async usage, set `async: true` and poll `/qwen-image/tasks` until completion.

> **MCP:** See [all MCP servers](../_shared/mcp-servers.md) for tool-use integration.
