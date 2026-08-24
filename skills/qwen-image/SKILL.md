---
name: qwen-image
description: Generate and edit images with Qwen Image 3 via the AceDataCloud API. Use for text-to-image generation and prompt-guided image editing with up to three source images.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Qwen Image 3

Generate images or edit supplied images with Qwen Image 3.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/qwen-image/images \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-image-3.0","prompt":"A watercolor painting of a red panda reading in a library"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /qwen-image/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `qwen-image-3.0` | General image generation and editing |
| `qwen-image-3.0-pro` | Higher-quality image generation and editing |

## Workflows

### 1. Text-to-Image

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0",
  "prompt": "A cinematic aerial view of a coastal village at sunrise",
  "size": "1024x1024"
}
```

### 2. Image Editing

Provide one to three source images and describe the desired change.

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0-pro",
  "prompt": "Replace the background with a moonlit forest",
  "image_urls": ["https://example.com/source.jpg"]
}
```

### 3. Async Generation

Use `callback_url` to receive a task ID immediately, then poll `/qwen-image/tasks`.

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0",
  "prompt": "A geometric poster of a hummingbird",
  "callback_url": "https://example.com/webhook"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | Yes | `"qwen-image-3.0"`, `"qwen-image-3.0-pro"` | Model to use (default: `qwen-image-3.0`) |
| `prompt` | Yes | string | Image-generation or editing instruction |
| `image_urls` | No | array of 1–3 URLs | Source images for image editing |
| `n` | No | integer, 1–6 | Number of images to generate (default: 1) |
| `size` | No | string | Output image size |
| `prompt_extend` | No | boolean | Enable prompt expansion (default: `true`) |
| `prompt_extend_mode` | No | `"direct"`, `"agent"` | Prompt expansion mode (default: `direct`) |
| `enable_thinking` | No | boolean | Enable model reasoning (default: `true`) |
| `negative_prompt` | No | string | Content to exclude |
| `seed` | No | integer | Seed for reproducible generation |
| `watermark` | No | boolean | Add a watermark (default: `false`) |
| `callback_url` | No | string | Async webhook notification URL |
| `async` | No | boolean | Request asynchronous processing |

## Gotchas

- Both `model` and `prompt` are required.
- `image_urls` accepts at most three source images.
- Task polling supports one `id`, or `ids` with `action: "retrieve_batch"`.

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
