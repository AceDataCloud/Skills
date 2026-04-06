---
name: luma-video
description: Generate AI videos with Luma Dream Machine via AceDataCloud API. Use when creating videos from text prompts, generating videos from reference images, extending existing videos, or any video generation task with Luma. Supports text-to-video, image-to-video, and video extension.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-luma for tool-use.
---

# Luma Video Generation

Generate AI videos through AceDataCloud's Luma Dream Machine API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/luma/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a drone flying over a mountain lake at sunrise", "action": "generate", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /luma/tasks` with `{"task_id": "..."}`.

## Workflows

### 1. Text-to-Video

Generate video purely from a text description.

```json
POST /luma/videos
{
  "prompt": "a timelapse of flowers blooming in a garden",
  "action": "generate",
  "aspect_ratio": "16:9",
  "loop": false,
  "enhancement": true
}
```

### 2. Image-to-Video

Use start and/or end reference images to guide generation.

```json
POST /luma/videos
{
  "prompt": "the scene comes alive with gentle wind",
  "action": "generate",
  "start_image_url": "https://example.com/scene.jpg",
  "end_image_url": "https://example.com/scene-end.jpg",
  "aspect_ratio": "16:9"
}
```

### 3. Extend a Video

Continue an existing video with a new prompt.

```json
POST /luma/videos
{
  "action": "extend",
  "video_id": "existing-video-id",
  "prompt": "the camera continues forward through the forest"
}
```

## Aspect Ratios

| Ratio | Use Case |
|-------|----------|
| `16:9` | Landscape (default) — YouTube, TV |
| `9:16` | Portrait — TikTok, Instagram Stories |
| `1:1` | Square — Social media |
| `4:3` | Classic — Presentations |
| `21:9` | Ultra-wide — Cinematic |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | — | Text description of the video (required) |
| `action` | string | `"generate"` | `"generate"` or `"extend"` |
| `aspect_ratio` | string | `"16:9"` | Video aspect ratio |
| `loop` | bool | `false` | Create seamless loop |
| `enhancement` | bool | `true` | Enhance prompt for better results |
| `start_image_url` | string | — | Reference image for first frame |
| `end_image_url` | string | — | Reference image for last frame |
| `video_id` | string | — | ID of video to extend (alternative to `video_url`) |
| `video_url` | string | — | URL of video to extend (alternative to `video_id`) |
| `timeout` | number | — | Timeout in seconds for the API to return data |
| `callback_url` | string | — | Webhook URL for async notifications |

## Gotchas

- `enhancement: true` (default) improves prompt quality but may alter your intent — set to `false` for literal prompts
- Start/end image URLs must be publicly accessible
- `loop: true` creates seamless looping video — good for backgrounds and social media
- Extend requires either `video_id` or `video_url` from a previously completed generation
- Video generation takes 1–5 minutes depending on complexity
- Both start and end images are optional — you can use just one for partial guidance

> **MCP:** `pip install mcp-luma` | Hosted: `https://luma.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
