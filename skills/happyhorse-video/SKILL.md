---
name: happyhorse-video
description: Generate AI videos with HappyHorse via AceDataCloud API. Use when creating videos from text prompts, animating images into video, transferring reference video style/character, or editing existing videos. Supports text-to-video, image-to-video, reference-to-video, and video-edit workflows with configurable resolution, aspect ratio, and audio settings.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-happyhorse for tool-use.
---

# HappyHorse Video Generation

Generate AI videos through AceDataCloud's HappyHorse API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/happyhorse/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "a horse galloping through a sunlit meadow", "model": "happyhorse-1.1-t2v", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /happyhorse/tasks` with `{"id": "..."}`.
This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/happyhorse/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Action | Best For |
|-------|--------|----------|
| `happyhorse-1.1-t2v` | `generate` | Text-to-video, latest (default) |
| `happyhorse-1.0-t2v` | `generate` | Text-to-video, v1.0 |
| `happyhorse-1.1-i2v` | `image_to_video` | Image-to-video, latest |
| `happyhorse-1.0-i2v` | `image_to_video` | Image-to-video, v1.0 |
| `happyhorse-1.1-r2v` | `reference_to_video` | Reference video transfer, latest |
| `happyhorse-1.0-r2v` | `reference_to_video` | Reference video transfer, v1.0 |
| `happyhorse-1.0-video-edit` | `video_edit` | Video editing |

## Workflows

### 1. Text-to-Video

Generate a video from a text description.

```json
POST /happyhorse/videos
{
  "action": "generate",
  "prompt": "a futuristic city skyline at dusk with flying vehicles",
  "model": "happyhorse-1.1-t2v",
  "resolution": "1080P",
  "ratio": "16:9",
  "duration": 5
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /happyhorse/videos
{
  "action": "image_to_video",
  "prompt": "gentle waves ripple across the surface",
  "model": "happyhorse-1.1-i2v",
  "image_url": "https://example.com/ocean.jpg",
  "resolution": "1080P",
  "duration": 5
}
```

### 3. Reference-to-Video

Transfer style or character from a reference video into new content.

```json
POST /happyhorse/videos
{
  "action": "reference_to_video",
  "prompt": "the character walks through a neon-lit city at night",
  "model": "happyhorse-1.1-r2v",
  "video_url": "https://example.com/reference.mp4"
}
```

### 4. Video Editing

Edit an existing video with a text instruction.

```json
POST /happyhorse/videos
{
  "action": "video_edit",
  "prompt": "change the background to a snowy mountain landscape",
  "model": "happyhorse-1.0-video-edit",
  "video_url": "https://example.com/original.mp4"
}
```

### 5. Multi-image Input

Pass multiple reference images for a single generation.

```json
POST /happyhorse/videos
{
  "action": "image_to_video",
  "prompt": "smooth transition through multiple scenes",
  "model": "happyhorse-1.1-i2v",
  "image_urls": [
    "https://example.com/scene1.jpg",
    "https://example.com/scene2.jpg"
  ]
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"generate"`, `"image_to_video"`, `"reference_to_video"`, `"video_edit"` | Generation mode (default: generate) |
| `model` | see Models table | Model to use (default: `happyhorse-1.1-t2v`) |
| `prompt` | string | Scene or edit description |
| `image_url` | string | Single source image URL — for `image_to_video` |
| `image_urls` | array of strings | Multiple source image URLs — for `image_to_video` |
| `video_url` | string | Source or reference video URL — for `reference_to_video` and `video_edit` |
| `resolution` | `"720P"`, `"1080P"` | Output resolution (default: 1080P) |
| `ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio (default: 16:9) |
| `duration` | integer | Video duration in seconds (default: 5) |
| `audio_setting` | `"auto"`, `"origin"` | Audio mode: auto-generate or preserve original (default: auto) |
| `watermark` | boolean | Add a watermark to the video (default: false) |
| `seed` | integer | Seed for reproducible generation |
| `callback_url` | string | Webhook URL for async result delivery |
| `async` | boolean | Force async mode |

## Gotchas

- Use `image_url` for a single image or `image_urls` for multiple images — do not combine both in the same request
- `video_url` is required for `reference_to_video` and `video_edit` actions
- `audio_setting: "origin"` preserves the original audio from the source video; `"auto"` generates new audio
- Task polling uses `id` in the `/happyhorse/tasks` request body

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
