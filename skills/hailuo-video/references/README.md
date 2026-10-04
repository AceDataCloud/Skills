<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Hailuo Video Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/hailuo/tasks` | `id`, `ids`, `action` |
| POST | `/hailuo/videos` | `model`, `action`, `prompt`, `callback_url`, `async`, `first_image_url` |

Full schema: [hailuo.json](openapi/hailuo.json).

### Guides

- [development_hailuo_tasks.md](guides/development_hailuo_tasks.md)
- [development_hailuo_videos.md](guides/development_hailuo_videos.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
