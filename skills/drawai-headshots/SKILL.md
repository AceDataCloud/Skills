---
name: drawai-headshots
description: Generate AI ID/headshot photos with DrawAI via AceDataCloud API. Use when creating business portraits, ID-style photos, wedding portraits, kindergarten photos, logo T-shirt mockups, or other template-driven headshots from uploaded person images.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# DrawAI Headshots

Generate template-based ID photos and portraits through AceDataCloud's DrawAI
headshots API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/headshots/generate \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "business_photo",
    "mode": "fast",
    "image_urls": ["https://example.com/person.jpg"],
    "callback_url": "https://api.acedata.cloud/health"
  }'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via
> `POST /headshots/tasks` with `{"action":"retrieve","id":"<task_id>"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /headshots/generate` | Generate photos from one or more input person images |
| `POST /headshots/tasks` | Retrieve one task or a batch of tasks |

## Parameters

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `template` | ✓ | `male_portrait`, `male_portrait2`, `kindergarten`, `logo_tshirt`, `wedding`, `business_photo`, `bob_suit`, `female_portrait` | Output template |
| `mode` | ✓ | `fast`, `relax` | Processing mode; `fast` is the default |
| `image_urls` | ✓ | array of URLs | Source person photos |
| `callback_url` | | URL | Webhook for async delivery |
| `async` | | boolean | Return a task response for polling |

## Task Queries

Retrieve one task:

```json
POST /headshots/tasks
{"action": "retrieve", "id": "<task_id>"}
```

Retrieve several tasks:

```json
POST /headshots/tasks
{"action": "retrieve_batch", "ids": ["<id1>", "<id2>"]}
```

## Gotchas

- Use clear, front-facing person photos for best results.
- Choose one of the documented template enum values; arbitrary template names
  are rejected.
- Pass `callback_url` or `async: true` for async handling, then poll
  `/headshots/tasks`.

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
