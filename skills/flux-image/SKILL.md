---
name: flux-image
description: Generate and edit Flux images and FLUX 3 videos via AceDataCloud API. Use when creating images from text prompts, editing existing images with text instructions, or when high-quality image generation is needed. Supports image models plus text/image/video generation, video editing, upscaling and temporary owned video drafts.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN in .env file (see _shared/authentication.md). Optionally pair with mcp-flux-pro for tool-use.
---

# Flux Image Generation

Generate and edit images through AceDataCloud's Flux API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/flux/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "a cat wearing a space helmet, photorealistic", "model": "flux-dev", "callback_url": "https://api.acedata.cloud/health"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /flux/tasks` with `{"id": "..."}`.

## Models

| Model | Quality | Speed | Sizes | Best For |
|-------|---------|-------|-------|----------|
| `flux-dev` | Good | Fast | 256–1440px | Quick generation (default) |
| `flux-pro` | High | Medium | 256–1440px | Production work |
| `flux-2-klein` | Good | Fastest | 256–1440px | Compact / lowest-latency Flux 2 generation |
| `flux-2-flex` | High | Fast | 256–1440px | Faster high-quality generation |
| `flux-2-pro` | Higher | Medium | 256–1440px | Better prompt following |
| `flux-2-max` | Highest | Slow | 256–1440px | Maximum quality generation |
| `flux-kontext-pro` | High | Medium | Aspect ratios | Image editing |
| `flux-kontext-max` | Highest | Slow | Aspect ratios | Complex editing |

## Generate Images

```json
POST /flux/images
{
  "prompt": "a minimalist logo of a mountain",
  "action": "generate",
  "model": "flux-2-pro",
  "size": "1024x1024",
  "count": 1
}
```

### Size Options

**For dev/pro/flux-2** (pixel dimensions):
- `"1024x1024"`, `"1344x768"`, `"768x1344"`, `"1024x576"`, `"576x1024"`

**For kontext** (aspect ratios):
- `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`, `"3:2"`, `"2:3"`, `"21:9"`, `"9:21"`

## Edit Images

Use kontext models for text-guided image editing:

```json
POST /flux/images
{
  "prompt": "change the background to a beach sunset",
  "action": "edit",
  "image_url": "https://example.com/photo.jpg",
  "model": "flux-kontext-pro"
}
```

## Gotchas

- Use pixel dimensions (e.g., `"1024x1024"`) with dev/pro/flux-2 models, aspect ratios (e.g., `"16:9"`) with kontext models
- Editing requires kontext models (`flux-kontext-pro` or `flux-kontext-max`) — other models only support generation
- `count` parameter generates multiple images in one request (increases cost proportionally)
- `flux-2-klein` is the lightest Flux 2 model — useful when latency matters more than peak quality
- `flux-2-max` produces highest quality but is slowest — use dev/klein/flex for iteration and max for final output
- All generation is async — always set `"callback_url"` to get a task id immediately, then poll `/flux/tasks` using `{"id":"<task_id>"}` or `{"ids":[...],"action":"retrieve_batch"}`

> **MCP:** `pip install mcp-flux-pro` | Hosted: `https://flux.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)

## FLUX 3 video tools

`POST /flux/videos` handles all video operations with `action=generate/edit/upscale`. Omitted action defaults to generate. For generation, use `mode=t2v/i2v/v2v/draft_enhance`. T2V needs prompt; I2V also needs keyframes; V2V also needs start_video. Normal video requests support hd/fhd/qhd/uhd, integer duration 5–20 seconds (V2V up to 15) or auto, draft and generate_audio flags. Preserve explicit false.

Draft enhancement uses an owned platform draft_task_id and requires its temporary cache to remain available. It does not promise indefinite retention.

For `action=edit`, send video and prompt to `/flux/videos`; for `action=upscale`, send input_video, optional upscale_factor 1.5–3 and creativity 0/1 to the same endpoint. Do not mix generation fields into editing or upscaling requests. Upscale billing uses actual output MP-seconds (1048576 pixels per MP) with FPS/24 scaling. Do not substitute requested duration for measured final usage.

Companion MCP tools: flux_generate_video, flux_edit_video, flux_upscale_video. CLI commands: flux video, video-edit, video-upscale with --request-file. MCP/CLI requests submit asynchronously by default and are polled through the existing /flux/tasks endpoint. For raw HTTP requests, set async=true to receive a task ID immediately. The unified `flux video --request-file` command accepts all three actions; utility commands/tools supply their matching action automatically.
