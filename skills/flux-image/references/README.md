<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Flux

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/flux/images` | `size`, `count`, `model`, `action`, `prompt`, `image_url`, `callback_url`, `async` |
| POST | `/flux/tasks` | `id`, `ids`, `action` |
| POST | `/flux/videos` | `action`, `prompt`, `aspect_ratio`, `duration`, `resolution`, `version`, `generate_audio`, `safety_tolerance`, `draft`, `mode`, `async`, `callback_url`, `model`, `keyframes`, `start_video`, `draft_task_id` |

Full schema: [flux.json](openapi/flux.json).

### Guides

- [development_flux_generate_video.md](guides/development_flux_generate_video.md)
- [development_flux_images.md](guides/development_flux_images.md)
- [development_flux_tasks.md](guides/development_flux_tasks.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
