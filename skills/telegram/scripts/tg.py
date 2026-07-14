#!/usr/bin/env python3
"""Personal Telegram (MTProto / Telethon) CLI — shipped with the `telegram` skill.

Self-contained: the only third-party dep is `telethon` (preinstalled in the
sandbox). URL downloads for `send-file` use the stdlib only, so a remote image
is fetched to a real local file before upload — Telethon sending a bare remote
URL is unreliable and often lands the media as a document (or fails outright).

Secrets (`TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`) are read from the env
and never printed.
"""

import asyncio
import json
import mimetypes
import os
import sys
import tempfile
import urllib.request
from urllib.parse import urlparse

from telethon import TelegramClient, errors, utils
from telethon.sessions import StringSession
from telethon.tl import functions
from telethon.tl.types import ReactionEmoji, User

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION_STRING"]

_raw = sys.argv[1:]
# --confirm is only honored as the LAST token, and only one is stripped, so a
# message/caption that merely contains "--confirm" cannot silently confirm a write.
CONFIRM = bool(_raw) and _raw[-1] == "--confirm"
a = _raw[:-1] if CONFIRM else list(_raw)
cmd = a[0] if a else "help"
args = a[1:]
GATED = {"send", "reply", "send-file", "forward", "edit", "delete", "react", "mark-read", "join", "leave"}


def out(o):
    print(json.dumps(o, ensure_ascii=False, default=str))


def _ext_from_content_type(ct):
    ct = (ct or "").split(";")[0].strip().lower()
    if not ct:
        return ""
    return mimetypes.guess_extension(ct) or ""


def materialize_file(src):
    """Return (local_path, cleanup) for `src`.

    If `src` is an http(s) URL, download it to a temp file with a sensible
    extension (so Telethon detects images/videos as media, not documents).
    Local paths are returned unchanged with a no-op cleanup.
    """
    parsed = urlparse(src)
    if parsed.scheme not in ("http", "https"):
        return src, (lambda: None)

    # Pick an extension from the URL path first, then the response Content-Type.
    _, url_ext = os.path.splitext(parsed.path)
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (telegram-skill)"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 - user-supplied media URL
        ext = url_ext or _ext_from_content_type(resp.headers.get("Content-Type"))
        fd, path = tempfile.mkstemp(suffix=ext or ".bin", prefix="tg_send_")

        def cleanup():
            try:
                os.remove(path)
            except OSError:
                pass

        try:
            with os.fdopen(fd, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
        except BaseException:
            cleanup()  # don't orphan the temp file if the download fails mid-stream
            raise

    return path, cleanup


async def resolve(client, target):
    # 1) try direct resolve; 2) fall back to scanning dialogs by id or exact name
    #    (StringSession doesn't persist the entity cache, so a numeric id from a
    #    previous invocation may need the dialog scan to recover its access hash).
    for attempt in (lambda: client.get_entity(int(target)), lambda: client.get_entity(target)):
        try:
            return await attempt()
        except Exception:
            pass
    ti = None
    try:
        ti = int(target)
    except (ValueError, TypeError):
        pass
    async for d in client.iter_dialogs():
        if (ti is not None and d.id == ti) or d.name == target:
            return d.entity
    raise ValueError(f"could not resolve target: {target}")


def msg_row(m):
    return {"id": m.id, "date": str(m.date), "out": m.out, "sender_id": m.sender_id,
            "text": m.message, "media": bool(m.media)}


def need(n):
    if len(args) < n:
        raise ValueError(f"{cmd} needs {n} argument(s), got {len(args)}")


def _pop_opt(argv, name):
    """Extract `--name VALUE` from argv; return (value_or_None, remaining_argv).

    Only a standalone `--name` token matches, so a message that merely contains
    the flag text as part of one argument is left untouched.
    """
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1], argv[:i] + argv[i + 2:]
    return None, argv


