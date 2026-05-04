---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, upscaling/extending videos, re-shooting with new camera motion, or inserting/removing objects. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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
| `veo2` | No | Cost-effective generation |
| `veo2-fast` | No | Fast, cost-effective generation (default) |
| `veo3` | Yes (native) | Full audiovisual generation |
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
  "model": "veo2",
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
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — for `image2video` (up to 2) or `ingredients2video` (up to 3) |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

## Post-Generation Endpoints

After generating a video, use these endpoints to further process it:

### Upsample (`POST /veo/upsample`)

Upscale a generated video to 1080p, 4K, or convert to GIF.

```json
POST /veo/upsample
{
  "video_id": "your-video-id",
  "action": "4k"
}
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | Task ID from `/veo/videos`, `/veo/extend`, `/veo/reshoot`, or `/veo/objects` |
| `action` | `"1080p"`, `"4k"`, `"gif"` | Upsample target |

### Extend (`POST /veo/extend`)

Continue an existing video — AI auto-generates the next segment.

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera slowly zooms out"
}
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | Task ID from `/veo/videos` or a prior `/veo/extend` |
| `model` | `"veo31-fast"`, `"veo31"` | Only Veo 3.1 series is supported |
| `prompt` | string | Optional: guides the extended segment |

### Reshoot (`POST /veo/reshoot`)

Re-render a video keeping the same content but applying new camera motion.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "LEFT_TO_RIGHT"
}
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | Task ID from `/veo/videos` (cannot use `/veo/extend` output) |
| `motion_type` | see table below | Camera motion to apply |

**`motion_type` values:**
`STATIONARY`, `STATIONARY_UP`, `STATIONARY_DOWN`, `STATIONARY_LEFT`, `STATIONARY_RIGHT`, `STATIONARY_DOLLY_IN_ZOOM_OUT`, `STATIONARY_DOLLY_OUT_ZOOM_IN`, `UP`, `DOWN`, `LEFT_TO_RIGHT`, `RIGHT_TO_LEFT`, `FORWARD`, `BACKWARD`, `DOLLY_IN_ZOOM_OUT`, `DOLLY_OUT_ZOOM_IN`

### Objects (`POST /veo/objects`)

Insert or remove objects in a video using mask-based inpainting.

```json
POST /veo/objects
{
  "video_id": "your-video-id",
  "action": "insert",
  "prompt": "add a flying bird"
}
```

```json
POST /veo/objects
{
  "video_id": "your-video-id",
  "action": "remove",
  "image_mask": "https://example.com/mask.jpg"
}
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | Task ID (cannot use `/veo/extend` output) |
| `action` | `"insert"`, `"remove"` | Operation type |
| `prompt` | string | Required for `insert`; optional for `remove` |
| `image_mask` | string | URL or base64 JPEG — white pixels = target region. Required for `remove`; optional for `insert` |

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- The `get1080p` action uses `video_id` (from a prior generation), not a URL
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — up to 2 images for `image2video`, up to 3 for `ingredients2video`
- `veo31-fast-ingredients` **requires** image input — it cannot do text-only generation
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling
- `/veo/extend` output **cannot** be used as input for `/veo/reshoot` or `/veo/objects`

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
