---
name: fish-audio
description: Generate AI text-to-speech audio and clone voices with Fish Audio via AceDataCloud API. Use when creating voiceover/narration audio (TTS), synthesizing speech, or cloning a reference voice. Chinese + multilingual.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Fish Audio — Text-to-Speech & Voice Cloning

Generate narration / voiceover and clone voices through AceDataCloud's Fish Audio API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start (TTS — synchronous, ~3s)

```bash
curl -X POST https://api.acedata.cloud/fish/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action":"speech","model":"fish-tts","voice_id":"543e4181d81b4ef6874b0e8fbdf27c78","prompt":"你好,欢迎使用 AceData Cloud。"}'
```

Response (synchronous — no polling needed for `speech`):

```json
{"success": true, "data": [{"audio_url": "https://platform.r2.fish.audio/task/....mp3"}]}
```

→ download `data[0].audio_url`. `voice_id` is **required**. A good default Mandarin
news-anchor voice is **`543e4181d81b4ef6874b0e8fbdf27c78`**.

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /fish/audios` | TTS (`action: "speech"`) — synchronous |
| `POST /fish/voices` | List / register (clone) voices |

## Workflows

### 1. Text-to-Speech (the common case)

```json
POST /fish/audios
{
  "action": "speech",
  "model": "fish-tts",
  "voice_id": "543e4181d81b4ef6874b0e8fbdf27c78",
  "prompt": "你的旁白文本。"
}
```

### 2. Clone a voice from a reference sample

```json
POST /fish/voices
{
  "voice_url": "https://example.com/reference-voice.mp3",
  "title": "My Custom Voice",
  "description": "Clear, neutral-toned speaker"
}
```

Then pass the returned id as `voice_id` in workflow 1.

## Parameters — `/fish/audios`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | yes | Use `"speech"` for TTS |
| `model` | string | yes | `"fish-tts"` |
| `voice_id` | string | yes | A Fish reference/cloned voice id (default Mandarin: `543e4181d81b4ef6874b0e8fbdf27c78`) |
| `prompt` | string | yes | Text to synthesize |

## Gotchas

- **TTS (`action:"speech"`) is synchronous** — the response carries `data[0].audio_url`; do NOT poll `/fish/tasks` for it.
- `voice_id` is **required** — a bare `{"prompt": "..."}` returns `400 voice_id is required when action is speech`.
- `model` must be `"fish-tts"` for speech (NOT `speech-1.5`); sending a different model returns `400 model is invalid if action is speech`.
- Pricing is based on the **byte count** of the generated audio. Multilingual is automatic.
