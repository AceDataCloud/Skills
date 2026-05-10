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
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "...", "action": "retrieve"}` (single task) or `{"ids": ["..."], "action": "retrieve_batch"}` (batch).

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish-compatible text-to-speech generation |
| `GET /fish/model` | List voice models with filters |
| `GET /fish/model/{id}` | Get one voice model by ID |
| `POST /fish/tasks` | Poll task status (`retrieve` / `retrieve_batch`) |

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

### 2. Async Text-to-Speech with Callback

```json
POST /fish/tts
{
  "text": "Welcome to our platform.",
  "callback_url": "https://example.com/fish-callback"
}
```

Immediate response:

```json
{
  "task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "started_at": "2025-05-09T12:34:56.789Z"
}
```

Then poll with `POST /fish/tasks`:

```json
{
  "id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "action": "retrieve"
}
```

### 3. List Voice Models

```http
GET /fish/model?page_size=10&page_number=1&self=true&language=en
```

### 4. Get One Voice Model

```http
GET /fish/model/d7900c21663f485ab63ebdb7e5905036
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Voice model ID |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Output sample rate |
| `mp3_bitrate` | integer | MP3 bitrate: `64`, `128`, `192` |
| `opus_bitrate` | integer | Opus bitrate |
| `latency` | string | `normal` or `balanced` |
| `chunk_length` | integer | Chunk length control |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Max generated tokens |
| `normalize` | boolean | Enable text normalization |
| `prosody` | object | Prosody overrides |
| `references` | array<object> | Inline reference samples |
| `callback_url` | string | Async callback URL (returns `task_id` immediately) |
| `model` (header) | string | TTS model header: `s1` or `s2-pro` (default `s2-pro`) |

### `GET /fish/model` (query)

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page (default: 10) |
| `page_number` | integer | 1-based page number (default: 1) |
| `title` | string | Partial title filter |
| `tag` | string | Tag filter |
| `self` | boolean | Only models owned by current account |
| `author_id` | string | Author filter |
| `language` | string | Language filter |
| `title_language` | string | Title language filter |
| `sort_by` | string | Upstream sort field (e.g. `created_at`, `task_count`) |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID |
| `ids` | array<string> | Multiple task IDs |
| `action` | string | `retrieve` (single) or `retrieve_batch` (multiple) |

## Gotchas

- `POST /fish/tts` is compatible with Fish Audio's TTS request/response format; use the `model` HTTP header (`s1` or `s2-pro`) instead of a JSON `model` field
- If `latency` is omitted, platform defaults it to `normal` for upstream compatibility
- For async mode, include `callback_url`; the immediate response returns `task_id`, and final result contains `audio_url`
- Polling uses `POST /fish/tasks` with `action: "retrieve"` or `"retrieve_batch"` (not `task_id`)
- `GET /fish/model/{id}` returns model details; use `_id` values from model list responses
