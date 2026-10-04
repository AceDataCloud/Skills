<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Suno Music Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/suno/audios` | `lyric`, `model`, `max_mode`, `variety`, `style`, `variation_category`, `title`, `action`, `custom`, `prompt`, `lyric_prompt`, `audio_id`, `stem_type`, `audio_format`, `sound`, `sound_type`, `bpm`, `key`, `speed_multiplier`, `keep_pitch`, `mashup_audio_ids`, `audio_urls`, `weirdness`, `persona_id`, `overpainting_start`, `overpainting_end`, `samples_start`, `samples_end`, `underpainting_start`, `underpainting_end`, `continue_at`, `callback_url`, `async`, `instrumental`, `vocal_gender`, `negative_tags`, `style_influence`, `audio_weight`, `duration`, `replace_section_end`, `replace_section_result_mode`, `replace_section_start` |
| POST | `/suno/persona` | `name`, `audio_id`, `vox_audio_id`, `vocal_start`, `vocal_end`, `description` |
| GET | `/suno/persona` | See OpenAPI |
| DELETE | `/suno/persona` | See OpenAPI |
| POST | `/suno/mp4` | `audio_id` |
| POST | `/suno/voices` | `audio_url`, `name`, `description` |
| POST | `/suno/timing` | `audio_id` |
| POST | `/suno/vox` | `audio_id`, `vocal_start`, `vocal_end`, `callback_url`, `async` |
| POST | `/suno/wav` | `audio_id`, `callback_url`, `async` |
| POST | `/suno/midi` | `audio_id`, `callback_url`, `async` |
| POST | `/suno/mp3` | `audio_id`, `callback_url`, `async` |
| POST | `/suno/style` | `prompt` |
| POST | `/suno/lyrics` | `model`, `prompt` |
| POST | `/suno/mashup-lyrics` | `lyrics_a`, `lyrics_b` |
| POST | `/suno/tasks` | `id`, `ids`, `action` |
| POST | `/suno/upload` | `audio_url`, `mode`, `name`, `callback_url` |

Full schema: [suno.json](openapi/suno.json).

### Guides

- [development_suno_audios.md](guides/development_suno_audios.md)
- [development_suno_lyrics.md](guides/development_suno_lyrics.md)
- [development_suno_mashup_lyrics.md](guides/development_suno_mashup_lyrics.md)
- [development_suno_midi.md](guides/development_suno_midi.md)
- [development_suno_mp3.md](guides/development_suno_mp3.md)
- [development_suno_mp4.md](guides/development_suno_mp4.md)
- [development_suno_persona.md](guides/development_suno_persona.md)
- [development_suno_style.md](guides/development_suno_style.md)
- [development_suno_tasks.md](guides/development_suno_tasks.md)
- [development_suno_timing.md](guides/development_suno_timing.md)
- [development_suno_upload.md](guides/development_suno_upload.md)
- [development_suno_voices.md](guides/development_suno_voices.md)
- [development_suno_vox.md](guides/development_suno_vox.md)
- [development_suno_wav.md](guides/development_suno_wav.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
