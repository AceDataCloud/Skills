---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports grok-imagine-video models with multiple aspect ratios and resolutions.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-grok-video for tool-use.
---

# Grok Video Generation

Generate AI videos through AceDataCloud's xAI Grok API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a dolphin jumping through ocean waves at golden hour", "model": "grok-imagine-video", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | Standard video generation |
| `grok-imagine-video-1.5-preview` | Preview of next-generation Grok video |

## Workflows

### 1. Text-to-Video

Generate a video from a text description.

```json
POST /grok/videos
{
  "prompt": "a time-lapse of flowers blooming in a meadow",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /grok/videos
{
  "prompt": "gentle wind blows through the scene",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/landscape.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Image-to-Video with Reference Images

Use multiple reference images to guide the generation.

```json
POST /grok/videos
{
  "prompt": "the character walks through a futuristic city",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": [
    "https://example.com/character.jpg",
    "https://example.com/city.jpg"
  ]
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | Recommended | string | Video description — required for text-to-video; optional for image-to-video |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model to use |
| `image_url` | For i2v | string | Source image URL — required for image-to-video workflows |
| `reference_image_urls` | No | array of strings | Reference image URLs for guided generation |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"` | Output resolution |
| `duration` | No | integer | Video duration in seconds |
| `callback_url` | No | string | Async webhook notification URL |
| `async` | No | boolean | Return immediately with a task ID |

## Task Polling

```json
POST /grok/tasks
{
  "id": "<task_id>"
}
```

Batch polling:

```json
POST /grok/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

## Gotchas

- For **text-to-video**, always provide a `prompt` — the API accepts it as optional but results are meaningless without it
- For **image-to-video**, provide `image_url` (and optionally a `prompt` for animation guidance)
- `reference_image_urls` enables multi-image guided generation alongside or instead of `image_url`
- `grok-imagine-video-1.5-preview` is a preview model and may change
- Default resolution is `720p` if not specified
- Task polling uses `id` (not `task_id`) in the `/grok/tasks` request body

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
