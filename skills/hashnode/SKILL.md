---
name: hashnode
description: Publish, draft and read blog posts on the user's Hashnode blog using their own login cookies (BYOC) — no Hashnode Pro plan required. Use when the user mentions Hashnode, publishing/cross-posting an article to their Hashnode blog, saving a Hashnode draft, or listing their Hashnode publications.
when_to_use: |
  Trigger when the user wants to publish a Markdown article to their Hashnode
  blog, save it as a private draft, or list their Hashnode publications. This
  drives the user's REAL blog, so publishing is gated behind an explicit
  confirmation (save a draft first if unsure).
connections: [hashnode]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.0"
---

# hashnode — publish to your Hashnode blog via your own cookies (no Pro)

Hashnode moved its **public GraphQL API behind a paid Pro plan** (2026-05-13), so
a Personal Access Token can no longer publish for free. This skill instead drives
the **same first-party REST API the Hashnode web editor uses**
(`https://hashnode.com/api/...`), authenticated by the user's login **session
cookie** — which is free and needs no Pro plan.

The connector injects the cookie jar as `HASHNODE_COOKIES` (a JSON array; the
session cookie is `hashnode-session`). **Secret — full account access. Never echo
or print it.**

> E2E-verified 2026-07-12 on a real connected blog: list publications, create +
> save draft (title / subtitle / cover / tags / Markdown), publish, and delete —
> all via cookie auth, no Pro.

## Setup — anchor on our own script

```sh
# $SKILL_DIR can point at another skill loaded this turn — anchor on our script.
H="$SKILL_DIR/scripts/hashnode.py"; [ -f "$H" ] || H=$(find /tmp -maxdepth 8 -path '*/skills/*/hashnode/scripts/hashnode.py' 2>/dev/null | head -1)
[ -f "$H" ] || { echo "hashnode script not found (SKILL_DIR=$SKILL_DIR)" >&2; exit 1; }
python3 "$H" publications          # list the user's blogs (verifies the cookie)
```

On an auth error the cookie is expired — have the user reconnect at
<https://auth.acedata.cloud/user/connections>. Do **not** loop-retry.

## ⚠️ Non-Pro blogs are automoderated — write EDITORIAL, not ads

This is the single most important rule. A **non-Pro** publication is subject to
Hashnode **automoderation**: an overtly promotional post (hypey language,
"free credits!!", the *same* CTA link repeated 3–4 times) is **auto-removed
within seconds** — the publish call still returns success, but the live URL then
404s. (Pro's one benefit here is "protection from automoderation removal".)

To stay live, write a genuinely useful **how-to / guide** that happens to feature
the product:

- Educational framing and a concrete title (e.g. *"… (Beginner's Guide)"*).
- At most a couple of **tasteful** links, not the same CTA repeated.
- No "limited-time!! grab now!!" marketing voice.

`publish` re-fetches the live URL after publishing and returns a `warning` if the
post was moderated away — if you see that, rewrite it editorially and republish.

## Read

```sh
python3 "$H" publications        # {publications:[{id,title,url}]}
```

## Save a private draft (safe, non-public)

```sh
python3 "$H" draft \
  --title "My Title" \
  --subtitle "Optional subtitle" \
  --content-file article.md \
  --cover "https://cdn.example.com/cover.jpg" \
  --tags ai,apis
# → {draft_id, editor_url}. Nothing is public yet.
```

- `--content-file` is the Markdown body (use a file for long posts; `--content`
  for a short inline string). Inline **images** and **links** are just Markdown.
- `--cover` sets the header/cover image (also used as the OG image).
- `--tags` are comma-separated slugs (`ai,apis,web-development`); they're resolved
  to real Hashnode tag ids automatically (up to 5).
- `--publication <id>` is only needed if the account has more than one blog.

## Publish — GATED (dry-run unless trailing `--confirm`)

```sh
python3 "$H" publish --title "My Title" --content-file article.md --cover "https://…" --tags ai,apis          # dry-run
python3 "$H" publish --title "My Title" --content-file article.md --cover "https://…" --tags ai,apis --confirm # LIVE
# → {ok, url}  (or {ok:false, warning:"…automoderation removed…"} — rewrite editorially)
```

A confirmed `publish` is **immediately public** on the user's real blog. Always
show the final title + body, get an explicit "yes", then run with `--confirm` as
the **last** argument.

## Delete a draft or post — GATED

```sh
python3 "$H" delete --id <draftOrPostId>            # dry-run
python3 "$H" delete --id <draftOrPostId> --confirm  # delete
```

## Gotchas

- **No Pro, no PAT.** This uses the cookie-authed `hashnode.com/api/*` editor API,
  not `gql-beta.hashnode.com` (which requires a paid Pro plan).
- **Automoderation** (above) is the main failure mode on free blogs — keep it
  editorial.
- **This is the user's real blog.** Confirm before any publish/delete.
- **Never print `HASHNODE_COOKIES`** — it is full account access.
- **First-party internal API** — it can change when Hashnode updates the editor;
  if a call starts returning HTML/404 unexpectedly, report it as upstream drift.

## Record the output

After you successfully publish and obtain the live result URL, call the built-in
`publish_artifact` tool ONCE so the user can track this deliverable in **My Outputs**:

```
publish_artifact(kind="article", channel="hashnode", title="<title>", url="<the REAL returned URL>", status="delivered")
```

Use the real returned URL — never fabricate one. Call it once per published item,
only after delivery is confirmed; skip it (or use `status="failed"`) if publishing failed.
See `_shared/artifacts.md`.
