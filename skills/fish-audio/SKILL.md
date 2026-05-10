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

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API. The API is fully compatible with Fish Audio's official OpenAPI, so existing Fish Audio SDK code can be migrated by replacing the base URL and auth token.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** Pass `callback_url` in the request body. The API returns `{"task_id": "..."}` immediately; the final result is POSTed to your callback URL when done. Poll via `POST /fish/tasks` with `{"id": "<task_id>", "action": "retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish Audio-compatible text-to-speech synthesis |
| `GET /fish/model` | List/search available voice models |
| `GET /fish/model/{id}` | Get a specific voice model by ID |
| `POST /fish/tasks` | Poll async task status |

## Workflows

### 1. Text-to-Speech

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "The quick brown fox jumps over the lazy dog."
}
```

Response:
```json
{"audio_url": "https://..."}
```

### 2. Text-to-Speech with a Cloned Voice

Use a voice model's `_id` as the `reference_id`:

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "Welcome to our platform.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3",
  "sample_rate": 44100
}
```

### 3. Browse Available Voice Models

```bash
GET /fish/model?page_size=10&page_number=1&self=true
```

Returns paginated list with `{total, items}`. Each item's `_id` can be used as `reference_id` in TTS requests.

### 4. Async TTS with Callback

```json
POST /fish/tts
{
  "text": "This long text will be synthesized asynchronously.",
  "callback_url": "https://your-server.com/webhook"
}
```

Immediate response:
```json
{"task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5", "started_at": "..."}
```

Poll status:
```json
POST /fish/tasks
{"id": "<task_id>", "action": "retrieve"}
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string* | Text to synthesize (required) |
| `reference_id` | string | Voice model ID to use for synthesis |
| `format` | string | Output format: `mp3`, `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Output sample rate (e.g. 16000, 22050, 44100) |
| `mp3_bitrate` | integer | MP3 bit rate: `64`, `128`, `192` |
| `opus_bitrate` | integer | Opus bit rate when `format=opus` |
| `latency` | string | `normal` or `balanced` (defaults to `normal`) |
| `chunk_length` | integer | Chunk length for the upstream synthesiser |
| `temperature` | number | Sampling temperature (0.0–1.0) |
| `top_p` | number | Top-p nucleus sampling parameter |
| `repetition_penalty` | number | Repetition penalty during generation |
| `max_new_tokens` | integer | Maximum new tokens to generate |
| `normalize` | boolean | Apply text normalization |
| `prosody` | object | Prosody overrides (e.g. speed, volume) |
| `references` | array | Inline reference samples forwarded to upstream |
| `callback_url` | string | Webhook URL for async delivery |

**Request header:** `model: s1` or `model: s2-pro` (default: `s2-pro`)

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page (default: 10) |
| `page_number` | integer | 1-based page number (default: 1) |
| `title` | string | Filter by partial title match |
| `tag` | string | Filter by tag |
| `self` | boolean | When `true`, only return models owned by caller |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language code (e.g. `en`, `zh`) |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort field (e.g. `created_at`, `task_count`) |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | array | Multiple task IDs for batch retrieval |
| `action` | string | `retrieve` (single) or `retrieve_batch` (multiple) |

## Gotchas

- The **model is set via HTTP header** `model: s1` or `model: s2-pro`, not in the request body
- `callback_url` is a platform extension — Fish Audio's official API does not support it
- Use a voice model's `_id` field (from `GET /fish/model`) as the `reference_id` in TTS requests
- Text-to-speech supports multiple languages automatically
- Pricing is based on the byte count of the generated audio
- When `latency` is omitted, the platform automatically sets `latency=normal` to match Fish Audio's default behavior
