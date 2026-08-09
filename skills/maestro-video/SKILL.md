---
name: maestro-video
description: "Produce complete AI videos with Maestro via AceDataCloud API from one prompt (or reference media), including remix/edit/extend workflows and async task polling."
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-maestro for tool-use.
---

# Maestro End-to-End Video Production

Use Maestro when the user wants a **finished video** (script, visuals, voiceover, edit, captions), not just a single generated shot.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/maestro/videos \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a 30-second beginner-friendly video explaining vector databases.",
    "aspect": "16:9",
    "duration": 30,
    "quality": "standard",
    "scenario": "narrated",
    "langs": ["en"]
  }'
```

The API returns `task_id`; poll it with `POST /maestro/tasks`:

```bash
curl -X POST https://api.acedata.cloud/maestro/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"id":"<task_id>","action":"retrieve"}'
```

## Create Video Parameters (`POST /maestro/videos`)

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `prompt` | string | required | Natural-language production brief |
| `action` | string | `generate` | `generate`, `remix`, `edit`, `extend` |
| `ref_task_id` | string | - | Required when `action` is `remix` / `edit` / `extend` |
| `file_urls` | string[] | - | Optional reference image/video/audio URLs |
| `langs` | string[] | `["zh-cn"]` | Output language list |
| `aspect` | string | `9:16` | `9:16`, `16:9`, `1:1` |
| `duration` | integer | `30` | `1` to `600` seconds |
| `quality` | string | `standard` | `draft`, `standard`, `premium` |
| `scenario` | string | `auto` | `auto`, `narrated`, `drama`, `avatar`, `motion`, `slideshow` |
| `style` | string | `auto` | Preset style or freeform hint |
| `voice` | string | `auto` | Preset voice or raw 32-char Fish `reference_id` |
| `callback_url` | string | - | Optional terminal-state webhook |

## Task Response (`POST /maestro/tasks`)

Request body supports:

- `id` (required)
- `action` (optional, currently `retrieve`)

Status values: `pending`, `scripting`, `generating`, `rendering`, `captioning`, `qc`, `succeeded`, `failed`.

Task payload includes top-level timing fields: `created_at`, `started_at`, `finished_at`, `elapsed`.

On success, `response.data.variants` contains localized outputs (`lang`, `output_url`, `captions_url`, `cover_url`, `qc_score`, `duration` when available).

## Gotchas

- This API is asynchronous; always persist and poll `task_id`.
- `remix`, `edit`, and `extend` require `ref_task_id`.
- `file_urls` must be public URLs (not local paths).
- Do not assume history/listing support on `/maestro/tasks`; the documented action is `retrieve` for a specific `id`.

> **MCP:** `pip install mcp-maestro` | Hosted: `https://maestro.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
