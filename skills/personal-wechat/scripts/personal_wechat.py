#!/usr/bin/env python3
"""Small CLI for the Personal WeChat / Wisdom BYOC skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from unattended import unattended_confirm_allowed


BASE_URL = os.environ.get("PERSONALWECHAT_BASE_URL", "").rstrip("/")
API_TOKEN = os.environ.get("PERSONALWECHAT_API_TOKEN", "")
MAX_TEXT_CHARS = 800
SKILL_SLUGS = {"personal-wechat", "acedatacloud/personal-wechat"}

# Wisdom rejects an over-ceiling limit with 422 instead of clamping, so clamp here: a
# generous --limit degrades to the largest page rather than failing the whole command.
MAX_LIMIT = {"contacts": 200, "conversations": 200, "messages": 200, "poll": 500, "moments": 200, "tasks": 200}


def _die(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def _json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, default=str))


def clamp(value: int, ceiling: int) -> int:
    return max(1, min(value, ceiling))


def request(method: str, path: str, *, params: dict | None = None, body: dict | None = None):
    if not BASE_URL:
        _die("PERSONALWECHAT_BASE_URL is not set. Reconnect the Personal WeChat connector.")
    if not API_TOKEN:
        _die("PERSONALWECHAT_API_TOKEN is not set. Reconnect the Personal WeChat connector.")

    query = dict(params or {})
    suffix = f"?{urllib.parse.urlencode(query)}" if query else ""
    url = f"{BASE_URL}{path}{suffix}"
    payload = None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read().decode("utf-8", "replace")
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"raw": raw}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw}
        _die(f"HTTP {exc.code}: {body}", code=2)
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None) or "connection failed"
        _die(f"Cannot reach Wisdom at {BASE_URL}: {reason}", code=3)


def wait_task(task_id: str, *, timeout: float = 600.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        task = request("GET", f"/api/tasks/{task_id}")
        status = task.get("status")
        if status == "succeeded":
            return task.get("result")
        if status == "failed":
            error = task.get("error") or {}
            _die(f"Task failed: {error.get('message') or error}", code=2)
        time.sleep(0.35)
    _die(f"Task {task_id} did not finish within {timeout:g}s", code=2)


def request_task(method: str, path: str, *, params: dict | None = None, body: dict | None = None, timeout: float = 600.0):
    task = request(method, path, params=params, body=body)
    task_id = task.get("id")
    if not task_id:
        return task
    return wait_task(task_id, timeout=timeout)


def compact_conversation(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": item.get("type"),
        "is_pinned": item.get("is_pinned"),
        "unread_count": item.get("unread_count"),
        "last_active_at": item.get("last_active_at"),
        "last_message_count": len(item.get("messages") or []),
    }


def compact_message(item: dict) -> dict:
    text = item.get("text")
    if isinstance(text, str) and len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + f"... [truncated {len(text) - MAX_TEXT_CHARS} chars]"
    return {
        "id": item.get("id"),
        "conversation_id": item.get("conversation_id"),
        "conversation_name": item.get("conversation_name"),
        "conversation_type": item.get("conversation_type"),
        "sender_id": item.get("sender_id"),
        "sender_name": item.get("sender_name"),
        "direction": item.get("direction"),
        "type": item.get("type"),
        "text": text,
        "mentions": item.get("mentions"),
        "quoted_text": item.get("quoted_text"),
        "sent_at": item.get("sent_at"),
    }


def compact_moment(item: dict) -> dict:
    return {
        "feed_id": item.get("feed_id"),
        "author_name": item.get("author_name"),
        "is_self": item.get("is_self"),
        "caption": item.get("caption"),
        "article_title": item.get("article_title"),
        "article_url": item.get("article_url"),
        "media_count": item.get("media_count"),
        "create_time": item.get("create_time"),
    }


def gate(args, *, action: str, preview: dict) -> bool:
    """Return True when the write may proceed, else print the dry-run and stop.

    Writes touch the user's real WeChat account, so they need either explicit approval
    of this exact payload (--confirm) or a platform pre-authorization (--unattended-confirm).
    """
    if getattr(args, "unattended_confirm", False):
        allowed, reason = unattended_confirm_allowed(SKILL_SLUGS)
        if allowed:
            return True
        _json({"dry_run": True, "action": action, **preview, "error": "unattended_confirmation_denied", "reason": reason})
        return False
    if getattr(args, "confirm", False):
        return True
    _json(
        {
            "dry_run": True,
            "action": action,
            **preview,
            "note": "Re-run with --confirm after explicit user approval, or --unattended-confirm when this Skill is pre-authorized for an AceDataCloud scheduled task.",
        }
    )
    return False


def add_write_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--unattended-confirm", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal WeChat (Wisdom) CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("account")

    contacts = sub.add_parser("contacts")
    contacts.add_argument("--limit", type=int, default=20)
    contacts.add_argument("--offset", type=int, default=0)
    contacts.add_argument("--type", choices=["friend", "group", "official"], default=None)

    convs = sub.add_parser("conversations")
    convs.add_argument("--limit", type=int, default=20)
    convs.add_argument("--offset", type=int, default=0)

    msgs = sub.add_parser("messages")
    msgs.add_argument("conversation_id")
    msgs.add_argument("--limit", type=int, default=50)
    msgs.add_argument("--offset", type=int, default=0)
    msgs.add_argument("--order", choices=["asc", "desc"], default="asc")

    poll = sub.add_parser("poll")
    poll.add_argument("--since", type=int, required=True, help="Unix timestamp in seconds")
    poll.add_argument("--limit", type=int, default=100)

    search = sub.add_parser("search")
    search.add_argument("query")

    send = sub.add_parser("send")
    send.add_argument("target")
    send.add_argument("text", nargs="?", default=None)
    send.add_argument("--type", choices=["text", "image", "video", "file"], default="text")
    send.add_argument("--image-url", default=None)
    send.add_argument("--video-url", default=None)
    send.add_argument("--file-url", default=None)
    send.add_argument("--mention", action="append", default=None, metavar="NAME", help="Real @-mention of a group member; repeatable")
    send.add_argument("--mention-all", action="store_true", help="@-mention everyone (group owner/admin only)")
    send.add_argument("--quote-text", default=None, help="Quote-reply to the newest message whose text matches this")
    send.add_argument("--idempotency-key", default=None)
    add_write_flags(send)

    moments = sub.add_parser("moments")
    moments.add_argument("--limit", type=int, default=30)
    moments.add_argument("--self-only", action="store_true")

    moment_post = sub.add_parser("moment-post")
    moment_post.add_argument("text", nargs="?", default=None)
    moment_post.add_argument("--image-url", action="append", default=None, metavar="URL")
    moment_post.add_argument("--visibility", choices=["public", "private", "partial", "exclude"], default="public")
    add_write_flags(moment_post)

    moment_delete = sub.add_parser("moment-delete")
    moment_delete.add_argument("match", help="Distinctive substring of one of your own Moments; must be unique")
    add_write_flags(moment_delete)

    group_create = sub.add_parser("group-create")
    group_create.add_argument("members", nargs="+", help="Names of at least 2 contacts")
    group_create.add_argument("--name", default=None)
    add_write_flags(group_create)

    group_invite = sub.add_parser("group-invite")
    group_invite.add_argument("group")
    group_invite.add_argument("members", nargs="+")
    add_write_flags(group_invite)

    group_remove = sub.add_parser("group-remove")
    group_remove.add_argument("group")
    group_remove.add_argument("members", nargs="+")
    add_write_flags(group_remove)

    group_rename = sub.add_parser("group-rename")
    group_rename.add_argument("group")
    group_rename.add_argument("new_name")
    add_write_flags(group_rename)

    tasks = sub.add_parser("tasks")
    tasks.add_argument("--limit", type=int, default=20)

    task = sub.add_parser("task")
    task.add_argument("task_id")

    return parser


def build_send_body(args) -> dict:
    if args.type == "text" and not args.text:
        _die("text is required for --type text")
    media = {"image": args.image_url, "video": args.video_url, "file": args.file_url}.get(args.type)
    if args.type != "text" and not media:
        _die(f"--{args.type}-url is required for --type {args.type}")

    body = {"target": args.target, "type": args.type, "text": args.text}
    if args.image_url:
        body["image_url"] = args.image_url
    if args.video_url:
        body["video_url"] = args.video_url
    if args.file_url:
        body["file_url"] = args.file_url
    if args.mention:
        body["mentions"] = args.mention
    if args.mention_all:
        body["mention_all"] = True
    if args.quote_text:
        body["quote_text"] = args.quote_text
    if args.idempotency_key:
        body["idempotency_key"] = args.idempotency_key
    return body


def main() -> None:
    args = build_parser().parse_args()

    if args.cmd == "status":
        _json(request("GET", "/api/status"))
    elif args.cmd == "account":
        _json(request("GET", "/api/account"))
    elif args.cmd == "contacts":
        params = {"limit": clamp(args.limit, MAX_LIMIT["contacts"]), "offset": args.offset}
        if args.type:
            params["type"] = args.type
        data = request("GET", "/api/contacts", params=params)
        _json({"total": data.get("total"), "contacts": data.get("contacts", [])})
    elif args.cmd == "conversations":
        params = {"limit": clamp(args.limit, MAX_LIMIT["conversations"]), "offset": args.offset}
        data = request("GET", "/api/conversations", params=params)
        _json({"total": data.get("total"), "conversations": [compact_conversation(i) for i in data.get("conversations", [])]})
    elif args.cmd == "messages":
        data = request(
            "GET",
            "/api/messages",
            params={
                "conversation_id": args.conversation_id,
                "limit": clamp(args.limit, MAX_LIMIT["messages"]),
                "offset": args.offset,
                "order": args.order,
            },
        )
        _json([compact_message(i) for i in data])
    elif args.cmd == "poll":
        data = request("GET", "/api/messages/poll", params={"since": args.since, "limit": clamp(args.limit, MAX_LIMIT["poll"])})
        _json([compact_message(i) for i in data])
    elif args.cmd == "search":
        _json(request_task("POST", "/api/search", body={"query": args.query}, timeout=120))
    elif args.cmd == "send":
        body = build_send_body(args)
        if not gate(args, action="send", preview={"target": args.target, "payload": body}):
            return
        _json(request_task("POST", "/api/messages/send", body=body))
    elif args.cmd == "moments":
        params = {"limit": clamp(args.limit, MAX_LIMIT["moments"]), "self_only": "true" if args.self_only else "false"}
        data = request("GET", "/api/moments", params=params)
        _json({"total": data.get("total"), "moments": [compact_moment(i) for i in data.get("moments", [])]})
    elif args.cmd == "moment-post":
        if not args.text and not args.image_url:
            _die("a Moment needs text, images, or both")
        body = {"text": args.text, "visibility": args.visibility}
        if args.image_url:
            body["image_urls"] = args.image_url
        if not gate(args, action="moment-post", preview={"payload": body}):
            return
        _json(request_task("POST", "/api/moments", body=body))
    elif args.cmd == "moment-delete":
        body = {"match": args.match}
        if not gate(args, action="moment-delete", preview={"payload": body, "warning": "Deleting a Moment is irreversible."}):
            return
        _json(request_task("DELETE", "/api/moments", body=body))
    elif args.cmd == "group-create":
        if len(args.members) < 2:
            _die("group-create needs at least 2 members")
        body = {"members": args.members}
        if args.name:
            body["name"] = args.name
        if not gate(args, action="group-create", preview={"payload": body}):
            return
        _json(request_task("POST", "/api/groups", body=body))
    elif args.cmd == "group-invite":
        body = {"group": args.group, "members": args.members}
        if not gate(args, action="group-invite", preview={"payload": body}):
            return
        _json(request_task("POST", "/api/groups/invite", body=body))
    elif args.cmd == "group-remove":
        body = {"group": args.group, "members": args.members}
        if not gate(args, action="group-remove", preview={"payload": body, "warning": "Removing members is visible to the whole group."}):
            return
        _json(request_task("POST", "/api/groups/remove", body=body))
    elif args.cmd == "group-rename":
        body = {"group": args.group, "new_name": args.new_name}
        if not gate(args, action="group-rename", preview={"payload": body, "warning": "Renaming changes the group name for every member."}):
            return
        _json(request_task("POST", "/api/groups/rename", body=body))
    elif args.cmd == "tasks":
        _json(request("GET", "/api/tasks", params={"limit": clamp(args.limit, MAX_LIMIT["tasks"])}))
    elif args.cmd == "task":
        _json(request("GET", f"/api/tasks/{args.task_id}"))


if __name__ == "__main__":
    main()