async def run():
    if cmd in GATED and not CONFIRM:
        out({"dry_run": True, "command": cmd, "args": args,
             "note": "re-run with --confirm as the LAST argument to actually perform this write"})
        return
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as cl:
        if cmd == "whoami":
            me = await cl.get_me()
            out({"id": me.id, "username": me.username,
                 "name": ((me.first_name or "") + " " + (me.last_name or "")).strip(), "phone": me.phone})

        elif cmd == "list-chats":
            limit = int(args[0]) if args and args[0].lstrip("-").isdigit() else 20
            unread_only = "unread-only" in args
            res = []
            async for d in cl.iter_dialogs(limit=limit):
                if unread_only and not d.unread_count:
                    continue
                res.append({"name": d.name, "id": d.id, "group": d.is_group,
                            "channel": d.is_channel, "user": d.is_user, "unread": d.unread_count})
            out(res)

        elif cmd == "unread":
            res = []
            async for d in cl.iter_dialogs():
                if d.unread_count:
                    res.append({"name": d.name, "id": d.id, "unread": d.unread_count,
                                "group": d.is_group, "channel": d.is_channel})
            out(sorted(res, key=lambda x: -x["unread"]))

        elif cmd == "get-messages":
            need(1); ent = await resolve(cl, args[0])
            n = int(args[1]) if len(args) > 1 else 50
            rows = [msg_row(m) async for m in cl.iter_messages(ent, limit=n)]
            rows.reverse()
            out(rows)

        elif cmd == "search":
            need(2); ent = await resolve(cl, args[0])
            q = args[1]; n = int(args[2]) if len(args) > 2 else 30
            out([msg_row(m) async for m in cl.iter_messages(ent, search=q, limit=n)])

        elif cmd == "search-global":
            need(1); q = args[0]; n = int(args[1]) if len(args) > 1 else 30
            rows = []
            async for m in cl.iter_messages(None, search=q, limit=n):
                r = msg_row(m); r["chat_id"] = m.chat_id
                rows.append(r)
            out(rows)

        elif cmd == "contacts":
            res = await cl(functions.contacts.GetContactsRequest(hash=0))
            out([{"id": u.id, "username": u.username,
                  "name": ((u.first_name or "") + " " + (u.last_name or "")).strip(), "phone": u.phone}
                 for u in res.users])

        elif cmd == "chat-info":
            need(1); ent = await resolve(cl, args[0])
            info = {"id": ent.id, "type": type(ent).__name__,
                    "title": getattr(ent, "title", None),
                    "name": ((getattr(ent, "first_name", "") or "") + " " + (getattr(ent, "last_name", "") or "")).strip() or None,
                    "username": getattr(ent, "username", None)}
            try:
                info["participants"] = (await cl.get_participants(ent, limit=1)).total
            except Exception:
                pass
            out(info)

        elif cmd == "list-topics":
            # Forum-style supergroups organize messages into topics (threads).
            # A plain send to the group root is rejected (TOPIC_CLOSED); you must
            # post into an open topic via `send --topic <top_message>`.
            need(1); ent = await resolve(cl, args[0])
            limit = int(args[1]) if len(args) > 1 else 100
            res = await cl(functions.messages.GetForumTopicsRequest(
                channel=ent, offset_date=0, offset_id=0, offset_topic=0, limit=limit))
            out([{"id": getattr(t, "id", None), "title": getattr(t, "title", None),
                  "closed": getattr(t, "closed", None), "hidden": getattr(t, "hidden", None),
                  "top_message": getattr(t, "top_message", None)} for t in res.topics])

        elif cmd == "message-link":
            need(2); ent = await resolve(cl, args[0]); mid = int(args[1])
            try:
                r = await cl(functions.channels.ExportMessageLinkRequest(channel=ent, id=mid))
                out({"link": r.link})
            except Exception as e:
                out({"error": f"links only available for channels/supergroups: {e}"})

        elif cmd == "download-media":
            need(2); ent = await resolve(cl, args[0]); mid = int(args[1])
            outdir = args[2] if len(args) > 2 else "./tg_downloads"
            os.makedirs(outdir, exist_ok=True)
            m = await cl.get_messages(ent, ids=mid)
            if not m or not m.media:
                out({"error": "no media on that message"}); return
            path = await cl.download_media(m, file=outdir)
            out({"downloaded": path})

        # ---- gated writes (need trailing --confirm) ----
        elif cmd == "send":
            # `--topic <top_message>` posts into a forum topic thread (reply_to);
            # required for forum-style supergroups where a root send is rejected.
            topic, sargs = _pop_opt(args, "--topic")
            if len(sargs) < 2:
                raise ValueError("send needs <target> <text> (optional --topic <id>)")
            ent = await resolve(cl, sargs[0])
            kw = {"reply_to": int(topic)} if topic is not None else {}
            m = await cl.send_message(ent, sargs[1], **kw)
            out({"sent": True, "id": m.id, "topic": int(topic) if topic is not None else None})

        elif cmd == "reply":
            need(3); ent = await resolve(cl, args[0])
            m = await cl.send_message(ent, args[2], reply_to=int(args[1]))
            out({"sent": True, "id": m.id, "reply_to": int(args[1])})

        elif cmd == "send-file":
            need(2); ent = await resolve(cl, args[0])
            caption = args[2] if len(args) > 2 else None
            # Download remote URLs to a real local file first so images/videos
            # upload as media instead of failing or landing as a document.
            path, cleanup = materialize_file(args[1])
            try:
                m = await cl.send_file(ent, path, caption=caption)
            finally:
                cleanup()
            out({"sent": True, "id": m.id})

        elif cmd == "forward":
            need(3); src = await resolve(cl, args[0]); mid = int(args[1]); dst = await resolve(cl, args[2])
            fwd = await cl.forward_messages(dst, mid, src)
            out({"forwarded": True, "id": getattr(fwd, "id", None) or [x.id for x in fwd]})

        elif cmd == "edit":
            need(3); ent = await resolve(cl, args[0])
            m = await cl.edit_message(ent, int(args[1]), args[2])
            out({"edited": True, "id": m.id})

        elif cmd == "delete":
            need(2); ent = await resolve(cl, args[0])
            await cl.delete_messages(ent, int(args[1]))
            out({"deleted": True, "id": int(args[1])})

        elif cmd == "react":
            need(3); ent = await resolve(cl, args[0]); mid = int(args[1]); emoji = args[2]
            await cl(functions.messages.SendReactionRequest(
                peer=ent, msg_id=mid, reaction=[ReactionEmoji(emoticon=emoji)]))
            out({"reacted": True, "id": mid, "emoji": emoji})

        elif cmd == "mark-read":
            need(1); ent = await resolve(cl, args[0])
            await cl.send_read_acknowledge(ent)
            out({"marked_read": True})

        elif cmd == "join":
            need(1); target = args[0]
            # A public @username / t.me/<user> resolves + JoinChannelRequest; a
            # private invite (t.me/+HASH, joinchat/HASH, tg://join?invite=HASH)
            # can't be resolved without joining, so import it by hash directly.
            link_hash, is_invite = utils.parse_username(target)
            try:
                if is_invite:
                    res = await cl(functions.messages.ImportChatInviteRequest(link_hash))
                    chat = (getattr(res, "chats", None) or [None])[0]
                    out({"joined": True, "via": "invite",
                         "id": getattr(chat, "id", None), "title": getattr(chat, "title", None)})
                else:
                    ent = await resolve(cl, target)
                    await cl(functions.channels.JoinChannelRequest(ent))
                    out({"joined": True, "via": "public", "id": ent.id,
                         "title": getattr(ent, "title", None), "username": getattr(ent, "username", None)})
            except errors.UserAlreadyParticipantError:
                out({"joined": True, "already_member": True, "target": target})

        elif cmd == "leave":
            need(1); ent = await resolve(cl, args[0])
            if isinstance(ent, User):
                out({"error": "leave applies to groups/channels, not private chats"}); return
            await cl.delete_dialog(ent)
            out({"left": True, "id": ent.id})

        else:
            out({"error": f"unknown command: {cmd}"}); sys.exit(1)


async def main():
    try:
        await run()
    except SystemExit:
        raise
    except Exception as e:
        out({"error": f"{type(e).__name__}: {e}"})
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
