---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, extending or reshooting existing videos, upsampling to 4K/1080p, or editing objects in video. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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
| `veo31-fast-ingredients` | Yes (native) | Veo 3.1 fast, multi-image fusion mode (1–3 images required) |

### Image Input Rules

| Model | Image Count | Mode |
|-------|-------------|------|
| `veo2-fast` | 1 | First-frame mode |
| `veo3-fast`, `veo31-fast` | 1 | First-frame mode |
| `veo3-fast`, `veo31-fast` | 2 | First+last-frame mode |
| `veo2`, `veo3`, `veo31` | 1 | First-frame mode |
| `veo2`, `veo3`, `veo31` | 2 | First+last-frame mode |
| `veo31-fast-ingredients` | 1–3 (required) | Multi-image fusion mode |

- **No images** → text-to-video mode (not supported by `veo31-fast-ingredients`)
- **With images** → image-to-video mode (behavior depends on count, see table)

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

### 3. Upscale to 1080p

Convert a previously generated video to full 1080p resolution.

```json
POST /veo/videos
{
  "action": "get1080p",
  "video_id": "your-video-id",
  "model": "veo3"
}
```

### 4. Ingredients-to-Video (Multi-Image Fusion)

Fuse 1–3 reference images into a single video. Only supported by `veo31-fast-ingredients`.

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "image_urls": [
    "https://example.com/subject1.jpg",
    "https://example.com/subject2.jpg"
  ],
  "prompt": "the two characters interact on a futuristic stage",
  "model": "veo31-fast-ingredients"
}
```

### 5. Extend a Video

Continue an existing Veo video with additional AI-generated footage. Only `veo31-fast` and `veo31` are supported.

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera slowly zooms out to reveal more of the landscape"
}
```

### 6. Upsample a Video

Convert an existing video to a higher resolution or GIF preview.

```json
POST /veo/upsample
{
  "video_id": "your-video-id",
  "action": "4k"
}
```

| `action` | Output | Credit |
|----------|--------|--------|
| `1080p` | 1080p resolution | 0.16 / call |
| `4k` | 4K resolution | 0.50 / call |
| `gif` | Animated GIF preview | 0.13 / call |

### 7. Reshoot with New Camera Motion

Regenerate an existing video using a different camera movement. Content stays the same, only the camera motion changes.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "LEFT_TO_RIGHT"
}
```

Supported `motion_type` values: `STATIONARY`, `STATIONARY_UP`, `STATIONARY_DOWN`, `STATIONARY_LEFT`, `STATIONARY_RIGHT`, `STATIONARY_DOLLY_IN_ZOOM_OUT`, `STATIONARY_DOLLY_OUT_ZOOM_IN`, `UP`, `DOWN`, `LEFT_TO_RIGHT`, `RIGHT_TO_LEFT`, `FORWARD`, `BACKWARD`, `DOLLY_IN_ZOOM_OUT`, `DOLLY_OUT_ZOOM_IN`.

### 8. Insert or Remove Objects

Add or erase objects in an existing video using a mask.

```json
POST /veo/objects
{
  "video_id": "your-video-id",
  "action": "insert",
  "prompt": "add a flying pig with black wings"
}
```

```json
POST /veo/objects
{
  "video_id": "your-video-id",
  "action": "remove",
  "image_mask": "https://example.com/mask.jpg",
  "prompt": "remove the white cloud"
}
```

| `action` | `prompt` | `image_mask` |
|----------|----------|--------------|
| `insert` | Required — describes the object to add | Optional — white pixels = insertion area; omit to let AI decide |
| `remove` | Optional — describes what to erase | Required — white pixels = area to erase |

`image_mask` accepts a public HTTP(S) URL or a base64-encoded JPEG string.

## Parameters

### `/veo/videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` | Generation mode |
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — required for `image2video` and `ingredients2video` |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

### `/veo/extend`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `video_id` | Yes | Source video ID (from `/veo/videos`) |
| `model` | Yes | `"veo31-fast"` or `"veo31"` only |
| `prompt` | No | Text to guide the extended segment |

### `/veo/upsample`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `video_id` | Yes | Source video ID (from any Veo endpoint) |
| `action` | Yes | `"1080p"`, `"4k"`, or `"gif"` |

### `/veo/reshoot`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `video_id` | Yes | Source video ID — must NOT be from `/veo/extend` |
| `motion_type` | Yes | Camera motion style (see motion_type list in Workflow 7) |

### `/veo/objects`

| Parameter | Required | Description |
|-----------|----------|-------------|
| `video_id` | Yes | Source video ID — must NOT be from `/veo/extend` |
| `action` | Yes | `"insert"` or `"remove"` |
| `prompt` | Conditional | Required for `insert`; optional for `remove` |
| `image_mask` | Conditional | Required for `remove`; optional for `insert` |

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- `veo31-fast-ingredients` **requires** `image_urls` (1–3 images) and does NOT support text-only generation
- `veo2-fast` only supports **1 image** input (first-frame mode)
- The `get1080p` action uses `video_id` (from a prior generation), not a URL
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — pass one or more image URLs for image-to-video
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling
- `/veo/extend` results can be extended again but **cannot** be passed to `/veo/reshoot` or `/veo/objects`
- `/veo/reshoot` and `/veo/objects` require video IDs from `/veo/videos` (not from `/veo/extend`)
- `/veo/upsample` accepts video IDs from any Veo endpoint (videos, extend, reshoot, objects)

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
