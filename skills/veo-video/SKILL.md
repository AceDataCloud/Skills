---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, extending or reshooting existing videos, inserting/removing objects, or upscaling. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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

### 3. Ingredients-to-Video

Generate from 1–3 reference images using ingredient mode (Veo 3.1 fast).

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "prompt": "a bowl of fresh ingredients being tossed in a salad",
  "image_urls": ["https://example.com/tomato.jpg", "https://example.com/lettuce.jpg"]
}
```

### 4. Upscale / Convert

Upscale a previously generated video to 1080p, 4K, or GIF using the dedicated endpoint.

```json
POST /veo/upsample
{
  "action": "1080p",
  "video_id": "your-video-id"
}
```

| `action` | Result |
|----------|--------|
| `"1080p"` | Upscale to 1080p resolution |
| `"4k"` | Upscale to 4K resolution |
| `"gif"` | Generate an animated GIF preview |

### 5. Extend Video

Continue an existing Veo 3.1 video with more content (Veo 3.1 series only).

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera slowly pans to reveal a mountain range"
}
```

### 6. Reshoot with Camera Motion

Re-render an existing video with a different camera motion applied.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "FORWARD"
}
```

Available `motion_type` values: `STATIONARY`, `STATIONARY_UP`, `STATIONARY_DOWN`, `STATIONARY_LEFT`, `STATIONARY_RIGHT`, `STATIONARY_DOLLY_IN_ZOOM_OUT`, `STATIONARY_DOLLY_OUT_ZOOM_IN`, `UP`, `DOWN`, `LEFT_TO_RIGHT`, `RIGHT_TO_LEFT`, `FORWARD`, `BACKWARD`, `DOLLY_IN_ZOOM_OUT`, `DOLLY_OUT_ZOOM_IN`.

### 7. Insert or Remove Objects

Add or remove objects from an existing video.

```json
POST /veo/objects
{
  "action": "insert",
  "video_id": "your-video-id",
  "prompt": "a red umbrella appearing in the foreground"
}
```

```json
POST /veo/objects
{
  "action": "remove",
  "video_id": "your-video-id",
  "image_mask": "https://example.com/mask.jpg"
}
```

## Parameters

### `/veo/videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` | Generation mode (`get1080p` is deprecated — use `/veo/upsample` instead) |
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — for `image2video` (1–2 images) or `ingredients2video` (1–3 images) |
| `video_id` | string | Video to upscale — only for `get1080p` (deprecated) |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

### `/veo/upsample`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"1080p"`, `"4k"`, `"gif"` | Upsample target format |
| `video_id` | string | ID of a previously generated video |
| `callback_url` | string | Optional async callback URL |

### `/veo/extend`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video (required) |
| `model` | `"veo31-fast"`, `"veo31"` | Veo 3.1 model to use for extension (required) |
| `prompt` | string | Optional prompt guiding the extended section |
| `callback_url` | string | Optional async callback URL |

### `/veo/reshoot`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video — not from `/veo/extend` (required) |
| `motion_type` | see list above | Camera motion style (required) |
| `callback_url` | string | Optional async callback URL |

### `/veo/objects`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"insert"`, `"remove"` | Operation type (required) |
| `video_id` | string | ID of a previously generated video — not from `/veo/extend` (required) |
| `prompt` | string | Required for `insert`; optional for `remove` |
| `image_mask` | string | Mask image URL or base64 JPEG; required for `remove`, optional for `insert` |
| `callback_url` | string | Optional async callback URL |

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- The `get1080p` action in `/veo/videos` is deprecated — use `POST /veo/upsample` with `action="1080p"` instead
- `/veo/extend` only supports `veo31-fast` and `veo31` models; extended videos can be extended again
- `/veo/reshoot` and `/veo/objects` cannot use videos produced by `/veo/extend` as source
- For `objects` `remove`, `image_mask` is required; for `insert`, it is optional (AI auto-determines placement)
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — 1–2 URLs for `image2video`, 1–3 URLs for `ingredients2video`
- `ingredients2video` forces the `veo31-fast-ingredients` model internally
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
