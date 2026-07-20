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


def _die(message: str, code: int = 1) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), file=sys.stderr)
    raise SystemExit(code)


def _json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, default=str))


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
        "id": item.get("id") or item.get("strUsrName"),
        "name": item.get("name") or item.get("display_name") or item.get("strNickName"),
        "type": item.get("type"),
        "unread_count": item.get("unread_count") if "unread_count" in item else item.get("nUnReadCount"),
        "last_active_at": item.get("last_active_at") or item.get("nTime"),
        "last_message_count": len(item.get("messages") or []),
    }


def compact_message(item: dict) -> dict:
    text = item.get("text") or item.get("StrContent") or item.get("DisplayContent")
    if isinstance(text, str) and len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + f"... [truncated {len(text) - MAX_TEXT_CHARS} chars]"
    return {
        "id": item.get("id") or item.get("MsgSvrID") or item.get("localId"),
        "conversation_id": item.get("conversation_id") or item.get("StrTalker"),
        "conversation_name": item.get("conversation_name"),
        "sender_id": item.get("sender_id"),
        "sender_name": item.get("sender_name"),
        "direction": item.get("direction"),
        "type": item.get("type") or item.get("Type"),
        "text": text,
        "sent_at": item.get("sent_at") or item.get("CreateTime"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal WeChat (Wisdom) CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("account")

    contacts = sub.add_parser("contacts")
    contacts.add_argument("--limit", type=int, default=20)

    convs = sub.add_parser("conversations")
    convs.add_argument("--limit", type=int, default=20)
    convs.add_argument("--history", action="store_true")

    msgs = sub.add_parser("messages")
    msgs.add_argument("conversation_id")
    msgs.add_argument("--limit", type=int, default=50)
    msgs.add_argument("--offset", type=int, default=0)
    msgs.add_argument("--order", choices=["asc", "desc"], default="asc")

    hist = sub.add_parser("history")
    hist.add_argument("--talker", default="")
    hist.add_argument("--limit", type=int, default=50)
    hist.add_argument("--offset", type=int, default=0)

    sql = sub.add_parser("sql")
    sql.add_argument("db")
    sql.add_argument("sql")

    search = sub.add_parser("search")
    search.add_argument("query")

    send = sub.add_parser("send")
    send.add_argument("target")
    send.add_argument("text")
    send.add_argument("--confirm", action="store_true")
    send.add_argument("--unattended-confirm", action="store_true")

    refresh = sub.add_parser("refresh-history")
    refresh.set_defaults(cmd="refresh-history")

    args = parser.parse_args()

    if args.cmd == "status":
        _json({"status": request("GET", "/api/status"), "auth": request("GET", "/api/auth/status")})
    elif args.cmd == "account":
        _json(request("GET", "/api/account"))
    elif args.cmd == "contacts":
        data = request("GET", "/api/contacts", params={"limit": args.limit, "version": "2.0"})
        _json({"total": data.get("total"), "contacts": data.get("contacts", [])})
    elif args.cmd == "conversations":
        if args.history:
            data = request("GET", "/api/conversations/history", params={"limit": args.limit})
            _json({"count": data.get("count"), "conversations": [compact_conversation(i) for i in data.get("conversations", [])]})
        else:
            data = request("GET", "/api/conversations", params={"limit": args.limit})
            _json({"total": data.get("total"), "conversations": [compact_conversation(i) for i in data.get("conversations", [])]})
    elif args.cmd == "messages":
        data = request(
            "GET",
            "/api/messages",
            params={"conversation_id": args.conversation_id, "limit": args.limit, "offset": args.offset, "order": args.order},
        )
        _json([compact_message(i) for i in data])
    elif args.cmd == "history":
        params = {"limit": args.limit, "offset": args.offset}
        if args.talker:
            params["talker"] = args.talker
        data = request("GET", "/api/messages/history", params=params)
        _json({"count": data.get("count"), "db_ready": data.get("db_ready"), "messages": [compact_message(i) for i in data.get("messages", [])]})
    elif args.cmd == "sql":
        data = request("POST", "/api/messages/history/query", body={"db": args.db, "sql": args.sql})
        _json(data)
    elif args.cmd == "search":
        _json(request_task("POST", "/api/search", body={"query": args.query}, timeout=120))
    elif args.cmd == "send":
        if args.unattended_confirm:
            allowed, reason = unattended_confirm_allowed(SKILL_SLUGS)
            if not allowed:
                _json({"dry_run": True, "target": args.target, "text": args.text, "error": "unattended_confirmation_denied", "reason": reason})
                return
        elif not args.confirm:
            _json({"dry_run": True, "target": args.target, "text": args.text, "note": "Re-run with --confirm after explicit user approval, or --unattended-confirm when this Skill is pre-authorized for an AceDataCloud scheduled task."})
            return
        _json(request_task("POST", "/api/messages/send", body={"target": args.target, "type": "text", "text": args.text}))
    elif args.cmd == "refresh-history":
        _json(request("POST", "/api/messages/history/refresh"))


if __name__ == "__main__":
    main()
