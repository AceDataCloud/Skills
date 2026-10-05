# MCP Server Integration

Each AceDataCloud service has a corresponding MCP server that provides tool-use capabilities for AI agents. Skills provide **knowledge** (when to use, parameters, gotchas); MCP servers provide **tools** (executable functions).

## Available Servers

| Skill | Package | Hosted Endpoint |
|-------|---------|-----------------|
| suno-music | `pip install mcp-suno` | `https://suno.mcp.acedata.cloud/mcp` |
| producer-music | — | — |
| google-search | `pip install mcp-serp` | `https://serp.mcp.acedata.cloud/mcp` |
| flux-image | `pip install mcp-flux-pro` | `https://flux.mcp.acedata.cloud/mcp` |
| luma-video | `pip install mcp-luma` | `https://luma.mcp.acedata.cloud/mcp` |
| sora-video | `pip install mcp-sora` | `https://sora.mcp.acedata.cloud/mcp` |
| veo-video | `pip install mcp-veo` | `https://veo.mcp.acedata.cloud/mcp` |
| seedream-image | `pip install mcp-seedream` | `https://seedream.mcp.acedata.cloud/mcp` |
| seedance-video | `pip install mcp-seedance` | `https://seedance.mcp.acedata.cloud/mcp` |
| happyhorse-video | `pip install mcp-happyhorse` | `https://happyhorse.mcp.acedata.cloud/mcp` |
| maestro-video | `pip install mcp-maestro` | `https://maestro.mcp.acedata.cloud/mcp` |
| nano-banana-image | `pip install mcp-nano-banana` | `https://nanobanana.mcp.acedata.cloud/mcp` |
| short-url | `pip install mcp-shorturl` | `https://short-url.mcp.acedata.cloud/mcp` |
| wan-video | `pip install mcp-wan` | `https://wan.mcp.acedata.cloud/mcp` |
| acedatacloud | `pip install mcp-acedatacloud` | `https://mcp.acedata.cloud/mcp` |
| minimax-video | `pip install mcp-minimax` | `https://minimax.mcp.acedata.cloud/mcp` |

## Hosted MCP setup

Merge the service entry into the client's existing configuration; do not replace other services or settings. Never commit tokens. For the environment-variable examples below, set `ACEDATACLOUD_API_TOKEN` privately and start the client from that same terminal; a new terminal or desktop-launched client must also receive the variable.

### Claude Code

Merge into the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "suno": {
      "type": "http",
      "url": "https://suno.mcp.acedata.cloud/mcp",
      "headers": {
        "Authorization": "Bearer ${ACEDATACLOUD_API_TOKEN}"
      }
    }
  }
}
```

Review and approve the project service when prompted. In the Claude Code session, run `/mcp` and verify both connection and loaded tools; saving configuration alone is not proof of connectivity.

### Amp

Merge into `.amp/settings.json` for the project or `~/.config/amp/settings.json` for the current user. Amp uses `amp.mcpServers`, not `mcpServers`:

```json
{
  "amp.mcpServers": {
    "suno": {
      "url": "https://suno.mcp.acedata.cloud/mcp",
      "headers": {
        "Authorization": "Bearer ${ACEDATACLOUD_API_TOKEN}"
      }
    }
  }
}
```

Run `amp mcp doctor` to check connection and tools. If the reviewed project service shows `awaiting approval`, run `amp mcp approve suno`, then check again. Replace `suno` with the configured service ID when using a different service.
