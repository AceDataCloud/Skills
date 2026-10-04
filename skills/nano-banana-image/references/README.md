<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Nano Banana Image Generation

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/nano-banana/images` | `action`, `model`, `prompt`, `image_urls`, `count`, `aspect_ratio`, `resolution`, `callback_url`, `async` |
| POST | `/nano-banana/tasks` | `id`, `ids`, `action` |

Full schema: [nano-banana.json](openapi/nano-banana.json).

### Guides

- [development_nanobanana_images.md](guides/development_nanobanana_images.md)
- [development_nanobanana_tasks.md](guides/development_nanobanana_tasks.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
