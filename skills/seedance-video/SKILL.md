---
name: seedance-video
description: Generate and edit AI videos with Seedance via AceDataCloud API. Use for text/image video, Seedance 2.x multimodal image/audio/video reference, Seedance 2.5 pure-audio reference, edit, extend, and up to 30-second output. Supports multiple models, up to 4k, aspect ratio, and optional audio generation.
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
  -d '{"model": "doubao-seedance-2-0-260128", "content": [{"type": "text", "text": "a dancer performing contemporary ballet in a misty forest"}], "callback_url": "https://api.acedata.cloud/health"}'
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

### Seedance 2.5 (latest flagship)

| Model | Best For | Limits |
|-------|----------|--------|
| `doubao-seedance-2-5-260628` | Up to 30 seconds, pure-audio or multimodal reference, video edit/extend | `480p`, `720p`, `1080p`; 30 images / 10 videos / 10 audios / 50 total |

Use `omni_reference_task_type: "auto"`, `"reference"`, `"edit"`, or `"extend"`. Edit and extend require `reference_video` and `ratio: "adaptive"`; edit also requires `duration: -1`. Optional `output_format` is `mp4` or `mov`.

### Seedance 2.0 (multimodal reference, up to 4k)

The 2.0 series adds multimodal reference inputs: real-person / character **image** references, reference **audio**, and reference **video** (see the workflows below).

| Model | Best For | Max resolution |
|-------|----------|----------------|
| `doubao-seedance-2-0-260128` | Highest quality, real-person/character reference, 4k output | `4k` |
| `doubao-seedance-2-0-fast-260128` | Faster 2.0 generation | `720p` |
| `doubao-seedance-2-0-mini-260615` | Lightweight / most cost-effective 2.0 | `720p` |

### Seedance 1.x

| Model | Type | Best For |
|-------|------|----------|
| `doubao-seedance-1-5-pro-251215` | Text+Image-to-Video | 1.5 flagship, audio support |
| `doubao-seedance-1-0-pro-250528` | Text+Image-to-Video | General-purpose, reliable quality |
| `doubao-seedance-1-0-pro-fast-251015` | Text+Image-to-Video | Faster Pro generation |
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
- `reference_image` — image is used as a style / subject / real-person reference (Seedance 2.0 keeps the referenced person or character consistent)

Reference media (Seedance 2.x):
- `audio_url` — use `role: "reference_audio"`
- `video_url` — use `role: "reference_video"`
- 2.5 accepts pure-audio reference; 2.0 requires an image or video alongside audio

### 3. First-frame + Last-frame

Provide both a start and end frame image:

```json
POST /seedance/videos
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "smooth transition between two scenes"},
    {"type": "image_url", "role": "first_frame", "image_url": {"url": "https://example.com/start.jpg"}},
    {"type": "image_url", "role": "last_frame", "image_url": {"url": "https://example.com/end.jpg"}}
  ]
}
```

### 4. Real-person / character reference (Seedance 2.0)

Seedance 2.0 models (`doubao-seedance-2-0-260128`, `doubao-seedance-2-0-fast-260128`, `doubao-seedance-2-0-mini-260615`) can keep a **specific person or character** consistent across a brand-new scene. Pass one or more photos as `image_url` items with `role: "reference_image"` — the model preserves that subject's appearance. Up to 9 reference images are accepted.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "the same person walking through a neon-lit night market, cinematic"},
    {"type": "image_url", "role": "reference_image", "image_url": {"url": "https://example.com/person.jpg"}}
  ],
  "resolution": "1080p",
  "duration": 8
}
```

### 5. Reference audio / video (Seedance 2.0)

2.0 models also accept reference **audio** (voice timbre, background music) and reference **video** (subject content, camera movement, motion, overall style). Add `audio_url` and/or `video_url` content items. Limits: up to 3 audio and 3 video references per request.

```json
POST /seedance/videos
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "a singer performing on stage, matching the reference voice and motion"},
    {"type": "image_url", "role": "reference_image", "image_url": {"url": "https://example.com/person.jpg"}},
    {"type": "audio_url", "role": "reference_audio", "audio_url": {"url": "https://example.com/voice.mp3"}},
    {"type": "video_url", "role": "reference_video", "video_url": {"url": "https://example.com/motion.mp4"}}
  ],
  "generate_audio": true
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | see Models table | Model to use (required) |
| `content` | array | Input items: `text`, `image_url`, `audio_url` (2.0), `video_url` (2.0) (required) |
| `resolution` | `"480p"`, `"720p"`, `"1080p"`, `"4k"` | Output resolution. `4k` is `doubao-seedance-2-0-260128` (standard) only; `2-0-fast` / `2-0-mini` max out at `720p` (default: 720p for pro/2.0, 480p for lite) |
| `ratio` | `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`, `"21:9"`, `"adaptive"` | Aspect ratio (default: 16:9) |
| `duration` | `2` – `30`, or `-1` | 1.0: 2–12 (no auto); 1.5 Pro: 4–12/-1; 2.0: 4–15/-1; 2.5: 4–30/-1 |
| `frames` | 29–289 (must satisfy 25+4n) | Frame count — mutually exclusive with `duration` |
| `seed` | -1 to 4294967295 | Seed for reproducible results (-1 = random) |
| `generate_audio` | `true` / `false` | Generate audio (supported by `doubao-seedance-1-5-pro-251215` and the `doubao-seedance-2-0` series; other models ignore it) |
| `camerafixed` | `true` / `false` | Fix the camera position during generation |
| `watermark` | `true` / `false` | Add a watermark to the generated video |
| `return_last_frame` | `true` / `false` | Return the last frame of the generated video |
| `omni_reference_task_type` | `auto`, `reference`, `edit`, `extend` | Seedance 2.5 task type |
| `output_format` | `mp4`, `mov` | Seedance 2.5 output format |
| `tools` | object[] | Seedance 2.5 web search tool, e.g. `[{"type":"web_search"}]` |
| `priority` | 0–9 | Seedance 2.5 queue priority |
| `safety_identifier` | string | Stable anonymous end-user ID (max 64 chars; do not send PII) |
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
- Image and text scenarios are mutually exclusive per content item — each item has either `text` or `image_url`, not both
- `first_frame` and `last_frame` may be combined in one request, but `reference_image` is mutually exclusive with `first_frame` / `last_frame` — do not mix a reference image with first/last frames
- `generate_audio: true` is supported by `doubao-seedance-1-5-pro-251215` and the `doubao-seedance-2-0` series; other models ignore this field
- Lite models are split: `*-lite-t2v-*` only accepts text, `*-lite-i2v-*` only accepts image-to-video
- `audio_url` and `video_url` reference items are supported by Seedance 2.0 and 2.5; 2.5 also supports pure-audio reference
- Resolution options are `480p`, `720p`, `1080p`, and `4k` (`4k` is `doubao-seedance-2-0-260128` only; `2-0-fast` / `2-0-mini` max out at `720p`) — there is no 360p or 540p
- Duration is model-specific: 1.0 supports 2–12; 1.5 Pro supports 4–12/-1; 2.0 supports 4–15/-1; 2.5 supports 4–30/-1
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-seedance` | Hosted: `https://seedance.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
