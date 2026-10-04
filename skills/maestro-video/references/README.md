<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Maestro AI Video Studio

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/maestro/videos` | `prompt`, `action`, `ref_task_id`, `file_urls`, `langs`, `aspect`, `duration`, `scenario`, `style`, `voice`, `callback_url` |
| POST | `/maestro/tasks` | `id`, `action`, `limit`, `created_at_min`, `created_at_max` |

Full schema: [maestro.json](openapi/maestro.json).

### Guides

- [development_maestro_tasks.md](guides/development_maestro_tasks.md)
- [development_maestro_videos.md](guides/development_maestro_videos.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
