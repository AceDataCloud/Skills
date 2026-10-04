<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Luma Video Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/luma/tasks` | `id`, `ids`, `action` |
| POST | `/luma/videos` | `loop`, `action`, `prompt`, `timeout`, `video_id`, `aspect_ratio`, `video_url`, `enhancement`, `callback_url`, `async`, `end_image_url`, `start_image_url` |

Full schema: [luma.json](openapi/luma.json).

### Guides

- [development_luma_tasks.md](guides/development_luma_tasks.md)
- [development_luma_videos.md](guides/development_luma_videos.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
