---
name: qwen-image
description: Generate and edit AI images with Qwen Image 3 via AceDataCloud API. Use when creating images from text prompts or editing up to three reference images. Supports qwen-image-3.0 and qwen-image-3.0-pro.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Qwen Image Generation

Generate and edit AI images through AceDataCloud's Qwen Image 3 API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/qwen-image/images \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-image-3.0","prompt":"A minimalist technology poster","size":"1024*1024","n":1}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /qwen-image/tasks` with `{"action":"retrieve","id":"..."}`.

## Models

| Model | Best For |
|-------|----------|
| `qwen-image-3.0` | Standard image generation (default) |
| `qwen-image-3.0-pro` | Higher-quality generation and editing |

## Workflows

### 1. Text-to-Image

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0",
  "prompt": "A minimalist technology poster",
  "size": "1024*1024",
  "n": 1
}
```

### 2. Image Editing

Provide one to three public image URLs with an editing prompt:

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0-pro",
  "prompt": "Keep the subject and change the scene to a warm poster style",
  "image_urls": ["https://example.com/photo.png"],
  "size": "2048*2048",
  "prompt_extend": true,
  "prompt_extend_mode": "direct",
  "enable_thinking": true
}
```

### 3. Async Generation

Set `async` to receive a `task_id` immediately, optionally with a `callback_url` for result delivery:

```json
POST /qwen-image/images
{
  "model": "qwen-image-3.0",
  "prompt": "An editorial illustration of sustainable cities",
  "async": true,
  "callback_url": "https://example.com/qwen-image-result"
}
```

Query one task or a batch:

```json
POST /qwen-image/tasks
{"action": "retrieve", "id": "<task_id>"}
```

```json
POST /qwen-image/tasks
{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"qwen-image-3.0"`, `"qwen-image-3.0-pro"` | Model to use (default: `qwen-image-3.0`) |
| `prompt` | string, 1–18,000 characters | Image description or editing instruction (required) |
| `image_urls` | 1–3 public image URLs | Reference images for editing |
| `n` | integer, 1–6 | Number of images to generate (default: 1) |
| `size` | `"<width>*<height>"` | Output dimensions, e.g. `"1024*1024"` |
| `prompt_extend` | boolean | Enable prompt expansion (default: true) |
| `prompt_extend_mode` | `"direct"`, `"agent"` | Prompt expansion mode (default: `direct`) |
| `enable_thinking` | boolean | Enable model reasoning (default: true) |
| `negative_prompt` | string | Elements to avoid in the image |
| `seed` | integer, 0–2147483647 | Seed for reproducible results |
| `watermark` | boolean | Add a watermark (default: false) |
| `async` | boolean | Return a `task_id` immediately (default: false) |
| `callback_url` | URL | Webhook URL for asynchronous result delivery |

## Gotchas

- Image editing uses the same `/qwen-image/images` endpoint as text-to-image; add one to three public `image_urls`.
- Use an asterisk in dimensions (`"1024*1024"`), not `x` or colon notation.
- The output size must be 512×512 to 2048×2048 pixels, with an aspect ratio between 1:8 and 8:1.
- `prompt_extend_mode: "agent"` is only supported for text-to-image; use `"direct"` when supplying `image_urls`.
- Poll tasks with `action: "retrieve"` and `id`; batch polling requires `action: "retrieve_batch"` and `ids`.
