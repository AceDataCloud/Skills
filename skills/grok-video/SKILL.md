---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images using Grok's video generation models. Supports text-to-video and image-to-video with configurable resolution and aspect ratio.
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
  -d '{"prompt": "a futuristic city at night with flying cars and neon lights", "model": "grok-imagine-video-1.5-fast:reverse", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Resolution | Default | Notes |
|-------|-----------|---------|-------|
| `grok-imagine-video-1.5-fast:reverse` | up to 1080p | ✓ | Best value. 6–30s, billed by duration tier |
| `grok-imagine-video:reverse` | up to 1080p | | Better value. 1–15s, billed per output second |
| `grok-imagine-video:official` | up to 1080p | | Higher quality. 1–15s, billed per output second |
| `grok-imagine-video-1.5:official` | up to 1080p | | Higher quality, **image-to-video only** (`image_url` required) |
| `grok-imagine-video` | up to 720p | | Base model, text-to-video only |
| `grok-imagine-video-1.5-preview` | up to 720p | | 1.5 preview (grok-video.json surface) |

## Workflows

### 1. Text-to-Video

Generate a video from a text description.

```json
POST /grok/videos
{
  "prompt": "a majestic eagle soaring over snow-capped mountains at dawn",
  "model": "grok-imagine-video-1.5-fast:reverse",
  "resolution": "720p",
  "aspect_ratio": "16:9",
  "duration": 6
}
```

### 2. Image-to-Video

Animate a still image into motion. Provide the image URL via `image_url`.

```json
POST /grok/videos
{
  "prompt": "the eagle lifts off and flies into the sunset",
  "image_url": "https://example.com/eagle.jpg",
  "model": "grok-imagine-video:official",
  "resolution": "720p",
  "aspect_ratio": "16:9"
}
```

### 3. Multi-Reference Generation

Supply up to several reference images via `reference_image_urls` for style or subject consistency.

```json
POST /grok/videos
{
  "prompt": "the character walks through a cyberpunk alley",
  "reference_image_urls": [
    "https://example.com/character.jpg",
    "https://example.com/style.jpg"
  ],
  "model": "grok-imagine-video-1.5-fast:reverse",
  "resolution": "1080p"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the desired video |
| `model` | see Models table | Model to use (default: `grok-imagine-video-1.5-fast:reverse`) |
| `image_url` | URL | Single reference image for image-to-video |
| `reference_image_urls` | array of URLs | Multiple reference images for style/subject guidance |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`; `1080p` only for `:reverse`/`:official` models) |
| `duration` | integer | Duration in seconds (default: 6) |
| `callback_url` | URL | Webhook URL for async delivery |
| `async` | boolean | Return a task ID immediately for polling |

## Task Queries

```json
POST /grok/tasks
{"id": "<task_id>", "action": "retrieve"}
```

Batch retrieval:

```json
POST /grok/tasks
{"ids": ["<id1>", "<id2>"], "action": "retrieve_batch"}
```

## Gotchas

- `1080p` resolution is only supported by `:reverse` and `:official` model variants
- `image_url` provides a single driving image; `reference_image_urls` provides multiple style/subject references
- Set `callback_url` to get the task ID immediately without blocking on completion
- Poll `POST /grok/tasks` with `{"id": "..."}` until a final video URL appears in the response

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
