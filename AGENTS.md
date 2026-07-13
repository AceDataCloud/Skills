# AceDataCloud Agent Skills

This repository contains Agent Skills for [AceDataCloud](https://platform.acedata.cloud) AI services.

## Available Skills

Skills are located in the `skills/` directory (also mirrored to `.agents/skills/` and `.github/skills/`).

### AI Music & Audio
- **suno-music** — Generate AI music, lyrics, covers, and vocal extraction with Suno
- **producer-music** — Generate music, covers, extend tracks, swap vocals with Producer
- **fish-audio** — Text-to-speech and voice synthesis with Fish Audio

### AI Image Generation
- **flux-image** — Generate and edit images with Flux (Black Forest Labs)
- **seedream-image** — Generate and edit images with ByteDance Seedream
- **nano-banana-image** — Generate and edit images with Google Gemini (NanoBanana)

### AI Video Generation
- **luma-video** — Generate videos with Luma Dream Machine
- **sora-video** — Generate videos with OpenAI Sora
- **veo-video** — Generate videos with Google Veo (native audio)
- **kling-video** — Generate videos with Kuaishou Kling (motion control)
- **hailuo-video** — Generate videos with Hailuo / MiniMax
- **happyhorse-video** — Generate and edit videos with Happy Horse
- **seedance-video** — Generate dance/motion videos with ByteDance Seedance
- **wan-video** — Generate videos with Alibaba Wan
- **maestro-video** — Produce complete videos from a brief with scripting, media, voiceover, editing, captions, and multilingual variants

### AI Chat & Tools
- **ai-chat** — Unified LLM gateway — GPT, Claude, Gemini, Kimi, Grok (50+ models)
- **google-search** — Search the web, images, news, maps, places, and videos via Google
- **tgstat** — Discover and analyze public Telegram channels/groups (BYOC username; no login)
- **face-transform** — Face analysis, beautification, age/gender transform, swap, cartoon
- **short-url** — Create and manage short URLs
- **onepage-pdf** — Convert an HTML page into one tall single-page PDF (local; no API token; needs Python + pymupdf + Chrome/Edge)
- **apple-notes** — Manage Apple Notes on macOS: create, search, read, export, organize notes (macOS-only; local; no API token; drives Notes.app via AppleScript)
- **acedatacloud** — Manage your AceDataCloud account — balance, usage/spend, API keys, services, orders, announcements

## Authentication

All skills require an API token:

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

Get your token at [platform.acedata.cloud](https://platform.acedata.cloud).

## Paired MCP Servers

Each skill has a corresponding MCP server for tool-use capabilities. See the main [README](README.md) for the full mapping.
