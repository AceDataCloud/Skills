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

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "..."}` or `{"ids": ["..."], "action": "retrieve_batch"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech from text |
| `GET /fish/model` | Browse available voice models |
| `GET /fish/model/{id}` | Fetch one voice model by ID |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "format": "mp3"
}
```

### 2. Text-to-Speech with a Specific Voice Model

Use a Fish voice model ID as `reference_id`.

```json
POST /fish/tts
{
  "text": "Welcome to our platform.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "wav"
}
```

### 3. Browse Voice Models

```json
GET /fish/model?page_number=1&page_size=10&language=en&title=Marcus
```

### 4. Fetch One Voice Model

```json
GET /fish/model/d7900c21663f485ab63ebdb7e5905036
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize into speech (required) |
| `reference_id` | string or array | Voice model ID for a single-speaker or multi-speaker request |
| `format` | string | Output format: `"mp3"`, `"wav"`, `"pcm"`, or `"opus"` |
| `model` | string (header) | TTS model header: `"s1"` or `"s2-pro"` |
| `sample_rate` | integer | Output sample rate such as `16000`, `22050`, or `44100` |
| `mp3_bitrate` | integer | MP3 bitrate: `64`, `128`, or `192` |
| `opus_bitrate` | integer | Opus bitrate when `format` is `"opus"` |
| `latency` | string | `"normal"` or `"balanced"` |
| `callback_url` | string | Optional webhook URL for async delivery |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Number of voice models to return per page |
| `page_number` | integer | Page number to fetch |
| `title` | string | Filter by voice title |
| `tag` | string | Filter by voice tag |
| `self` | boolean | Limit results to your own voice models |
| `author_id` | string | Filter by voice author |
| `language` | string | Filter by voice language |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort key passed through to the upstream API |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | array of strings | Multiple task IDs for batch polling |
| `action` | string | `"retrieve"` (default) or `"retrieve_batch"` |

## Gotchas

- `POST /fish/tts` requires `text`; the voice selector is `reference_id`, not `voice_id`
- Choose the synthesis model with the `model` request header, not a JSON body field
- Async callbacks may return a `task_id`, but polling still uses `POST /fish/tasks` with `id` / `ids`
- Use `GET /fish/model` to browse public or owned voices, then `GET /fish/model/{id}` for one record
- Pricing is based on generated audio usage and the selected Fish model
