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
  -H "accept: application/json" \
  -H "model: s2-pro" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id":"...","action":"retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech audio (Fish-compatible TTS) |
| `GET /fish/model` | List available voice models |
| `GET /fish/model/{id}` | Get a single voice model by ID |
| `POST /fish/tasks` | Retrieve async task status by `id` or `ids` |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3",
  "sample_rate": 44100
}
```

Use header `model: s1` or `model: s2-pro` (default: `s2-pro`).

### 2. Async TTS with Callback

```json
POST /fish/tts
{
  "text": "Generate this asynchronously.",
  "callback_url": "https://example.com/webhook/fish"
}
```

This returns `task_id` immediately. Retrieve task results:

```json
POST /fish/tasks
{
  "id": "<task_id>",
  "action": "retrieve"
}
```

### 3. Query Voice Models

```json
GET /fish/model?page_size=10&page_number=1&self=true
```

### 4. Get a Voice Model by ID

```json
GET /fish/model/{id}
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Voice model ID for single-speaker synthesis |
| `format` | string | Output audio format: `mp3`, `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Output sample rate (e.g. 16000, 22050, 44100) |
| `mp3_bitrate` | integer | MP3 bitrate (`64`, `128`, `192`) when `format=mp3` |
| `opus_bitrate` | integer | Opus bitrate when `format=opus` |
| `latency` | string | `normal` or `balanced` |
| `chunk_length` | integer | Chunk size control |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Maximum generated tokens |
| `normalize` | boolean | Enable text normalization |
| `prosody` | object | Prosody overrides (forwarded upstream) |
| `references` | array<object> | Inline reference samples (forwarded upstream) |
| `callback_url` | string | Async callback URL (returns `task_id` immediately) |

Header parameter:
- `model`: `s1` or `s2-pro` (defaults to `s2-pro`)

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page (default: 10) |
| `page_number` | integer | 1-based page number (default: 1) |
| `title` | string | Partial title search |
| `tag` | string | Filter by tag |
| `self` | boolean | Return only models from the current account |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language code |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort field accepted by upstream |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID for `action: "retrieve"` |
| `ids` | array<string> | Multiple task IDs for `action: "retrieve_batch"` |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- Fish-compatible TTS uses `POST /fish/tts`, not the legacy `/fish/audios` route
- TTS model selection is in the **HTTP header** `model` (`s1` or `s2-pro`)
- If `callback_url` is provided, the first response contains `task_id`; use `/fish/tasks` to retrieve status/results
- For task polling, use `id`/`ids` + `action` (`retrieve` or `retrieve_batch`)
