---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, extending/reshooting existing videos, or inserting/removing objects. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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
| `veo31-fast-ingredients` | Yes (native) | Veo 3.1 fast, multi-image blend mode |

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

### 3. Multi-Image Blend (Ingredients)

Blend multiple reference images into a single video using `veo31-fast-ingredients` (1–3 images required).

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "image_urls": [
    "https://example.com/scene1.jpg",
    "https://example.com/scene2.jpg"
  ],
  "model": "veo31-fast-ingredients"
}
```

### 4. Upscale Video

Upscale a previously generated video to a higher resolution or convert to GIF.

```json
POST /veo/upsample
{
  "action": "4k",
  "video_id": "your-video-id"
}
```

| `action` value | Output |
|----------------|--------|
| `1080p` | Upscale to 1080p |
| `4k` | Upscale to 4K |
| `gif` | Convert to animated GIF preview |

### 5. Extend Video

Continue a previously generated video, adding more footage after the last frame (Veo 3.1 only).

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera slowly zooms out to reveal more of the landscape"
}
```

### 6. Reshoot with Camera Motion

Re-render a video with a new camera motion while preserving the visual content.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "LEFT_TO_RIGHT"
}
```

Available `motion_type` values: `STATIONARY`, `STATIONARY_UP`, `STATIONARY_DOWN`, `STATIONARY_LEFT`, `STATIONARY_RIGHT`, `STATIONARY_DOLLY_IN_ZOOM_OUT`, `STATIONARY_DOLLY_OUT_ZOOM_IN`, `UP`, `DOWN`, `LEFT_TO_RIGHT`, `RIGHT_TO_LEFT`, `FORWARD`, `BACKWARD`, `DOLLY_IN_ZOOM_OUT`, `DOLLY_OUT_ZOOM_IN`

### 7. Insert or Remove Objects

Add or erase objects in a video using a mask.

```json
POST /veo/objects
{
  "action": "insert",
  "video_id": "your-video-id",
  "prompt": "add a flying pig with black wings"
}
```

```json
POST /veo/objects
{
  "action": "remove",
  "video_id": "your-video-id",
  "image_mask": "https://example.com/mask.jpg",
  "prompt": "remove the white cloud"
}
```

## Parameters

### `/veo/videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` | Generation mode |
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — required for `image2video`/`ingredients2video` |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

### `/veo/upsample`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"1080p"`, `"4k"`, `"gif"` | Upsample target format |
| `video_id` | string | ID of a previously generated video task |

### `/veo/extend`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"veo31-fast"`, `"veo31"` | Model for extension (Veo 3.1 series only) |
| `video_id` | string | ID of a previously generated video task |
| `prompt` | string | Optional prompt to guide the extended footage |

### `/veo/reshoot`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video task |
| `motion_type` | see motion types above | Camera motion style to apply |

### `/veo/objects`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"insert"`, `"remove"` | Object operation |
| `video_id` | string | ID of a previously generated video task |
| `prompt` | string | Required for `insert`; optional for `remove` |
| `image_mask` | string (URL or base64) | Mask image — required for `remove`, optional for `insert` |

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- `ingredients2video` is only supported by `veo31-fast-ingredients` and requires 1–3 `image_urls`
- `aspect_ratio` is **only valid** for the `image2video` action
- `/veo/extend` only supports `veo31-fast` and `veo31` models
- Videos produced by `/veo/extend` **cannot** be further processed by `/veo/reshoot` or `/veo/objects`
- `/veo/upsample` accepts video IDs from any endpoint (`/veo/videos`, `/veo/extend`, `/veo/reshoot`, `/veo/objects`)
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
