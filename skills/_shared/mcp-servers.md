# MCP Server Integration

Each AceDataCloud service has a corresponding MCP server that provides tool-use capabilities for AI agents. Skills provide **knowledge** (when to use, parameters, gotchas); MCP servers provide **tools** (executable functions).

## Available Servers

| Skill | Package | Hosted Endpoint |
|-------|---------|-----------------|
| suno-music | `pip install mcp-suno` | `https://suno.mcp.acedata.cloud/mcp` |
| producer-music | — | — |
| midjourney-image | `pip install mcp-midjourney` | `https://midjourney.mcp.acedata.cloud/mcp` |
| google-search | `pip install mcp-serp` | `https://serp.mcp.acedata.cloud/mcp` |
| flux-image | Hosted only | `https://flux.mcp.acedata.cloud/mcp` |
| luma-video | `pip install mcp-luma` | `https://luma.mcp.acedata.cloud/mcp` |
| sora-video | `pip install mcp-sora` | `https://sora.mcp.acedata.cloud/mcp` |
| veo-video | `pip install mcp-veo` | `https://veo.mcp.acedata.cloud/mcp` |
| seedream-image | `pip install mcp-seedream` | `https://seedream.mcp.acedata.cloud/mcp` |
| seedance-video | `pip install mcp-seedance` | `https://seedance.mcp.acedata.cloud/mcp` |
| nano-banana-image | `pip install mcp-nano-banana` | `https://nano-banana.mcp.acedata.cloud/mcp` |
| short-url | `pip install mcp-shorturl` | `https://short-url.mcp.acedata.cloud/mcp` |
| wan-video | `pip install mcp-wan` | `https://wan.mcp.acedata.cloud/mcp` |

## Configuration Example

```json
{
  "mcpServers": {
    "suno": {
      "url": "https://suno.mcp.acedata.cloud/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```
