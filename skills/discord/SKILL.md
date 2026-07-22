---
name: discord
description: Work with the user's Discord account. Two modes, auto-selected by how they connected — OAuth (read-only identity + server list) or User Token / BYOC (full personal-account actions: list channels, read messages, send & reply). Use when the user mentions Discord, asks which servers they are in, or wants to read/post in a channel as themselves.
when_to_use: |
  Trigger for anything on the user's connected Discord account. What you can do
  depends on how they connected:
  - OAuth connection → read-only: their identity (username, avatar, email) and
    the list of servers (guilds) they belong to. No channel messages.
  - User Token (BYOC) connection → full personal-account actions: list channels,
    read recent messages, and send / reply in a channel as the user. Writes are
    gated behind an explicit confirmation.
connections: [discord]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "2.0"
---

# discord — work with the user's Discord account

This skill has **two modes**, picked automatically by which credential the
connector injected. Check the environment first and follow the matching section:

- **`$DISCORD_USER_TOKEN` is set** → **User Token (BYOC) mode**: full
  personal-account actions via the `scripts/discord_user.py` CLI (list channels, read
  messages, send / reply). This acts as the user's **real account**.
- **only `$DISCORD_TOKEN` is set** → **OAuth mode**: read-only identity + server
  list via `curl`. Channel messages are **not** available in this mode.

```sh
if [ -n "$DISCORD_USER_TOKEN" ]; then echo "mode: user-token (full)"; \
elif [ -n "$DISCORD_TOKEN" ]; then echo "mode: oauth (read-only)"; \
else echo "no Discord connection — connect at https://auth.acedata.cloud/user/connections"; fi
```

Both tokens are **secret — full account access. Never echo or print them.** On
`401`, the token expired or was revoked — tell the user to reconnect at
`auth.acedata.cloud/user/connections`. On `429`, sleep the `retry_after`
seconds, then retry; never parallelize.

---

## User Token (BYOC) mode — full actions

When `$DISCORD_USER_TOKEN` is set, drive the user's real account through
[`discord.py-self`](https://github.com/dolfies/discord.py-self) via the CLI at
`scripts/discord_user.py` (run with `python3`). It logs in with the token only (no
gateway) and prints JSON.

`discord.py-self` is preinstalled in the hosted sandbox (import name `discord`).
Do **not** `pip install` it at runtime; if import fails, report that the sandbox
image is missing the dependency and stop.

**Writes (`send` / `reply`) are gated by a trailing `--confirm`.** Without it
they dry-run and print what they *would* send. **Confirm the exact channel and
content with the user before sending** — it's irreversible and public. Only
append `--confirm` (as the very last argument) once the user approves.

```sh
# identity (always run first)
python3 scripts/discord_user.py whoami
# list the servers (guilds) the account is in
python3 scripts/discord_user.py guilds
# list text channels in a server
python3 scripts/discord_user.py channels --guild 1133012399448928276
# read recent messages in a channel
python3 scripts/discord_user.py messages --channel 1133012400174534792 --limit 20
# send — dry-run first, then re-run with a trailing --confirm
python3 scripts/discord_user.py send --channel 1133012400174534792 --text "hello"
python3 scripts/discord_user.py send --channel 1133012400174534792 --text "hello" --confirm
# reply to a specific message
python3 scripts/discord_user.py reply \
  --channel 1133012400174534792 --message 987654321098765432 --text "on it" --confirm
```

`--confirm` is honored ONLY as the final argument (one strip), so a message body
that merely contains the text `--confirm` can never silently trigger a send. IDs
are numeric Discord snowflakes. A proxy can be forced via `DISCORD_PROXY` (falls
back to `HTTPS_PROXY` / `ALL_PROXY`) if the sandbox needs one to reach
`discord.com`.

---

## OAuth mode — read-only

When only `$DISCORD_TOKEN` is set, drive the
[Discord API](https://discord.com/developers/docs/reference) with `curl + jq`.
Auth header is `Authorization: Bearer $DISCORD_TOKEN`; base URL
`https://discord.com/api/v10`.

**Scope is read-only `identify` + `email` + `guilds`.** This mode can ONLY read
the account's identity and its guild list. It CANNOT read/send channel messages,
list a guild's channels or members, or manage anything — `/guilds/{id}/channels`,
`/channels/...`, `/guilds/{id}/members` return 401/403 with an OAuth token. If the
user needs those, they must connect Discord with a **User Token** (the BYOC mode
above), or use a **Discord Bot** (`discordbot` connection) to act as a bot.

```sh
# identity (always run first)
curl -sS -H "Authorization: Bearer $DISCORD_TOKEN" \
  "https://discord.com/api/v10/users/@me" \
  | jq '{id, username, global_name, email, avatar}'

# the servers (guilds) the user is in (add ?with_counts=true for member counts)
curl -sS -H "Authorization: Bearer $DISCORD_TOKEN" \
  "https://discord.com/api/v10/users/@me/guilds?with_counts=true" \
  | jq 'map({id, name, owner, members: .approximate_member_count})'
```

---

## Notes

- A "server" in the UI is a "guild" in the API; messages live in channels inside
  guilds. In User Token mode: `guilds` → `channels --guild <id>` → act on a
  channel id. Don't invent ids.
- In OAuth mode, `owner: true` means the user owns that guild. Guild icon URL
  (when `icon` is non-null): `https://cdn.discordapp.com/icons/<guild_id>/<icon>.png`
  (use `.gif` if the hash starts with `a_`). The guild list paginates at 200;
  paginate with `?after=<last_guild_id>` if you ever hit it.
