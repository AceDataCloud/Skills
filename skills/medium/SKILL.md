---
name: medium
description: Read and publish on Medium (medium.com) with the user's own login cookies (BYOC) — list their posts with clap/response stats, inspect one post, and publish a new story. Use when the user mentions Medium, "my Medium posts", reading their post stats (claps/reads), or publishing a story to Medium.
when_to_use: |
  Trigger for anything on the user's Medium (medium.com) account driven by their
  own login cookie: show who they are, list their posts with clap / response /
  reading-time data, look at one post, or publish a new story. This acts as the
  user's real account, so writes are gated behind an explicit confirmation.
connections: [medium]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# medium — read & publish on Medium via your own cookies

Drives the user's **real** Medium account through the same internal web API the
site uses (Medium retired its public write API in 2023), authenticated by the
login cookie they captured with the ACE extension. No browser, no third-party
deps — just `urllib`.

The connector injects the cookie jar as an env var:

- `MEDIUM_COOKIES` — a JSON array of cookies (`sid`, `uid`, `xsrf`). **Secret —
  never echo or print it.** The CLI echoes the `xsrf` cookie as the
  `x-xsrf-token` header on writes for you. If the captured jar has no `xsrf`
  cookie (common), the CLI mints one automatically before writing, so publishes
  no longer fail with "Missing xsrf token".

## CLI

The skill ships [`scripts/medium.py`](scripts/medium.py) — self-contained, stdlib only.

```sh
MED=$SKILL_DIR/scripts/medium.py
python3 $MED whoami                       # who is logged in
python3 $MED articles --limit 20          # my posts + clap/response stats
python3 $MED article <post-id>            # one post's details
```

## Verify the connection first

```sh
python3 $MED whoami
# → {"user_id": "...", "name": "...", "username": "..."}
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Content is **Markdown** (converted
to Medium paragraph blocks: `#`/`##`→heading, `###`→sub-heading, `>`→quote,
```` ``` ````→code, `-`/`*`→bullet list, `1.`→numbered list, tables→aligned
code block). Inline **bold**, *italic*, `code`, and `[links](url)` render as
real Medium formatting (clickable links included). Bare `https://…` URLs in text
are auto-linked too (URLs inside code spans are left untouched).
Without a trailing `--confirm` it dry-runs. `--confirm` is honored **only as the
last argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
python3 $MED publish --title "Title" --content-file a.md                       # dry-run
python3 $MED publish --title "Title" --content-file a.md --draft-only --confirm   # private draft
python3 $MED publish --title "Title" --content-file a.md --confirm                # PUBLIC story
```

Publishing is Medium's multi-step editor flow (new-story → write deltas →
publish). `--draft-only` stops at the draft (visible only at the user's
`/me/stories/drafts`). Default to `--draft-only` unless the user asked to go live.

## Images

`publish` automatically uploads each external markdown image (`![](url)`) to
Medium and inserts it as a real image block — Medium has no markdown-image
syntax, so this is the only way images render. Pass `--no-rehost-images` to
degrade images to link-only paragraphs. An image that fails to upload falls back
to a link paragraph (never blocks the post).

## Gotchas

- **This is the user's real Medium account.** Confirm before any publish.
- Markdown→Medium conversion covers headings, quotes, fenced code, bullet/
  numbered lists, images, and inline markups (bold/italic/code/links). Medium's
  editor has no table element: a narrow markdown table renders as an aligned
  monospace code block, while a wide one (long cells / URLs, which would wrap into
  an unreadable grid) is rendered as per-row records — the first column bolded as
  a lead-in, the remaining columns as `header: value` bullets.
- Medium sits behind Cloudflare; an occasional 403/429 is transient — the CLI
  auto-retries once after a short pause. A *persistent* 403 means the cookie is
  genuinely expired (reconnect).
- **Never print `MEDIUM_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="medium", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
