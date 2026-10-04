<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## ByteDance Seedream Image Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/seedream/images` | `model`, `prompt`, `image`, `size`, `sequential_image_generation`, `sequential_image_generation_options`, `stream`, `response_format`, `watermark`, `output_format`, `tools`, `optimize_prompt_options`, `callback_url`, `async`, `layer_decomposition`, `background` |
| POST | `/seedream/tasks` | `id`, `ids`, `action` |

Full schema: [seedream.json](openapi/seedream.json).

### Guides

- [development_seedream_images.md](guides/development_seedream_images.md)
- [development_seedream_tasks.md](guides/development_seedream_tasks.md)

Source: [PlatformBackend@bdae773e02f3](https://github.com/AceDataCloud/PlatformBackend/tree/bdae773e02f3f51d2896eef497b569748577b753).
