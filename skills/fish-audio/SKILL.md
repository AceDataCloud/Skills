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

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API. This API is fully compatible with the [Fish Audio Official OpenAPI](https://docs.fish.audio).

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis."}'
```

Response:

```json
{"audio_url": "https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"}
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Include `callback_url` in the request body for async delivery; poll via `POST /fish/tasks` with `{"id": "...", "action": "retrieve"}`.

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/fish/tts` | POST | Text-to-speech synthesis (Fish Audio-compatible) |
| `/fish/model` | GET | List/query available voice models |
| `/fish/model/{id}` | GET | Get a specific voice model by ID |
| `/fish/tasks` | POST | Poll async task status |

## Workflows

### 1. Basic Text-to-Speech

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "The quick brown fox jumps over the lazy dog."
}
```

### 2. TTS with a Cloned Voice

Obtain a `reference_id` from `GET /fish/model` or use a known voice model ID.

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

### 3. Async TTS with Callback

For long texts, use `callback_url` to avoid long-lived connections:

```json
POST /fish/tts
Headers: model: s2-pro
{
  "text": "A long text passage...",
  "callback_url": "https://your-webhook.example.com/hook"
}
```

Immediate response:

```json
{"task_id": "2725a2d3-f87e-4905-9c53-9988d5a7b2f5", "started_at": "2025-05-09T12:34:56.789Z"}
```

### 4. List Voice Models

```bash
curl "https://api.acedata.cloud/fish/model?page_size=20" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

### 5. Get a Voice Model by ID

```bash
curl "https://api.acedata.cloud/fish/model/d7900c21663f485ab63ebdb7e5905036" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | **Required.** Text to synthesize |
| `reference_id` | string | Voice model ID for voice cloning (single or array for multi-speaker) |
| `format` | string | Output format: `mp3` (default), `wav`, `pcm`, `opus` |
| `sample_rate` | integer | Sampling rate (e.g. 16000, 22050, 44100) |
| `mp3_bitrate` | integer | MP3 bit rate: `64`, `128`, `192` |
| `opus_bitrate` | integer | Opus bit rate |
| `latency` | string | Latency mode: `normal` (default) or `balanced` |
| `chunk_length` | integer | Chunk length for the upstream synthesiser |
| `min_chunk_length` | integer | Minimum chunk length |
| `temperature` | number | Sampling temperature (0.0–1.0) |
| `top_p` | number | Top-p nucleus sampling |
| `repetition_penalty` | number | Repetition penalty |
| `max_new_tokens` | integer | Maximum tokens to generate |
| `normalize` | boolean | Apply text normalization |
| `prosody` | object | Prosody overrides (e.g. speed, volume) |
| `references` | array | Inline reference samples |
| `callback_url` | string | Webhook URL for async delivery |

**HTTP Header:**

| Header | Values | Description |
|--------|--------|-------------|
| `model` | `s1`, `s2-pro` | TTS model. Defaults to `s2-pro` |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Number of results per page |
| `page_number` | integer | Page number |
| `title` | string | Filter by model title |
| `tag` | string | Filter by tag |
| `self` | boolean | Only return models owned by the caller |
| `author_id` | string | Filter by author ID |
| `language` | string | Filter by language |
| `title_language` | string | Language of the title field |
| `sort_by` | string | Sort field |

### `POST /fish/tasks` (Polling)

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Task ID (single task) |
| `ids` | array | Task IDs (batch) |
| `action` | string | `retrieve` (single) or `retrieve_batch` (batch) |

## Gotchas

- **Primary endpoint is `/fish/tts`** — the old `/fish/audios` and `/fish/voices` endpoints have been replaced
- **Model is set via HTTP header** — pass `model: s1` or `model: s2-pro` in the request headers, not the body
- **Default latency is `normal`** — the platform adds this automatically if omitted (Fish official would reject missing `latency`)
- **Authentication** uses `Authorization: Bearer {token}` with your AceDataCloud token, not a Fish Audio key
- **Async via `callback_url`** — include `callback_url` in the request body; the response immediately returns `{task_id, started_at}` and the result is POSTed to your URL when ready
- **Poll with `id` + `action`** — use `{"id": "<task_id>", "action": "retrieve"}` when polling `/fish/tasks`, not `{"task_id": "..."}`
- **Voice cloning** uses `reference_id` in `/fish/tts` — get model IDs from `GET /fish/model` or `GET /fish/model/{id}`
- Pricing is based on byte count of generated audio
