---
name: veo-video
description: Generate AI videos with Google Veo via AceDataCloud API. Use when creating videos from text descriptions, animating still images into video, or converting lower-resolution results to full resolution. Supports Veo 2, Veo 2 Fast, Veo 3, Veo 3 Fast, Veo 3.1, and Veo 3.1 Fast models.
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
  -d '{"prompt": "a whale breaching in slow motion at golden hour", "model": "veo3", "action": "text2video", "callback_url": "https://api.acedata.cloud/health"}'
```

This returns a `task_id` immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/veo/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id from above>"}'
```

## Models

| Model | Duration | Audio | Best For |
|-------|----------|-------|----------|
| `veo2` | 5–8s | No | Fast, cost-effective generation |
| `veo2-fast` | 5–8s | No | Fastest Veo 2 generation |
| `veo3` | 8s | Yes (native) | Full audiovisual generation |
| `veo3-fast` | 8s | Yes (native) | Faster Veo 3 generation |
| `veo31` | 8s | Yes (native) | Latest model, highest quality |
| `veo31-fast` | 8s | Yes (native) | Faster Veo 3.1 generation |
| `veo31-fast-ingredient` | 8s | Yes (native) | Ingredient mode for Veo 3.1 |

## Workflows

### 1. Text-to-Video

```json
POST /veo/videos
{
  "action": "text2video",
  "prompt": "cinematic aerial shot of the Northern Lights over Iceland",
  "model": "veo3",
  "aspect_ratio": "16:9"
}
```

### 2. Image-to-Video

Animate a still image into video.

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

Convert a generated video to full 1080p resolution.

```json
POST /veo/videos
{
  "action": "get1080p",
  "video_id": "your-video-id"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"get1080p"` | Generation mode (required) |
| `model` | `"veo2"`, `"veo2-fast"`, `"veo3"`, `"veo3-fast"`, `"veo31"`, `"veo31-fast"`, `"veo31-fast-ingredient"` | Model to use (default: `veo2-fast`) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"3:4"`, `"4:3"` | Video aspect ratio (image2video only) |
| `resolution` | `"4k"`, `"1080p"`, `"gif"` | Output resolution |
| `image_urls` | array of URLs | Reference images (image2video only) |
| `video_id` | string | Video ID to upscale (get1080p only) |
| `translation` | `true` / `false` | Auto-translate prompt (default: false) |
| `generate_audio` | `true` / `false` | Enable/disable audio (veo3/veo31 default to true) |

## Task Polling

Always use `callback_url` to get a `task_id` immediately without blocking:

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
{"task_id": "your-task-id"}
```

States: `pending` → `succeeded` or `failed`.

## MCP Server

```bash
pip install mcp-veo
```

Or hosted: `https://veo.mcp.acedata.cloud/mcp`

Key tools: `veo_generate_video`, `veo_generate_video_from_image`, `veo_get_1080p_video`

## Gotchas

- Veo 3 and 3.1 generate **native audio** — use `generate_audio: false` to suppress
- The `action` parameter is **required** — use `"text2video"`, `"image2video"`, or `"get1080p"`
- For image-to-video, provide `image_urls` as an array (not a single `image_url`)
- For upscaling, use `"action": "get1080p"` with `video_id` (not a separate endpoint)
- Model names use no hyphens: `veo2`, `veo3`, `veo31` (not `veo-2`, `veo-3`, `veo-3.1`)
- `fast` variants are cheaper and faster but may have lower quality
- `veo2` does NOT support audio generation
- Task states use `"succeeded"` (not "completed") — check for this value when polling
