<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Veo Video Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/veo/videos` | `model`, `resolution`, `action`, `prompt`, `video_id`, `translation`, `aspect_ratio`, `image_urls`, `callback_url`, `async` |
| POST | `/veo/tasks` | `id`, `ids`, `action`, `trace_id`, `trace_ids`, `offset`, `limit`, `type`, `created_at_min`, `created_at_max` |

Full schema: [veo.json](openapi/veo.json).

### Guides

- [development_veo_tasks.md](guides/development_veo_tasks.md)
- [development_veo_videos.md](guides/development_veo_videos.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
