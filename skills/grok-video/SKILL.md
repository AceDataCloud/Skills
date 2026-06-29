---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or reference images with Grok Imagine Video models. Supports text-to-video, image-to-video, multiple aspect ratios, and resolutions up to 1080p.
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
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a lone astronaut walking on the surface of Mars at sunset", "model": "grok-imagine-video", "aspect_ratio": "16:9", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | General-purpose video generation (default) |
| `grok-imagine-video-1.5-preview` | Preview of Grok Imagine Video 1.5, improved quality |

## Workflows

### 1. Text-to-Video

Generate a video from a text description.

```json
POST /grok/videos
{
  "prompt": "a timelapse of a city skyline transitioning from day to night",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 2. Image-to-Video

Animate a reference image into a video.

```json
POST /grok/videos
{
  "prompt": "the scene comes to life with gentle motion",
  "model": "grok-imagine-video-1.5-preview",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Image-to-Video with Reference Images

Use one or more reference images to guide the generation style or characters.

```json
POST /grok/videos
{
  "prompt": "the character walks through a forest",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": ["https://example.com/character.jpg"],
  "aspect_ratio": "9:16"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | Yes | string | Video description |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model to use |
| `image_url` | No | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Reference image URLs for style/character guidance |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | No | `"480p"`, `"720p"`, `"1080p"` | Output resolution |
| `duration` | No | integer | Duration in seconds |
| `callback_url` | No | string | Async callback URL |

## Gotchas

- All generation is async — always set `"callback_url"` to get a task id immediately, then poll `/grok/tasks` using `{"id":"<task_id>"}` or `{"ids":[...],"action":"retrieve_batch"}`
- `image_url` and `reference_image_urls` can be combined for richer guided generation
- Higher resolutions (`1080p`) increase generation time and cost

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
