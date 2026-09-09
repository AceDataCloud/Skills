# Async Task Polling

Generation endpoints can take time. Follow the service-specific contract: some endpoints support a native `async: true` flag, some return a task by default, and others can deliver completion to a webhook. Do not assume one switch works for every service.

## Poll a task

When the service returns a task ID, poll its documented task endpoint every 3–5 seconds until the status is terminal.

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id>"}'
```

Use the exact ID field and terminal states documented by the service Skill. Stop after a bounded timeout, and surface terminal failures instead of polling forever.

## Use callbacks only with a real webhook

Set `callback_url` only when the user owns a real public HTTP(S) webhook that can receive completion POSTs. A health endpoint, documentation page, placeholder URL, or URL the user does not control is not a webhook.

Callbacks and polling are independent completion mechanisms. If a request returns a task ID, polling may be sufficient without a callback. If the service documents a native `async: true` flag, prefer that flag for task-based execution and omit `callback_url` unless webhook delivery is also required.

## Rules

- Confirm the selected service supports the requested async mechanism before adding fields.
- Never invent `async`, `callback_url`, or task fields that are absent from the service contract.
- Never use a health endpoint as a fake callback.
- Do not log tokens or include them in callback URLs.
- Treat generation as potentially credit-consuming; review live pricing and obtain explicit user confirmation before the first paid request.
