---
name: sora-video
description: Generate AI videos with OpenAI Sora via AceDataCloud API. Use when creating videos from text prompts, generating videos from reference images, or using character references from existing videos. Supports text-to-video, image-to-video, and character-driven generation with multiple models and resolutions.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-sora for tool-use.
---

# Sora Video Generation

Generate AI videos through AceDataCloud's OpenAI Sora API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/sora/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a golden retriever running on a beach at sunset", "model": "sora-2", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /sora/tasks` with `{"id": "..."}`.

## Models

| Model | Duration | Quality | Best For |
|-------|----------|---------|----------|
| `sora-2` | 10–15s | Standard | Most tasks (default) |
| `sora-2-pro` | 10–25s | Higher | Premium quality, longer videos |

## Workflows

### 1. Text-to-Video

```json
POST /sora/videos
{
  "prompt": "a busy Tokyo street at night with neon signs reflecting in rain puddles",
  "model": "sora-2",
  "size": "small",
  "duration": 10,
  "orientation": "landscape"
}
```

### 2. Image-to-Video

Use reference images to guide generation.

```json
POST /sora/videos
{
  "prompt": "the scene gradually comes alive with gentle motion",
  "image_urls": ["https://example.com/scene.jpg"],
  "model": "sora-2",
  "orientation": "landscape"
}
```

### 3. Character-Driven Video

Extract a character from an existing video and use them in a new scene.

```json
POST /sora/videos
{
  "prompt": "the character walks through a futuristic city",
  "character_url": "https://example.com/source-video.mp4",
  "character_start": 2.0,
  "character_end": 5.0,
  "model": "sora-2-pro"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"sora-2"`, `"sora-2-pro"` | Model to use (required) |
| `size` | `"small"`, `"large"`, `"720x1280"`, `"1280x720"`, `"1024x1792"`, `"1792x1024"` | Video resolution — named sizes for version `1.0`, pixel sizes for version `2.0` |
| `duration` | `4`, `8`, `10`, `12`, `15`, `25` | Duration in seconds — version `1.0` supports `10/15` (`25` with `sora-2-pro`), version `2.0` supports `4/8/12` |
| `orientation` | `"landscape"` (16:9), `"portrait"` (9:16) | Video orientation; only applies to version `1.0` |
| `version` | `"1.0"`, `"2.0"` | API version — use `1.0` for orientation/character references and `2.0` for short clips with pixel-based sizes |

## Version Guide

- **Version `1.0`** supports `orientation`, character-driven video (`character_url`, `character_start`, `character_end`), and named sizes (`"small"`, `"large"`).
- **Version `2.0`** supports shorter clips (`4`, `8`, `12` seconds), pixel-based sizes (`"720x1280"`, `"1280x720"`, `"1024x1792"`, `"1792x1024"`), and image-guided generation using the first item in `image_urls`.

## Gotchas

- Duration of **25 seconds** is only available with `sora-2-pro` model
- `size: "large"` is only for version `1.0` and only supported by `sora-2-pro`
- Character-driven generation requires `character_start` and `character_end` timestamps (in seconds) from the source video
- `orientation` sets the aspect ratio — use `"portrait"` for mobile-first content, but only on version `1.0`
- Task states use `"succeeded"` (not "completed") — check for this value when polling

> **MCP:** `pip install mcp-sora` | Hosted: `https://sora.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
