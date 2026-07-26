---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, blending 1-3 reference images, or converting an existing generated Veo video to 1080p. Supports current Veo 3 and Veo 3.1 model variants, including ingredient mode.
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
  -d '{"action": "text2video", "prompt": "a whale breaching in slow motion at golden hour", "model": "veo31-fast", "async": true, "callback_url": "https://api.acedata.cloud/health"}'
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

| Model | Best For | Input Rules |
|-------|----------|-------------|
| `veo3` | Higher-quality text-to-video or image-to-video | No images = text-to-video; 1-2 images = first-frame / first-and-last-frame mode |
| `veo3-fast` | Faster text-to-video or image-to-video | No images = text-to-video; 1-2 images = first-frame / first-and-last-frame mode |
| `veo31` | Veo 3.1 quality mode | No images = text-to-video; 1-2 images = first-frame / first-and-last-frame mode |
| `veo31-fast` | Veo 3.1 fast mode | No images = text-to-video; 1-2 images = first-frame / first-and-last-frame mode |
| `veo31-fast-ingredients` | Multi-image ingredient blending | Requires `image_urls`; supports 1-3 images; not for text-only generation |

## Workflows

### 1. Text-to-Video

```json
POST /veo/videos
{
  "action": "text2video",
  "prompt": "cinematic aerial shot of the Northern Lights over Iceland",
  "model": "veo31-fast",
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

Blend 1–3 reference images into a video. This mode is specifically for
`veo31-fast-ingredients`.

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

### 4. Get a 1080p Output from an Existing Generated Video

Convert a previously generated Veo result to a 1080p output. Use the generated
video's `data[].id` as `video_id`.

```json
POST /veo/videos
{
  "action": "get1080p",
  "video_id": "your-video-id",
  "model": "veo31-fast"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"ingredients2video"`, `"get1080p"` | Generation mode |
| `model` | see Models table | Current documented models are `veo3`, `veo3-fast`, `veo31-fast`, `veo31`, and `veo31-fast-ingredients` |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution. Docs note that omitted values fall back to the service default. |
| `aspect_ratio` | `"16:9"`, `"9:16"` | Aspect ratio hint |
| `image_urls` | array of strings | Reference image URLs — up to 2 for normal image-to-video, or 1-3 for `veo31-fast-ingredients` |
| `video_id` | string | Generated Veo video ID — used for `get1080p` |
| `translation` | `true` / `false` | Auto-translate the prompt to English before generation |
| `callback_url` | string | Optional webhook for completion |
| `async` | boolean | If `true`, return a task ID immediately and poll `/veo/tasks` |

## Task Retrieval

Poll a single task:

```json
POST /veo/tasks
{
  "id": "your-task-id",
  "action": "retrieve"
}
```

Poll multiple tasks:

```json
POST /veo/tasks
{
  "ids": ["task-1", "task-2"],
  "action": "retrieve_batch"
}
```

Single-task responses include the original `request` and a final `response`.
Successful results return `response.data[]` items with fields such as `id`,
`video_url`, `created_at`, `complete_at`, and `state`.

## Gotchas

- The current documented API surface is `POST /veo/videos` plus `POST /veo/tasks`; older routes such as `/veo/extend`, `/veo/reshoot`, `/veo/objects`, and `/veo/upsample` are not in the current OpenAPI spec.
- `veo31-fast-ingredients` requires image input and is the only documented 1-3 image blend mode.
- For other models, omit `image_urls` for text-to-video, use 1 image for first-frame mode, and 2 images for first-and-last-frame mode.
- The `get1080p` action uses a previously generated video's `data[].id` as `video_id`, not the task ID and not a URL.
- `translation: true` auto-translates non-English prompts before sending them to Veo.
- Task polling uses `id` or `ids` in the `/veo/tasks` request body; `retrieve_batch` is supported.
- Successful results use `response.data[]` with per-video `state` values such as `succeeded`.

> **MCP:** `pip install mcp-veo` | Hosted: `https://veo.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
