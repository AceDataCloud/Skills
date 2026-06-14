---
name: fish-audio
description: Generate AI audio and synthesize voices with Fish Audio via AceDataCloud API. Use when creating text-to-speech audio, synthesizing voices, or generating audio content. Supports multiple voice models and TTS capabilities.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Text-to-Speech

Generate speech audio through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "model: s2-pro" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "..."}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech audio from text |
| `GET /fish/model` | List available voice/reference models |
| `GET /fish/model/{id}` | Fetch details for one voice/reference model |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "default"
}
```

### 2. List Voice Models

```bash
curl "https://api.acedata.cloud/fish/model?page_size=10&page_number=1" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 3. Get One Voice Model

```bash
curl "https://api.acedata.cloud/fish/model/<model_id>" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 4. Async TTS

```json
POST /fish/tts
{
  "text": "Welcome to our platform.",
  "reference_id": "<voice_model_id>",
  "callback_url": "https://api.acedata.cloud/health"
}
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize into speech |
| `reference_id` | string/array | Voice model ID; may be an array for multi-speaker variants |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, or `opus` |
| `sample_rate` | integer | Output sample rate such as `16000`, `22050`, or `44100` |
| `mp3_bitrate` | integer | MP3 bitrate when `format=mp3` (`64`, `128`, or `192`) |
| `opus_bitrate` | integer | Opus bitrate when `format=opus` |
| `latency` | string | Latency mode: `normal` or `balanced` |
| `chunk_length` | integer | Chunk length forwarded to the upstream synthesizer |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p nucleus sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Maximum new tokens to generate |
| `normalize` | boolean | Enable text normalization |
| `prosody` | object | Prosody overrides such as speed or volume |
| `references` | array | Inline reference samples |
| `callback_url` | string | Webhook URL for async delivery; returns `task_id` immediately |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Number of items per page (default: `10`) |
| `page_number` | integer | 1-based page number (default: `1`) |
| `title` | string | Partial title match filter |
| `tag` | string | Filter by one tag |
| `self` | boolean | When `true`, return only models owned by the caller |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language code such as `en` or `zh` |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Upstream sort field such as `created_at` or `task_count` |

### Headers

| Header | Endpoint | Description |
|--------|----------|-------------|
| `model` | `POST /fish/tts` | TTS model header: `s1` or `s2-pro` (default: `s2-pro`) |
| `accept` | all endpoints | Response format header; defaults to `application/json` |

## Gotchas

- `POST /fish/tts` is the current generation endpoint; this skill does not use the older `/fish/audios` or `/fish/voices` routes
- Async polling uses `POST /fish/tasks` with `{"id":"<task_id>"}` for single tasks or `{"ids":[...],"action":"retrieve_batch"}` for batches
- The `action` field on `/fish/tasks` defaults to `retrieve`
- Set the `model` header to `s1` or `s2-pro`; omit it to use `s2-pro`
- `callback_url` forces async mode and returns a `task_id` immediately
