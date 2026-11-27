---
name: tripo-3d
description: Generate 3D models from text, an image or multiple views through AceDataCloud. Use for importing, texturing or converting a 3D model, checking riggability, rigging a character, retargeting animations and retrieving Tripo tasks.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires curl and an AceDataCloud service API token.
---

# Tripo 3D

Use `https://api.acedata.cloud` with `Authorization: Bearer $ACEDATACLOUD_API_TOKEN` and JSON bodies. A restricted token needs the requested operation and `/tripo/tasks` for polling. [Token setup](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/authentication.md)

## Submit and retrieve

Use `POST /tripo/generations` to create a model. Choose exactly one of `prompt`, `image_url`, or `image_urls`. The following H-series text request costs **2 Ace Credits** on successful delivery. Standard texture is the default and costs 4 for H-series text.

```bash
curl --fail-with-body --silent --show-error https://api.acedata.cloud/tripo/generations \
  -H "Authorization: Bearer ${ACEDATACLOUD_API_TOKEN:?Set your Ace service token}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: ${TRIPO_REQUEST_KEY:?Set one unique key for this operation}" \
  -d '{"prompt":"A wooden chair with four straight legs","texture":"none","async":true}'
```

Generate one unique idempotency key before the first submission. Save the key and request body together. For a retry of the same operation use that same key and body. Save the returned `task_id` as `TASK_ID` as soon as the server acknowledges it.

```bash
curl --fail-with-body --silent --show-error https://api.acedata.cloud/tripo/tasks \
  -H "Authorization: Bearer ${ACEDATACLOUD_API_TOKEN:?Set your Ace service token}" \
  -H 'Content-Type: application/json' \
  -d "{\"id\":\"${TASK_ID:?Use the original task ID}\"}"
```

Query every few seconds until the task record contains `response.success`. On success, read `response.data[0].model_url` and the optional `image_url`; keep `response.data[0].id` for subsequent operations on this user's model. Report `response.error` and the trace ID on failure. For `submission_unknown` keep the original ID for reconciliation. A single missing or inaccessible task returns `{}`.

Requests are synchronous by default and return the result directly at `data[0]`. Either `async: true` or `callback_url` returns the receipt `{"task_id":"<TASK_ID>"}`. The completion callback receives the terminal result. Batch lookup uses `{"action":"retrieve_batch","ids":["<FIRST_ID>","<SECOND_ID>"]}` or `trace_ids`, up to 100. Read `items` in input order; an unavailable task occupies a `null` slot.

[Asynchronous task reference](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/async-tasks.md) · [Ace MCP directory](https://github.com/AceDataCloud/Skills/blob/main/skills/_shared/mcp-servers.md)

## Choose the operation

| User request | JSON body fields |
| --- | --- |
| Generate from text | `/tripo/generations` with `prompt`. For geometry only set `texture: "none"`. |
| Generate from one or several views | Use `image_url` or `image_urls` on `/tripo/generations`. Images must be public HTTPS PNG or JPEG up to 20 MiB each. Supply 2–4 slots in front, left, back, right order, with front plus at least one other image. Use `null` to skip an intermediate view. |
| Import an existing file | `/tripo/models` with `action: "import"` and a publicly accessible HTTPS `model_url` for GLB, GLTF, OBJ, FBX or STL up to 150 MiB. Keep the returned model ID. |
| Change materials | `/tripo/models` with `action: "texture"`, an owned `model_id` or a `model_url`, and optionally a text prompt or reference images. `texture_quality` accepts `fast`, `standard`, `detailed` or `extreme`. |
| Convert a file | `/tripo/models` with `action: "convert"`, the model reference and `format` set to `GLTF`, `FBX`, `USDZ`, `OBJ`, `STL` or `3MF`. Preserve the returned format and container when saving. OBJ is delivered as a ZIP with its materials. |
| Check a character | `/tripo/animations` with `action: "rig_check"` and a `model_id` or `model_url`. Inspect the boolean `data[0].riggable` even when false. |
| Add a skeleton | `/tripo/animations` with `action: "rig"` and a model reference. Use the resulting rigged model ID for motion. |
| Animate a rigged model | `/tripo/animations` with `action: "retarget"`, the owned rigged `model_id` and either `animation: "preset:walk"` or `animations: ["preset:walk","preset:idle"]`. Choose 1–5 compatible presets. The result can be one file with multiple animation tracks. |

To test the integration without using credits, check the [Khronos sample Box](https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Box). Submit this JSON to `POST /tripo/animations`, then query the returned task ID.

```json
{
  "action": "rig_check",
  "model_url": "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Box/glTF-Binary/Box.glb",
  "async": true
}
```

## Estimate Ace Credits

| Generation model | Text, geometry / standard texture | Image or multiview, geometry / standard texture |
| --- | --- | --- |
| H (default `v3.1-20260211`) | 2 / 4 | 4 / 6 |
| `P1-20260311` | 6 / 8 | 8 / 10 |
| `P2-20260801` | 20 / 22 | 20 / 22 |

Texture processing costs 2, 2, 4 or 6 Credits for `fast`, `standard`, `detailed` or `extreme`. Basic and advanced format conversion cost 1 and 2. Rigging costs 5. Retargeting costs 2 per animation preset. Import, rig check and task lookup are free. [Service pricing](https://platform.acedata.cloud/services/tripo) · [API examples](https://github.com/AceDataCloud/APIs/tree/main/tripo)
