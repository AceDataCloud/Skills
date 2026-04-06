---
name: kling-video
description: Generate AI videos with Kuaishou Kling via AceDataCloud API. Use when creating videos from text or images, extending existing videos, or applying motion control. Supports text-to-video, image-to-video, extend, and motion generation with multiple models and quality modes.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable.
---

# Kling Video Generation

Generate AI videos through AceDataCloud's Kuaishou Kling API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/kling/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "text2video", "prompt": "a cat playing piano on a rooftop at sunset", "model": "kling-v2-5-turbo", "mode": "std", "duration": 5}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /kling/tasks` with `{"task_id": "..."}`.
## Models

| Model | Quality | Best For |
|-------|---------|----------|
| `kling-v1` | Standard | Basic generation, lowest cost |
| `kling-v1-6` | Improved | Better quality than v1 |
| `kling-v2-master` | High | High-quality output |
| `kling-v2-1-master` | High | Improved v2 |
| `kling-v2-5-turbo` | High + Fast | Best speed/quality trade-off (recommended) |
| `kling-video-o1` | Premium | Highest quality |

## Quality Modes

| Mode | Speed | Cost | Use For |
|------|-------|------|---------|
| `std` (Standard) | Slower | Lower | Draft/preview |
| `pro` (Professional) | Faster | Higher | Final output |

## Workflows

### 1. Text-to-Video

```json
POST /kling/videos
{
  "action": "text2video",
  "prompt": "a futuristic city with flying cars",
  "model": "kling-v2-5-turbo",
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
  "model": "kling-v2-5-turbo",
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

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"text2video"`, `"image2video"`, `"extend"` | Generation mode |
| `model` | See models table | Model to use |
| `mode` | `"std"`, `"pro"` | Quality mode |
| `duration` | `5`, `10` | Duration in seconds |
| `aspect_ratio` | `"16:9"`, `"9:16"`, `"1:1"` | Video aspect ratio |
| `cfg_scale` | 0–1 | Prompt relevance strength |
| `negative_prompt` | string | What to avoid in the video |
| `camera_control` | object | Camera movement parameters |
| `element_list` | array | Reference subjects from the element library (each item has `element_id`). Combined with `video_list`, total reference images + subjects ≤ 7 (or ≤ 4 if a reference video is included) |
| `video_list` | array | Reference video(s) via `video_url` (MP4/MOV, 3–10s, ≤200MB, max 1 video). Each item has `video_url`, `refer_type` (`"feature"` or `"base"`), and optional `keep_original_sound` |
| `callback_url` | string | Async callback URL |

## Gotchas

- `duration` only supports `5` or `10` seconds
- `end_image_url` is only for `image2video` action — it defines the last frame
- Motion control (`/kling/motion`) is a separate endpoint from video generation
- `pro` mode costs roughly 2x `std` mode but generates faster with better quality
- Task states use `"succeed"` (not "succeeded") — check for this value when polling
- `negative_prompt` helps avoid unwanted elements (e.g., "blurry, low quality, text")
