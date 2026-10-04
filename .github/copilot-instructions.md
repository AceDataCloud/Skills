# Copilot Instructions for Skills

## Sync from Docs

When working on a sync task (issue labeled `auto-sync`), follow these rules:

1. **Source of truth** — Clone/checkout `AceDataCloud/Docs` and read the relevant OpenAPI specs in `openapi/` and MCP guides in `mcp/`.
2. **Compare skills** — Each skill in `skills/` should accurately reflect the API capabilities described in the Docs.
3. **Update SKILL.md** — When API endpoints, parameters, or models change, update the corresponding `skills/<name>/SKILL.md` to reflect the new capabilities.
4. **New services** — If a new service appears in Docs that doesn't have a skill yet, consider creating one based on `template/SKILL.md`.
5. **PR title** — Use format: `sync: <description> [auto-sync]`
6. **No changes needed** — If everything is already in sync, close the issue with a comment.

## Project Structure

```
skills/
  _shared/                 — Shared reference files (auth, async tasks, MCP servers)
  suno-music/SKILL.md
  luma-video/SKILL.md
  flux-image/SKILL.md
  ...                      — 19 skill definitions
.agents/skills -> ../skills  — Symlink (do NOT create files here)
.github/skills -> ../skills  — Symlink (do NOT create files here)
template/SKILL.md            — Template for new skills
```

## Important

- `.agents/skills/` and `.github/skills/` are **symlinks** to `skills/`. Do NOT modify files via these paths — always edit in `skills/` directly.
- Each SKILL.md references shared content via `../_shared/authentication.md`, `../_shared/async-tasks.md`, and `../_shared/mcp-servers.md`. When adding a new skill, use these references instead of duplicating auth/polling/MCP sections.
- `skills/_shared/` contains reference material, not skills — it has no SKILL.md and should be skipped by validation.
