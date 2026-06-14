# Async Task Polling

Most generation APIs (images, video, music) are asynchronous — they return a `task_id` immediately, and you poll for the result.

## Pattern

**Step 1:** Submit with `async: true` (or `callback_url`) to get a `task_id` immediately.

**Option A — `async: true` (simplest):**

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "async": true}'
```

Set `"async": true` to return a `task_id` immediately without requiring a `callback_url`. Poll the tasks endpoint to retrieve the result.

**Option B — `callback_url` webhook:**

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "callback_url": "https://your-server.com/webhook"}'
```

Using `"callback_url": "https://api.acedata.cloud/health"` as a placeholder also forces async mode even without a real webhook endpoint.

**Step 2:** Poll the task endpoint every 3-5 seconds until the status is terminal.

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"id": "<task_id from step 1>"}'
```

For batch polling, use:

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: ******" \
  -H "Content-Type: application/json" \
  -d '{"action": "retrieve_batch", "ids": ["<task_id_1>", "<task_id_2>"]}'
```

## Important Notes

- Use `async: true` or `callback_url` to avoid long-running HTTP connections that time out
- Poll every 3-5 seconds for music, every 5 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Task polling uses `id` (single) or `ids` (batch). `action` defaults to `retrieve`; set `action: "retrieve_batch"` for `ids`.
