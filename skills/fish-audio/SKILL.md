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
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). For Fish, poll via `POST /fish/tasks` with `{"id": "...", "action": "retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate speech from text |
| `GET /fish/model` | Query Fish voice models (paginated/filterable) |
| `GET /fish/model/{id}` | Fetch details for a specific voice model |
| `POST /fish/tasks` | Retrieve async task result(s) |

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

### 2. Query Available Models

```http
GET /fish/model?page_size=10&page_number=1&language=en&tag=narration
```

### 3. Get Model Details by ID

```http
GET /fish/model/8d2c17a9b26d4d83888ea67a1ee565b2
```

### 4. Poll Async Task Result

Single task:

```json
POST /fish/tasks
{
  "id": "79d82713-2897-4eeb-9934-e7544d471aa7",
  "action": "retrieve"
}
```

Batch tasks:

```json
POST /fish/tasks
{
  "ids": ["task-id-1", "task-id-2"],
  "action": "retrieve_batch"
}
```

## Parameters

### `/fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to synthesize (required) |
| `format` | string | Output format (`mp3`, `wav`, `pcm`, `opus`) |
| `reference_id` | string | Existing Fish model ID for cloned voice synthesis |
| `references` | array | Inline reference samples (`audio` + `text`) |
| `sample_rate` | integer | Output sample rate |
| `mp3_bitrate` | integer | MP3 bitrate (`64`, `128`, `192`) |
| `opus_bitrate` | integer | Opus bitrate |
| `prosody` | object | Prosody overrides object (example: `{"speed": 1.2, "volume": 3}`; key/range constraints follow Fish upstream docs) |
| `latency` | string | `normal` or `balanced` |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p sampling |
| `repetition_penalty` | number | Penalize repeated tokens |
| `max_new_tokens` | integer | Max generated token count |
| `normalize` | boolean | Enable text normalization |
| `chunk_length` | integer | Upstream chunk length |
| `min_chunk_length` | integer | Minimum chunk length |
| `callback_url` | string | Webhook URL for async completion |

Headers:

| Header | Values | Description |
|--------|--------|-------------|
| `model` | `s1`, `s2-pro` | Optional model selector. Use `s1` for more stable long-text synthesis, or `s2-pro` for more expressive output. Default: `s2-pro` |
| `accept` | `application/json` | Optional response media type |

### `/fish/model` (GET)

| Query Parameter | Type | Description |
|-----------------|------|-------------|
| `page_size` | integer | Page size |
| `page_number` | integer | Page number (1-based) |
| `title` | string | Fuzzy title filter |
| `tag` | string | Tag filter |
| `self` | boolean | `true` to return only models from current account |
| `author_id` | string | Filter by model author ID |
| `language` | string | Language filter |
| `title_language` | string | Title language filter |
| `sort_by` | string | Upstream-supported sort field |

### `/fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID (use with `action: "retrieve"`) |
| `ids` | string[] | Multiple task IDs (use with `action: "retrieve_batch"`) |
| `action` | string | `retrieve` or `retrieve_batch` |

## Gotchas

- Use `POST /fish/tts` for synthesis. Legacy `POST /fish/audios` and `POST /fish/voices` are not part of the current Fish OpenAPI spec
- For stable behavior, always pass `format` explicitly (production integrations commonly use `mp3`)
- `GET /fish/model/{id}` returns richer model detail and often fresher signed sample URLs than list responses
- Async task polling uses `id` / `ids` plus `action`, not `task_id`

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
