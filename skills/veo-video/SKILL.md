---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, upscaling, extending, reshooting, or editing objects in video. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
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
| `veo31` | Yes (native) | Veo 3.1 highest quality (extend only) |
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

Generate a video from a set of reference ingredient images (Veo 3.1 fast ingredient models).

```json
POST /veo/videos
{
  "action": "ingredients2video",
  "prompt": "combine these items into a recipe video",
  "image_urls": ["https://example.com/item1.jpg", "https://example.com/item2.jpg"],
  "model": "veo31-fast-ingredients"
}
```

### 4. Upscale to 1080p / 4K / GIF

Convert a previously generated video to a higher resolution or GIF using the dedicated `/veo/upsample` endpoint.

```json
POST /veo/upsample
{
  "action": "1080p",
  "video_id": "your-video-id"
}
```

| `action` | Output |
|----------|--------|
| `1080p` | Upscale to 1080p |
| `4k` | Upscale to 4K |
| `gif` | Convert to animated GIF |

### 5. Extend a Video

Append additional seconds to an existing video. Only Veo 3.1 series models are supported.

```json
POST /veo/extend
{
  "video_id": "your-video-id",
  "model": "veo31-fast",
  "prompt": "the camera slowly pulls back to reveal the full landscape"
}
```

### 6. Reshoot with Different Camera Motion

Re-render an existing video with a different camera movement.

```json
POST /veo/reshoot
{
  "video_id": "your-video-id",
  "motion_type": "PAN_LEFT"
}
```

Common `motion_type` values: `STATIONARY`, `STATIONARY_UP`, `STATIONARY_DOWN`, `STATIONARY_LEFT`, `STATIONARY_RIGHT`, `PAN_LEFT`, `PAN_RIGHT`, `ZOOM_IN`, `ZOOM_OUT`, `TILT_UP`, `TILT_DOWN`, `TRACKING`.

### 7. Insert or Remove Objects

Add or remove objects from a video using a mask image.

```json
POST /veo/objects
{
  "action": "insert",
  "video_id": "your-video-id",
  "prompt": "a red balloon floating in the upper-right corner",
  "image_mask": "https://example.com/mask.png"
}
```

```json
POST /veo/objects
{
  "action": "remove",
  "video_id": "your-video-id",
  "image_mask": "https://example.com/mask.png"
}
```

## Parameters

### `/veo/videos`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` *(legacy)* | Generation mode (`get1080p` is superseded by `/veo/upsample`) |
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — for `image2video` and `ingredients2video` |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |
| `callback_url` | string | Webhook URL called when generation completes |

### `/veo/upsample`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"1080p"`, `"4k"`, `"gif"` | Target format |
| `video_id` | string | ID of a previously generated video task |
| `callback_url` | string | Webhook URL called when upsampling completes |

### `/veo/extend`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video task (not itself extended) |
| `model` | `"veo31-fast"`, `"veo31"` | Veo 3.1 series only |
| `prompt` | string | Optional prompt guiding the extended section |
| `callback_url` | string | Webhook URL called when extension completes |

### `/veo/reshoot`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `video_id` | string | ID of a previously generated video task |
| `motion_type` | string | Camera motion style (see Workflow 6 for values) |
| `callback_url` | string | Webhook URL called when reshoot completes |

### `/veo/objects`

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"insert"`, `"remove"` | Insert a new object or remove an existing one |
| `video_id` | string | ID of a previously generated video task |
| `prompt` | string | Required for `insert`: describes what to add; optional for `remove` |
| `image_mask` | string | Mask image URL/base64 — white pixels indicate the target region |
| `callback_url` | string | Webhook URL called when operation completes |

## Task Polling

The `/veo/tasks` endpoint supports both single and batch retrieval:

```json
POST /veo/tasks
{ "action": "retrieve", "id": "<task_id>" }
```

```json
POST /veo/tasks
{ "action": "retrieve_batch", "ids": ["<id1>", "<id2>"] }
```

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- `/veo/upsample` is the dedicated upscaling endpoint; `/veo/videos` action `get1080p` also works for legacy use
- `/veo/extend` only supports Veo 3.1 series (`veo31-fast`, `veo31`); the source video must not itself be extended
- `/veo/reshoot` and `/veo/objects` cannot be applied to extended videos
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — pass one or more image URLs
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
