<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Qwen Image

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/qwen-image/images` | `model`, `prompt`, `image_urls`, `n`, `size`, `prompt_extend`, `prompt_extend_mode`, `enable_thinking`, `negative_prompt`, `seed`, `watermark`, `callback_url`, `async` |
| POST | `/qwen-image/tasks` | `id`, `ids`, `action` |

Full schema: [qwen-image.json](openapi/qwen-image.json).

### Guides

- [development_qwen_image_images.md](guides/development_qwen_image_images.md)
- [development_qwen_image_tasks.md](guides/development_qwen_image_tasks.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
