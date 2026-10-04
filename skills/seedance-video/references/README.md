<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## ByteDance Seedance Video Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/seedance/videos` | `model`, `content`, `resolution`, `ratio`, `duration`, `frames`, `seed`, `camerafixed`, `watermark`, `generate_audio`, `callback_url`, `async`, `return_last_frame`, `execution_expires_after`, `omni_reference_task_type`, `output_format`, `tools`, `priority`, `safety_identifier` |
| POST | `/seedance/tasks` | `id`, `ids`, `action` |

Full schema: [seedance.json](openapi/seedance.json).

### Guides

- [development_seedance_tasks.md](guides/development_seedance_tasks.md)
- [development_seedance_videos.md](guides/development_seedance_videos.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
