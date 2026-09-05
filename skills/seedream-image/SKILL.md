---
name: seedream-image
description: Generate, edit, stream, or decompose images with Seedream 5.0 via AceDataCloud. Use for text-to-image, reference-image editing, related image sets, transparent-background edits, or editable layer extraction.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires ACEDATACLOUD_API_TOKEN (see ../_shared/authentication.md). Optionally pair with mcp-seedream-pro or seedream-cli.
---

# Seedream Image

Use `POST https://api.acedata.cloud/seedream/images`. Authenticate with `Authorization: Bearer $ACEDATACLOUD_API_TOKEN` and JSON request bodies.

## Pick the model from the requested capability

| Capability | Seedream 5.0 Pro | Seedream 5.0 Lite |
|---|---|---|
| Model ID | `doubao-seedream-5-0-pro-260628` | `doubao-seedream-5-0-260128` (alias: `doubao-seedream-5-0-lite-260128`) |
| Generate/edit one image | Yes | Yes |
| Reference images | Up to 10 | Up to 14 |
| Related image set | No | Yes; input + output ≤ 15 |
| Streaming / web search | No | Yes |
| Layer decomposition / transparent background | Yes | No |
| Prompt optimization | `standard`, `fast` | `standard` |
| Preset sizes | `1K`, `1.5K`, `2K` | `2K`, `3K`, `4K` |

Seedream 4.5 and 4.0 remain available for compatibility. Do not send a parameter to a model that does not support it.

## Generate or edit

```bash
curl https://api.acedata.cloud/seedream/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "a four-panel storyboard of a courier crossing a rainy neon city",
    "size": "2K",
    "sequential_image_generation": "auto",
    "sequential_image_generation_options": {"max_images": 4},
    "watermark": false
  }'
```

For editing, add `image` as one URL/Base64 string or an array. `response_format` is `url` or `b64_json`; 5.0 Pro/Lite also support `output_format` as `jpeg` or `png`. Explicit dimensions use `WIDTHxHEIGHT` and must satisfy the selected model's pixel and aspect-ratio limits.

Use Lite web search only when current information matters:

```json
{"tools": [{"type": "web_search"}]}
```

## Transparent-background Pro edit

Use one transparent PNG input and PNG output:

```json
{
  "model": "doubao-seedream-5-0-pro-260628",
  "prompt": "replace the parrot with a peacock",
  "image": "https://example.com/layer.png",
  "background": "transparent",
  "output_format": "png",
  "size": "1.5K"
}
```

Do not combine `background` with layer decomposition. `transparent` with JPEG is invalid.

## Decompose an image into editable layers

`layer_decomposition` is Pro-only and requires exactly one PNG/JPEG. Omit `prompt` for automatic decomposition, describe desired elements in natural language, or use normalized `<bbox>` coordinates.

```bash
curl https://api.acedata.cloud/seedream/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-5-0-pro-260628",
    "image": "https://example.com/poster.png",
    "layer_decomposition": true,
    "size": "auto",
    "watermark": false
  }'
```

The response contains one base image (`z_index: 0`) and up to 16 transparent PNG layers. Each layer can include `name`, `description`, and `bounding_box.absolute`/`normalized`. To recompose, scale each layer to its bounding-box width and height, place it at left/top, and draw in ascending `z_index`. Any layer failure fails the whole decomposition.

## Async tasks

Generation can take time. Prefer `"async": true`; the response returns `task_id`. Poll using:

```json
POST /seedream/tasks
{"action": "retrieve", "id": "<task_id>"}
```

Follow [async task polling](../_shared/async-tasks.md). Use `callback_url` only when a real public webhook exists. Do not use a health endpoint as a fake callback.

## Streaming

Lite/4.x support streaming. Send `"stream": true` with `Accept: application/x-ndjson`; read one normalized JSON event per line until `image_generation.completed`. Do not combine streaming with `async` or `callback_url`.

- `image_generation.partial_succeeded`: one generated image
- `image_generation.partial_failed`: one failed item; other Lite images may still succeed
- `image_generation.completed`: final usage and the only billing completion

## Agent tools

- MCP: `pip install mcp-seedream-pro`; use `seedream_generate_image`, `seedream_edit_image`, `seedream_decompose_image`, then poll with `seedream_get_task`.
- CLI: `pip install seedream-cli`; use `seedream generate`, `seedream edit`, `seedream decompose`, or `seedream generate --stream --json`.
- Hosted MCP: `https://seedream.mcp.acedata.cloud/mcp`.

MCP image tools are asynchronous, so use REST or CLI for real-time streaming.

## Result and billing safeguards

- URL results expire; persist files promptly.
- Lite `data[]` may mix successful images and per-item `error` objects. Count only successful images.
- Pro layer items are billed individually by actual output size; the base and every successful layer count separately.
- Preserve `z_index`, bounding boxes, item errors, `tools`, and `usage`; do not flatten the response to a URL list.
- Never estimate final billed cost from requested size alone. Use the returned `cost`/usage and the live pricing page: https://platform.acedata.cloud/services/seedream?tab=pricing.
