---
name: fish-audio
description: Generate text-to-speech, find saved voices, create a persistent public voice model, or make a one-shot clone from an HTTPS audio URL and exact transcript via AceDataCloud API.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (get an API key at https://platform.acedata.cloud/console/applications).
---

# Fish Audio — Text-to-Speech

Generate narration / voiceover through AceDataCloud's Fish Audio API.

## First-time setup

1. Install the official Skill with `clawhub install @acedatacloud/fish-audio`. Check that the ClawHub publisher is **@acedatacloud**.
2. Sign in at [AceDataCloud → Applications](https://platform.acedata.cloud/console/applications), open **General application**, and check Fish Audio access, balance, and current pricing. Copy its API key, or select **Manage Keys → Create** for a separate key. Copy the key value without `Bearer `; a `platform-...` management token is not a service API key.
3. If you enable **Allowed APIs** restrictions, include `/fish/tts` (and `/fish/tasks` for asynchronous TTS). Advanced workflows below may call additional routes.
4. On the OpenClaw Gateway host, put `ACEDATACLOUD_API_TOKEN=your_api_key_here` in `~/.openclaw/.env`, then restart the Gateway and start a new session. For a direct terminal test, run `export ACEDATACLOUD_API_TOKEN="your_api_key_here"` in that shell. Never put the key in a prompt or commit an `.env` file.
5. Run the **Quick Start** below. If this workflow returns a task ID, query that same task until it finishes; do not submit the same billable request again just to check progress.

[Illustrated key setup, first run, and troubleshooting](https://github.com/AceDataCloud/Skills#first-run-with-clawhub-and-openclaw) · [Token details](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md)

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/fish/tts \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "model: s2-pro" \
  -d '{"text":"你好，欢迎使用 AceData Cloud。","reference_id":"d7900c21663f485ab63ebdb7e5905036","format":"mp3"}'
```

Synchronous responses return a direct audio URL:

```json
{"audio_url":"https://platform.r2.fish.audio/task/8a72ff9840234006a9f74cb2fa04f978.mp3"}
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/tts` | Text-to-speech generation |
| `POST /fish/model` | Create a persistent public voice model from an audio URL |
| `GET /fish/model` | Browse/search public voices or list voices created through this platform with `self=true` |
| `GET /fish/model/{id}` | Fetch one reference voice by ID |
| `POST /fish/tasks` | Poll async TTS jobs when `async: true` |

## Workflows

### 1. Find a reference voice

```bash
curl "https://api.acedata.cloud/fish/model?page_size=10&page_number=1&title=Marcus" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

The response includes `items[]` with public voice metadata such as `_id`, `title`,
`languages`, `tags`, `visibility`, and `state`. Use an item `_id` as
`reference_id` in TTS requests.

### 2. Text-to-Speech

```json
POST /fish/tts
Headers:
  model: s2-pro

{
  "text": "Your narration text.",
  "reference_id": "d7900c21663f485ab63ebdb7e5905036",
  "format": "mp3"
}
```

### 3. One-shot voice cloning

Use a temporary reference voice without creating a persistent model:

```json
POST /fish/tts
Headers:
  model: s2-pro

{
  "text": "New speech in the referenced voice.",
  "format": "mp3",
  "references": [{
    "audio": "https://cdn.acedata.cloud/reference.mp3",
    "text": "The exact words spoken in the reference audio."
  }]
}
```

`audio` must be a public HTTPS MP3/WAV URL and `text` must be the exact transcript. Use one reference lasting 10–270 seconds. Do not combine `references` with `reference_id`; use `reference_id` when the same saved/public voice will be reused. Raw bytes, Base64, data URIs, and MessagePack are not accepted by the AceDataCloud endpoint.

### 4. Async TTS

```json
POST /fish/tts
Headers:
  model: s1

{
  "text": "Longer narration for background processing.",
  "callback_url": "https://your-domain.example/fish-webhook"
}
```

Use an actual public webhook that you operate; replace the example URL. If you
do not have one, use the synchronous Quick Start above. After an asynchronous
submission returns a task ID, see [async task polling](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md) and query `POST /fish/tasks` with `{"id":"..."}`.

### 5. Create a persistent public voice model

Only use audio the user has permission to clone and publish. Before submitting, obtain explicit confirmation that the voice will be saved publicly long-term and other users may search for and use it. Do not proceed if a private saved voice is required: `visibility` does not change publication, even when set to `private` or `unlist`. Omit it from requests. For a temporary reference without a saved model, use the one-shot workflow above.

Replace `HTTPS_REFERENCE_AUDIO_URL` with a publicly downloadable audio URL, preferably ending in `.mp3` or `.wav`:

```json
POST /fish/model
{
  "title": "My authorized narration voice",
  "voices": "HTTPS_REFERENCE_AUDIO_URL"
}
```

Send the same AceDataCloud Bearer token and JSON content type. `title` and `voices` are required; `voices` must be a single URL string, not an array, multipart upload, or binary data. Optional fields include `description`, `cover_image`, `tags` (string array), `texts` (reference transcript array), `enhance_audio_quality`, and `generate_sample`.

HTTP 201 returns the model object directly. Save its actual `_id` and inspect `state`; use that `_id` as `reference_id` for later TTS, not a fabricated ID. On HTTP 400, check that the audio downloads, has sufficient duration, and has a recognized format; do not repeat an unchanged request.

### 6. List voices created by the calling account

```bash
curl "https://api.acedata.cloud/fish/model?self=true&page_size=10&page_number=1&sort_by=created_at" \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN"
```

`self=true` returns voices created and saved through this platform by the current calling account, including those created with different API Tokens for that same account. It is only a list filter, not an access restriction: these voices remain public and usable by others. It is not equivalent to filtering by a shared author ID.

Results default to newest creation first with 1-based `page_number` pagination. `sort_by` supports `created_at` and `task_count` for `self=true`; `author_id` can further filter the saved voices by author. `title`, `tag`, and `language` also filter results. `title_language` is not supported with `self=true`; omit `self` to search the public voice library by title language.

Read `items`, `total`, and `has_more`. For `self=true`, `has_more` is boolean; stop when false. Public-library queries may return `has_more: null`; use `total` and `page_size` to determine remaining pages instead of treating null as false.

## Parameters — `/fish/tts`

### Header

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"s1"`, `"s2-pro"`, `"s2.1-pro"` | Fish TTS engine selection |

### JSON body

| Parameter | Type / Values | Description |
|-----------|---------------|-------------|
| `text` | string | Text to synthesize (required) |
| `reference_id` | string | Public/reference voice ID from `GET /fish/model` |
| `format` | `"mp3"`, `"wav"`, `"pcm"` | Output format |
| `sample_rate` | integer | Optional output sample rate |
| `mp3_bitrate` | `64`, `128`, `192` | MP3 bitrate |
| `latency` | `"normal"`, `"balanced"` | TTS latency mode |
| `chunk_length` / `min_chunk_length` | integer | Chunking controls |
| `temperature`, `top_p`, `repetition_penalty` | number | Sampling controls |
| `max_new_tokens` | integer | Maximum generated tokens |
| `normalize` | boolean | Normalize generated audio |
| `prosody` | object | Prosody tuning |
| `references` | array | One `{audio, text}` object for a one-shot voice clone; mutually exclusive with `reference_id` |
| `callback_url` | string | Async callback URL |
| `async` | boolean | Run asynchronously and poll `/fish/tasks` |

## Gotchas

- The documented TTS endpoint is `POST /fish/tts` — not `/fish/audios`.
- Choose the Fish engine with the **`model` request header**, not a JSON `model` field.
- Use `reference_id` from `GET /fish/model` — not `voice_id`.
- Use `references` for a one-shot clone that is not saved as a model.
- Billing is based on the target text UTF-8 byte count; the reference audio does not add a separate clone fee.
- Synchronous requests return `audio_url` directly; async jobs should be polled via `/fish/tasks`.
