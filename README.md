# AceDataCloud Agent Skills

<p align="center">
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent_Skills-agentskills.io-blue" alt="Agent Skills"></a>
  <a href="https://platform.acedata.cloud"><img src="https://img.shields.io/badge/API-platform.acedata.cloud-green" alt="Platform"></a>
  <a href="https://www.npmjs.com/package/acedatacloud-skills"><img src="https://img.shields.io/npm/v/acedatacloud-skills.svg" alt="npm"></a>
  <a href="https://github.com/AceDataCloud/Skills/actions"><img src="https://github.com/AceDataCloud/Skills/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-orange" alt="License"></a>
</p>

[Agent Skills](https://agentskills.io/) for [AceDataCloud](https://platform.acedata.cloud) AI services — music, image, video generation, LLM chat, web search, and more.

Compatible with **15+ AI coding agents**: Claude Code, GitHub Copilot, Gemini CLI, OpenAI Codex, OpenHands, Roo Code, TRAE, Goose, Mistral Vibe, and all [agentskills.io](https://agentskills.io/)-compatible tools.

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

## Quick Install (npm)

```bash
# Install globally
npm install -g acedatacloud-skills

# Copy all skills into your project
acedatacloud-skills install                          # → .agents/skills/ (universal)
acedatacloud-skills install --target .claude/skills  # → .claude/skills/ (Claude Code)
acedatacloud-skills install --target .github/skills  # → .github/skills/ (GitHub Copilot)

# Or use npx without installing
npx acedatacloud-skills install
```

## Usage by Platform

### Claude Code

**Option A: Plugin Marketplace (recommended)**

```bash
# Add the marketplace source
/plugin marketplace add AceDataCloud/Skills

# Install skill bundles
/plugin install acedatacloud-ai-media@acedatacloud-skills    # 13 media skills
/plugin install acedatacloud-ai-tools@acedatacloud-skills     # 5 tool skills
```

After installation, Claude Code automatically loads relevant skills when you ask about music/image/video generation, search, etc.

**Option B: Add skills directory directly**

```bash
# Clone the repo
git clone https://github.com/AceDataCloud/Skills.git

# Add all skills at once
claude --add-dir ./Skills/skills

# Or add specific skills
claude --add-dir ./Skills/skills/suno-music
claude --add-dir ./Skills/skills/midjourney-image
```

**Option C: Copy into your project**

```bash
# Copy skills into your project's .claude/skills/ directory
mkdir -p .claude/skills
cp -r Skills/skills/* .claude/skills/
```

Then Claude Code auto-discovers them when working in that project.

### GitHub Copilot (VS Code)

Copy skills into your project under `.github/skills/` or `.agents/skills/`:

```bash
# Option 1: .github/skills/ (GitHub Copilot native path)
mkdir -p .github/skills
cp -r Skills/skills/* .github/skills/

# Option 2: .agents/skills/ (agentskills.io standard path)
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

GitHub Copilot in VS Code will auto-discover skills on file save and use them when relevant.

### Gemini CLI

Gemini CLI supports the agentskills.io format via `.agents/skills/`:

```bash
# Copy into your project
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/

# Or point Gemini CLI to the skills directory
gemini --add-dir ./Skills/skills
```

### OpenAI Codex

Codex supports the agentskills.io standard via `.agents/skills/` and `AGENTS.md`:

```bash
# Copy skills into your project
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/

# AGENTS.md is already included in this repo for Codex discovery
cp Skills/AGENTS.md .
```

Codex auto-discovers skills from `.agents/skills/` and reads `AGENTS.md` for context.

### OpenHands / OpenDevin

```bash
# Copy skills into your workspace
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

OpenHands auto-discovers `SKILL.md` files in `.agents/skills/`.

### Roo Code

```bash
# Roo Code uses the agentskills.io standard path
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

### TRAE (ByteDance)

```bash
# TRAE supports .agents/skills/ directory
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

### Goose (Block)

```bash
# Goose follows the agentskills.io standard
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

### Cursor

Cursor supports skills via the `.cursor/rules/` directory:

```bash
# Copy skills into your project
mkdir -p .cursor/rules
cp -r Skills/skills/*/*.md .cursor/rules/
```

Alternatively, Cursor can use `.agents/skills/` with newer versions.

### Windsurf

```bash
# Windsurf uses the agentskills.io standard
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

### Cline

Cline supports custom instructions and can load skills from `.agents/skills/`:

```bash
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

Or add skills directly in Cline's settings:

1. Open Cline sidebar → Settings → Custom Instructions
2. Paste the content from any `SKILL.md` file
3. Cline will use the skill context in conversations

### Continue.dev

```bash
# Continue supports the agentskills.io standard
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

Or configure in `.continue/config.yaml`:

```yaml
docs:
  - title: "AceDataCloud Skills"
    startUrl: "https://github.com/AceDataCloud/Skills"
```

### Amazon Q Developer

```bash
# Copy skills to your project
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

Amazon Q Developer can reference skills from the workspace context.

### Zed

Zed AI assistant can use context from workspace files:

```bash
mkdir -p .agents/skills
cp -r Skills/skills/* .agents/skills/
```

Skills are automatically picked up as workspace context.

### Any agentskills.io-compatible Agent

The universal pattern works with all compatible agents:

```bash
git clone https://github.com/AceDataCloud/Skills.git
# Then point your agent to ./Skills/skills/
```

## Pairing Skills with MCP Servers

Skills provide **knowledge** (when to use, parameters, gotchas). MCP servers provide **tools** (executable functions the agent can call). Together they give the best experience.

| Skill | MCP Server | Install | Hosted Endpoint |
|-------|-----------|---------|-----------------|
| suno-music | [mcp-suno](https://pypi.org/project/mcp-suno/) | `pip install mcp-suno` | `https://suno.mcp.acedata.cloud/mcp` |
| midjourney-image | [mcp-midjourney](https://pypi.org/project/mcp-midjourney/) | `pip install mcp-midjourney` | `https://midjourney.mcp.acedata.cloud/mcp` |
| google-search | [mcp-serp](https://pypi.org/project/mcp-serp/) | `pip install mcp-serp` | `https://serp.mcp.acedata.cloud/mcp` |
| flux-image | [mcp-flux](https://pypi.org/project/mcp-flux/) | `pip install mcp-flux` | `https://flux.mcp.acedata.cloud/mcp` |
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
