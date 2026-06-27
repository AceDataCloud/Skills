---
name: grok-video
description: Generate AI videos with Grok (xAI) via AceDataCloud API. Use when creating videos from text prompts or animating images with Grok Imagine. Supports text-to-video and image-to-video with configurable aspect ratio, resolution, and duration.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-grok for tool-use.
---

# Grok Video Generation

Generate AI videos through AceDataCloud's Grok (xAI) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/grok/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cinematic shot of a kitten chasing a butterfly in a sunlit garden", "model": "grok-imagine-video", "resolution": "480p", "duration": 8, "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /grok/tasks` with `{"id": "..."}`.
This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/grok/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Type | Notes |
|-------|------|-------|
| `grok-imagine-video` | Text-to-Video or Image-to-Video | Default model; duration up to 30s |
| `grok-imagine-video-1.5-preview` | Image-to-Video only | Requires `image_url`; duration up to 15s |

## Workflows

### 1. Text-to-Video

Generate video from a text prompt using `grok-imagine-video`.

```json
POST /grok/videos
{
  "prompt": "A drone flying over a mountain lake at sunrise",
  "model": "grok-imagine-video",
  "aspect_ratio": "16:9",
  "resolution": "720p",
  "duration": 8
}
```

### 2. Image-to-Video

Animate an image with an optional descriptive prompt.

```json
POST /grok/videos
{
  "prompt": "the scene comes alive with gentle wind",
  "model": "grok-imagine-video",
  "image_url": "https://example.com/scene.jpg",
  "aspect_ratio": "16:9",
  "resolution": "1080p",
  "duration": 10
}
```

### 3. Image-to-Video with grok-imagine-video-1.5-preview

For higher-quality image animation (requires `image_url`):

```json
POST /grok/videos
{
  "model": "grok-imagine-video-1.5-preview",
  "image_url": "https://example.com/portrait.jpg",
  "prompt": "the subject turns and smiles",
  "aspect_ratio": "9:16",
  "resolution": "720p",
  "duration": 8
}
```

### 4. With Reference Images

Provide additional reference images to guide style or content:

```json
POST /grok/videos
{
  "prompt": "paint the scene in the style of the references",
  "model": "grok-imagine-video",
  "reference_image_urls": [
    "https://example.com/style-ref-1.jpg",
    "https://example.com/style-ref-2.jpg"
  ],
  "aspect_ratio": "16:9",
  "resolution": "480p",
  "duration": 8
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `prompt` | string | Text description of the video. Required for text-to-video; optional when `image_url` is provided |
| `model` | see Models table | Model to use (default: `grok-imagine-video`) |
| `image_url` | string | Input image URL for image-to-video. Required for `grok-imagine-video-1.5-preview` |
| `reference_image_urls` | array of strings | Optional reference images to guide style or content |
| `aspect_ratio` | `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"` | Video aspect ratio (default: `"16:9"`) |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: `"480p"`) |
| `duration` | `1` – `30` | Duration in seconds (default: 8). Max is 30 for `grok-imagine-video`, 15 for `grok-imagine-video-1.5-preview` |
| `callback_url` | string | Webhook URL for async completion notification |
| `async` | `true` / `false` | Return task ID immediately without waiting for completion |

## Gotchas

- `grok-imagine-video` supports both text-to-video (prompt only) and image-to-video (with `image_url`)
- `grok-imagine-video-1.5-preview` requires `image_url` — it does not support text-only generation
- Duration maximum differs by model: 30s for `grok-imagine-video`, 15s for `grok-imagine-video-1.5-preview`
- `prompt` is required for text-to-video with `grok-imagine-video`; it becomes optional when `image_url` is supplied
- Resolution defaults to `"480p"` — set explicitly for higher quality
- Task state values are `pending`, `succeeded`, and `failed` — check for `"succeeded"` when polling
- Image and reference image URLs must be publicly accessible

> **MCP:** See [all MCP servers](../_shared/mcp-servers.md)
