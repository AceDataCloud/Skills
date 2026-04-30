# AceDataCloud Agent Skills

This repository contains Agent Skills for [AceDataCloud](https://platform.acedata.cloud) AI services.

## Available Skills

Skills are located in the `skills/` directory (also mirrored to `.agents/skills/` and `.github/skills/`).

### AI Music & Audio
- **suno-music** — Generate AI music, lyrics, covers, and vocal extraction with Suno
- **producer-music** — Generate music, covers, extend tracks, swap vocals with Producer
- **fish-audio** — Text-to-speech and voice synthesis with Fish Audio

### AI Image Generation
- **midjourney-image** — Generate, edit, blend, describe, and upscale images with Midjourney
- **flux-image** — Generate and edit images with Flux (Black Forest Labs)
- **seedream-image** — Generate and edit images with ByteDance Seedream
- **nano-banana-image** — Generate and edit images with Google Gemini (NanoBanana)

### AI Video Generation
- **luma-video** — Generate videos with Luma Dream Machine
- **sora-video** — Generate videos with OpenAI Sora
- **veo-video** — Generate videos with Google Veo (native audio)
- **kling-video** — Generate videos with Kuaishou Kling (motion control)
- **hailuo-video** — Generate videos with Hailuo / MiniMax
- **seedance-video** — Generate dance/motion videos with ByteDance Seedance
- **wan-video** — Generate videos with Alibaba Wan

### AI Chat & Tools
- **ai-chat** — Unified LLM gateway — GPT, Claude, Gemini, DeepSeek, Grok (50+ models)
- **google-search** — Search the web, images, news, maps, places, and videos via Google
- **face-transform** — Face analysis, beautification, age/gender transform, swap, cartoon
- **short-url** — Create and manage short URLs
- **acedatacloud-api** — API usage guide — authentication, SDKs, error handling
- **validate-nano** — Production validation suite for Nano Banana generation/edit callback flows

## Authentication

All skills require an API token:

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

Get your token at [platform.acedata.cloud](https://platform.acedata.cloud).

## Paired MCP Servers

Each skill has a corresponding MCP server for tool-use capabilities. See the main [README](README.md) for the full mapping.
