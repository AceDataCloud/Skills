---
name: wan-video
description: Generate AI videos with Wan (Alibaba) via AceDataCloud API. Use when creating videos from text prompts or animating images into video. Supports text-to-video, image-to-video, reference video transfer, multi-resolution (480P-1080P), and optional audio.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-wan for tool-use.
---

# Wan Video Generation

Generate AI videos through AceDataCloud's Wan (Alibaba) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/wan/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "text2video", "prompt": "a dolphin jumping through ocean waves at golden hour", "model": "wan2.6-t2v"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /wan/tasks` with `{"id": "..."}`.
## Models

| Model | Type | Best For |
|-------|------|----------|
| `wan2.6-t2v` | Text-to-Video | Creating video from text description |
| `wan2.6-i2v` | Image-to-Video | Animating a still image into video |
| `wan2.6-r2v` | Reference Video-to-Video | Character extraction and transfer from reference video |
| `wan2.6-i2v-flash` | Image-to-Video (Fast) | Quick image-to-video generation |
| `wan3.0-video` | All-in-One | Text, frames, reference media, files, and public links |

## Workflows

### 1. Text-to-Video

```json
POST /wan/videos
{
  "action": "text2video",
  "prompt": "a time-lapse of flowers blooming in a meadow",
  "model": "wan2.6-t2v",
  "resolution": "720P",
  "duration": 5
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /wan/videos
{
  "action": "image2video",
  "prompt": "gentle wind blows through the scene",
  "model": "wan2.6-i2v",
  "image_url": "https://example.com/landscape.jpg",
  "resolution": "720P",
  "duration": 5
}
```

### 3. Image-to-Video (Flash)

Faster image-to-video generation with reduced latency.

```json
POST /wan/videos
{
  "action": "image2video",
  "prompt": "camera slowly pans across the landscape",
  "model": "wan2.6-i2v-flash",
  "image_url": "https://example.com/scene.jpg"
}
```

### 4. Reference Video Transfer

Extract characters or timbres from a reference video and transfer them into a new generation.

```json
POST /wan/videos
{
  "action": "text2video",
  "prompt": "the character walks through a futuristic city at night",
  "model": "wan2.6-r2v",
  "reference_video_urls": ["https://example.com/reference.mp4"]
}
```

### 5. Multi-Cut Editing

Generate a video with multiple shots rather than a single continuous take.

```json
POST /wan/videos
{
  "action": "text2video",
  "prompt": "a chef preparing a meal in a busy kitchen",
  "model": "wan2.6-t2v",
  "shot_type": "multi",
  "duration": 10
}
```

### 6. Video with Audio

Enable audio generation alongside the video.

```json
POST /wan/videos
{
  "action": "text2video",
  "prompt": "ocean waves crashing on a rocky shore",
  "model": "wan2.6-t2v",
  "audio": true
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `model` | Yes | `"wan2.6-t2v"`, `"wan2.6-i2v"`, `"wan2.6-r2v"`, `"wan2.6-i2v-flash"`, `"wan3.0-video"` | Model |
| `action` | Wan 2.6 | `"text2video"`, `"image2video"` | Action type for Wan 2.6 flows |
| `prompt` | Usually | string | Scene description (optional for some reference-only Wan 3 flows) |
| `image_url` | For image2video | string | Source image URL (required for image-to-video) |
| `negative_prompt` | No | string (max 500 chars) | Content to exclude from generation |
| `reference_video_urls` | For r2v | array of strings | Reference videos for character/timbre extraction |
| `shot_type` | No | `"single"`, `"multi"` | Continuous shot or multi-cut editing |
| `audio` | No | boolean | Enable audio in the generated video |
| `audio_url` | No | string | Reference audio URL |
| `resolution` | No | `"480P"`, `"720P"`, `"1080P"` | Output resolution (default: 720P) |
| `ratio` | No | `"adaptive"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"` | Aspect ratio (Wan 3) |
| `size` | No | string | The size of the generated video |
| `duration` | No | Wan 2.6: `5`, `10`, `15`; Wan 3: `2`–`30` or `-1` | Video duration in seconds |
| `media` | Wan 3 | array | Wan 3 media descriptors (`first_frame`, `last_frame`, `reference_image`, `reference_video`, `reference_audio`, `file`, `link`) |
| `prompt_extend` | No | boolean | Enable LLM-based prompt rewriting |
| `seed` | No | integer (`0` to `2147483647`) | Deterministic seed |
| `watermark` | No | boolean | Enable or disable watermark |
| `async` | No | boolean | Return task immediately (poll `/wan/tasks`) |
| `callback_url` | No | string | Async webhook notification URL |

## Gotchas

- `image_url` is **required** for `wan2.6-i2v` and `wan2.6-i2v-flash` models
- `reference_video_urls` is used only with `wan2.6-r2v` for character/timbre transfer
- `negative_prompt` has a maximum length of 500 characters
- Wan 2.6 durations are 5, 10, or 15 seconds; Wan 3 supports 2–30 seconds or `-1` auto duration
- Default resolution is 720P; use 1080P for higher quality at increased cost
- `shot_type: "multi"` produces multi-cut edits rather than a single continuous shot

> **MCP:** `pip install mcp-wan` | Hosted: `https://wan.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)


## Wan 3 All-in-One

`wan3.0-video` infers the workflow from `media`. Supported types are `first_frame`, `last_frame`, `reference_image` (up to 10), `reference_video` (up to 5, 15 seconds total), `reference_audio` (up to 5, 15 seconds total), `file`, and `link`. Frame mode cannot be mixed with reference/file/link mode.

```json
POST /wan/videos
{
  "model": "wan3.0-video",
  "prompt": "Use image 1 to create a cinematic product video",
  "media": [{"type":"reference_image","url":"https://cdn.acedata.cloud/r9vsv9.png"}],
  "resolution": "720P",
  "ratio": "16:9",
  "duration": 5,
  "audio": true,
  "async": true
}
```

Wan 3 supports 2–30 seconds or `-1` automatic duration. Poll with the existing `/wan/tasks` endpoint.
