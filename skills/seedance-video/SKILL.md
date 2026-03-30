---
name: seedance-video
description: Generate AI dance and motion videos with Seedance (ByteDance) via AceDataCloud API. Use when creating videos from text prompts or animating images into motion videos. Supports multiple models with configurable resolution, duration, and service tiers.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-seedance for tool-use.
---

# Seedance Video Generation

Generate AI dance and motion videos through AceDataCloud's Seedance (ByteDance) API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/seedance/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "doubao-seedance-1-0-pro-250528", "content": [{"type": "text", "text": "a dancer performing contemporary ballet in a misty forest"}], "callback_url": "https://api.acedata.cloud/health"}'
```

This returns a `task_id` immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/seedance/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id from above>"}'
```

## Models

| Model | Type | Best For |
|-------|------|----------|
| `doubao-seedance-1-0-pro-250528` | Pro | High-quality general-purpose |
| `doubao-seedance-1-0-pro-fast-251015` | Pro Fast | Faster pro-quality generation |
| `doubao-seedance-1-5-pro-251215` | Pro 1.5 | Latest model, best quality, supports audio |
| `doubao-seedance-1-0-lite-t2v-250428` | Lite Text-to-Video | Fast, lightweight text-to-video |
| `doubao-seedance-1-0-lite-i2v-250428` | Lite Image-to-Video | Fast, lightweight image-to-video |

## Workflows

### 1. Text-to-Video

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-0-pro-250528",
  "content": [
    {
      "type": "text",
      "text": "a street dancer doing breakdancing moves in an urban setting"
    }
  ],
  "resolution": "720p",
  "ratio": "16:9",
  "duration": 5
}
```

### 2. Image-to-Video

Animate a still image into a motion video.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-5-pro-251215",
  "content": [
    {
      "type": "image_url",
      "role": "first_frame",
      "image_url": {
        "url": "https://example.com/dancer.jpg"
      }
    },
    {
      "type": "text",
      "text": "the person starts dancing gracefully"
    }
  ],
  "resolution": "720p",
  "duration": 5
}
```

### 3. First-and-Last-Frame Video

Interpolate video between a start and end image.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-0-pro-250528",
  "content": [
    {
      "type": "image_url",
      "role": "first_frame",
      "image_url": {"url": "https://example.com/start.jpg"}
    },
    {
      "type": "image_url",
      "role": "last_frame",
      "image_url": {"url": "https://example.com/end.jpg"}
    },
    {
      "type": "text",
      "text": "smooth transition between the two frames"
    }
  ]
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | See models table | Model to use (required) |
| `content` | array | Input items: `text` prompt and/or `image_url` items (required) |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default varies by model) |
| `ratio` | `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`, `"21:9"`, `"adaptive"` | Aspect ratio (default: `"16:9"`) |
| `duration` | `2` – `12` | Duration in seconds (mutually exclusive with `frames`) |
| `frames` | `29` – `289` | Frame count (must satisfy 25+4n; mutually exclusive with `duration`) |
| `seed` | `-1` – `4294967295` | Seed for reproducible results (-1 for random) |
| `camerafixed` | `true` / `false` | Fix the camera position during generation |
| `watermark` | `true` / `false` | Add a watermark to the video |
| `generate_audio` | `true` / `false` | Generate audio (only supported by `doubao-seedance-1-5-pro-251215`) |
| `return_last_frame` | `true` / `false` | Return the last frame of generated video (default: false) |
| `service_tier` | `"default"`, `"flex"` | Processing tier (default: `"default"`) |

### Content Item Roles (for image_url items)

| Role | Description |
|------|-------------|
| `first_frame` | Use image as the first frame of the video |
| `last_frame` | Use image as the last frame of the video |
| `reference_image` | Use image as a reference (not as a frame) |

Note: `first_frame`, `first_frame`+`last_frame`, and `reference_image` scenarios are mutually exclusive.

## Task Polling

Always use `callback_url` to get a `task_id` immediately without blocking:

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-0-pro-250528",
  "content": [{"type": "text", "text": "..."}],
  "callback_url": "https://api.acedata.cloud/health"
}
```

Then poll every 5 seconds until complete:

```json
POST /seedance/tasks
{"task_id": "your-task-id"}
```

States: `pending` → `succeeded` or `failed`.

## MCP Server

```bash
pip install mcp-seedance
```

Or hosted: `https://seedance.mcp.acedata.cloud/mcp`

Key tools: `seedance_generate_video`, `seedance_generate_video_from_image`

## Gotchas

- Model IDs use the full `doubao-seedance-*` naming — short names like `seedance-1.0` are no longer valid
- `content` is an array of typed items — use `{"type": "text", "text": "..."}` for prompts and `{"type": "image_url", "role": "...", "image_url": {"url": "..."}}` for images
- Duration range is **2–12 seconds** — values outside this range will fail
- `frames` and `duration` are mutually exclusive — use one or the other
- Audio generation is only supported by `doubao-seedance-1-5-pro-251215`
- `service_tier` values are `"default"` and `"flex"` (not `"standard"`/`"premium"`)
- Task states use `"succeeded"` (not "completed") — check for this value when polling
