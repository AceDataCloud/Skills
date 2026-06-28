# Unattended Scheduled-Task Confirmation

Write-capable Skill helpers may support unattended scheduled-task execution with
a common `--unattended-confirm` flag. The flag must only bypass the normal
dry-run/confirmation flow when all platform-provided environment checks pass:

- `AICHAT_UNATTENDED_MODE=true`
- `AICHAT_ACTIVE_SKILL` matches the helper's Skill slug
- `AICHAT_ACTIVE_SKILL` is present in `AICHAT_UNATTENDED_ALLOWED_SKILLS`
- `AICHAT_UNATTENDED_EXPIRES_AT`, when present, is still in the future

If any check fails, the helper must return a dry-run style response and must not
perform the write/send/publish/delete action. The current Skills packaging does
not automatically bundle `_shared` files into each Skill, so helpers that need
runtime code should vendor a small guard module in their own `scripts/` folder
until packaging grows shared-runtime support.