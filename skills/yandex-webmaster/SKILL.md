---
name: yandex-webmaster
description: Read verified sites and search visibility from Yandex Webmaster for Russian-language SEO analysis. Use when the user asks about Yandex indexing, sites, or search queries.
when_to_use: |
  Use for the connected user's Yandex Webmaster properties. This skill is
  read-only and requires a Yandex OAuth token with webmaster:hostinfo access.
connections: [yandexwebmaster]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Yandex Webmaster

The BYOC token is injected as `$YANDEXWEBMASTER_ACCESS_TOKEN`. Never display it
or place it in a URL. The script calls Yandex's official Webmaster API v4 and
prints only site and search data.

```bash
SCRIPT="$SKILL_DIR/scripts/yandex_webmaster.py"
python3 "$SCRIPT" hosts
python3 "$SCRIPT" popular-queries --host-id 'https:example.com:443' --limit 20
```

`hosts` discovers the user ID and verified host IDs. Copy the **exact**
`host_id` returned by the API into the second command. Do not guess or mutate
host IDs. If the token is expired or has insufficient scope, ask the user to
reconnect; do not retry with a broader token.

Official API: https://yandex.com/dev/webmaster/ .
