---
name: seedance-video
description: Generate AI dance and motion videos with Seedance (ByteDance) via AceDataCloud API. Use when creating videos from text prompts, animating images into motion videos, or guiding Seedance 2.0 with human/character, audio, and video references. Supports multiple models with configurable resolution, aspect ratio, duration, and optional audio generation.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-seedance for tool-use.
---

# Seedance Video Generation

Generate AI dance and motion videos through AceDataCloud's Seedance (ByteDance) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/seedance/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "doubao-seedance-1-0-pro-250528", "content": [{"type": "text", "text": "a dancer performing contemporary ballet in a misty forest"}], "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /seedance/tasks` with `{"id": "..."}`.
This returns a task ID immediately. Poll for the result:

```bash
curl -X POST https://api.acedata.cloud/seedance/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from above>"}'
```

## Models

| Model | Type | Best For |
|-------|------|----------|
| `doubao-seedance-1-0-pro-250528` | Text+Image-to-Video | General-purpose, reliable quality |
| `doubao-seedance-1-0-pro-fast-251015` | Text+Image-to-Video | Faster Pro generation |
| `doubao-seedance-1-5-pro-251215` | Text+Image-to-Video | Latest model, highest quality, audio support |
| `doubao-seedance-1-0-lite-t2v-250428` | Text-to-Video only | Lightweight text-to-video |
| `doubao-seedance-1-0-lite-i2v-250428` | Image-to-Video only | Lightweight image-to-video |
| `doubao-seedance-2-0-260128` | Multi-modal Video | Seedance 2.0 standard — supports character, audio, and video references; up to 4k |
| `doubao-seedance-2-0-fast-260128` | Multi-modal Video | Seedance 2.0 fast — identity/reference workflows with quicker turnaround |
| `doubao-seedance-2-0-mini-260615` | Multi-modal Video | Seedance 2.0 lightweight — faster, lower-cost reference generation |

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
- `reference_image` — Seedance 2.0 human / character / subject reference

Seedance 2.0 also accepts:
- `{"type": "audio_url", "role": "reference_audio", "audio_url": {"url": "https://example.com/ref.mp3"}}`
- `{"type": "video_url", "role": "reference_video", "video_url": {"url": "https://example.com/ref.mp4"}}`

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

### 4. Character / identity reference (Seedance 2.0)

Use `reference_image` to keep the same person or character across a new scene or motion:

```json
POST /seedance/videos
{
  "model": "doubao-seedance-2-0-fast-260128",
  "content": [
    {"type": "text", "text": "the same person smiles and waves at the camera in soft studio light"},
    {
      "type": "image_url",
      "role": "reference_image",
      "image_url": {"url": "https://example.com/person.jpg"}
    }
  ],
  "resolution": "720p",
  "ratio": "9:16",
  "duration": 5
}
```

`reference_image` is only for Seedance 2.0 models. It cannot be combined with `first_frame` or `last_frame` in the same request.

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | see Models table | Model to use (required) |
| `content` | array | Input items: `text`, `image_url`, `audio_url`, and `video_url` objects (required) |
| `resolution` | `"480p"`, `"720p"`, `"1080p"`, `"4k"` | Output resolution (`4k` is only available on `doubao-seedance-2-0-260128`; `2-0-fast` / `2-0-mini` top out at `720p`) |
| `ratio` | `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`, `"21:9"`, `"adaptive"` | Aspect ratio (default: 16:9) |
| `duration` | `2` – `15` | Duration in seconds (`1.x` models top out at 12; `2.0` models allow up to 15) |
| `frames` | 29–361 (must satisfy 25+4n) | Frame count — mutually exclusive with `duration` |
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

## Gotchas

- Model names use the `doubao-*` convention (e.g. `doubao-seedance-1-0-pro-250528`) — old short names like `seedance-1.0` are not valid
- The `content` array replaces the old `prompt` + `image_url` fields; always use `content`
- Each content item should contain only one content type: `text`, `image_url`, `audio_url`, or `video_url`
- `reference_image` is only supported on Seedance 2.0 models, and cannot be mixed with `first_frame` / `last_frame`
- `reference_audio` and `reference_video` are Seedance 2.0-only roles
- `generate_audio: true` is only supported by `doubao-seedance-1-5-pro-251215`; other models ignore this field
- Lite models are split: `*-lite-t2v-*` only accepts text, `*-lite-i2v-*` only accepts image-to-video
- `4k` output is only available on `doubao-seedance-2-0-260128`; `2-0-fast` / `2-0-mini` max out at `720p`
- `service_tier` values are `"default"` and `"flex"` (not "standard"/"premium")
- Duration range is **2–15 seconds** overall, but `1.x` models are still effectively capped at **12 seconds**
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-seedance` | Hosted: `https://seedance.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
