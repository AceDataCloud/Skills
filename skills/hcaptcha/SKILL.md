---
name: hcaptcha
description: Solve hCaptcha challenges and classify hCaptcha recognition prompts through AceDataCloud. Use for hCaptcha token generation, Enterprise rqdata challenges, image selection recognition, and captcha task polling.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md).
---

# hCaptcha Solver

Solve hCaptcha token challenges through `POST https://api.acedata.cloud/captcha/token/hcaptcha`, or classify hCaptcha recognition prompts through `POST /captcha/recognition/hcaptcha`.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Token API

```bash
curl -X POST https://api.acedata.cloud/captcha/token/hcaptcha \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{
    "website_key": "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2",
    "website_url": "https://accounts.hcaptcha.com/demo",
    "async": true
  }'
```

Use the returned `token` as the `h-captcha-response` value when submitting the target form.

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `website_key` | ✓ | The hCaptcha site key from the target page |
| `website_url` | ✓ | The full URL of the page containing the hCaptcha widget |
| `rqdata` | | Raw `data-rqdata` value for hCaptcha Enterprise challenges; omit for ordinary hCaptcha widgets |
| `proxy` | | Bring-your-own proxy URL, e.g. `scheme://[user:pass@]host:port`; omit to use the platform default proxy |
| `async` | | When `true`, return immediately with a `task_id`; poll `POST /captcha/tasks` to retrieve the token |

## Recognition API

Use `POST /captcha/recognition/hcaptcha` when you already have hCaptcha recognition queries and need the matching box/label solution.

```json
{
  "queries": ["https://cdn.example.com/hcaptcha-tile.png"],
  "question": "Please click the center of the seahorses head",
  "async": false
}
```

The synchronous response includes `solution` plus timing fields. The `solution` object contains fields such as `box`, `label`, and `confidence`.

## Async Mode

Pass `async: true` to either hCaptcha endpoint to return a task id, then poll:

```bash
curl -X POST https://api.acedata.cloud/captcha/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"61138bb6-19aa-11ec-a9c8-0242ac110002"}'
```

Continue polling until `status` is `ready`. Token tasks return `token`; recognition tasks return `solution`.

> **Async:** See [async task polling](../_shared/async-tasks.md) for general polling guidance.

## Gotchas

- Both `website_key` and `website_url` are required for token solving.
- Send `rqdata` only when the target Enterprise widget provides a `data-rqdata` value.
- Use a public URL or proxy endpoint that the solving service can reach.
- Synchronous requests may block while the challenge is solved; use `async: true` for non-blocking flows.

> **MCP:** See [MCP servers](../_shared/mcp-servers.md) for tool-use integration.
