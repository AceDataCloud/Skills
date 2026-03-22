---
name: ai-headshots
description: Generate professional AI headshots and portraits via AceDataCloud API. Use when creating professional photos, corporate portraits, ID-style photos, or styled headshots from a source image. Supports male and female templates with fast and relaxed modes.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable.
---

# AI Headshots — Professional Portrait Generation

Generate professional AI headshots through AceDataCloud's Headshots API.

## Authentication

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/headshots/generate \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/selfie.jpg", "template": "男士形象照"}'
```

## Templates

| Template | Description |
|----------|-------------|
| `男士形象照` | Male professional portrait |
| `女士形象照` | Female professional portrait |

Additional corporate/ID photo templates may be available.

## Quality Modes

| Mode | Speed | Cost | Best For |
|------|-------|------|----------|
| `fast` | Quick | Higher | Urgent needs |
| `relax` | Standard | Lower | Cost optimization |

## Workflows

### 1. Generate Professional Headshots

```json
POST /headshots/generate
{
  "image_url": "https://example.com/selfie.jpg",
  "template": "男士形象照",
  "mode": "fast"
}
```

### 2. Multiple Variations (Relaxed Mode)

```json
POST /headshots/generate
{
  "image_url": "https://example.com/casual-photo.jpg",
  "template": "女士形象照",
  "mode": "relax"
}
```

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `image_url` | Yes | string | Source photo URL (clear face visible) |
| `template` | Yes | string | Portrait template name |
| `mode` | No | `"fast"`, `"relax"` | Generation speed/cost trade-off |
| `callback_url` | No | string | Async callback URL |

## Task Polling

```json
POST /headshots/tasks
{"task_id": "your-task-id"}
```

## Response

```json
{
  "success": true,
  "task_id": "abc123",
  "data": [
    {
      "id": "headshot-1",
      "template": "男士形象照",
      "image_url": "https://cdn.example.com/headshot1.jpg"
    },
    {
      "id": "headshot-2",
      "template": "男士形象照",
      "image_url": "https://cdn.example.com/headshot2.jpg"
    }
  ]
}
```

## Gotchas

- Source photo should have a **clearly visible, front-facing face** for best results
- Returns **multiple variations** in a single request — choose the best one
- `fast` mode costs ~2x `relax` mode but generates much quicker
- Template names are in Chinese — use them as-is in the request
- The source image quality directly affects output quality — use high-resolution photos
- Async task-based processing — always poll for results
