---
name: fish-audio
description: Generate speech with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, browsing available voice models, and polling async Fish tasks.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Text-to-Speech

Generate speech and inspect available Fish models through AceDataCloud's Fish API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s1" \
  -d '{"text": "Hello, this is a Fish Audio demo.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "..."}`.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fish/tts` | POST | Generate speech from text |
| `/fish/model` | GET | List available Fish voice models |
| `/fish/model/{id}` | GET | Get details for a single Fish model |
| `/fish/tasks` | POST | Retrieve one or more async task results |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "format": "mp3",
  "reference_id": "optional-model-or-voice-id"
}
```

Supported `model` header values:
- `s1`
- `s2-pro`

### 2. TTS with advanced controls

```json
POST /fish/tts
{
  "text": "Read this with a calm and friendly tone.",
  "format": "opus",
  "sample_rate": 44100,
  "latency": "balanced",
  "temperature": 0.7,
  "top_p": 0.9,
  "repetition_penalty": 1.1,
  "normalize": true,
  "callback_url": "https://api.acedata.cloud/health"
}
```

### 3. List available models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode "page_size=20" \
  --data-urlencode "page_number=1" \
  --data-urlencode "language=en"
```

### 4. Get one model by ID

```bash
curl https://api.acedata.cloud/fish/model/model_123 \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize |
| `reference_id` | string | Optional model / reference voice ID |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, or `opus` |
| `sample_rate` | integer | Output sample rate |
| `mp3_bitrate` | integer | MP3 bitrate override |
| `opus_bitrate` | integer | Opus bitrate override |
| `latency` | string | Latency / quality tradeoff |
| `chunk_length` | integer | Preferred stream chunk size |
| `min_chunk_length` | integer | Minimum chunk size |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Nucleus sampling |
| `repetition_penalty` | number | Penalize repeated tokens |
| `max_new_tokens` | integer | Maximum generated tokens |
| `normalize` | boolean | Normalize output loudness |
| `prosody` | object | Prosody controls |
| `references` | array | Extra reference voices / clips |
| `callback_url` | string | Optional webhook to force async processing |

### `GET /fish/model`

Supported query parameters:
- `page_size`
- `page_number`
- `title`
- `tag`
- `self`
- `author_id`
- `language`
- `title_language`
- `sort_by`

### `POST /fish/tasks`

```json
POST /fish/tasks
{
  "id": "task_id_here"
}
```

For batch polling:

```json
POST /fish/tasks
{
  "action": "retrieve_batch",
  "ids": ["task_1", "task_2"]
}
```

## Gotchas

- The generation endpoint is `POST /fish/tts`, not the older `/fish/audios` path
- Fish model selection is sent in the `model` HTTP header (`s1` or `s2-pro`)
- `POST /fish/tasks` uses `id` / `ids`; `action` defaults to `retrieve`
- `GET /fish/model` and `GET /fish/model/{id}` are read-only discovery endpoints for available Fish models
- Use `callback_url` when you want a task ID immediately instead of waiting on a long-running request
