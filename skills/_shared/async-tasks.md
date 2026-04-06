# Async Task Polling

Most generation APIs (images, video, music) are asynchronous — they return a `task_id` immediately, and you poll for the result.

## Pattern

**Step 1:** Submit with `callback_url` to force async mode and get a `task_id` immediately.

```bash
curl -X POST https://api.acedata.cloud/<service>/<resource> \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "...", "callback_url": "https://api.acedata.cloud/health"}'
```

Using `"callback_url": "https://api.acedata.cloud/health"` as a placeholder forces async mode even without a real webhook endpoint.

**Step 2:** Poll the task endpoint every 3-5 seconds until the status is terminal.

```bash
curl -X POST https://api.acedata.cloud/<service>/tasks \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "<task_id from step 1>"}'
```

## Important Notes

- Always use `callback_url` to avoid long-running HTTP connections that time out
- Poll every 3-5 seconds for music, every 5 seconds for images/video
- Terminal states vary by service (e.g., `succeeded`, `succeed`, `completed`, `failed`) — check each skill's Gotchas section
- Some services use `id` instead of `task_id` in the poll request (e.g., Veo, Seedream, NanoBanana)
