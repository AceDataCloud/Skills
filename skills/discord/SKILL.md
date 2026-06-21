---
name: discord
description: Read your Discord identity and the list of servers (guilds) you belong to via the Discord API. Use when the user mentions Discord, asks which servers/guilds they are in, or wants their Discord account info.
when_to_use: |
  Trigger when the user wants to read their Discord account identity
  (username, avatar, email) or list the servers (guilds) their connected
  Discord account belongs to. This connection is read-only identity +
  guild list; it CANNOT read or send channel messages.
connections: [discord]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

We drive the [Discord API](https://discord.com/developers/docs/reference)
with `curl + jq`. The user's OAuth bearer token is in `$DISCORD_TOKEN`;
every call needs it as `Authorization: Bearer $DISCORD_TOKEN`. Use the
versioned base URL `https://discord.com/api/v10`.

Discord returns standard JSON. Errors look like
`{"code": <n>, "message": "<reason>"}`. A `401 Unauthorized` means the
token expired or the connection was revoked — tell the user to re-connect
Discord at `auth.acedata.cloud/user/connections`. A `429` carries a
`retry_after` (seconds) field — sleep that long, then retry; never
parallelize.

**Scope is read-only `identify` + `email` + `guilds`.** This OAuth
connection can ONLY read the account's identity and the list of guilds it
belongs to. It CANNOT read/send channel messages, list a guild's channels
or members, or manage anything — those require a **Discord Bot** (bot
token + gateway), which this connector does not provide. Do not call
`/guilds/{id}/channels`, `/channels/...`, or `/guilds/{id}/members` — they
return 401/403 with a user OAuth token. If the user asks for those, say it
needs a Discord bot integration, which isn't set up.

## Recipes

### Verify auth + identity (always run first)

```sh
curl -sS -H "Authorization: Bearer $DISCORD_TOKEN" \
  "https://discord.com/api/v10/users/@me" \
  | jq '{id, username, global_name, email, avatar}'
```

### List the servers (guilds) the user is in

```sh
curl -sS -H "Authorization: Bearer $DISCORD_TOKEN" \
  "https://discord.com/api/v10/users/@me/guilds" \
  | jq 'map({id, name, owner, approximate_member_count})'
```

Add `?with_counts=true` to include `approximate_member_count` /
`approximate_presence_count`:

```sh
curl -sS -H "Authorization: Bearer $DISCORD_TOKEN" \
  "https://discord.com/api/v10/users/@me/guilds?with_counts=true" \
  | jq 'map({id, name, owner, members: .approximate_member_count})'
```

## Notes

- A "server" in the UI is a "guild" in the API. `owner: true` means the
  user owns that guild.
- Guild icon URL (when `icon` is non-null):
  `https://cdn.discordapp.com/icons/<guild_id>/<icon>.png` (use `.gif` if
  the icon hash starts with `a_`).
- The guild list paginates at 200; the typical user is in far fewer, so a
  single call is usually enough. If you ever hit 200, paginate with
  `?after=<last_guild_id>`.
