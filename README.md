# AceDataCloud Agent Skills

<p align="center">
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent_Skills-agentskills.io-blue" alt="Agent Skills"></a>
  <a href="https://platform.acedata.cloud"><img src="https://img.shields.io/badge/API-platform.acedata.cloud-green" alt="Platform"></a>
  <a href="https://www.npmjs.com/package/@acedatacloud/skills"><img src="https://img.shields.io/npm/v/@acedatacloud/skills.svg" alt="npm"></a>
  <a href="https://github.com/AceDataCloud/Skills/actions"><img src="https://github.com/AceDataCloud/Skills/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-orange" alt="License"></a>
</p>

[Agent Skills](https://agentskills.io/) for [AceDataCloud](https://platform.acedata.cloud) AI services — music, image, video generation, LLM chat, web search, and more.

Compatible with **30+ AI coding agents** via the [agentskills.io](https://agentskills.io/) open standard: Claude Code, GitHub Copilot, Gemini CLI, OpenAI Codex, Cursor, Roo Code, Goose, and more.

## Available Skills (19)

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

## Prerequisites

Get your API token at [platform.acedata.cloud](https://platform.acedata.cloud):

1. Register an account
2. Browse and subscribe to a service (most have free quota)
3. Create an API credential (token)

```bash
export ACEDATACLOUD_API_TOKEN="your-token-here"
```

## Quick Install

**One command** to install skills into your project — works with all agents:

```bash
# Install all skills (for any agentskills.io-compatible agent)
npx skills add AceDataCloud/Skills --skill '*' --yes

# Install specific skills only
npx skills add AceDataCloud/Skills --skill suno-music --skill midjourney-image --yes
```

The [`skills` CLI](https://github.com/vercel-labs/skills) auto-detects your agent and installs to the correct path.

## Usage by Platform

### Claude Code

**Option A: `skills` CLI (recommended)**

```bash
# Install all skills for Claude Code
npx skills add AceDataCloud/Skills --skill '*' -a claude-code --yes

# Install specific skills
npx skills add AceDataCloud/Skills --skill suno-music -a claude-code --yes
```

Skills are symlinked into `.claude/skills/` and auto-discovered by Claude Code.

**Option B: Plugin Marketplace**

```
/plugin marketplace add AceDataCloud/Skills
/plugin install acedatacloud-ai-media@acedatacloud-skills
/plugin install acedatacloud-ai-tools@acedatacloud-skills
```

**Option C: npm package**

```bash
npx @acedatacloud/skills install --target .claude/skills
```

**Option D: Manual copy**

```bash
git clone https://github.com/AceDataCloud/Skills.git
cp -r Skills/skills/* .claude/skills/
```

### GitHub Copilot

```bash
npx skills add AceDataCloud/Skills --skill '*' -a github-copilot --yes
```

### Gemini CLI

```bash
npx skills add AceDataCloud/Skills --skill '*' -a gemini-cli --yes
```

### OpenAI Codex

```bash
npx skills add AceDataCloud/Skills --skill '*' -a codex --yes
```

### Cursor

```bash
npx skills add AceDataCloud/Skills --skill '*' -a cursor --yes
```

### Roo Code

```bash
npx skills add AceDataCloud/Skills --skill '*' -a roo --yes
```

### Goose

```bash
npx skills add AceDataCloud/Skills --skill '*' -a goose --yes
```

### Windsurf

```bash
npx skills add AceDataCloud/Skills --skill '*' -a windsurf --yes
```

### Cline

```bash
npx skills add AceDataCloud/Skills --skill '*' -a cline --yes
```

### Other Agents

The `skills` CLI supports 40+ agents. Use `npx skills add --help` to see all options, or install to the universal `.agents/skills/` path:

```bash
npx skills add AceDataCloud/Skills --skill '*' --yes
```

## Pairing Skills with MCP Servers

Skills provide **knowledge** (when to use, parameters, gotchas). MCP servers provide **tools** (executable functions the agent can call). Together they give the best experience.

| Skill | MCP Server | Install | Hosted Endpoint |
|-------|-----------|---------|-----------------|
| suno-music | [mcp-suno](https://pypi.org/project/mcp-suno/) | `pip install mcp-suno` | `https://suno.mcp.acedata.cloud/mcp` |
| midjourney-image | [mcp-midjourney](https://pypi.org/project/mcp-midjourney/) | `pip install mcp-midjourney` | `https://midjourney.mcp.acedata.cloud/mcp` |
| google-search | [mcp-serp](https://pypi.org/project/mcp-serp/) | `pip install mcp-serp` | `https://serp.mcp.acedata.cloud/mcp` |
| flux-image | [mcp-flux-pro](https://pypi.org/project/mcp-flux-pro/) | `pip install mcp-flux-pro` | `https://flux.mcp.acedata.cloud/mcp` |
| luma-video | [mcp-luma](https://pypi.org/project/mcp-luma/) | `pip install mcp-luma` | `https://luma.mcp.acedata.cloud/mcp` |
| sora-video | [mcp-sora](https://pypi.org/project/mcp-sora/) | `pip install mcp-sora` | `https://sora.mcp.acedata.cloud/mcp` |
| veo-video | [mcp-veo](https://pypi.org/project/mcp-veo/) | `pip install mcp-veo` | `https://veo.mcp.acedata.cloud/mcp` |
| seedream-image | [mcp-seedream](https://pypi.org/project/mcp-seedream/) | `pip install mcp-seedream` | `https://seedream.mcp.acedata.cloud/mcp` |
| seedance-video | [mcp-seedance](https://pypi.org/project/mcp-seedance/) | `pip install mcp-seedance` | `https://seedance.mcp.acedata.cloud/mcp` |
| nano-banana-image | [mcp-nano-banana](https://pypi.org/project/mcp-nano-banana/) | `pip install mcp-nano-banana` | `https://nano-banana.mcp.acedata.cloud/mcp` |
| short-url | [mcp-shorturl](https://pypi.org/project/mcp-shorturl/) | `pip install mcp-shorturl` | `https://short-url.mcp.acedata.cloud/mcp` |
| wan-video | [mcp-wan](https://pypi.org/project/mcp-wan/) | `pip install mcp-wan` | `https://wan.mcp.acedata.cloud/mcp` |

**Using hosted MCP endpoints** (no local install needed):

```json
{
  "mcpServers": {
    "suno": {
      "url": "https://suno.mcp.acedata.cloud/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

## Quick Example

Ask your AI agent:

> "Generate a lo-fi hip hop track with rain sounds using Suno"

The agent will:
1. Read the `suno-music` skill to understand the API
2. Call the Suno MCP server (if configured) or guide you through the API call
3. Handle task polling until the music is ready
4. Return the audio URL

## Contributing

We welcome contributions! To add a new skill:

1. Create a directory under `skills/` matching the skill name
2. Add a `SKILL.md` following the [Agent Skills specification](https://agentskills.io/specification)
3. Use the [template](template/SKILL.md) as a starting point
4. Reference shared files (`../_shared/authentication.md`, `../_shared/async-tasks.md`, `../_shared/mcp-servers.md`) instead of duplicating common sections
5. Submit a pull request — CI will validate your skill format

**Note:** `.agents/skills/` and `.github/skills/` are symlinks to `skills/` — do not modify files via those paths.

## License

[Apache-2.0](LICENSE)
