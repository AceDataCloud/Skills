<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Fish voice generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/fish/tts` | `text`, `reference_id`, `format`, `sample_rate`, `mp3_bitrate`, `latency`, `chunk_length`, `min_chunk_length`, `temperature`, `top_p`, `repetition_penalty`, `max_new_tokens`, `normalize`, `prosody`, `references`, `callback_url`, `async` |
| POST | `/fish/model` | `title`, `voices`, `description`, `cover_image`, `tags`, `texts`, `enhance_audio_quality`, `generate_sample` |
| GET | `/fish/model` | See OpenAPI |
| GET | `/fish/model/{id}` | See OpenAPI |
| POST | `/fish/tasks` | `id`, `ids`, `action` |

Full schema: [fish.json](openapi/fish.json).

### Guides

- [development_fish_model.md](guides/development_fish_model.md)
- [development_fish_model_get.md](guides/development_fish_model_get.md)
- [development_fish_model_query.md](guides/development_fish_model_query.md)
- [development_fish_tasks.md](guides/development_fish_tasks.md)
- [development_fish_tts.md](guides/development_fish_tts.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
