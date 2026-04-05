---
name: seedance-video
description: Generate AI dance and motion videos with Seedance (ByteDance) via AceDataCloud API. Use when creating videos from text prompts or animating images into motion videos. Supports multiple models with configurable resolution, aspect ratio, duration, and optional audio generation.
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

This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/seedance/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id from above>"}'
```

## Models

| Model | Type | Best For |
|-------|------|----------|
| `doubao-seedance-1-0-pro-250528` | Text+Image-to-Video | General-purpose, reliable quality |
| `doubao-seedance-1-0-pro-fast-251015` | Text+Image-to-Video | Faster Pro generation |
| `doubao-seedance-1-5-pro-251215` | Text+Image-to-Video | Latest model, highest quality, audio support |
| `doubao-seedance-1-0-lite-t2v-250428` | Text-to-Video only | Lightweight text-to-video |
| `doubao-seedance-1-0-lite-i2v-250428` | Image-to-Video only | Lightweight image-to-video |

## Workflows

### 1. Text-to-Video

Pass a text content item in the `content` array.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-0-pro-250528",
  "content": [
    {"type": "text", "text": "a street dancer doing breakdancing moves in an urban setting"}
  ],
  "resolution": "1080p",
  "ratio": "16:9",
  "duration": 5
}
```

### 2. Image-to-Video

Include an image content item (with an optional `role`) alongside the text.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-5-pro-251215",
  "content": [
    {"type": "text", "text": "the person starts dancing gracefully"},
    {
      "type": "image_url",
      "role": "first_frame",
      "image_url": {"url": "https://example.com/dancer.jpg"}
    }
  ],
  "resolution": "720p",
  "duration": 5
}
```

Image roles:
- `first_frame` — image is used as the opening frame
- `last_frame` — image is used as the closing frame
- `reference_image` — image is used as a style/content reference

### 3. First-frame + Last-frame

Provide both a start and end frame image:

```json
POST /seedance/videos
{
  "model": "doubao-seedance-1-0-pro-250528",
  "content": [
    {"type": "text", "text": "smooth transition between two scenes"},
    {"type": "image_url", "role": "first_frame", "image_url": {"url": "https://example.com/start.jpg"}},
    {"type": "image_url", "role": "last_frame", "image_url": {"url": "https://example.com/end.jpg"}}
  ]
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | see Models table | Model to use (required) |
| `content` | array | Input items: text and/or image_url objects (required) |
| `resolution` | `"480p"`, `"720p"`, `"1080p"` | Output resolution (default: 720p for pro, 480p for lite) |
| `ratio` | `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`, `"21:9"`, `"adaptive"` | Aspect ratio (default: 16:9) |
| `duration` | `2` – `12` | Duration in seconds |
| `frames` | 29–289 (must satisfy 25+4n) | Frame count — mutually exclusive with `duration` |
| `seed` | -1 to 4294967295 | Seed for reproducible results (-1 = random) |
| `generate_audio` | `true` / `false` | Generate audio (only supported by `doubao-seedance-1-5-pro-251215`) |
| `camerafixed` | `true` / `false` | Fix the camera position during generation |
| `watermark` | `true` / `false` | Add a watermark to the generated video |
| `return_last_frame` | `true` / `false` | Return the last frame of the generated video |
| `service_tier` | `"default"`, `"flex"` | Processing tier (default: default) |
| `execution_expires_after` | number | Task timeout threshold in seconds |

## Inline Parameter Syntax

You can also embed generation parameters directly in the text prompt using the `--param value` syntax:

```
A kitten yawning at the camera. --rs 720p --rt 16:9 --dur 5 --fps 24 --seed 42
```

Supported inline params: `--rs` (resolution), `--rt` (ratio), `--dur` (duration), `--frames`, `--fps` (24 only), `--seed`, `--cf` (camera_fixed), `--wm` (watermark).

## Task Polling

Always use `callback_url` to get a task ID immediately without blocking:

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

Key tools: `seedance_generate_video`, `seedance_generate_video_from_image`, `seedance_get_task`, `seedance_get_tasks_batch`, `seedance_list_models`

## Gotchas

- Model names use the `doubao-*` convention (e.g. `doubao-seedance-1-0-pro-250528`) — old short names like `seedance-1.0` are not valid
- The `content` array replaces the old `prompt` + `image_url` fields; always use `content`
- Image and text scenarios are mutually exclusive per content item — each item has either `text` or `image_url`, not both
- `first_frame`, `last_frame`, and `reference_image` roles are mutually exclusive scenarios — pick one pattern per request
- `generate_audio: true` is only supported by `doubao-seedance-1-5-pro-251215`; other models ignore this field
- Lite models are split: `*-lite-t2v-*` only accepts text, `*-lite-i2v-*` only accepts image-to-video
- Resolution options are `480p`, `720p`, `1080p` — there is no 360p or 540p
- `service_tier` values are `"default"` and `"flex"` (not "standard"/"premium")
- Duration range is **2–12 seconds** — values outside this range will fail
- Task states use `"succeeded"` (not "completed") — check for this value when polling
