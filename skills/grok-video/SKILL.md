---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports text-to-video and image-to-video with multiple aspect ratios and resolutions.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-grok-video for tool-use.
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video", "aspect_ratio": "16:9"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Best For |
|-------|----------|
| `grok-imagine-video` | Fast video generation (default) |
| `grok-imagine-video-1.5-preview` | Higher quality preview model |

## Workflows

### 1. Text-to-Video

```json
POST /grok/videos
{
  "prompt": "a time-lapse of a city skyline at sunset turning to night",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /grok/videos
{
  "prompt": "the waves crash gently against the shore",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/beach.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Video with Reference Images

Provide reference images for additional style or content guidance.

```json
POST /grok/videos
{
  "prompt": "a futuristic city at night with flying cars",
  "model": "grok-imagine-video-1.5-preview",
  "reference_image_urls": [
    "https://example.com/style-ref.jpg"
  ],
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

### 4. Async Generation with Task Polling

Pass `async: true` to get a task ID immediately and poll for the result:

```json
POST /grok/videos
{
  "prompt": "a dragon soaring through clouds at golden hour",
  "model": "grok-imagine-video",
  "callback_url": "https://api.acedata.cloud/health",
  "async": true
}
```

Poll the returned `task_id`:

```json
POST /grok/tasks
{"id": "<task_id>"}
```

## Parameters

### `POST /grok/videos`

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `prompt` | Conditionally | string | Text description of the video to generate (required for text-to-video when `image_url` is not provided) |
| `model` | No | `"grok-imagine-video"`, `"grok-imagine-video-1.5-preview"` | Model (default: `grok-imagine-video`) |
| `image_url` | No | string | Source image URL for image-to-video |
| `reference_image_urls` | No | array of strings | Additional reference image URLs for style/content guidance |
| `aspect_ratio` | No | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Aspect ratio of the output video |
| `resolution` | No | `"480p"`, `"720p"` | Output resolution (default: `480p`) |
| `duration` | No | integer (1–15) | Video duration in seconds (default: 8) |
| `callback_url` | No | string | Webhook URL for async delivery |
| `async` | No | boolean | Return a `task_id` immediately and process asynchronously |

### `POST /grok/tasks`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `id` | string | Task ID to retrieve |
| `ids` | array | Multiple task IDs to retrieve in batch |
| `action` | `"retrieve"`, `"retrieve_batch"` | Action type (default: `retrieve`) |

## Gotchas

- `prompt` is required when not providing an `image_url` for text-to-video generation
- `image_url` enables image-to-video mode; combine with `prompt` for guided animation
- `reference_image_urls` provides additional style or content context, separate from the main `image_url`
- Task states use `"succeeded"` (not "completed") — check for this value when polling
- Poll using `id` (the task ID from the response), not `task_id`

> **MCP:** `pip install mcp-grok-video` | Hosted: `https://grok-video.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
