---
name: suno-music
description: Generate AI music with Suno via AceDataCloud API. Use when creating songs from text prompts, generating lyrics, extending tracks, creating covers, extracting vocals, managing voice personas, editing and rendering multitrack Studio projects, training custom music models from authorized audio, or any music generation task. Supports text-to-music, custom styles, multi-format output (MP3, WAV, MIDI, MP4), and vocal separation.
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
  -d '{"prompt": "a happy pop song about coding", "model": "chirp-v6", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** All generation is async. See [async task polling](../_shared/async-tasks.md). Poll via `POST /suno/tasks` with `{"id": "<task_id>"}` every 3-5 seconds.

## Available Models

| Model | Best For |
|-------|---------|
| `chirp-v6` | Current v6 model |
| `chirp-v6-wild` | v6 Wild model |
| `chirp-v6-mini` | v6 Mini model |
| `chirp-v5-5` | Previous model name, retained for compatibility |
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
  "model": "chirp-v6",
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
  "model": "chirp-v6",
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
4. **Poll task** — `POST /suno/tasks` with `id` (or `ids` for batch) until status is complete
5. **Optional: Extend** — Use extend action to add more sections
6. **Optional: Concat** — Use concat action to merge extended segments
7. **Optional: Convert** — Get MP3 (`/suno/mp3`), WAV (`/suno/wav`), MIDI (`/suno/midi`), or MP4 (`/suno/mp4`)

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
| `inspo` | Generate a song inspired by an existing audio |

## Custom Music Models (Beta)

Custom models learn reusable musical characteristics from 6–24 authorized audio files. Creation is a paid, long-running operation. Ask the user to confirm the files and cost before submitting it.

### Create

```json
POST /suno/custom-models
{
  "action": "create",
  "name": "My Album Sound",
  "audio_urls": [
    "https://cdn.example.com/track-01.mp3",
    "https://cdn.example.com/track-02.mp3",
    "https://cdn.example.com/track-03.mp3",
    "https://cdn.example.com/track-04.mp3",
    "https://cdn.example.com/track-05.mp3",
    "https://cdn.example.com/track-06.mp3"
  ]
}
```

Send a stable `Idempotency-Key` header and reuse it after network failures. Save the returned `id`; query it until `status` is `ready`.

### Query and list

```json
POST /suno/custom-models
{"action": "retrieve", "id": "<custom-model-id>"}
```

```json
POST /suno/custom-models
{"action": "retrieve_batch", "status": "ready", "limit": 20, "offset": 0}
```

### Generate

```json
POST /suno/custom-models
{
  "action": "generate",
  "id": "<ready-custom-model-id>",
  "lyric": "[Verse]\nOriginal lyrics here",
  "style": "warm indie pop",
  "title": "New Song",
  "async": true
}
```

Async acceptance is not terminal success: poll the returned task and inspect `response.success`. A custom-model request never falls back to another model. The model must belong to the current Suno application and have `status: "ready"`.

### Archive

```json
POST /suno/custom-models
{"action": "delete", "id": "<custom-model-id>"}
```

`delete` archives the platform resource and prevents further use. `capacity_released: false` means it does not promise that model capacity was released.

## Studio Projects (Beta)

Use `POST /suno/projects` for versioned multitrack editing, not `/suno/audios`. Only process audio the user has rights to use. Send an `Idempotency-Key` header (1–128 characters) for every action except `retrieve`; keep the same key and payload when recovering an uncertain request. A new operation needs a new key; reusing a key with a different payload returns 409.

### Create, retrieve, and save

```json
POST /suno/projects
{"action":"create","title":"My Studio Project"}
```

Save `data.id`, then `retrieve` with that project `id` before editing. The returned `state` is authoritative; modify it rather than inventing track/clip structures. An empty project starts with `{"tracks":[],"timing":{"bps":2}}`.

```json
POST /suno/projects
{"action":"retrieve","id":"PROJECT_ID"}
```

```json
POST /suno/projects
{"action":"save","id":"PROJECT_ID","state":{"tracks":[],"timing":{"bps":2}}}
```

`save` replaces the complete state, not a patch: preserve unknown fields from `retrieve.data.state`. It completes synchronously even if its result includes `task_id`. Only the first save of a new, unversioned project may omit `version_id`. Afterwards, include the latest `version_id` in every modification, candidate generation, and render. After `save`, `add_track`, `commit_candidate`, or `remove_track`, retain the new version from the result. `upload`, `render`, `generate_track`, and `replace_section` do not change the project version. On HTTP 409, retrieve the current project, reconcile changes, and submit with a new key; do not blindly replay stale edits.

