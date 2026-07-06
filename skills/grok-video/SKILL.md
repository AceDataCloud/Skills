---
name: grok-video
description: Generate AI videos with xAI Grok via AceDataCloud API. Use when creating videos from text prompts or animating images into video with Grok Imagine. Supports text-to-video and image-to-video with reference image guidance, multiple aspect ratios, and resolutions up to 1080p.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-grok for tool-use.
---

# Grok Video Generation

Generate AI videos through AceDataCloud's xAI Grok Imagine API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video-1.5-fast"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.

## Models

| Model | Supports | Best For |
|-------|----------|----------|
| `grok-imagine-video-1.5-fast` | Text-to-video & image-to-video | Default; lower cost, fast generation |
| `grok-imagine-video-1.5` | Image-to-video **only** | Higher quality; requires `image_url` |

## Workflows

### 1. Text-to-Video

Only supported with `grok-imagine-video-1.5-fast`.

```json
POST /grok/videos
{
  "prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden",
  "model": "grok-imagine-video-1.5-fast",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate a still image into a video. `image_url` is **required** when using `grok-imagine-video-1.5`.

```json
POST /grok/videos
{
  "prompt": "The character slowly turns around and smiles at the camera",
  "model": "grok-imagine-video-1.5",
  "image_url": "https://cdn.acedata.cloud/5hmkdg.jpg",
  "resolution": "720p",
  "duration": 8
}
```

### 3. Reference Image Guidance

Pass one or more reference images in `reference_image_urls` to guide the style or content of the video.

```json
POST /grok/videos
{
  "prompt": "A character dancing in the same art style",
  "model": "grok-imagine-video-1.5-fast",
  "reference_image_urls": [
    "https://cdn.acedata.cloud/vunnjf.png"
  ]
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the video. Required for text-to-video; optional when `image_url` is provided |
| `model` | `"grok-imagine-video-1.5-fast"`, `"grok-imagine-video-1.5"` | Model to use (default: `grok-imagine-video-1.5-fast`) |
| `image_url` | string | Input image URL for image-to-video. Required when using `grok-imagine-video-1.5` |
| `reference_image_urls` | array of strings | Optional reference image URLs to guide style or content |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Output aspect ratio |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `480p`). Higher resolution consumes more quota |
| `duration` | integer 1–30 | Duration in seconds (default: 8). Billing is based on output seconds |
| `callback_url` | string | Async callback URL; returns a `task_id` immediately and POSTs the result when done |
| `async` | boolean | Force async mode — returns task ID immediately without waiting |

## Polling Tasks

```json
POST /grok/tasks
{
  "id": "<task_id>",
  "action": "retrieve"
}
```

Batch retrieve:

```json
POST /grok/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

## Gotchas

- `grok-imagine-video-1.5` **only** supports image-to-video — `image_url` is required
- `grok-imagine-video-1.5-fast` supports both text-to-video (prompt only) and image-to-video (`image_url`)
- `prompt` is required when using `grok-imagine-video-1.5-fast` for text-to-video (no `image_url`); it is optional when `image_url` is provided
- Task polling uses `id` (not `task_id`) in the `/grok/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling
- Duration billing is per output second — shorter videos cost less

> **MCP:** `pip install mcp-grok` | Hosted: `https://grok.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
