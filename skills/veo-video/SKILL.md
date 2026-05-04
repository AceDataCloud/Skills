---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, extending or reshooting videos, inserting/removing objects, or upscaling. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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
| `veo31-fast-ingredients` | Yes (native) | Veo 3.1 fast, ingredient mode (auto-selected for `ingredients2video`) |

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

Animate still images into video (1–2 reference images: first frame, or first + last frames).

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

Generate from 1–3 reference images using the `veo31-fast-ingredients` model (model is forced internally).

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "prompt": "combine these elements into a dynamic scene",
  "image_urls": ["https://example.com/obj1.jpg", "https://example.com/obj2.jpg"]
}
```

### 4. Upscale Video

Convert a previously generated video to a higher resolution or animated GIF.

```json
POST /veo/upsample
{
  "action": "1080p",
  "video_id": "your-video-id"
}
```

`action` options: `"1080p"` (upscale to 1080p), `"4k"` (upscale to 4K), `"gif"` (animated GIF preview).

### 5. Extend Video

Seamlessly lengthen an existing video using Veo 3.1 models.

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera continues sweeping over the mountain range"
}
```

### 6. Reshoot Video

Re-render a video with a different camera motion.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "FORWARD"
}
```

### 7. Insert or Remove Objects

Add or delete objects from a video using a mask image.

```json
POST /veo/objects
{
  "action": "insert",
  "video_id": "your-video-id",
  "prompt": "a red balloon floating upward"
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
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"` | Generation mode (`"get1080p"` is deprecated — use `/veo/upsample` instead) |
| `model` | see Models table | Model to use (default: `veo2-fast`; forced to `veo31-fast-ingredients` for `ingredients2video`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — for `image2video` (1–2) or `ingredients2video` (1–3) |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

### `/veo/upsample`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"1080p"`, `"4k"`, `"gif"` | Upsample target |
| `video_id` | string | ID of a previously generated video |

### `/veo/extend`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video |
| `model` | `"veo31"`, `"veo31-fast"` | Only Veo 3.1 series supported |
| `prompt` | string | Optional prompt to guide the extended section |

### `/veo/reshoot`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video (extend outputs not accepted) |
| `motion_type` | `"STATIONARY"`, `"STATIONARY_UP"`, `"STATIONARY_DOWN"`, `"STATIONARY_LEFT"`, `"STATIONARY_RIGHT"`, `"STATIONARY_DOLLY_IN_ZOOM_OUT"`, `"STATIONARY_DOLLY_OUT_ZOOM_IN"`, `"UP"`, `"DOWN"`, `"LEFT_TO_RIGHT"`, `"RIGHT_TO_LEFT"`, `"FORWARD"`, `"BACKWARD"`, `"DOLLY_IN_ZOOM_OUT"`, `"DOLLY_OUT_ZOOM_IN"` | Camera motion |

### `/veo/objects`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"insert"`, `"remove"` | `insert` adds an object (requires `prompt`); `remove` deletes from a masked region (requires `image_mask`) |
| `video_id` | string | ID of a previously generated video (extend outputs not accepted) |
| `prompt` | string | What to add (`insert`) or optionally what to remove (`remove`) |
| `image_mask` | string | Mask URL or base64 JPEG — white pixels define the region; required for `remove` |

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- `get1080p` on `/veo/videos` is a **deprecated alias** — prefer `POST /veo/upsample` with `action="1080p"`
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — 1–2 for `image2video`, 1–3 for `ingredients2video`
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling
- `/veo/extend` supports only `veo31` or `veo31-fast` models
- `/veo/reshoot` does not accept videos produced by `/veo/extend` as the source
- For `remove` on `/veo/objects`, `image_mask` is required; for `insert`, it is optional

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
