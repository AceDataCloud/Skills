---
name: ace-music
description: Generate ACE Music songs and lyrics through AceDataCloud. Use for idea-to-song generation, custom lyrics and musical style, reference-audio upload, cover, two-source mashup, or retrieving ACE Music task results. Supports acemusic-v1.1 and acemusic-v1.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# ACE Music

Create a song group from an idea or supplied lyrics. Read [authentication](../../README.md#api-key) for credential setup and account access. Check the caller's [current service price](https://platform.acedata.cloud/services/024e09b4-52cf-5e98-a91a-efedf43104c4) before submitting. Lyrics generation is a separate priced operation; task lookup is free and authenticated.

## Choose a workflow

- Use **idea mode** for a song concept, mood, style, instruments or language.
- Use **custom mode** when the user supplies lyrics or wants to edit generated lyrics first.
- Call the lyrics assistant only when the user needs lyrics; do not add an extra lyrics request to every music generation.

Models are `acemusic-v1.1` (default) and `acemusic-v1`. One generation, cover or mashup task targets two MP3 candidates. Upload imports one track as a separate priced operation. Each candidate has its own title, lyrics, style, duration, audio URL and optional cover. Describe observed results without promising a fixed duration or quality relative to another model.

### Idea mode

```bash
curl --request POST https://api.acedata.cloud/acemusic/audios \
  --header "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"action":"generate","model":"acemusic-v1.1","custom":false,"prompt":"A warm folk song about returning home, acoustic guitar and gentle vocals","async":true}'
```

Save the returned platform `task_id` immediately. An accepted task is not a finished song.

### Custom lyrics

```json
{
  "action": "generate",
  "model": "acemusic-v1.1",
  "custom": true,
  "title": "The Road Home",
  "lyric": "[Verse]\nThe evening lights are calling\n[Chorus]\nEvery road leads me home",
  "style": "Warm acoustic folk, gentle vocals",
  "async": true
}
```

Send this JSON to `POST /acemusic/audios`. The platform field is **`lyric`**, singular. Section markers such as `[Verse]`, `[Chorus]`, `[Bridge]` and `[Outro]` can express song structure. Do not copy Suno-specific fields, limits or actions into this request.

### Import a reference, cover or mashup

Use `POST /acemusic/audios` for each explicit operation. Check current pricing before submission; do not add a paid upload automatically when the user asks for a cover.

| Action | Required fields | Optional fields |
| --- | --- | --- |
| `upload` | `audio_url`: public HTTPS MP3 audio the user owns or may use | `name`, caller-owned `audio_id` anchor, `async`, `callback_url` |
| `cover` | `audio_id`, `lyric`, `style`; model `acemusic-v1.1` | `title`, `audio_influence` 1–100 (default 60), `async`, `callback_url` |
| `mashup` | Exactly two distinct `mashup_audio_ids`, `lyric`, `style`; model `acemusic-v1.1` | Same as cover |

Use the platform **audio ID** in a successful task's `response.data`, not its group `task_id`. Sources must belong to the caller and be compatible for reference use. The service validates them; on an incompatibility error, report it without changing sources or importing again. An upload's optional `audio_id` anchors it to an existing owned source for subsequent reference use. Query the returned upload task until its single track succeeds before selecting it.

```json
{
  "action": "cover",
  "model": "acemusic-v1.1",
  "audio_id": "OWNED_PLATFORM_AUDIO_ID",
  "lyric": "[Verse]\nAn original lyric supplied by the user",
  "style": "Warm acoustic folk",
  "audio_influence": 60,
  "async": true
}
```

For a mashup, change `action` to `mashup` and replace `audio_id` with `"mashup_audio_ids":["OWNED_AUDIO_A","OWNED_AUDIO_B"]`. Every submission has its own task ID; poll that same ID. Complete two-track generation groups and successful single-track imports are billed under the current service rules; final failed/partial generation groups and failed imports are free.

### Lyrics assistant

Send `POST /acemusic/lyrics` with `{"prompt":"A song about returning home","style":"Warm folk"}`. The response includes a title and text in `data`. Show or edit those lyrics, then submit a separate custom music task only when requested.

## Retrieve the original task

Read [async task guidance](../../README.md#task-recovery), with these ACE Music group-state rules taking precedence over generic URL-based completion checks:

```bash
curl --request POST https://api.acedata.cloud/acemusic/tasks \
  --header "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"action":"retrieve","id":"ORIGINAL_TASK_ID"}'
```

Query the same ID roughly every 10 seconds within a bounded wait. The persisted result is in `response`; look at the **group state** and each candidate. A nonempty URL does not prove that the entire group has completed.

- `succeeded` / `complete` / `completed`: present the final audio URLs, title, lyrics and duration.
- `partial_failed`: terminal; retain any successful candidate and report that the other candidate failed. Do not silently label the group fully successful.
- `failed` / `error` / cancellation: stop, report the error and retain task/trace IDs.
- Processing or media delivery: continue querying the same task; on client wait timeout, keep its identity for later recovery.
- Submission times out before a task ID arrives: the outcome is unknown. Reconcile the original request rather than automatically paying for a replacement.

For batches use `{"action":"retrieve_batch","ids":["TASK_A","TASK_B"]}`. History uses `{"action":"list","limit":20,"offset":0}`. Credentials and task ownership still apply when the account balance is zero. Use `callback_url` only for an actual webhook under the user's control.

## Supported boundary

The API supports generation, lyrics, explicit URL upload, cover and two-source mashup. Continuation, voices, stems, WAV, MIDI, video export, pure-instrumental controls and style-strength sliders are not part of this contract. Do not infer support from similarly named Suno or Producer parameters.

The companion MCP tools are `acemusic_generate_music`, `acemusic_generate_custom_music`, `acemusic_upload_audio`, `acemusic_cover_audio`, `acemusic_mashup_audio`, `acemusic_generate_lyrics`, `acemusic_get_task`, `acemusic_get_tasks_batch`, `acemusic_list_tasks`, `acemusic_list_models` and `acemusic_get_capabilities`. The `mcp-acemusic` package and hosted endpoint are release targets; verify publication before recommending installation. API, package and hosted availability are separate checks.
