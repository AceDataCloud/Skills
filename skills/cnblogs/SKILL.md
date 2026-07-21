---
name: cnblogs
description: Publish, update and read CNBlogs (博客园) posts with a personal access token through the API used by the official vscode-cnb client. Use when the user wants to publish Markdown to 博客园, save a CNBlogs draft, edit or delete a post, or list posts or categories.
when_to_use: |
  Trigger for 博客园 / CNBlogs blog management: verify the connected account,
  list categories or recent posts, create a Markdown draft, publish or update
  a post, or delete a post. Public writes and destructive actions require
  explicit confirmation.
connections: [cnblogs]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Use the bundled standard-library CLI. The connector injects the user's 博客园
personal access token as `$CNBLOGS_TOKEN`. Never print it. The CLI follows the
current official `cnblogs/vscode-cnb` client contract at
`https://write.cnblogs.com/api` (`Authorization: Bearer` plus
`Authorization-Type: pat`).

```bash
python3 "$SKILL_DIR/scripts/cnblogs.py" whoami
```

If authentication fails, ask the user to create a PAT at
`https://account.cnblogs.com/settings/tokens` and reconnect. Do not ask for
their account password or Cookie.

## Read the blog

```bash
# Verify the token and inspect the account's post template.
python3 "$SKILL_DIR/scripts/cnblogs.py" whoami

# Categories and recent posts.
python3 "$SKILL_DIR/scripts/cnblogs.py" categories
python3 "$SKILL_DIR/scripts/cnblogs.py" posts --limit 20
python3 "$SKILL_DIR/scripts/cnblogs.py" post POST_ID
```

## Create a draft or publish

Prepare the complete Markdown in a file. Category values are numeric IDs from
the `categories` command; tags are names.

```bash
# First call is always a dry run and does not load credentials or call the API.
python3 "$SKILL_DIR/scripts/cnblogs.py" create \
  --title "标题" --content-file /tmp/article.md \
  --category-ids "123,456" --tags "agent,api"

# Save as a private draft after the user confirms.
python3 "$SKILL_DIR/scripts/cnblogs.py" create \
  --title "标题" --content-file /tmp/article.md \
  --category-ids "123,456" --tags "agent,api" --confirm

# Public publishing additionally requires --publish.
python3 "$SKILL_DIR/scripts/cnblogs.py" create \
  --title "标题" --content-file /tmp/article.md \
  --category-ids "123,456" --tags "agent,api" --publish --confirm
```

`--confirm` is valid only as the final argument. Always show the title,
categories, tags, visibility and full content to the user before a public
publish. Default to a draft unless the user explicitly requests publication.

## Update and delete

Updating requires an explicit visibility choice so an existing post is not
silently unpublished. All commands below dry-run without trailing `--confirm`.

```bash
python3 "$SKILL_DIR/scripts/cnblogs.py" update POST_ID \
  --title "新标题" --content-file /tmp/article.md --publish --confirm

python3 "$SKILL_DIR/scripts/cnblogs.py" update POST_ID \
  --title "新标题" --content-file /tmp/article.md --draft --confirm

python3 "$SKILL_DIR/scripts/cnblogs.py" delete POST_ID --confirm
```

Use the real returned `post_id`, URL, or media URL. Do not retry a timed-out
write automatically because its outcome may be unknown; list recent posts or
inspect the post first.

## Record the output

After a confirmed public publish returns a real URL, call `publish_artifact`
once with `kind="article"`, `channel="cnblogs"`, the title, returned URL, and
`status="delivered"`. Do not record drafts or failed/unknown writes.
