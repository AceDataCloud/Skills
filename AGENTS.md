# AceDataCloud Agent Skills

The canonical skill files are `skills/<name>/SKILL.md`. Use `README.md`
or the `skills/` directory to find the current catalog; do not maintain a
second skill list here. `.agents/skills/` and `.github/skills/` are
symlinks to `skills/`, so edit the canonical path.

- Keep each skill's description short and specific to when that skill
  should load. Put task procedures and examples in its body or relevant
  supporting files.
- Reuse `skills/_shared/` references for common AceDataCloud API
  authentication, async tasks, and MCP guidance.
- Skills that call AceDataCloud APIs need an AceDataCloud Bearer token.
  Local skills such as `onepage-pdf` and `apple-notes` do not. Follow
  the selected skill's authentication instructions; never commit or
  print tokens.
- When adding or changing a skill, update its own instructions and any
  catalog entry that describes it, then run the applicable checks from
  `.github/workflows/validate.yml`.
