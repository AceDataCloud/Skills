<!-- Generated from PlatformBackend; edit the backend source. -->
# API reference

These are the public HTTP API contracts. Native MCP tools and CLI commands are described in the package README.

## Search Engine

| Method | Endpoint | Request fields |
| --- | --- | --- |
| POST | `/serp/google` | `page`, `type`, `query`, `range`, `number`, `country`, `language`, `image_size` |

Full schema: [serp.json](openapi/serp.json).

### Guides

- [development_serp_google.md](guides/development_serp_google.md)

Source: [PlatformBackend@945664eca88d](https://github.com/AceDataCloud/PlatformBackend/tree/945664eca88d16d21159d3739f874c830c046005).
