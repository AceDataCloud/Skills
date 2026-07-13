# Xiaohongshu Connector Skill

AceDataCloud adaptation for operating Xiaohongshu through an encrypted BYOC cookie connector. It runs Chromium directly over CDP inside the existing Skill sandbox; no hosted or long-running MCP server is required.

## Provenance

This Skill is rewritten from [`xpzouying/xiaohongshu-mcp`](https://github.com/xpzouying/xiaohongshu-mcp), used by AceDataCloud with permission from its author. The connector-cookie adapter, direct-CDP process isolation, confirmation gates, and Agent Skill integration are AceDataCloud changes.

The browser business modules, workflow structure, split preview/confirmation approach, validation ideas, and operational guidance are adapted from MIT-licensed [`autoclaw-cc/xiaohongshu-skills`](https://github.com/autoclaw-cc/xiaohongshu-skills):

- Business modules: commit `b043748282a57e347c52f517dfb59819121134ab`.
- Hardened direct-CDP runtime: commit `406e0590523f`.
- The upstream MIT license is retained at `scripts/vendor/LICENSE.autoclaw-xiaohongshu-skills`.

No AutoClaw browser extension, local WebSocket bridge, persistent Chrome profile, or hosted MCP server is used.

## Capabilities

- Login status and connected account identity.
- Home recommendations, filtered search, note details and comments, and user profiles.
- Image, video, and formatted text-only long-article publishing.
- Tags, scheduled publishing, visibility, original declaration, templates, and product binding.
- Comments, comment replies, likes/unlikes, and favorites/unfavorites.
- Private messages remain in the Android-only `xhs-dm` Skill.

## Security model

- AuthBackend stores the browser-extension cookie jar encrypted.
- aichat2 injects it as `XIAOHONGSHU_COOKIES` only while this Skill is active.
- The CLI validates domains and converts Chrome-extension cookie fields to CDP `CookieParam` records.
- Cookies are injected through `Storage.setCookies` into an incognito Chromium context instead of being passed through files or command arguments.
- Each command creates a private temporary profile, starts Chromium on a random loopback CDP port, then terminates Chromium and removes the entire profile.
- Chromium receives a minimal child environment that excludes `XIAOHONGSHU_COOKIES`; Cookie values are never placed in process arguments or model-visible output.
- Real account writes dry-run unless the invocation ends with `--confirm`; the Skill instructions require a structured user confirmation before that second invocation.

Xiaohongshu's web "draft box" is stored in the browser profile rather than the connected account. This Skill deliberately destroys its temporary profile after each command, so it uses code-enforced dry-run previews instead of claiming durable Xiaohongshu drafts. Confirmation is an orchestration policy, not a cryptographic authorization boundary.
