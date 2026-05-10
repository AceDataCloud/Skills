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
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

> **Async:** For legacy task polling, use `POST /fish/tasks` with `{"id": "<task_id>", "action": "retrieve"}`. `callback_url` on `POST /fish/tts`, `POST /fish/audios`, or `POST /fish/voices` returns a task ID immediately and completes asynchronously.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Fish-compatible text-to-speech endpoint |
| `POST /fish/model` | Create a cloned voice model from sample URLs |
| `GET /fish/model` | List voice models visible to the current account |
| `POST /fish/audios` | Legacy AceDataCloud TTS endpoint |
| `POST /fish/voices` | Legacy voice cloning endpoint |
| `POST /fish/tasks` | Poll legacy async task status |

## Workflows

### 1. Fish-compatible Text-to-Speech

```json
POST /fish/tts
Headers: { "model": "s2-pro" }
{
  "text": "The quick brown fox jumps over the lazy dog."
}
```

### 2. Async Text-to-Speech Callback

```json
POST /fish/tts
Headers: { "model": "s2-pro" }
{
  "text": "Welcome to our platform.",
  "callback_url": "https://example.com/webhook/fish"
}
```

Immediate response:

```json
{
  "task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5",
  "started_at": "2025-05-09T12:34:56.789Z"
}
```

### 3. Create a Voice Model

```json
POST /fish/model
{
  "title": "My cloned voice",
  "description": "Cloned from a podcast recording",
  "voices": [
    "https://example.com/sample-voice.mp3"
  ],
  "cover_image": "https://example.com/cover.png",
  "visibility": "private"
}
```

### 4. List Voice Models

```text
GET /fish/model?page_size=10&page_number=1&self=true
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `model` (header) | `"s1"` / `"s2-pro"` | Fish TTS model selector; defaults to `s2-pro` |
| `text` | string | Text to synthesize |
| `reference_id` | string | Cloned voice model ID from `POST /fish/model` |
| `references` | array | Fish-compatible reference voices |
| `format` | string | Output audio format |
| `sample_rate` | number | Output sample rate |
| `mp3_bitrate` | number | MP3 bitrate when using MP3 output |
| `chunk_length` | number | Chunk size for long-form synthesis |
| `temperature` | number | Sampling temperature |
| `top_p` | number | Top-p sampling value |
| `callback_url` | string | Platform extension for async callback delivery |

### `POST /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | string | Display title for the cloned voice model |
| `voices` | array of strings | Required audio sample URLs |
| `description` | string | Optional model description |
| `cover_image` | string | Cover image URL |
| `visibility` | `"private"` / `"public"` | Voice model visibility |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | number | Items per page, default 10 |
| `page_number` | number | Page index, starting at 1 |
| `title` | string | Fuzzy search by title |
| `tag` | string | Filter by tag |
| `self` | boolean | Return only models created by the current account |
| `author_id` | string | Filter by creator |
| `language` | string | Filter by voice language |
| `title_language` | string | Filter by title language |

### Legacy endpoints

| Endpoint | Key parameters |
|----------|----------------|
| `POST /fish/audios` | `action`, `prompt`, `voice_id`, `model`, `callback_url` |
| `POST /fish/voices` | `voice_url`, `title`, `description`, `image_url`, `callback_url` |
| `POST /fish/tasks` | `id` or `ids`, plus `action: "retrieve"` / `"retrieve_batch"` |

## Gotchas

- `POST /fish/tts` is Fish-compatible, but the TTS model is selected via the HTTP `model` header, not a JSON body field
- Passing `callback_url` to `POST /fish/tts` returns `{task_id, started_at}` immediately and sends the final `{audio_url, ...}` payload to your webhook later
- `POST /fish/model` currently supports JSON requests with sample URLs in `voices`; multipart/msgpack sample uploads are not implemented
- `POST /fish/model` and `GET /fish/model` forward the upstream Fish response shape directly instead of wrapping it in the platform success envelope
- Legacy `/fish/audios`, `/fish/voices`, and `/fish/tasks` endpoints remain available for existing integrations
