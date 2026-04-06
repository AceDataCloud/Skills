---
name: suno-music
description: Generate AI music with Suno via AceDataCloud API. Use when creating songs from text prompts, generating lyrics, extending tracks, creating covers, extracting vocals, managing voice personas, or any music generation task. Supports text-to-music, custom styles, multi-format output (MP3, WAV, MIDI, MP4), and vocal separation.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-suno for tool-use.
---

# Suno Music Generation

Generate AI-powered music through AceDataCloud's Suno API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/suno/audios \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a happy pop song about coding", "model": "chirp-v5-5", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** All generation is async. See [async task polling](../_shared/async-tasks.md). Poll via `POST /suno/tasks` with `{"task_id": "..."}` every 3-5 seconds.

## Available Models

| Model | Best For |
|-------|---------|
| `chirp-v5-5` | Latest, highest quality |
| `chirp-v5` | High quality |
| `chirp-v4-5-plus` | Enhanced v4.5 |
| `chirp-v4-5` | Good balance of quality and speed |
| `chirp-v4` | Fast, reliable |
| `chirp-v3-5` | Legacy, stable |
| `chirp-v3-0` | Legacy |

## Core Workflows

### 1. Quick Generation (Inspiration Mode)

Generate a song from a text description. Suno creates lyrics, style, and music automatically.

```json
POST /suno/audios
{
  "prompt": "an upbeat electronic track about the future of AI",
  "model": "chirp-v5-5",
  "instrumental": false
}
```

### 2. Custom Generation (Full Control)

Provide your own lyrics, title, and style for precise control.

```json
POST /suno/audios
{
  "custom": true,
  "lyric": "[Verse]\nCode is poetry in motion\n[Chorus]\nWe build the future tonight",
  "title": "Digital Dreams",
  "style": "Synthwave, Electronic, Dreamy",
  "model": "chirp-v5-5",
  "vocal_gender": "f"
}
```

### 3. Extend a Song

Continue an existing song from a specific timestamp with new lyrics.

```json
POST /suno/audios
{
  "action": "extend",
  "audio_id": "existing-audio-id",
  "lyric": "[Bridge]\nNew section lyrics here",
  "continue_at": 120.0,
  "style": "Same style as original"
}
```

### 4. Cover / Remix

Create a new version of an existing song in a different style.

```json
POST /suno/audios
{
  "action": "cover",
  "audio_id": "existing-audio-id",
  "style": "Jazz, Acoustic, Mellow"
}
```

### 5. Full Song Creation Workflow

For best results follow this multi-step workflow:

1. **Generate lyrics** — `POST /suno/lyrics` with a topic/prompt
2. **Optimize style** — `POST /suno/style` to refine style description
3. **Generate music** — `POST /suno/audios` with custom action, lyrics + style
4. **Poll task** — `POST /suno/tasks` with task_id until status is complete
5. **Optional: Extend** — Use extend action to add more sections
6. **Optional: Concat** — Use concat action to merge extended segments
7. **Optional: Convert** — Get WAV (`/suno/wav`), MIDI (`/suno/midi`), or MP4 (`/suno/mp4`)

## Available Actions

| Action | Description |
|--------|-------------|
| `generate` | Generate from prompt (default) |
| `extend` | Continue an existing audio from a timestamp |
| `upload_extend` | Upload external audio, then extend it |
| `upload_cover` | Upload external audio, then create a cover |
| `concat` | Concatenate extended segments into one track |
| `cover` | Copy the style of an existing audio |
| `artist_consistency` | Generate in a custom singer's style |
| `artist_consistency_vox` | Artist consistency with vocal focus |
| `stems` | Separate a track into stems |
| `all_stems` | Separate into all available stems |
| `replace_section` | Replace a specific time range in a song |
| `underpainting` | Add accompaniment to an uploaded song |
| `overpainting` | Add vocals to an uploaded song |
| `remaster` | Remaster an existing audio |
| `mashup` | Blend multiple audio IDs together |
| `samples` | Add samples to an uploaded song |

## Auxiliary Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/suno/lyrics` | POST | Generate structured lyrics from a prompt (`model`: `"default"` or `"remi-v1"`) |
| `/suno/style` | POST | Optimize/refine a style description |
| `/suno/mashup-lyrics` | POST | Combine two sets of lyrics |
| `/suno/mp4` | POST | Get MP4 video version of a song |
| `/suno/wav` | POST | Convert to lossless WAV format |
| `/suno/midi` | POST | Extract MIDI data for DAW editing |
| `/suno/vox` | POST | Extract vocal track (stem separation) |
| `/suno/timing` | POST | Get word-level timing/subtitles |
| `/suno/persona` | POST | Save a vocal style as a reusable persona |
| `/suno/upload` | POST | Upload external audio for extend/cover |
| `/suno/tasks` | POST | Query task status and results |

## Advanced Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `lyric_prompt` | string | Prompt for auto-generating lyrics (used when `custom: true` without explicit `lyric`) |
| `style_negative` | string | Style tags to avoid (e.g., `"heavy metal, distortion"`) |
| `style_influence` | number | Strength of style influence (advanced custom mode, v5+ only) |
| `audio_weight` | number | Weight for audio reference when covering (advanced, v5+ only) |

## Lyrics Format

Use section markers in square brackets:

```
[Verse 1]
Your verse lyrics here

[Chorus]
Catchy chorus lyrics

[Bridge]
Bridge section

[Outro]
Ending lyrics
```

## Gotchas

- All generation is **async** — always set `"callback_url"` to get a `task_id` immediately, then poll `/suno/tasks`
- **CRITICAL:** Check the `state` field — only `state: "complete"` with `success: true` means done. During `pending`, the API may return intermediate `audio_url` values (streaming previews). Do NOT stop polling just because `audio_url` is non-empty
- Lyrics max ~3000 characters. For longer songs, use the **extend** workflow
- Style tags are descriptive phrases, not enum values (e.g., "Synthwave, Electronic, Dreamy")
- `vocal_gender` ("f"/"m") is only supported on v4.5+ models
- `variation_category` ("high"/"normal"/"subtle") is only supported on v5+ models
- The `concat` action merges extended song segments — requires audio_id of the extended track
- `persona` requires an existing audio_id to extract the vocal reference from
- Upload external audio via `/suno/upload` before using it with extend/cover

> **MCP:** `pip install mcp-suno` | Hosted: `https://suno.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
