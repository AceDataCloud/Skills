---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, or blending multiple reference images. Supports Veo 3 and Veo 3.1 models including fast and ingredient variants.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-veo for tool-use.
---

# Veo Video Generation

Generate AI videos through AceDataCloud's Google Veo API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/veo/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "text2video", "prompt": "a whale breaching in slow motion at golden hour", "model": "veo3", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /veo/tasks` with `{"id": "..."}`.
This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/veo/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Audio | Best For |
|-------|-------|----------|
| `veo3` | Yes (native) | Full audiovisual generation (default) |
| `veo3-fast` | Yes (native) | Faster audiovisual generation |
| `veo31` | Yes (native) | Veo 3.1, highest quality |
| `veo31-fast` | Yes (native) | Veo 3.1 fast variant |
| `veo31-fast-ingredients` | Yes (native) | Veo 3.1 fast, ingredient mode |

## Workflows

### 1. Text-to-Video

```json
POST /veo/videos
{
  "action": "text2video",
  "prompt": "cinematic aerial shot of the Northern Lights over Iceland",
  "model": "veo3",
  "resolution": "1080p"
}
```

### 2. Image-to-Video

Animate still images into video.

```json
POST /veo/videos
{
  "action": "image2video",
  "prompt": "the scene gently comes to life with wind and subtle motion",
  "image_urls": ["https://example.com/landscape.jpg"],
  "model": "veo3-fast",
  "aspect_ratio": "16:9"
}
```

### 3. Ingredients-to-Video (Multi-Image Blend)

Blend 1–3 reference images into a video (only `veo31-fast-ingredients`).

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "image_urls": [
    "https://example.com/img1.jpg",
    "https://example.com/img2.jpg"
  ],
  "model": "veo31-fast-ingredients"
}
```

### 4. Upscale to 1080p

Convert a previously generated video to full 1080p resolution.

```json
POST /veo/videos
{
  "action": "get1080p",
  "video_id": "your-video-id",
  "model": "veo3"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` | Generation mode |
| `model` | see Models table | Model to use (default: `veo3`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — for `image2video` (up to 2) or `ingredients2video` (up to 3) |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

## Gotchas

- All Veo 3 and 3.1 models generate **native audio**
- The `get1080p` action uses `video_id` (from a prior generation), not a URL
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — up to 2 images for `image2video`, up to 3 for `ingredients2video`
- `veo31-fast-ingredients` **requires** image input — it cannot do text-only generation
- Documented `aspect_ratio` values are only `"16:9"` and `"9:16"`
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
