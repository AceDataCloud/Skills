---
name: kling-video
description: Generate AI videos with Kuaishou Kling via AceDataCloud API. Use when creating videos from text or images, extending existing videos, applying motion control, or lip-syncing audio/text to video. Supports text-to-video, image-to-video, extend, motion generation, and lip-sync with multiple models and quality modes.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Kling Video Generation

Generate AI videos through AceDataCloud's Kuaishou Kling API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/kling/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "text2video", "prompt": "a cat playing piano on a rooftop at sunset", "model": "kling-v3", "mode": "std", "duration": 5}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /kling/tasks` with `{"id": "..."}`.
## Models

| Model | Quality | Best For |
|-------|---------|----------|
| `kling-v3` | Latest | Best quality, flexible 3–15s duration, optional audio generation |
| `kling-v3-omni` | Latest | Omni model with audio support, flexible 3–15s duration |
| `kling-v2-6` | High | High-quality output with optional audio (pro mode) |
| `kling-v2-5-turbo` | High + Fast | Best speed/quality trade-off |
| `kling-v2-master` | High | High-quality output |
| `kling-v2-1-master` | High | Improved v2 |
| `kling-v1-6` | Improved | Better quality than v1 |
| `kling-v1` | Standard | Basic generation, lowest cost |
| `kling-video-o1` | Premium | Highest quality (thinking model) |

## Quality Modes

| Mode | Speed | Cost | Use For |
|------|-------|------|---------|
| `std` (Standard) | Slower | Lower | Draft/preview |
| `pro` (Professional) | Faster | Higher | Final output |
| `4k` (Native 4K) | — | Premium | Native 4K output — only `kling-v3` and `kling-v3-omni`; incompatible with `camera_control` |

## Workflows

### 1. Text-to-Video

```json
POST /kling/videos
{
  "action": "text2video",
  "prompt": "a futuristic city with flying cars",
  "model": "kling-v3",
  "mode": "std",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

### 2. Image-to-Video

Animate a still image. Optionally specify an ending frame.

```json
POST /kling/videos
{
  "action": "image2video",
  "prompt": "the scene slowly comes alive with movement",
  "start_image_url": "https://example.com/scene.jpg",
  "end_image_url": "https://example.com/end-scene.jpg",
  "model": "kling-v3",
  "mode": "pro"
}
```

### 3. Extend Video

Continue an existing video with additional seconds.

```json
POST /kling/videos
{
  "action": "extend",
  "video_id": "existing-video-id",
  "prompt": "the camera pulls back to reveal the full landscape",
  "model": "kling-v2-5-turbo"
}
```

### 4. Motion Control

Apply precise camera/motion control from an image + reference video.

```json
POST /kling/motion
{
  "image_url": "https://example.com/subject.jpg",
  "video_url": "https://example.com/motion-reference.mp4"
}
```

### 5. Lip Sync

Create a lip-synced video from a source video plus either an audio track or input text.

```json
POST /kling/lip-sync
{
  "video_url": "https://example.com/source.mp4",
  "mode": "audio2video",
  "audio_url": "https://example.com/voiceover.mp3"
}
```

### 6. Talking Photo

Turn a single portrait image plus audio into a talking video.

```json
POST /kling/talking-photo
{
  "image_url": "https://example.com/portrait.jpg",
  "audio_url": "https://example.com/voice.mp3",
  "model": "kling-v2-1-master",
  "duration": 5,
  "mode": "pro"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"extend"` | Generation mode |
| `model` | See models table | Model to use |
| `mode` | `"std"`, `"pro"`, `"4k"` | Quality mode (`4k` only for `kling-v3` / `kling-v3-omni`, incompatible with `camera_control`) |
| `duration` | `5`, `10` (v3/v3-omni: `3`–`15`) | Duration in seconds |
| `generate_audio` | `true`, `false` | Generate audio with video (v3, v3-omni, v2-6 pro only) |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"` | Video aspect ratio |
| `cfg_scale` | 0–1 | Prompt relevance strength |
| `negative_prompt` | string | What to avoid in the video |
| `camera_control` | object | Camera movement parameters |
| `element_list` | array | Reference subjects from the element library (each item has `element_id`). Combined with `video_list`, total reference images + subjects ≤ 7 (or ≤ 4 if a reference video is included) |
| `video_list` | array | Reference video(s) via `video_url` (MP4/MOV, 3–10s, ≤200MB, max 1 video). Each item has `video_url`, `refer_type` (`"feature"` or `"base"`), and optional `keep_original_sound` |
| `callback_url` | string | Async callback URL |
| `image_url` (`/kling/talking-photo`) | URL | Portrait image URL (required) |
| `audio_url` (`/kling/talking-photo`) | URL | Driving audio URL (required) |
| `prompt` (`/kling/talking-photo`) | string | Motion/expression hint for animation (optional) |
| `model` (`/kling/talking-photo`) | `"kling-v1"`, `"kling-v1-6"`, `"kling-v2-master"`, `"kling-v2-1-master"`, `"kling-v2-5-turbo"`, `"kling-v2-6"` | Talking-photo model (default `kling-v2-1-master`) |
| `duration` (`/kling/talking-photo`) | `5`, `10` | Output length in seconds (default `5`) |
| `mode` (`/kling/talking-photo`) | `"std"`, `"pro"` | Talking-photo quality mode (default `pro`) |
| `callback_url` (`/kling/talking-photo`) | string | Async callback URL |
| `async` (`/kling/talking-photo`) | `true`, `false` | Async mode flag (default `false`) |
| `mode` (`/kling/lip-sync`) | `"audio2video"`, `"text2video"` | Lip-sync mode |
| `video_url` (`/kling/lip-sync`) | URL | Source video URL for lip-sync |
| `video_id` (`/kling/lip-sync`) | string | Existing Kling video ID for lip-sync |
| `audio_url` (`/kling/lip-sync`) | URL | Audio source URL (for `audio2video`) |
| `audio_type` (`/kling/lip-sync`) | `"url"`, `"file"` | Audio input type (default `url`) |
| `audio_file` (`/kling/lip-sync`) | string | Audio file payload when `audio_type=file` |
| `text` (`/kling/lip-sync`) | string | Input text to synthesize speech (for `text2video`) |
| `voice_id` (`/kling/lip-sync`) | string | Voice preset ID used in `text2video` |
| `voice_language` (`/kling/lip-sync`) | `"zh"`, `"en"` | TTS language for `text2video` (default `zh`) |
| `voice_speed` (`/kling/lip-sync`) | number | TTS speaking speed (default `1.0`) |

## Gotchas

- `duration` supports `5` or `10` seconds for most models; `kling-v3` and `kling-v3-omni` support flexible `3`–`15` seconds
- `mode=4k` is only available for `kling-v3` and `kling-v3-omni` and is incompatible with `camera_control`
- `generate_audio` enables synchronized audio generation (supported by `kling-v3`, `kling-v3-omni`, and `kling-v2-6` in pro mode)
- `end_image_url` is only for `image2video` action — it defines the last frame
- Motion control (`/kling/motion`) is a separate endpoint from video generation
- Lip-sync is a separate endpoint (`/kling/lip-sync`) and requires `mode`; use `audio_url` for `audio2video` or `text` + voice fields for `text2video`
- Talking photo (`/kling/talking-photo`) combines image animation + lip-sync in one request and requires both `image_url` and `audio_url`
- `pro` mode costs roughly 2x `std` mode but generates faster with better quality
- Task states use `"succeed"` (not "succeeded") — check for this value when polling
- `negative_prompt` helps avoid unwanted elements (e.g., "blurry, low quality, text")
