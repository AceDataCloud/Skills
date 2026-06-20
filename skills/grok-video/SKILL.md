---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or animating images into video using Grok's imagination models. Supports text-to-video and image-to-video with configurable aspect ratio and resolution.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a futuristic city at night with neon lights reflected in rain puddles",
    "model": "grok-imagine-video",
    "aspect_ratio": "16:9",
    "callback_url": "https://api.acedata.cloud/health"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | General-purpose video generation (default) |
| `grok-imagine-video-1.5-preview` | Latest preview — higher quality, improved motion |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a lone astronaut walking on the surface of Mars at sunrise",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 2. Image-to-Video

Animate a still image by providing `image_url` alongside a prompt.

```json
POST /grok/videos
{
  "prompt": "the scene comes to life with gentle movement",
  "model": "grok-imagine-video-1.5-preview",
  "image_url": "https://example.com/landscape.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Image-to-Video with Reference Images

Supply one or more reference images to guide style and content.

```json
POST /grok/videos
{
  "prompt": "a stylized animation in the same art style",
  "model": "grok-imagine-video",
  "reference_image_urls": ["https://example.com/style_ref.jpg"],
  "aspect_ratio": "1:1"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | No | string | Text description of the video to generate |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model (default: `grok-imagine-video`) |
| `image_url` | No | string (URI) | Source image for image-to-video |
| `reference_image_urls` | No | array of strings | Reference images for style/content guidance |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"` | Output resolution (default: `480p`) |
| `duration` | No | integer | Video duration in seconds |
| `callback_url` | No | string (URI) | Webhook to receive the result when done |
| `async` | No | boolean | Run asynchronously (recommended) |

## Poll for Results

```bash
curl -X POST https://api.acedata.cloud/grok/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>"}'
```

Batch polling:

```bash
curl -X POST https://api.acedata.cloud/grok/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["<task_id_1>", "<task_id_2>"], "action": "retrieve_batch"}'
```

## Gotchas

- Default resolution is `480p` — use `720p` for higher quality output
- Aspect ratio options: `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`
- `grok-imagine-video-1.5-preview` is a preview model — outputs may vary more than the stable model
- Generation is async — always supply `callback_url` to receive the task ID immediately, then poll `/grok/tasks`

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
