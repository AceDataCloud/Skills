---
name: yuque
description: Read and write Yuque (语雀) documents with the user's own personal access token through the official open API at https://www.yuque.com/api/v2. Use when the user wants to publish Markdown to 语雀, list their knowledge bases (知识库), read or update a 语雀 document, or delete one.
when_to_use: |
  Trigger for 语雀 / Yuque document management: verify the connected account,
  list knowledge bases or the documents inside one, read a document, create a
  Markdown document, update an existing one, or delete one. Writes and
  destructive actions require explicit confirmation.
connections: [yuque]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Use the bundled standard-library CLI. The connector injects the user's 语雀
personal access token as `$YUQUE_TOKEN`. Never print it. The CLI uses the
official open API at `https://www.yuque.com/api/v2` with the documented
`X-Auth-Token` header.

```bash
python3 "$SKILL_DIR/scripts/yuque.py" whoami
```

If `$SKILL_DIR` points at a different skill loaded in the same turn, resolve
this skill's directory explicitly before running the commands below.

If authentication fails, ask the user to create a token at
`https://www.yuque.com/settings/tokens` and reconnect at
`https://auth.acedata.cloud/user/connections`. Do not ask for their account
password or Cookie.

## Read

A `repo` is a 语雀 knowledge base, addressed either by its `namespace`
(`user/book`, as shown in the document URL) or by its numeric id. Always run
`repos` first — never guess a namespace.

```bash
# Verify the token and see the account.
python3 "$SKILL_DIR/scripts/yuque.py" whoami

# List knowledge bases, then the documents in one.
python3 "$SKILL_DIR/scripts/yuque.py" repos
python3 "$SKILL_DIR/scripts/yuque.py" docs REPO_NAMESPACE --limit 20
python3 "$SKILL_DIR/scripts/yuque.py" doc REPO_NAMESPACE DOC_ID
```

## Create and update

Prepare the complete Markdown in a file. 语雀 has no separate draft state — a
document is either private or public — so the CLI creates **private** documents
by default and only publishes publicly with an explicit `--public`.

```bash
# First call is always a dry run and does not load credentials or call the API.
python3 "$SKILL_DIR/scripts/yuque.py" create REPO_NAMESPACE \
  --title "标题" --content-file /tmp/article.md

# Create it privately after the user confirms.
python3 "$SKILL_DIR/scripts/yuque.py" create REPO_NAMESPACE \
  --title "标题" --content-file /tmp/article.md --confirm

# Public publishing additionally requires --public.
python3 "$SKILL_DIR/scripts/yuque.py" create REPO_NAMESPACE \
  --title "标题" --content-file /tmp/article.md --public --confirm

python3 "$SKILL_DIR/scripts/yuque.py" update REPO_NAMESPACE DOC_ID \
  --title "新标题" --content-file /tmp/article.md --public --confirm
```

`--confirm` is valid only as the final argument. Always show the target
knowledge base, title, visibility and full content to the user before a public
publish. Default to a private document unless the user explicitly asks to
publish publicly.

Note that `update` rewrites the whole document body. Read the current document
first if the user only wants part of it changed.

## Delete

```bash
python3 "$SKILL_DIR/scripts/yuque.py" delete REPO_NAMESPACE DOC_ID --confirm
```

Use the real returned `doc_id` and URL. Do not retry a timed-out write
automatically because its outcome may be unknown; list the documents first so
you do not create a duplicate.

## Gotchas

- Images referenced by external URL are not re-hosted; 语雀 renders them from
  the original host. If the source blocks hotlinking, upload the images to 语雀
  manually first and reference the returned URLs.
- 语雀's own terms state the open API is for normal reading and writing of 语雀
  content; abnormal automated behaviour can get the account blocked. Keep the
  volume human-scale.

## Record the output

After a confirmed public publish returns a real URL, call `publish_artifact`
once with `kind="article"`, `channel="yuque"`, the title, returned URL, and
`status="delivered"`. Do not record private documents or failed/unknown writes.
