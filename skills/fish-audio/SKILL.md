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
  -H "model: s1" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id":"your-task-id","action":"retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech audio from text |
| `GET /fish/model` | List available voice models |
| `GET /fish/model/{id}` | Get details for one voice model |
| `POST /fish/tasks` | Retrieve async task result(s) |

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

Response:

```json
{
  "audio_url": "https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"
}
```

### 2. List Voice Models

```bash
curl -X GET "https://api.acedata.cloud/fish/model?page_size=10&page_number=1" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 3. Get One Voice Model

```bash
curl -X GET "https://api.acedata.cloud/fish/model/d7900c21663f485ab63ebdb7e5905036" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | **Required.** Text to synthesize into speech |
| `reference_id` | string | Optional voice model ID |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Output sample rate |
| `mp3_bitrate` | integer | MP3 bitrate: `64`, `128`, `192` |
| `opus_bitrate` | integer | Opus bitrate |
| `latency` | string | `normal` or `balanced` |
| `chunk_length` | integer | Chunk length |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Max generated tokens |
| `normalize` | boolean | Enable text normalization |
| `prosody` | object | Prosody overrides |
| `references` | array | Inline reference samples |
| `callback_url` | string | Async webhook URL (returns `task_id` immediately) |
| `model` (header) | string | Optional upstream model: `s1`, `s2-pro` |

### `GET /fish/model` query params

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Page size (default `10`) |
| `page_number` | integer | Page number (default `1`) |
| `title` | string | Filter by title |
| `tag` | string | Filter by tag |
| `self` | boolean | Show caller-owned models |
| `author_id` | string | Filter by author |
| `language` | string | Filter by language |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sorting option |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID (for `action=retrieve`) |
| `ids` | array | Multiple task IDs (for `action=retrieve_batch`) |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- Pricing is based on **byte count** of the generated audio
- Use `POST /fish/tts` for generation and `GET /fish/model` endpoints for model discovery
- If you set `callback_url`, poll task status with `POST /fish/tasks` using `id`/`ids` + `action`
- `POST /fish/tasks` uses `id` / `ids` (not `task_id`)
