<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## HappyHorse Video

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/happyhorse/videos` | `action`, `model`, `prompt`, `image_url`, `image_urls`, `video_url`, `resolution`, `ratio`, `duration`, `watermark`, `audio_setting`, `seed`, `callback_url`, `async` |
| POST | `/happyhorse/tasks` | `id`, `ids`, `action` |

Full schema: [happyhorse.json](openapi/happyhorse.json).

### Guides

- [development_happyhorse_tasks.md](guides/development_happyhorse_tasks.md)
- [development_happyhorse_videos.md](guides/development_happyhorse_videos.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
