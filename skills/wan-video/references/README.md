<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Wan

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/wan/tasks` | `id`, `ids`, `action` |
| POST | `/wan/videos` | `audio`, `prompt_extend`, `action`, `resolution`, `shot_type`, `duration`, `prompt`, `negative_prompt`, `size`, `audio_url`, `reference_video_urls`, `model`, `callback_url`, `async`, `image_url`, `media`, `ratio`, `seed`, `watermark` |

Full schema: [wan.json](openapi/wan.json).

### Guides

- [development_wan_tasks.md](guides/development_wan_tasks.md)
- [development_wan_videos.md](guides/development_wan_videos.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
