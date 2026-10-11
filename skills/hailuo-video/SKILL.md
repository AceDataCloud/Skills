---
name: hailuo-video
description: Generate AI videos with Hailuo (MiniMax) via AceDataCloud API. Use when creating videos from text descriptions or animating images into video. Supports text-to-video and image-to-video with director mode for precise control.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (get an API key at https://platform.acedata.cloud/console/applications).
---

# Hailuo Video Generation

Generate AI videos through AceDataCloud's Hailuo (MiniMax) API.

## First-time setup

1. Install the official Skill with `clawhub install @acedatacloud/hailuo`. Check that the ClawHub publisher is **@acedatacloud**.
2. Sign in at [AceDataCloud → Applications](https://platform.acedata.cloud/console/applications), open **General application**, and check Hailuo access, balance, and current pricing. Copy its API key, or select **Manage Keys → Create** for a separate key. Copy the key value without `Bearer `; a `platform-...` management token is not a service API key.
3. If you enable **Allowed APIs** restrictions, include `/hailuo/videos` and `/hailuo/tasks`. Advanced workflows below may call additional routes.
4. On the OpenClaw Gateway host, put `ACEDATACLOUD_API_TOKEN=your_api_key_here` in `~/.openclaw/.env`, then restart the Gateway and start a new session. For a direct terminal test, run `export ACEDATACLOUD_API_TOKEN="your_api_key_here"` in that shell. Never put the key in a prompt or commit an `.env` file.
5. Run the **Quick Start** below. If this workflow returns a task ID, query that same task until it finishes; do not submit the same billable request again just to check progress.

[Illustrated key setup, first run, and troubleshooting](https://github.com/AceDataCloud/Skills#first-run-with-clawhub-and-openclaw) · [Token details](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md)

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/hailuo/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "a dolphin jumping through ocean waves at golden hour", "model": "minimax-t2v"}'
```

> **Async:** See [async task polling](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md). Poll via `POST /hailuo/tasks` with `{"id": "..."}`.
## Models

| Model | Type | Best For |
|-------|------|----------|
| `minimax-t2v` | Text-to-Video | Creating video from text description |
| `minimax-i2v` | Image-to-Video | Animating a still image |
| `minimax-i2v-director` | Image-to-Video (Director) | Precise control over animation from image |

## Workflows

### 1. Text-to-Video

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "a time-lapse of flowers blooming in a meadow",
  "model": "minimax-t2v"
}
```

### 2. Image-to-Video

Animate a still image into a video clip.

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "gentle wind blows through the scene",
  "model": "minimax-i2v",
  "first_image_url": "https://example.com/landscape.jpg"
}
```

### 3. Image-to-Video (Director Mode)

More precise control over the animation.

```json
POST /hailuo/videos
{
  "action": "generate",
  "prompt": "camera slowly zooms in while leaves fall gently",
  "model": "minimax-i2v-director",
  "first_image_url": "https://example.com/scene.jpg"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `action` | Yes | `"generate"` | Action type |
| `prompt` | Yes | string | Video description |
| `model` | Yes | `"minimax-t2v"`, `"minimax-i2v"`, `"minimax-i2v-director"` | Model |
| `first_image_url` | For i2v | string | Source image URL (required for image-to-video) |
| `callback_url` | No | string | Async callback URL |

## Gotchas

- `first_image_url` is **required** for `minimax-i2v` and `minimax-i2v-director` models
- Director mode (`minimax-i2v-director`) provides finer camera/motion control than standard i2v
- The `action` field currently only supports `"generate"` — no extend or edit
- Flat pricing per generation regardless of model