`timing.bps` is beats per second, must be positive, and defaults to 2 (120 BPM). Clip `startBeats`, `endBeats`, and `readStartBeats` are project beats, not audio-analysis bar positions. Request placement fields `start_beats` / `end_beats` are nonnegative project beats; `start_seconds` / `end_seconds` select source-audio seconds.

### Upload and add audio

```json
POST /suno/projects
{"action":"upload","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","audio_url":"https://cdn.example.com/reference.mp3","async":true}
```

Poll the upload task to success, then read `response.data.candidate.audio_id` and use it in `add_track`:

```json
POST /suno/projects
{"action":"add_track","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","audio_id":"AUDIO_ID","name":"Backing Vocals"}
```

Default placement preserves playback speed and converts audio duration to beats using `timing.bps`.

### Generate, choose, and commit candidates

Projects accept only these public model names: `chirp-v3-5`, `chirp-v4`, `chirp-v4-5`, `chirp-v4-5-plus`, `chirp-v5`, `chirp-v5-5`, `chirp-v6`, `chirp-v6-wild`, `chirp-v6-mini`. An unsupported name returns 400 before submission; an accepted name does not guarantee the selected operation succeeds. Never silently switch models.

```json
POST /suno/projects
{"action":"replace_section","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","source_audio_id":"AUDIO_ID","start_seconds":35.12,"end_seconds":48.76,"model":"chirp-v6","replacement_lyrics":"New section lyrics","async":true}
```

`replace_section` returns two candidates without selecting one. The end must not exceed the actual source duration. `prompt` supplies source lyrics/context; `replacement_lyrics` supplies the new interval lyrics. If `fixed=true`, the range must be shorter than 26 seconds; support is model-dependent and this mode is not verified by the documented Backend run.

For a new track, first add the source audio to the project, then retrieve the complete state and append an empty audio track with a fresh unique `id`, `type:"audio"`, `clips:[]`, `takeLanes:[]`, `mute:false`, `solo:false`, `amplitude:1`, `instrument:{"type":"song"}`, and `color:"#7251F7"`. Save the complete state before generating, retaining its new version and the destination track ID. Render that version to success and use `response.data.audio_id` as the mix reference:

```json
POST /suno/projects
{"action":"generate_track","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","source_audio_id":"AUDIO_ID","render_audio_id":"RENDER_AUDIO_ID","model":"chirp-v5","start_seconds":12,"end_seconds":20,"stem_control_tags":"add Piano","tags":"gentle piano, instrumental","batch_size":2,"instrumental":true,"vocal_gender":"unspecified","async":true}
```

`stem_control_tags` is descriptive text, not an enum. `batch_size` is 1–4 (default 2). `instrumental` defaults to true; use `prompt` for new-track text/lyrics and `vocal_gender` (`f`, `m`, `unspecified`, default `unspecified`) for a preference, not a guaranteed result. Both generation actions accept `tags` and `negative_tags` (default empty strings). Source-second ranges are not output-duration guarantees; inspect each candidate's actual duration. Generation does not add candidates to the project.

Poll to success, read `response.data.operation_id` and the chosen `response.data.candidates[].id` (do not substitute project IDs or the commit task ID), and let the user choose a candidate before committing:

```json
POST /suno/projects
{"action":"commit_candidate","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","operation_id":"OPERATION_ID","candidate_id":"CANDIDATE_ID","track_id":"TRACK_ID","async":true}
```

- Candidates are bound to the version used to generate them. Save an empty destination track **before** generating a new-track candidate; creating it afterwards makes the candidate stale.
- Replacement candidates must go back to the original track containing the unique source clip. A full take preserves its placement; an interval replacement preserves the surrounding clips. Do not supply `start_beats` / `end_beats` for these replacements. If duration cannot be matched reliably, the request returns 400 and leaves the project unchanged.
- New-track candidates use the saved empty track and default to the source clip's start, or an explicit non-overlapping range. Overlap on the destination track returns 400.
- To remove a track, confirm the intended track, then submit the current version and retrieve again to verify the remaining state:

```json
POST /suno/projects
{"action":"remove_track","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","track_id":"TRACK_ID"}
```

### Render and recover

```json
POST /suno/projects
{"action":"render","id":"PROJECT_ID","version_id":"CURRENT_VERSION_ID","title":"Final Mix","async":true}
```

