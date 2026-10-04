<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Producer Music Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/producer/upload` | `audio_url` |
| POST | `/producer/videos` | `audio_id` |
| POST | `/producer/wav` | `audio_id` |
| POST | `/producer/audios` | `lyric`, `model`, `title`, `action`, `custom`, `prompt`, `audio_id`, `continue_at`, `callback_url`, `async`, `seed`, `instrumental`, `sound_strength`, `lyrics_strength`, `weirdness`, `replace_section_end`, `replace_section_start` |
| POST | `/producer/tasks` | `id`, `ids`, `action` |
| POST | `/producer/lyrics` | `prompt` |

Full schema: [producer.json](openapi/producer.json).

### Guides

- [development_producer_audios.md](guides/development_producer_audios.md)
- [development_producer_lyrics.md](guides/development_producer_lyrics.md)
- [development_producer_tasks.md](guides/development_producer_tasks.md)
- [development_producer_upload.md](guides/development_producer_upload.md)
- [development_producer_videos.md](guides/development_producer_videos.md)
- [development_producer_wav.md](guides/development_producer_wav.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
