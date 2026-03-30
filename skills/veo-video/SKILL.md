---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, or upscaling to 1080p. Supports Veo 2, Veo 3, and Veo 3.1 models including fast variants.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-veo for tool-use.
---

# Veo Video Generation

Generate AI videos through AceDataCloud's Google Veo API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/veo/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "text2video", "prompt": "a whale breaching in slow motion at golden hour", "model": "veo3", "callback_url": "https://api.acedata.cloud/health"}'
```

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
| `veo31-fast-ingredient` | Yes (native) | Veo 3.1 fast, ingredient mode |

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

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"get1080p"` | Generation mode |
| `model` | see Models table | Model to use (default: `veo2-fast`) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution (default: 720p) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio — only valid for `image2video` |
| `image_urls` | array of strings | Reference image URLs — only for `image2video` |
| `video_id` | string | Video to upscale — only for `get1080p` |
| `translation` | `true` / `false` | Auto-translate prompt to English (default: false) |

## Task Polling

Always use `callback_url` to get a task ID immediately without blocking:

```json
POST /veo/videos
{
  "action": "text2video",
  "prompt": "...",
  "model": "veo3",
  "callback_url": "https://api.acedata.cloud/health"
}
```

Then poll every 5 seconds until complete:

```json
POST /veo/tasks
{"id": "your-task-id"}
```

For batch polling:

```json
POST /veo/tasks
{"ids": ["task-id-1", "task-id-2"], "action": "retrieve_batch"}
```

States: `pending` → `succeeded` or `failed`.

## MCP Server

```bash
pip install mcp-veo
```

Or hosted: `https://veo.mcp.acedata.cloud/mcp`

Key tools: `veo_text_to_video`, `veo_image_to_video`, `veo_get_1080p`, `veo_get_task`, `veo_get_tasks_batch`

## Gotchas

- Veo 3 and 3.1 models generate **native audio** — `veo2`/`veo2-fast` do NOT support audio
- The `get1080p` action uses `video_id` (from a prior generation), not a URL
- `aspect_ratio` is **only valid** for the `image2video` action
- `image_urls` accepts an array — pass one or more image URLs for image-to-video
- `translation: true` auto-translates Chinese or other non-English prompts before sending to Veo
- Task polling uses `id` (not `task_id`) in the `/veo/tasks` request body
- Task states use `"succeeded"` (not "completed") — check for this value when polling
