#!/usr/bin/env python3
"""Pinterest API v5 client with confirmation-gated Pin creation."""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.pinterest.com/v5"
RAW_ARGS = sys.argv[1:]
CONFIRMED = bool(RAW_ARGS) and RAW_ARGS[-1] == "--confirm"
ARGS = RAW_ARGS[:-1] if CONFIRMED else RAW_ARGS


def output(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fail(message: str) -> None:
    output({"error": message})
    raise SystemExit(1)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ.get("PINTEREST_TOKEN", "").strip()
    if not token:
        fail("PINTEREST_TOKEN is not set; reconnect Pinterest and retry")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if method == "POST" and exc.code >= 500:
            fail(
                "Pinterest write result is unknown after a server error; do not retry. "
                "List the board's Pins and reconcile the title/link before another create."
            )
        try:
            text = exc.read().decode("utf-8", "replace")
        except (OSError, TimeoutError, http.client.HTTPException):
            if method == "POST":
                fail(
                    "Pinterest write result is unknown because its response was incomplete; do not retry. "
                    "List the board's Pins and reconcile the title/link before another create."
                )
            raise
        try:
            detail = json.loads(text)
        except json.JSONDecodeError:
            detail = text[:500]
        fail(f"Pinterest API returned {exc.code}: {detail}")
    except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException, json.JSONDecodeError) as exc:
        if method == "POST":
            fail(
                "Pinterest write result is unknown after a network failure; do not retry. "
                "List the board's Pins and reconcile the title/link before another create."
            )
        reason = exc.reason if isinstance(exc, urllib.error.URLError) else str(exc)
        fail(f"network error reaching Pinterest: {reason}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("whoami")
    boards = commands.add_parser("boards")
    boards.add_argument("--limit", type=int, default=25)
    pins = commands.add_parser("pins")
    pins.add_argument("--board-id", required=True)
    pins.add_argument("--limit", type=int, default=25)
    create = commands.add_parser("create")
    create.add_argument("--board-id", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--description", default="")
    create.add_argument("--link")
    create.add_argument("--image-url", required=True)
    return parser


def bounded(value: int) -> int:
    return max(1, min(value, 100))


def main() -> None:
    args = build_parser().parse_args(ARGS)
    if args.command == "whoami":
        output(request("GET", "/user_account"))
        return
    if args.command == "boards":
        output(request("GET", f"/boards?page_size={bounded(args.limit)}"))
        return
    if args.command == "pins":
        board_id = urllib.parse.quote(args.board_id, safe="")
        output(request("GET", f"/boards/{board_id}/pins?page_size={bounded(args.limit)}"))
        return
    if not args.image_url.startswith("https://"):
        fail("--image-url must be a public HTTPS URL")
    pin = {
        "board_id": args.board_id,
        "title": args.title,
        "description": args.description,
        "media_source": {"source_type": "image_url", "url": args.image_url},
    }
    if args.link:
        pin["link"] = args.link
    if not CONFIRMED:
        output(
            {
                "dry_run": True,
                "operation": "create_pin",
                "request": pin,
                "confirm": "append --confirm as the final argument",
            }
        )
        return
    output(request("POST", "/pins", pin))


if __name__ == "__main__":
    main()
