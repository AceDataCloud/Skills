---
name: substack
description: Read and publish on Substack (substack.com) with the user's own login cookies (BYOC) — show who they are and their primary publication, list their published posts with stats, and publish a new post / newsletter. Use when the user mentions Substack, "my Substack", their newsletter, or publishing a post to Substack.
when_to_use: |
  Trigger for anything on the user's Substack account driven by their own login
  cookie: show who they are and their primary publication, list their published
  posts, or publish a new post / newsletter. This acts as the user's real
  account, so writes are gated behind an explicit confirmation and never email
  subscribers unless asked.
connections: [substack]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# substack — read & publish on Substack via your own cookies

Drives the user's **real** Substack account through the same internal web API
the site uses (Substack has no official public write API), authenticated by the
login cookie they captured with the ACE extension. No browser, no third-party
deps — just `urllib`. The publish flow mirrors the community `python-substack`
library: **create draft → prepublish → publish**.

The connector injects the cookie jar as an env var:

- `SUBSTACK_COOKIES` — a JSON array of cookies (`substack.sid`, `substack.lli`,
  …). **Secret — never echo or print it.** Substack authenticates writes with
  the session cookie alone (no CSRF token header needed).

## CLI

The skill ships [`scripts/substack.py`](scripts/substack.py) — self-contained, stdlib only.

```sh
SUB=$SKILL_DIR/scripts/substack.py
python3 $SUB whoami                       # who is logged in + primary publication
python3 $SUB articles --limit 20          # my published posts + stats
```

## Verify the connection first

```sh
python3 $SUB whoami
# → {"user_id": ..., "name": "...", "handle": "...", "publication": "...", "publication_url": "https://<sub>.substack.com"}
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## Publishing — GATED (dry-run unless trailing `--confirm`)

`publish` writes to the user's real account. Content is **Markdown**, converted
to Substack's ProseMirror blocks: `#`..`######`→heading, ```` ``` ````→code
block, `>`→blockquote, `-`/`*`/`1.`→lists, `---`→horizontal rule, everything else
→paragraphs. Inline **bold**, *italic*, `code`, ~~strike~~, and `[links](url)`
render as real Substack formatting; bare `https://…` URLs are auto-linked.

Without a trailing `--confirm` it dry-runs. `--confirm` is honored **only as the
last argument**. Always show the dry-run, get an explicit "yes", then re-run.

```sh
# dry-run (shows the plan, writes nothing)
python3 $SUB publish --title "Title" --content-file post.md

# private draft (visible only in the user's dashboard)
python3 $SUB publish --title "Title" --content-file post.md --draft-only --confirm

# go LIVE on the web (does NOT email subscribers)
python3 $SUB publish --title "Title" --content-file post.md --confirm

# go LIVE and email subscribers (use only when the user explicitly asks)
python3 $SUB publish --title "Title" --content-file post.md --send-email --confirm
```

- `--draft-only` stops at a draft — **default to this** unless the user asked to
  go live. Returns an `edit_url` to review in the Substack editor.
- Publishing **does NOT email subscribers** unless `--send-email` is passed.
  Emailing a newsletter is irreversible and hits every subscriber's inbox —
  never add `--send-email` without an explicit request.
- `--subtitle` sets the post subtitle; `--audience` is one of
  `everyone` (default, free/public), `only_paid`, `founding`, `only_free`.

## Gotchas

- **This is the user's real Substack account.** Confirm before any publish, and
  keep `--draft-only` as the safe default.
- **`--send-email` blasts the whole subscriber list** and cannot be undone — opt
  in only on explicit request.
- Substack sits behind Cloudflare; an occasional 403/429 on a read is transient —
  the CLI auto-retries reads once. A *persistent* 401/403 means the cookie is
  genuinely expired (reconnect); the CLI never retries a write.
- **Never print `SUBSTACK_COOKIES`** — it is full account access.
- **ToS**: acts only on the user's own account with their own captured cookie.


## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="substack", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
