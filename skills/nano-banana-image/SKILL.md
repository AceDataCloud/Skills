---
name: nano-banana-image
description: Generate and edit AI images with NanoBanana (Gemini-based) via AceDataCloud API. Use when creating images from text prompts or editing existing images with text instructions. Supports nano-banana, nano-banana-2, and nano-banana-pro models.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
compatibility: Requires ACEDATACLOUD_API_TOKEN environment variable. Optionally pair with mcp-nano-banana for tool-use.
---

# NanoBanana Image Generation

Generate and edit AI images through AceDataCloud's NanoBanana (Gemini-based) API.

> **Setup:** See [authentication](../_shared/authentication.md) for token setup.

## Quick Start

```bash
curl -X POST https://api.acedata.cloud/nano-banana/images \
  -H "Authorization: Bearer $ACEDATACLOUD_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "generate", "prompt": "a watercolor painting of a French countryside village", "model": "nano-banana"}'
```

> **Async:** See [async task polling](../_shared/async-tasks.md). Poll via `POST /nano-banana/tasks` with `{"id": "..."}`.
## Models

| Model | Best For |
|-------|----------|
| `nano-banana` | Standard image generation (default) |
| `nano-banana-2` | Improved quality, second generation |
| `nano-banana-pro` | Highest quality, most detailed output |

## Workflows

### 1. Text-to-Image

```json
POST /nano-banana/images
{
  "action": "generate",
  "prompt": "a photorealistic macro shot of morning dew on a spider web",
  "model": "nano-banana-pro",
  "aspect_ratio": "16:9",
  "resolution": "2K"
}
```

### 2. Image Editing

Edit existing images using natural language instructions — no mask needed. Pass source images via `image_urls`.

```json
POST /nano-banana/images
{
  "action": "edit",
  "prompt": "change the background to a starry night sky",
  "image_urls": ["https://example.com/photo.jpg"],
  "model": "nano-banana"
}
```

## Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `action` | `"generate"`, `"edit"` | Operation mode |
| `model` | `"nano-banana"`, `"nano-banana-2"`, `"nano-banana-pro"` | Model to use |
| `prompt` | string | Image description or editing instruction |
| `image_urls` | array of strings | Source image URLs (required for edit action) |
| `aspect_ratio` | `"1:1"`, `"3:2"`, `"2:3"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"` | Output aspect ratio |
| `resolution` | `"1K"`, `"2K"`, `"4K"` | Output resolution (1K=1024px, 2K=2048px, 4K=4096px) |
| `callback_url` | string | Async callback URL; returns a task ID immediately |

## Gotchas

- Editing does **NOT** require a mask — just describe the change in natural language
- Editing uses the same `/nano-banana/images` endpoint with `action: "edit"` and `image_urls` array (not a separate `/edit` path)
- `nano-banana-2` is the second-generation model; `nano-banana-pro` offers the highest quality
- Task polling uses `id` (not `task_id`) in the `/nano-banana/tasks` request body
- Aspect ratio uses colon notation (e.g., `"16:9"`) not pixel dimensions
- The Gemini-based model excels at understanding complex, conversational editing instructions

> **MCP:** `pip install mcp-nano-banana` | Hosted: `https://nano-banana.mcp.acedata.cloud/mcp` | See [all MCP servers](../_shared/mcp-servers.md)
