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

> **Async:** See [async task polling](../_shared/async-tasks.md). Pass `callback_url` in the request body for async delivery. Poll via `POST /fish/tasks` with `{"id": "<task_id>", "action": "retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Text-to-speech synthesis |
| `POST /fish/model` | Create a cloned voice model |
| `GET /fish/model` | List / search voice models |
| `GET /fish/model/{id}` | Get a single voice model by ID |
| `POST /fish/tasks` | Poll task status |

## Workflows

### 1. Text-to-Speech (minimal)

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "The quick brown fox jumps over the lazy dog.", "format": "mp3"}'
```

Response:

```json
{"audio_url": "https://platform.r2.fish.audio/task/05f81919f2e04e35bb404a88fb177854.mp3"}
```

`audio_url` is a signed Fish R2 link valid for ~1 hour. Download or re-host it promptly.

### 2. Text-to-Speech with a Cloned Voice

Use a voice `_id` from `GET /fish/model` as `reference_id`:

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Welcome to our platform.", "reference_id": "<_id from GET /fish/model>", "format": "mp3"}'
```

### 3. Clone a Voice

```bash
curl -X POST https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Voice Clone", "voices": "https://example.com/sample.mp3"}'
```

`voices` must be a **single URL string** (not an array). The response contains an `_id` to use as `reference_id` in `/fish/tts`.

### 4. Search Voice Models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode "language=en" \
  --data-urlencode "page_size=10"
```

## Parameters

### `POST /fish/tts`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | **Yes** | Text to synthesize (non-empty) |
| `format` | string | **Yes** | Output format: `mp3` or `pcm` |
| `reference_id` | string \| string[] | No | Cloned voice ID(s) from `GET /fish/model` |
| `references` | object[] | No | Inline reference samples (`audio` + `text`); alternative to `reference_id` |
| `sample_rate` | integer | No | Output sample rate (e.g. `16000`, `22050`, `44100`) |
| `mp3_bitrate` | integer | No | MP3 bitrate when `format=mp3` (e.g. `64`, `128`, `192`) |
| `prosody` | object | No | Prosody overrides: `speed` (1.0 = normal) and `volume` (dB gain) |
| `chunk_length` | integer | No | Upstream chunk length |
| `min_chunk_length` | integer | No | Minimum chunk length |
| `temperature` | number | No | Sampling temperature (0.0–1.0) |
| `top_p` | number | No | Top-p nucleus sampling parameter |
| `repetition_penalty` | number | No | Repetition penalty |
| `max_new_tokens` | integer | No | Maximum new tokens to generate |
| `latency` | string | No | `normal` or `balanced`; defaults to `normal` |
| `normalize` | boolean | No | Whether to apply text normalization |
| `callback_url` | string | No | Webhook URL; returns `{task_id, started_at}` immediately |

**Request headers:**

| Header | Description |
|--------|-------------|
| `model` | TTS model: `s1` (stable) or `s2-pro` (expressive, default) |
| `accept` | Response format; defaults to `application/json` |

### `POST /fish/model`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | **Yes** | Voice name displayed in the console |
| `voices` | string | **Yes** | Single HTTP(S) URL of the audio sample (not an array) |
| `description` | string | No | Voice description |
| `cover_image` | string | No | Cover image URL |
| `visibility` | string | No | `private` (default) or `public` |
| `tags` | string[] | No | Public library tags (e.g. `["male","narration","zh"]`) |
| `texts` | string[] | No | Reference texts for the samples (corrects pronunciation) |
| `enhance_audio_quality` | boolean | No | Apply audio enhancement before training |
| `generate_sample` | boolean | No | Auto-generate a sample audio after training |

### `GET /fish/model`

Query parameters (passed as URL params):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_size` | integer | 10 | Items per page |
| `page_number` | integer | 1 | 1-based page number |
| `title` | string | — | Partial title match |
| `tag` | string | — | Filter by a single tag |
| `self` | boolean | — | `true` = only return models owned by the caller |
| `author_id` | string | — | Filter by author ID |
| `language` | string | — | Filter by language code (`en`, `zh`, `es`, …) |
| `title_language` | string | — | Filter by title language |
| `sort_by` | string | — | Sort field (e.g. `created_at`, `task_count`) |

### `GET /fish/model/{id}`

| Parameter | Where | Description |
|-----------|-------|-------------|
| `id` | Path | 32-character hex voice `_id` |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | string[] | Multiple task IDs for batch retrieval |
| `action` | string | `retrieve` (single) or `retrieve_batch` (multiple) |

## Gotchas

- `format` is **required** for `/fish/tts`. Only `mp3` and `pcm` are accepted; other values (e.g. `wav`, `opus`) return a `400` error
- `voices` in `POST /fish/model` must be a **string** (single URL), not an array
- `audio_url` in TTS responses is a signed R2 link valid for ~1 hour — re-host promptly if persistence is needed
- For long texts, use `callback_url` to avoid connection timeouts; poll the returned `task_id` via `POST /fish/tasks`
- Task polling uses `id` (not `task_id`) in the request body for `/fish/tasks`
- `GET /fish/model` and `GET /fish/model/{id}` are free; only `POST /fish/model` (creating a clone) is billed
