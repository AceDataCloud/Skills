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

Generate AI audio and synthesize voices through AceDataCloud's Fish Audio API. Compatible with the [Fish Audio official API](https://docs.fish.audio).

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a demonstration of AI voice synthesis.", "format": "mp3"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /fish/tasks` with `{"id": "...", "action": "retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Generate audio from text (Fish Audio-compatible TTS) |
| `GET /fish/model` | Query / list available voice clone models |
| `GET /fish/model/{id}` | Get a single voice model by ID |
| `POST /fish/model` | Create a new voice clone from an audio sample |
| `POST /fish/tasks` | Poll async task status |

## Workflows

### 1. Text-to-Speech (basic)

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog.",
    "format": "mp3"
  }'
```

Returns:

```json
{ "audio_url": "https://platform.r2.fish.audio/task/<id>.mp3" }
```

### 2. TTS with a Cloned Voice

Use `reference_id` (a voice model `_id`) to synthesize in a specific voice:

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to our platform.",
    "reference_id": "<_id from GET /fish/model>",
    "format": "mp3"
  }'
```

### 3. Create a Voice Clone

Upload an audio sample URL to create a cloneable voice model:

```bash
curl -X POST https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Custom Voice",
    "voices": "https://example.com/reference-voice.mp3",
    "description": "Clear, neutral-toned speaker for TTS",
    "visibility": "private"
  }'
```

### 4. Search / List Voice Models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode "language=en" \
  --data-urlencode "page_size=10"
```

### 5. Get a Single Voice Model

```bash
curl https://api.acedata.cloud/fish/model/<id> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

## Parameters

### `POST /fish/tts`

| Header / Parameter | Type | Required | Description |
|--------------------|------|----------|-------------|
| `model` (header) | string | No | TTS model: `s1` or `s2-pro` (default `s2-pro`). `s2-pro` is more expressive; `s1` is more stable for long text. |
| `text` | string | Yes | Text to synthesize |
| `format` | string | Yes | Output format: `mp3` or `pcm` |
| `reference_id` | string | No | Cloned voice model `_id` to use |
| `references` | object[] | No | Inline reference samples (each with `audio` and `text`); alternative to `reference_id` |
| `sample_rate` | integer | No | Audio sample rate (e.g. `16000`, `44100`) |
| `mp3_bitrate` | integer | No | MP3 bitrate: `64`, `128`, or `192` |
| `opus_bitrate` | integer | No | Opus bitrate |
| `prosody` | object | No | Prosody overrides: `{"speed": 1.2, "volume": 0}` |
| `chunk_length` | integer | No | Upstream chunk length |
| `min_chunk_length` | integer | No | Minimum chunk length |
| `temperature` | number | No | Sampling temperature (0.0–1.0) |
| `top_p` | number | No | Top-p sampling parameter |
| `repetition_penalty` | number | No | Repetition penalty |
| `max_new_tokens` | integer | No | Maximum new tokens to generate |
| `normalize` | boolean | No | Whether to normalize the input text |
| `latency` | string | No | `normal` or `balanced`; default `normal` |
| `callback_url` | string | No | Webhook URL for async delivery |

### `GET /fish/model`

| Parameter | Type | Description |
|-----------|------|-------------|
| `page_size` | integer | Items per page (default 10) |
| `page_number` | integer | 1-based page number (default 1) |
| `title` | string | Fuzzy search by voice title |
| `tag` | string | Filter by a single tag |
| `self` | boolean | `true` to list only your own voices |
| `author_id` | string | Filter by upstream author `_id` |
| `language` | string | Filter by language code (e.g. `en`, `zh`, `es`) |
| `title_language` | string | Filter by title language |
| `sort_by` | string | Sort field (e.g. `created_at`, `task_count`) |

Returns: `{ "total": N, "items": [...], "has_more": null }`

Each item includes `_id`, `title`, `tags`, `languages`, `visibility`, `samples`, `like_count`, `task_count`, `author`.

### `GET /fish/model/{id}`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` (path) | string | Voice model `_id` (32-char hex string) |

Returns full model detail including `samples[].audio` download links (signed R2 URLs, typically valid for ~1 hour — download and store promptly).

### `POST /fish/model`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Voice name shown in the console |
| `voices` | string | Yes | Public HTTP(S) URL of the audio sample (single string — plural name is inherited from the upstream Fish Audio API) |
| `description` | string | No | Voice description |
| `cover_image` | string | No | Cover image HTTP(S) URL |
| `visibility` | string | No | `private` (default) or `public` |
| `tags` | string[] | No | Tags for the public voice library (e.g. `["male","narration","zh"]`) |
| `texts` | string[] | No | Reference transcripts for pronunciation correction |
| `enhance_audio_quality` | boolean | No | Apply audio quality enhancement before training |
| `generate_sample` | boolean | No | Auto-generate a sample audio after training |

### `POST /fish/tasks`

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | string[] | Multiple task IDs (use with `action: "retrieve_batch"`) |
| `action` | string | `retrieve` (single) or `retrieve_batch` (multiple) |

## Gotchas

- `format` is required for `POST /fish/tts`; only `mp3` and `pcm` are accepted (not `wav` or `opus`)
- `voices` in `POST /fish/model` is a single URL string (the plural name comes from the upstream Fish Audio API)
- `audio_url` returned by `/fish/tts` is a short-lived signed link (typically valid ~1 hour) — download and store it promptly
- Use `self=true` in `GET /fish/model` to list only voices you have created
- To use a public Fish Audio voice in TTS, find its `_id` via `GET /fish/model` and pass it as `reference_id`
