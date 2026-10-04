<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Minimax

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/minimax/videos` | `model`, `content`, `resolution`, `duration`, `ratio`, `callback_url`, `async` |
| POST | `/minimax/tasks` | `action`, `id`, `ids`, `limit`, `offset`, `created_at_min`, `created_at_max` |

Full schema: [minimax.json](openapi/minimax.json).

### Guides

- [development_minimax_tasks.md](guides/development_minimax_tasks.md)
- [development_minimax_videos.md](guides/development_minimax_videos.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
