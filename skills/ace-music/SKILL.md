---
name: ace-music
description: Generate ACE Music songs and lyrics through AceDataCloud. Use for idea-to-song generation, custom lyrics and musical style, two song candidates, or retrieving ACE Music task results. Supports acemusic-v1.1 and acemusic-v1.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# ACE Music

Create a song group from an idea or supplied lyrics. Read [authentication](../_shared/authentication.md) for credential setup and account access. Check the caller's [current service price](https://platform.acedata.cloud/services/024e09b4-52cf-5e98-a91a-efedf43104c4) before submitting. Lyrics generation is a separate priced operation; task lookup is free and authenticated.

## Choose a workflow

- Use **idea mode** for a song concept, mood, style, instruments or language.
- Use **custom mode** when the user supplies lyrics or wants to edit generated lyrics first.
- Call the lyrics assistant only when the user needs lyrics; do not add an extra lyrics request to every music generation.

Models are `acemusic-v1.1` (default) and `acemusic-v1`. One generation task targets two MP3 candidates. Each candidate has its own title, lyrics, style, duration, audio URL and optional cover. Describe observed results without promising a fixed duration or quality relative to another model.

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

### Lyrics assistant

Send `POST /acemusic/lyrics` with `{"prompt":"A song about returning home","style":"Warm folk"}`. The response includes a title and text in `data`. Show or edit those lyrics, then submit a separate custom music task only when requested.

## Retrieve the original task

Read [async task guidance](../_shared/async-tasks.md), with these ACE Music group-state rules taking precedence over generic URL-based completion checks:

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

For batches use `{"action":"retrieve_batch","ids":["TASK_A","TASK_B"]}`. History uses `{"action":"list","page":1,"page_size":20}`. Credentials and task ownership still apply when the account balance is zero. Use `callback_url` only for an actual webhook under the user's control.

## Supported boundary

The initial API supports generation and lyrics. Upload, reference-audio covers, continuation, voices, stems, WAV, MIDI, video export, pure-instrumental controls and style-strength sliders are not part of this contract. Do not infer support from similarly named Suno or Producer parameters.

The companion MCP tools are `acemusic_generate_music`, `acemusic_generate_custom_music`, `acemusic_generate_lyrics`, `acemusic_get_task`, `acemusic_get_tasks_batch`, `acemusic_list_tasks`, `acemusic_list_models` and `acemusic_get_capabilities`. The `mcp-acemusic` package and hosted endpoint are release targets; verify publication before recommending installation. API, package and hosted availability are separate checks.
