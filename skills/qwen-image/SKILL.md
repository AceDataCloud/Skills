---
name: qwen-image
description: Generate and edit images with Qwen Image 3 via Ace Data Cloud. Use for text-to-image, 1-3 reference-image editing, batch output, precise text rendering, or asynchronous image tasks.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN. Optionally pair with mcp-qwen-image.
---

# Qwen Image 3

Use `POST https://api.acedata.cloud/qwen-image/images` for generation and editing.

## Models

| Model | Best for |
|---|---|
| `qwen-image-3.0` | Value, throughput, batch production |
| `qwen-image-3.0-pro` | Complex layouts, small text, fine detail |

## Generate

```bash
curl -X POST https://api.acedata.cloud/qwen-image/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-image-3.0","prompt":"A clean bilingual product poster","size":"1024*1024","n":1}'
```

## Edit with references

```json
{
  "model": "qwen-image-3.0-pro",
  "prompt": "Keep the subject and change the scene to a cinematic city at night",
  "image_urls": ["https://cdn.acedata.cloud/r9vsv9.png"],
  "size": "2048*2048",
  "n": 1,
  "prompt_extend": true,
  "enable_thinking": true,
  "watermark": false
}
```

Use 1–3 reference images. `prompt_extend_mode=agent` is text-to-image only. `n` supports 1–6. Output size uses `WIDTH*HEIGHT`, with pixel area between 512×512 and 2048×2048 and aspect ratio between 1:8 and 8:1.

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `"qwen-image-3.0"`, `"qwen-image-3.0-pro"` | Required model |
| `prompt` | 1–18,000 characters | Required generation or editing instruction |
| `image_urls` | URL array | Optional reference images for editing |
| `n` | 1–6 (default `1`) | Number of images to generate |
| `size` | `WIDTH*HEIGHT` | Output dimensions |
| `prompt_extend` | boolean (default `true`) | Enable prompt expansion |
| `prompt_extend_mode` | `"direct"`, `"agent"` | Prompt expansion mode |
| `enable_thinking` | boolean (default `true`) | Enable model reasoning |
| `negative_prompt` | string | Content to avoid |
| `seed` | 0–2,147,483,647 | Reproducibility seed |
| `watermark` | boolean (default `false`) | Add a watermark |
| `async` | boolean (default `false`) | Return an asynchronous task |
| `callback_url` | URL | Async completion webhook |

## Async tasks

Set `async: true` or provide `callback_url`. Poll the returned task with:

```json
POST /qwen-image/tasks
{"action":"retrieve","id":"TASK_ID"}
```

Use `action: "retrieve_batch"` with `ids` to retrieve multiple tasks. Task retrieval is free. Keep polling every 15 seconds until the response is terminal.

> **MCP:** `pip install mcp-qwen-image` | Hosted: `https://qwen-image.mcp.acedata.cloud/mcp`
