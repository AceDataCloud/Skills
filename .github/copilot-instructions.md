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
  suno-music/SKILL.md
  luma-video/SKILL.md
  flux-image/SKILL.md
  ...                    — 18 skill definitions
template/SKILL.md        — Template for new skills
```
