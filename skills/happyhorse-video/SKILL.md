---
name: happyhorse-video
description: Generate AI videos with HappyHorse via AceDataCloud API. Use when creating text-to-video, animating images, using reference images, or editing existing videos with HappyHorse models.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-happyhorse for tool-use.
---

# HappyHorse Video Generation

Generate AI videos through AceDataCloud's HappyHorse API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/happyhorse/videos \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"generate","model":"happyhorse-1.1-t2v","prompt":"a cinematic drone shot over snowy mountains at sunrise"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /happyhorse/tasks` with `{"id":"..."}`.

## Models

| Model | Type |
|-------|------|
| `happyhorse-1.0-t2v` | Text-to-video |
| `happyhorse-1.1-t2v` | Text-to-video |
| `happyhorse-1.0-i2v` | Image-to-video |
| `happyhorse-1.1-i2v` | Image-to-video |
| `happyhorse-1.0-r2v` | Reference-image to video |
| `happyhorse-1.1-r2v` | Reference-image to video |
| `happyhorse-1.0-video-edit` | Video editing |

## Actions

- `generate`: text-to-video
- `image_to_video`: animate a single input image (`image_url`)
- `reference_to_video`: use multiple references (`image_urls`)
- `video_edit`: edit an existing clip (`video_url`)

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"generate"`, `"image_to_video"`, `"reference_to_video"`, `"video_edit"` | Generation mode |
| `model` | see Models table | HappyHorse model |
| `prompt` | string | Prompt text |
| `image_url` | string | Source image URL for `image_to_video` |
| `image_urls` | array of strings | Reference images for `reference_to_video` |
| `video_url` | string | Input video URL for `video_edit` |
| `resolution` | `"720P"`, `"1080P"` | Output resolution |
| `ratio` | `"16:9"`, `"9:16"`, `"1:1"`, `"4:3"`, `"3:4"` | Aspect ratio |
| `duration` | integer | Duration in seconds |
| `watermark` | boolean | Add watermark |
| `audio_setting` | `"auto"`, `"origin"` | Audio mode |
| `seed` | integer | Random seed |
| `callback_url` | string | Async webhook URL |
| `async` | boolean | Return immediately with task id |

## Task Polling

```json
POST /happyhorse/tasks
{
  "id": "<task_id>"
}
```

Batch polling:

```json
POST /happyhorse/tasks
{
  "ids": ["<task_id_1>", "<task_id_2>"],
  "action": "retrieve_batch"
}
```

## Gotchas

- `image_url`, `image_urls`, and `video_url` are action-specific; only send the fields required by your selected `action`
- `action` and `model` combinations should match (`*-t2v` for text, `*-i2v` for image, `*-r2v` for reference, `*-video-edit` for editing)
- Async responses include `task_id`; poll `/happyhorse/tasks` until `response.data[].state` is terminal (for example `succeeded` / `failed`)

> **MCP:** `pip install mcp-happyhorse` | Hosted: `https://happyhorse.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
