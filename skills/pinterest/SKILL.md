---
name: pinterest
description: Read Pinterest boards and Pins and create new image Pins through the official Pinterest API v5. Use when the user mentions Pinterest, boards, Pins, visual distribution, or publishing a generated image to Pinterest.
when_to_use: |
  Trigger when the user wants to inspect their Pinterest account or boards,
  list Pins, or publish user-created visual content to a board. Creating a Pin
  requires explicit confirmation.
connections: [pinterest]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Pinterest API v5

Use the official API through the bundled standard-library client. The user's
OAuth token is injected as `$PINTEREST_TOKEN`; never print it.

```bash
P="$SKILL_DIR/scripts/pinterest.py"
[ -f "$P" ] || P=$(find /tmp -maxdepth 8 -path '*/skills/*/pinterest/scripts/pinterest.py' 2>/dev/null | head -1)
[ -f "$P" ] || { echo "pinterest script not found" >&2; exit 1; }

python3 "$P" whoami
python3 "$P" boards --limit 25
python3 "$P" pins --board-id BOARD_ID --limit 25
```

## Create an image Pin

Pinterest's content API is for new content created by the user. Do not copy or
republish third-party images without authorization.

```bash
python3 "$P" create --board-id BOARD_ID --title "Title" \
  --description "Description" --link "https://example.com/article" \
  --image-url "https://cdn.example.com/pin.jpg"

python3 "$P" create --board-id BOARD_ID --title "Title" \
  --description "Description" --link "https://example.com/article" \
  --image-url "https://cdn.example.com/pin.jpg" --confirm
```

The first call is a dry run. Show the final image, title, description, board,
and link to the user before the confirmed call. The image URL must be public
HTTPS and point to content the user is entitled to publish.

Common failures:

| HTTP | Meaning | Action |
|---|---|---|
| 401 | Token expired or revoked | Reconnect Pinterest |
| 403 | Missing scope or app access | Ensure `pins:write`/`boards:read` were approved |
| 404 | Board not found | Re-list boards under the connected account |
| 429 | Pinterest rate limit | Stop and retry later; do not loop |

If a confirmed create ends with a network error, the result is unknown. Do not
repeat it. List the target board's Pins and compare title/link before deciding
whether a second create is safe.

After a confirmed create returns a real URL, record it once with
`publish_artifact(kind="image", channel="pinterest", ...)`.
