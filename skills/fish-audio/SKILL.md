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

> **Async:** Pass `callback_url` in the request body to get an immediate `{task_id, started_at}` response; the final result is POSTed to your URL. You can also poll via `POST /fish/tasks` with `{"id": "<task_id>", "action": "retrieve"}`.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Text-to-speech synthesis |
| `POST /fish/model` | Create (clone) a new voice model |
| `GET /fish/model` | List / search voice models (paginated) |
| `GET /fish/model/{id}` | Get a single voice model by ID |
| `POST /fish/tasks` | Poll async task status |

## Workflows

### 1. Text-to-Speech

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog.",
    "format": "mp3"
  }'
```

Response:

```json
{
  "audio_url": "https://platform.r2.fish.audio/task/05f81919f2e04e35bb404a88fb177854.mp3"
}
```

### 2. TTS with a Cloned Voice

Find a voice model ID via `GET /fish/model`, then pass it as `reference_id`:

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

### 3. Voice Cloning — Create a Voice Model

Provide a publicly accessible audio URL to create a cloneable voice:

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

Returns a `ModelEntity` object whose `_id` can be used as `reference_id` in `/fish/tts`.

### 4. List / Search Voice Models

```bash
curl -G https://api.acedata.cloud/fish/model \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --data-urlencode "language=en" \
  --data-urlencode "tag=narration" \
  --data-urlencode "page_size=5"
```

### 5. Async TTS with Callback

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long text that may take a while to synthesize.",
    "format": "mp3",
    "callback_url": "https://your-server.example.com/webhook"
  }'
```

Immediately returns `{"task_id": "...", "started_at": "..."}`. The result is POSTed to `callback_url` when ready.

## Parameters

### `POST /fish/tts`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | **yes** | Text to synthesize (non-empty) |
| `format` | string | **yes** | Output format: `mp3` or `pcm` (upstream rejects `wav`/`opus`) |
| `reference_id` | string / string[] | no | Cloned voice ID (from `POST /fish/model` or `GET /fish/model`) |
| `references` | object[] | no | Inline reference samples (`{audio, text}`); alternative to `reference_id` |
| `sample_rate` | integer | no | Sampling rate, e.g. `16000`, `22050`, `44100` |
| `mp3_bitrate` | integer | no | MP3 bit rate: `64`, `128`, or `192` |
| `prosody` | object | no | Prosody overrides, e.g. `{"speed": 1.2, "volume": 0}` |
| `latency` | string | no | `normal` (default) or `balanced` |
| `temperature` | number | no | Sampling temperature (0.0–1.0) |
| `top_p` | number | no | Top-p nucleus sampling |
| `normalize` | boolean | no | Whether to apply text normalization |
| `chunk_length` | integer | no | Chunk length for the upstream synthesiser |
| `callback_url` | string | no | Webhook URL for async delivery |

**Request header:**

| Header | Values | Description |
|--------|--------|-------------|
| `model` | `s1`, `s2-pro` (default) | TTS model. `s2-pro` has richer expression; `s1` is more stable for long text |

### `POST /fish/model` (Create Voice)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | **yes** | Voice name |
| `voices` | string | **yes** | Audio sample URL (**single string**, not an array) |
| `description` | string | no | Voice description |
| `cover_image` | string | no | Cover image URL |
| `visibility` | string | no | `private` (default) or `public` |
| `tags` | string[] | no | Search tags, e.g. `["male","narration","zh"]` |
| `texts` | string[] | no | Reference transcripts to improve pronunciation |
| `enhance_audio_quality` | boolean | no | Apply audio quality enhancement before training |
| `generate_sample` | boolean | no | Auto-generate a sample audio after training |

### `GET /fish/model` (List / Search)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_size` | integer | 10 | Results per page |
| `page_number` | integer | 1 | 1-based page number |
| `title` | string | — | Fuzzy title search |
| `tag` | string | — | Filter by tag |
| `self` | boolean | — | `true` to list only your own voices |
| `language` | string | — | Filter by language code, e.g. `en`, `zh`, `es` |
| `sort_by` | string | — | Sort field, e.g. `created_at`, `task_count` |

### `GET /fish/model/{id}`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (path) | **yes** | Voice `_id` (32-char hex) |

### `POST /fish/tasks` (Poll Status)

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Single task ID to retrieve |
| `ids` | array | Multiple task IDs for batch retrieval |
| `action` | string | `retrieve` (single) or `retrieve_batch` (multiple) |

## Gotchas

- `format` is **required** and must be `mp3` or `pcm` — the upstream rejects `wav` and `opus`
- `voices` in `POST /fish/model` must be a **string** (single URL), not an array
- `audio_url` in responses is a signed R2 URL valid for ~1 hour; save to your own storage if you need it longer
- For long texts, use `callback_url` to avoid connection timeouts
- List endpoint (`GET /fish/model`) returns cached R2 URLs; use `GET /fish/model/{id}` for freshly signed download links
