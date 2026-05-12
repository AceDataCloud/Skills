---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, or generating audio content. Supports multiple voice models and TTS capabilities.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Voice & Audio Synthesis

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "model: s2-pro" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech audio from text |
| `GET /fish/model` | List available voice models (supports filters/pagination) |
| `GET /fish/model/{id}` | Get details for a single model |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3"
}
```

Set the `model` request header to `s1` or `s2-pro` (`s2-pro` default).

### 2. List Voice Models

```json
GET /fish/model?page_size=20&page_number=1&language=en
```

### 3. Get a Single Model

```json
GET /fish/model/{id}
```

### 4. Async Polling

When `callback_url` is provided, create requests return `task_id` quickly. Poll with `id`:

```json
POST /fish/tasks
{"id": "<task_id from /fish/tts>"}
```

Use `ids` with `action: "retrieve_batch"` for batch polling.

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Voice/model ID for single-speaker synthesis |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, `opus` |
| `callback_url` | string | Optional webhook for async delivery |
| `model` (header) | string | TTS model header: `s1` or `s2-pro` |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | string[] | Batch task IDs for `retrieve_batch` |
| `action` | string | `retrieve` (default) or `retrieve_batch` |

## Gotchas

- `POST /fish/tts` returns `audio_url` when completed
- `text` is required and must be non-empty
- The TTS model is passed by **header** (`model`), not request body
- For async jobs, the create response returns `task_id`, but polling must use `id` in `/fish/tasks`
