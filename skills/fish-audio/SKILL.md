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
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, this is a demonstration of AI voice synthesis.","format":"mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id":"...","action":"retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech from text (Fish-compatible TTS API) |
| `GET /fish/model` | List/search available voice models |
| `GET /fish/model/{id}` | Fetch details for a specific voice model |
| `POST /fish/tasks` | Poll async task status (`retrieve` / `retrieve_batch`) |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "format": "mp3",
  "reference_id": "8d2c17a9b26d4d83888ea67a1ee565b2"
}
```

### 2. List/Search Models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode "title=narration" \
  --data-urlencode "language=en" \
  --data-urlencode "page_size=10"
```

### 3. Get Model by ID

```bash
curl https://api.acedata.cloud/fish/model/8d2c17a9b26d4d83888ea67a1ee565b2 \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 4. Poll Async Task

```json
POST /fish/tasks
{
  "id": "79d82713-2897-4eeb-9934-e7544d471aa7",
  "action": "retrieve"
}
```

Batch polling:

```json
POST /fish/tasks
{
  "ids": ["task-id-1", "task-id-2"],
  "action": "retrieve_batch"
}
```

## Parameters

### `/fish/tts` (request body)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | Yes | Text to synthesize |
| `format` | string | Yes | Output format: `mp3` or `pcm` |
| `reference_id` | string or string[] | No | Voice clone/model ID(s) |
| `references` | object[] | No | Inline reference samples (`audio` + `text`) |
| `sample_rate` | integer | No | Audio sample rate |
| `mp3_bitrate` | integer | No | MP3 bitrate (`64`, `128`, `192`) |
| `latency` | string | No | Latency mode (`normal`, `balanced`) |
| `chunk_length` | integer | No | Chunk length for generation |
| `temperature` | number | No | Sampling temperature |
| `top_p` | number | No | Top-p sampling |
| `normalize` | boolean | No | Normalize input text |
| `prosody` | object | No | Prosody controls (e.g. speed, volume) |
| `callback_url` | string | No | Webhook URL for async delivery |

### `/fish/tts` (headers)

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer <ACEDATACLOUD_API_TOKEN>` |
| `Content-Type` | Yes | `application/json` |
| `model` | No | TTS model: `s1` or `s2-pro` |

### `/fish/model` (query params)

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Page size (default `10`) |
| `page_number` | integer | Page number (default `1`) |
| `title` | string | Fuzzy title search |
| `tag` | string | Filter by a single tag |
| `self` | boolean | `true` to return only current account's models |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language code |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort field (e.g., `created_at`, `task_count`) |

### `/fish/tasks`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string | Conditionally | Single task ID (`action=retrieve`) |
| `ids` | string[] | Conditionally | Multiple task IDs (`action=retrieve_batch`) |
| `action` | string | Yes | `retrieve` or `retrieve_batch` |

## Gotchas

- `format` must be explicitly provided (`mp3` or `pcm`)
- Use the `model` **header** (not request body) for `s1` / `s2-pro`
- `GET /fish/model/{id}` is useful for retrieving a voice ID to pass as `reference_id`
- Returned audio URLs are signed links and can expire
