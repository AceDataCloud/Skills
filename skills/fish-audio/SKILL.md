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
  -H "model: s2-pro" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with required fields `id` and `action` (example: `{"id":"...","action":"retrieve"}`).

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech audio from text |
| `GET /fish/model` | Query voice models (public or self-created) |
| `GET /fish/model/{id}` | Get one voice model by ID |
| `POST /fish/tasks` | Retrieve one or many async task results |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "format": "mp3"
}
```

### 2. Text-to-Speech with a Cloned Voice

```json
POST /fish/tts
{
  "text": "Welcome to our platform.",
  "reference_id": "8d2c17a9b26d4d83888ea67a1ee565b2",
  "format": "mp3"
}
```

### 3. Query / Inspect Models

```json
GET /fish/model?page_size=10&page_number=1&self=true
```

```json
GET /fish/model/8d2c17a9b26d4d83888ea67a1ee565b2
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize |
| `format` | string | Output format (`mp3`, `wav`, `pcm`, `opus`) |
| `reference_id` | string / string[] | Voice model ID(s) |
| `references` | array | Inline reference audio+text objects |
| `sample_rate` | integer | Audio sample rate |
| `mp3_bitrate` | integer | MP3 bitrate |
| `latency` | string | Latency mode |
| `callback_url` | string | Optional async callback URL |
| Header `model` | string | TTS model header (`s1` or `s2-pro`) |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Page size |
| `page_number` | integer | Page number |
| `title` | string | Fuzzy title filter |
| `tag` | string | Tag filter |
| `self` | boolean | Return only current account models |
| `author_id` | string | Filter by author ID |
| `language` | string | Language filter |
| `title_language` | string | Title language filter |
| `sort_by` | string | Sort field |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID for `action="retrieve"` |
| `ids` | array | Task IDs for `action="retrieve_batch"` |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- `POST /fish/tts` is the generation endpoint.
- Use `GET /fish/model` and `GET /fish/model/{id}` to discover and inspect cloneable voices.
- For async tasks, use `POST /fish/tasks` with `id`/`ids` plus `action` (`retrieve` / `retrieve_batch`), not `task_id`.
