---
name: template-skill
description: A template for creating new AceDataCloud Agent Skills. Copy this directory and customize.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# Template Skill

Replace this with your skill instructions.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/<endpoint> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "..."}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /<service>/tasks` with `{"task_id": "..."}`.

## Workflow

1. Step one
2. Step two
3. Step three

## Gotchas

- List non-obvious behaviors here

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
