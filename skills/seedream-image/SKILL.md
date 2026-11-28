---
name: seedream-image
description: Generate, edit, stream, or decompose images with Seedream 5.5 or 5.0 via AceDataCloud. Use for text-to-image, reference-image editing, related image sets, transparent-background edits, or editable layer extraction.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.1"
compatibility: Requires ACEDATACLOUD_API_TOKEN (get an API key at https://platform.acedata.cloud/console/applications). Optionally pair with mcp-seedream-pro or seedream-cli.
---

# Seedream Image

Use `POST https://api.acedata.cloud/seedream/images`. Authenticate with `Authorization: Bearer $ACEDATACLOUD_API_TOKEN` and JSON request bodies.

## First-time setup

1. Install the official Skill with `clawhub install @acedatacloud/seedream`. Check that the ClawHub publisher is **@acedatacloud**.
2. Sign in to [Applications](https://platform.acedata.cloud/console/applications) and open **General Application**. If it is missing, choose **Initialize General Application**. Click the copy button marked **1** next to **API KEY**. Store the raw key in the agent process’s `ACEDATACLOUD_API_TOKEN` environment variable. Check Seedream access, balance, and current pricing.

   ![Copy button 1 beside the General Application API key](https://raw.githubusercontent.com/AceDataCloud/NanoBananaDify/2522b2f57210597af2db866445319334a1677a23/_assets/tutorial/get-api-key-en.png)

3. If you enable **Allowed APIs** restrictions, include `/seedream/images` and `/seedream/tasks`. Advanced workflows below may call additional routes.
4. On the OpenClaw Gateway host, put `ACEDATACLOUD_API_TOKEN=your_api_key_here` in `~/.openclaw/.env`, then restart the Gateway and start a new session. For a direct terminal test, run `export ACEDATACLOUD_API_TOKEN="your_api_key_here"` in that shell. Never put the key in a prompt or commit an `.env` file.
5. Follow the **Generate or edit** example below. If this workflow returns a task ID, query that same task until it finishes; do not submit the same billable request again just to check progress.

[Illustrated key setup, first run, and troubleshooting](https://github.com/AceDataCloud/Skills#first-run-with-clawhub-and-openclaw) · [Token details](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md)

## Pick the model from the requested capability

| Model | Use for |
|---|---|
| `doubao-seedream-5-5-261028` | Multi-turn editing, native transparent PNG, up to 99 editable layers and optional OCR |
| `doubao-seedream-5-0-flash-260915` | Fast single-image generation and editing, up to 16 editable layers |
| `doubao-seedream-5-0-pro-260628` | Precise editing, up to 16 editable layers, fast prompt optimization |
| `doubao-seedream-5-0-lite-260128` | Related image sets, streaming and web search |

5.5, 5.0 Flash and 5.0 Pro accept up to 10 references and support `1K`, `1.5K` and `2K`. Use 5.0 Lite for grouped generation. Its supported presets are `2K`, `3K` and `4K`. Seedream 4.5 and 4.0 remain available for compatibility.

## Generate or edit

```bash
curl https://api.acedata.cloud/seedream/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-5-0-lite-260128",
    "prompt": "a four-panel storyboard of a courier crossing a rainy neon city",
    "size": "2K",
    "sequential_image_generation": "auto",
    "sequential_image_generation_options": {"max_images": 4},
    "watermark": false
  }'
```

For editing, add `image` as one URL/Base64 string or an array. `response_format` is `url` or `b64_json`; 5.5 and 5.0 Pro/Flash/Lite support `output_format` as `jpeg` or `png`. Explicit dimensions use `WIDTHxHEIGHT` and must satisfy the selected model's pixel and aspect-ratio limits.

Use Lite web search only when current information matters:

```json
{"tools": [{"type": "web_search"}]}
```

## Generate or edit with a transparent background

For text-to-image with Seedream 5.5, set `background: "transparent"` and use PNG. Seedream 5.0 Pro and Flash support transparent output when editing one reference with an alpha channel:

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

`layer_decomposition` is supported by 5.5, 5.0 Flash and 5.0 Pro and requires one PNG/JPEG. Omit `prompt` for automatic decomposition, describe desired elements in natural language, or use normalized `<bbox>` coordinates.

```bash
curl https://api.acedata.cloud/seedream/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seedream-5-5-261028",
    "image": "https://example.com/poster.png",
    "layer_decomposition": true,
    "layer_decomposition_options": {"max_images": 12, "text_recognition": true},
    "size": "auto",
    "watermark": false
  }'
```

The response contains one base image (`z_index: 0`) and the generated transparent PNG layers. 5.5 supports up to 99 layers and returns recognized styled text in `data[].text_recognition` when requested. 5.0 Pro and Flash support up to 16 layers. Each layer can include `name`, `description`, and `bounding_box.absolute`/`normalized`. To recompose, scale each layer to its bounding-box width and height, place it at left/top, and draw in ascending `z_index`. Any layer failure fails the whole decomposition.

## Async tasks

Generation can take time. Prefer `"async": true`; the response returns `task_id`. Poll using:

```json
POST /seedream/tasks
{"action": "retrieve", "id": "<task_id>"}
```

Follow [async task polling](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md). Use `callback_url` only when a real public webhook exists. Do not use a health endpoint as a fake callback.

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
- The base and each layer count as outputs. 5.5 charges for each reference image and each output by its pixel tier. 5.0 Flash charges a flat rate per successful output and includes reference images.
- Preserve `z_index`, bounding boxes, item errors, `tools`, and `usage`; do not flatten the response to a URL list.
- Never estimate final billed cost from requested size alone. Use the returned `cost`/usage and the live pricing page: https://platform.acedata.cloud/services/seedream?tab=pricing.
