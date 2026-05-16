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

Generate text-to-speech audio through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). For async generation, pass `callback_url`, then poll `POST /fish/tasks` with `{"id": "<task_id>"}`.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fish/tts` | POST | Generate speech from text |
| `/fish/model` | GET | List available Fish voice/reference models |
| `/fish/model/{id}` | GET | Fetch one Fish model by ID |
| `/fish/tasks` | POST | Poll one or more async tasks |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
{
  "text": "The quick brown fox jumps over the lazy dog.",
  "reference_id": "default",
  "format": "mp3"
}
```

### 2. Choose the TTS model with a header

Use the `model` request header:

- `s1`
- `s2-pro`

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s1" \
  -d '{"text": "Lower-latency speech output", "format": "opus"}'
```

### 3. List available voice models

```bash
curl "https://api.acedata.cloud/fish/model?page_size=10&page_number=1" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

Common query filters: `title`, `tag`, `self`, `author_id`, `language`, `title_language`, `sort_by`.

### 4. Get a single voice model

```bash
curl "https://api.acedata.cloud/fish/model/<id>" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 5. Poll async tasks

```json
POST /fish/tasks
{
  "id": "task-id-from-callback-response"
}
```

For batch polling:

```json
POST /fish/tasks
{
  "action": "retrieve_batch",
  "ids": ["task-1", "task-2"]
}
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Voice model ID to use |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, or `opus` |
| `sample_rate` | integer | Output sampling rate |
| `mp3_bitrate` | integer | MP3 bitrate: `64`, `128`, or `192` |
| `opus_bitrate` | integer | Opus bitrate |
| `latency` | string | Latency mode: `normal` or `balanced` |
| `chunk_length` | integer | Upstream chunk length |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p nucleus sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Maximum number of generated tokens |
| `normalize` | boolean | Enable text normalization |
| `prosody` | object | Prosody overrides such as speed or volume |
| `references` | array | Inline reference samples |
| `callback_url` | string | Webhook URL for async delivery |

### `GET /fish/model`

| Query parameter | Type | Description |
|-----------------|------|-------------|
| `page_size` | integer | Page size (default: 10) |
| `page_number` | integer | 1-based page number (default: 1) |
| `title` | string | Partial title match |
| `tag` | string | Filter by one tag |
| `self` | boolean | Only return models owned by the caller |
| `author_id` | string | Filter by author |
| `language` | string | Language code filter |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Upstream sort field |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Retrieve one task |
| `ids` | array | Retrieve multiple tasks |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- The TTS model is selected with the **`model` HTTP header**, not a JSON body field
- Current OpenAPI endpoints are `/fish/tts`, `/fish/model`, `/fish/model/{id}`, and `/fish/tasks`
- Async responses may return a `task_id`, but task polling uses `{"id": "<task_id>"}` on `/fish/tasks`
- Use `GET /fish/model` to discover valid `reference_id` values before synthesis
- `format` supports `mp3`, `wav`, `pcm`, and `opus`

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
