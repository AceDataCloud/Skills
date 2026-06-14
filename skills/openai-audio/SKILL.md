---
name: openai-audio
description: Synthesize speech with OpenAI-compatible Text-to-Speech via AceDataCloud API. Use when generating audio from text using /v1/audio/speech with OpenAI SDK compatibility.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# OpenAI Audio Speech

Generate speech audio from text with an OpenAI-compatible endpoint.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/v1/audio/speech \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -o speech.mp3 \
  -d '{"model":"tts-1-hd","input":"Hello from AceData Cloud.","voice":"nova","response_format":"mp3"}'
```

## Endpoint

- `POST /v1/audio/speech` (alias: `POST /openai/audio/speech`)

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `input` | string | Text to synthesize (required) |
| `model` | `"tts-1"`, `"tts-1-hd"` | Speech model (`tts-1-hd` default) |
| `voice` | `"alloy"`, `"echo"`, `"fable"`, `"onyx"`, `"nova"`, `"shimmer"` | Voice preset (`alloy` default) |
| `response_format` | `"mp3"`, `"opus"`, `"aac"`, `"flac"`, `"wav"`, `"pcm"` | Audio format (`mp3` default) |
| `speed` | 0.25–4.0 | Playback speed (`1.0` default) |

## OpenAI SDK Compatibility

Use OpenAI SDKs by pointing `base_url` to AceDataCloud:

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.acedata.cloud/v1", api_key="YOUR_TOKEN")
client.audio.speech.create(model="tts-1-hd", voice="nova", input="Hello from AceData.").stream_to_file("speech.mp3")
```

## Gotchas

- The API returns audio bytes directly (for example `audio/mpeg` for mp3), not a JSON URL payload
- `input` is required and cannot be empty
- Use `-o <file>` in curl to save the binary response