Omit `start_beats` / `end_beats` to render from the earliest audible clip start to the latest audible end. Muted tracks/clips are excluded; when solo tracks exist, only those tracks participate. An empty or inaudible project, negative bounds, or an end not greater than the start returns 400. On terminal success, persist the returned `render_id`, `audio_id`, `audio_url`, and duration.

`upload`, `add_track`, `generate_track`, `replace_section`, `commit_candidate`, and `render` always run asynchronously, even with `async:false`. For every asynchronous Projects operation, poll `POST /suno/tasks` with `{"action":"retrieve","id":"TASK_ID"}` every 3–5 seconds. Success requires `finished_at` and `response.success=true`; `response.success=false` indicates failure. Read `response.error` on failure, including after a callback. HTTP 200 or a `task_id` is acceptance, not completed audio. This Projects rule is distinct from the `/suno/audios` clip-state rule below.

A readable candidate URL or successful commit does not prove the project can render. The documented Backend run generated and committed a new track, but rendering with it failed with `studio_audio_unavailable`; a replacement candidate also failed to commit because its duration matched neither the source nor the selected interval. Keep the original project and candidate for inspection; do not guess placement or automatically repeat paid generation. Before removing an unavailable track, confirm the intended edit with the user, retrieve the current state, remove only that track, then retrieve and render the new version to verify recovery. Projects and candidates are bound to their application and execution environment; do not assume cross-application reuse or automatic failover.

An identical key and payload replay the original result, including failure, without generating again. To explicitly retry, first confirm the original task failed, then use a new key. Never resubmit while the original is processing or uncertain. Keep `trace_id` for troubleshooting; report `studio_state_invalid` (400), `studio_model_unsupported` (400), `studio_unavailable` / `studio_model_unavailable` (503), `too_many_requests` (429), and `studio_audio_unavailable` / `content_rejected` (403) rather than changing models or discarding edits.

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
| `/suno/voices` | POST | Create a reusable voice from an audio URL; requires `audio_url`, with optional `name` and `description` |
| `/suno/timing` | POST | Get word-level timing/subtitles |
| `/suno/persona` | POST | Save a vocal style as a reusable persona; requires `audio_id` and `name` |
| `/suno/persona` | GET | List reusable personas |
| `/suno/persona` | DELETE | Delete a reusable persona |
| `/suno/upload` | POST | Upload external audio for extend/cover |
| `/suno/tasks` | POST | Query task status and results |
| `/suno/custom-models` | POST | Create, generate with, query, list, or archive custom music models |
| `/suno/projects` | POST | Create, retrieve, edit, generate candidates, and render versioned Studio projects (Beta) |

## Advanced Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `lyric_prompt` | object | Structured prompt payload for auto-generating lyrics (used when `custom: true` without explicit `lyric`) |
| `negative_tags` | string | Style or genre tags to avoid (e.g., `"heavy metal, distortion"`); used in custom mode |
| `style_influence` | number | Strength of style influence (advanced custom mode, v5+ only) |
| `audio_weight` | number | Weight for audio reference when covering (advanced, v5+ only) |
| `duration` | integer | Target track length in seconds (typically 10–360). Best supported on `generate` with `custom: true` on newer models such as `chirp-v5-5` |

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

- `/suno/audios` generation is **async** — set `"callback_url"` to get a task id immediately, then poll `/suno/tasks` using `{"id":"<task_id>"}` or `{"ids":[...],"action":"retrieve_batch"}`
- **CRITICAL for `/suno/audios`:** Check the clip `state` field — only `state: "complete"` with `success: true` means done. During `pending`, the API may return intermediate `audio_url` values (streaming previews). Do NOT stop polling just because `audio_url` is non-empty
- Lyrics max ~3000 characters. For longer songs, use the **extend** workflow
- Style tags are descriptive phrases, not enum values (e.g., "Synthwave, Electronic, Dreamy")
- `vocal_gender` ("f"/"m") is only supported on v4.5+ models
- `variation_category` ("high"/"normal"/"subtle") is only supported on v5+ models
- `duration` is forwarded as you send it — support varies by model and action, and an unsupported combination may ignore it or return an error, so verify with one request before batching. Note the request `duration` is a *target*; the `duration` in each returned clip is the *actual* length and will vary slightly
- The `concat` action merges extended song segments — requires audio_id of the extended track
- `persona` requires an existing `audio_id` and a `name`; optional `vox_audio_id`, `vocal_start`, `vocal_end`, and `description` refine the vocal reference
- Upload external audio via `/suno/upload` before using it with extend/cover

> **MCP:** `pip install mcp-suno` | Hosted: `https://suno.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
