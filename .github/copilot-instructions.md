# Copilot Instructions for Skills

## Incremental capability updates

The daily PlatformBackend Claude Code controller owns automatic sync PRs.
For manually requested updates, use the same source and scope:

1. Use the pinned `AceDataCloud/PlatformBackend` commit in the PR: `docs/`,
   OpenAPI and current public catalog visibility are authoritative.
2. Update the relevant `skills/<name>/SKILL.md` procedures and examples.
3. Reuse shared references; do not copy Backend guides or generate parallel
   `platform.generated` reference files.
4. Add a skill only for an explicitly published new capability that needs one.
5. Leave normal validation and review intact; do not close unrelated issues/PRs.

## Project Structure

```
skills/
  _shared/                 — Shared reference files (auth, async tasks, MCP servers)
  suno-music/SKILL.md
  luma-video/SKILL.md
  flux-image/SKILL.md
  ...                      — See the current catalog in README.md
.agents/skills -> ../skills  — Symlink (do NOT create files here)
.github/skills -> ../skills  — Symlink (do NOT create files here)
template/SKILL.md            — Template for new skills
```

## Important

- `.agents/skills/` and `.github/skills/` are **symlinks** to `skills/`. Do NOT modify files via these paths — always edit in `skills/` directly.
- Each SKILL.md references shared content via `../_shared/authentication.md`, `../_shared/async-tasks.md`, and `../_shared/mcp-servers.md`. When adding a new skill, use these references instead of duplicating auth/polling/MCP sections.
- `skills/_shared/` contains reference material, not skills — it has no SKILL.md and should be skipped by validation.
