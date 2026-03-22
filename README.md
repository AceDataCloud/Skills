# AceDataCloud Agent Skills

[Agent Skills](https://agentskills.io/) for [AceDataCloud](https://platform.acedata.cloud) AI services — music, image, video generation, LLM chat, web search, and more.

Works with **Claude Code**, **GitHub Copilot (VS Code)**, **Gemini CLI**, **OpenHands**, **Roo Code**, **TRAE**, **Goose**, and all [agentskills.io](https://agentskills.io/)-compatible agents.

## Available Skills (18)

### AI Music & Audio

| Skill | Description |
|-------|-------------|
| [suno-music](skills/suno-music/) | Generate AI music, lyrics, covers, and vocal extraction with Suno |
| [producer-music](skills/producer-music/) | Generate music, covers, extend tracks, swap vocals with Producer |
| [fish-audio](skills/fish-audio/) | Text-to-speech and voice synthesis with Fish Audio |

### AI Image Generation

| Skill | Description |
|-------|-------------|
| [midjourney-image](skills/midjourney-image/) | Generate, edit, blend, describe, and upscale images with Midjourney |
| [flux-image](skills/flux-image/) | Generate and edit images with Flux (Black Forest Labs) |
| [seedream-image](skills/seedream-image/) | Generate and edit images with ByteDance Seedream |
| [nano-banana-image](skills/nano-banana-image/) | Generate and edit images with Google Gemini (NanoBanana) |

### AI Video Generation

| Skill | Description |
|-------|-------------|
| [luma-video](skills/luma-video/) | Generate videos with Luma Dream Machine |
| [sora-video](skills/sora-video/) | Generate videos with OpenAI Sora |
| [veo-video](skills/veo-video/) | Generate videos with Google Veo (native audio) |
| [kling-video](skills/kling-video/) | Generate videos with Kuaishou Kling (motion control) |
| [hailuo-video](skills/hailuo-video/) | Generate videos with Hailuo / MiniMax |
| [seedance-video](skills/seedance-video/) | Generate dance/motion videos with ByteDance Seedance |

### AI Chat & Tools

| Skill | Description |
|-------|-------------|
| [ai-chat](skills/ai-chat/) | Unified LLM gateway — GPT, Claude, Gemini, DeepSeek, Grok (50+ models) |
| [google-search](skills/google-search/) | Search the web, images, news, maps, places, and videos via Google |
| [face-transform](skills/face-transform/) | Face analysis, beautification, age/gender transform, swap, cartoon |
| [short-url](skills/short-url/) | Create and manage short URLs |
| [acedatacloud-api](skills/acedatacloud-api/) | API usage guide — authentication, SDKs, error handling |

## Installation

### Claude Code (Plugin Marketplace)

```bash
/plugin marketplace add AceDataCloud/Skills
/plugin install acedatacloud-ai-media@acedatacloud-skills
/plugin install acedatacloud-ai-tools@acedatacloud-skills
```

### Claude Code (Manual)

```bash
claude --add-dir /path/to/Skills/skills
```

### GitHub Copilot / VS Code

Copy the skill folders into your project:

```bash
cp -r skills/* .github/skills/
# or
cp -r skills/* .agents/skills/
```

### Any agentskills.io-compatible agent

Clone and point your agent to the skills directory:

```bash
git clone https://github.com/AceDataCloud/Skills.git
```

## Authentication

All skills require an AceDataCloud API token. Get yours at [platform.acedata.cloud](https://platform.acedata.cloud).

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## MCP Server Integration

Each skill works standalone via direct API calls, but for best results, pair with the corresponding [MCP server](https://platform.acedata.cloud/services) for tool-use capabilities:

| Skill | MCP Server | Install |
|-------|-----------|---------|
| suno-music | [mcp-suno](https://pypi.org/project/mcp-suno/) | `pip install mcp-suno` |
| midjourney-image | [mcp-midjourney](https://pypi.org/project/mcp-midjourney/) | `pip install mcp-midjourney` |
| google-search | [mcp-serp](https://pypi.org/project/mcp-serp/) | `pip install mcp-serp` |
| flux-image | [mcp-flux](https://pypi.org/project/mcp-flux/) | `pip install mcp-flux` |
| luma-video | [mcp-luma](https://pypi.org/project/mcp-luma/) | `pip install mcp-luma` |
| sora-video | [mcp-sora](https://pypi.org/project/mcp-sora/) | `pip install mcp-sora` |
| veo-video | [mcp-veo](https://pypi.org/project/mcp-veo/) | `pip install mcp-veo` |
| seedream-image | [mcp-seedream](https://pypi.org/project/mcp-seedream/) | `pip install mcp-seedream` |
| seedance-video | [mcp-seedance](https://pypi.org/project/mcp-seedance/) | `pip install mcp-seedance` |
| nano-banana-image | [mcp-nano-banana](https://pypi.org/project/mcp-nano-banana/) | `pip install mcp-nano-banana` |
| short-url | [mcp-shorturl](https://pypi.org/project/mcp-shorturl/) | `pip install mcp-shorturl` |

## Contributing

We welcome contributions! To add a new skill:

1. Create a directory under `skills/` matching the skill name
2. Add a `SKILL.md` following the [Agent Skills specification](https://agentskills.io/specification)
3. Optionally add `scripts/`, `references/`, and `examples/` directories
4. Submit a pull request

## License

[Apache-2.0](LICENSE)
