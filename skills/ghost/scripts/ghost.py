#!/usr/bin/env python3
"""Minimal Ghost Admin API client with confirmation-gated writes."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import http.client
import ipaddress
import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

RAW_ARGS = sys.argv[1:]
CONFIRMED = bool(RAW_ARGS) and RAW_ARGS[-1] == "--confirm"
ARGS = RAW_ARGS[:-1] if CONFIRMED else RAW_ARGS


def output(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fail(message: str) -> None:
    output({"error": message})
    raise SystemExit(1)


def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def admin_token(key: str) -> str:
    try:
        key_id, secret = key.split(":", 1)
        secret_bytes = bytes.fromhex(secret)
    except (ValueError, TypeError):
        fail("GHOST_ADMIN_API_KEY must use the id:hexsecret format from a Ghost custom integration")
    now = int(time.time())
    header = b64url(json.dumps({"alg": "HS256", "kid": key_id, "typ": "JWT"}, separators=(",", ":")).encode())
    payload = b64url(json.dumps({"iat": now, "exp": now + 300, "aud": "/admin/"}, separators=(",", ":")).encode())
    signature = b64url(hmac.new(secret_bytes, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def config() -> tuple[str, int, str, str]:
    raw_site = os.environ.get("GHOST_SITE_URL", "").strip()
    key = os.environ.get("GHOST_ADMIN_API_KEY", "").strip()
    parsed = urllib.parse.urlsplit(raw_site)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        fail("GHOST_SITE_URL must be an HTTPS site root without credentials, path, query, or fragment")
    try:
        addresses = {
            ipaddress.ip_address(sockaddr[0])
            for _family, _type, _proto, _canonname, sockaddr in socket.getaddrinfo(
                parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM
            )
        }
    except socket.gaierror as exc:
        fail(f"GHOST_SITE_URL hostname could not be resolved: {exc}")
    if not addresses or any(not address.is_global for address in addresses):
        fail("GHOST_SITE_URL must resolve only to public network addresses")
    if not key:
        fail("GHOST_ADMIN_API_KEY is not set; reconnect Ghost and retry")
    return parsed.hostname.lower(), parsed.port or 443, str(sorted(addresses, key=str)[0]), key


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, port: int, address: str, timeout: int = 30):
        super().__init__(host, port=port, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self) -> None:
        sock = socket.create_connection((self.address, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def request(method: str, path: str, body: dict | None = None) -> dict:
    host, port, address, key = config()
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Authorization": f"Ghost {admin_token(key)}",
        "Accept-Version": "v6.0",
        "Accept": "application/json",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    connection = PinnedHTTPSConnection(host, port, address)
    write = method in {"POST", "PUT"}
    try:
        connection.request(method, f"/ghost/api/admin{path}", body=data, headers=headers)
        response = connection.getresponse()
        text = response.read().decode("utf-8", "replace")
        if response.status >= 300:
            if write and response.status >= 500:
                fail(
                    "Ghost write result is unknown after a server error; do not retry. "
                    "List posts and reconcile title/status before deciding whether another write is safe."
                )
            try:
                detail = json.loads(text)
            except json.JSONDecodeError:
                detail = text[:500]
            fail(f"Ghost Admin API returned {response.status}: {detail}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if write:
                fail(
                    "Ghost write result is unknown because its response was incomplete; do not retry. "
                    "List posts and reconcile title/status before deciding whether another write is safe."
                )
            fail(f"Ghost returned a malformed response: {text[:500]}")
    except SystemExit:
        raise
    except (OSError, TimeoutError, http.client.HTTPException, ssl.SSLError) as exc:
        if write:
            fail(
                "Ghost write result is unknown after a network failure; do not retry. "
                "List posts and reconcile title/status before deciding whether another write is safe."
            )
        fail(f"network error reaching Ghost: {exc}")
    finally:
        connection.close()


def read_html(path: str) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except OSError as exc:
        fail(f"cannot read HTML file: {exc}")


def gated(operation: str, path: str, body: dict) -> None:
    if not CONFIRMED:
        output(
            {
                "dry_run": True,
                "operation": operation,
                "request": body,
                "confirm": "append --confirm as the final argument",
            }
        )
        return
    result = request("POST" if operation == "create" else "PUT", path, body)
    output(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    posts = commands.add_parser("posts")
    posts.add_argument("--limit", type=int, default=15)

    create = commands.add_parser("create")
    create.add_argument("--title", required=True)
    create.add_argument("--html-file", required=True)
    create.add_argument("--status", choices=("draft", "published"), default="draft")

    update = commands.add_parser("update")
    update.add_argument("--id", required=True)
    update.add_argument("--updated-at", required=True)
    update.add_argument("--title")
    update.add_argument("--html-file")
    update.add_argument("--status", choices=("draft", "published"))
    return parser


def main() -> None:
    args = build_parser().parse_args(ARGS)
    if args.command == "posts":
        limit = max(1, min(args.limit, 100))
        output(request("GET", f"/posts/?limit={limit}&formats=html"))
        return
    if args.command == "create":
        post = {"title": args.title, "html": read_html(args.html_file), "status": args.status}
        gated("create", "/posts/?source=html", {"posts": [post]})
        return
    post = {"id": args.id, "updated_at": args.updated_at}
    if args.title is not None:
        post["title"] = args.title
    if args.html_file is not None:
        post["html"] = read_html(args.html_file)
    if args.status is not None:
        post["status"] = args.status
    gated("update", f"/posts/{urllib.parse.quote(args.id, safe='')}/?source=html", {"posts": [post]})


if __name__ == "__main__":
    main()
