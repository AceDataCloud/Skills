#!/usr/bin/env python3
"""Habr web-editor client using the user's encrypted Cookie jar."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "https://habr.com"
API = f"{BASE}/kek/v2"
RAW_ARGS = sys.argv[1:]
CONFIRMED = bool(RAW_ARGS) and RAW_ARGS[-1] == "--confirm"
ARGS = RAW_ARGS[:-1] if CONFIRMED else RAW_ARGS
CSRF_RE = re.compile(r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)', re.I)


class HabrError(Exception):
    pass


def output(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def fail(message: str) -> None:
    output({"error": message})
    raise SystemExit(1)


def load_cookies() -> list[dict]:
    raw = os.environ.get("HABR_COOKIES", "")
    if not raw:
        fail("HABR_COOKIES is not set; reconnect Habr and retry")
    try:
        cookies = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"HABR_COOKIES is not valid JSON: {exc}")
    if not isinstance(cookies, list):
        fail("HABR_COOKIES must be a JSON list")
    return cookies


def cookie_header(cookies: list[dict]) -> str:
    values = []
    for cookie in cookies:
        raw_domain = str(cookie.get("domain") or "").lower()
        if raw_domain not in {"habr.com", ".habr.com"}:
            continue
        name = cookie.get("name")
        value = cookie.get("value")
        if name and value is not None:
            values.append(f"{name}={value}")
    if not values:
        fail("HABR_COOKIES does not contain cookies scoped to habr.com")
    return "; ".join(values)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def raw_request(method: str, url: str, cookies: list[dict], body: dict | None = None, csrf: str = ""):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "habr.com":
        fail("refusing to send Habr credentials outside https://habr.com")
    data = json.dumps(body).encode() if body is not None else None
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Cookie": cookie_header(cookies),
        "Origin": BASE,
        "Referer": f"{BASE}/ru/article/new/",
        "User-Agent": "Mozilla/5.0 AceDataCloud-Habr-Skill/1.0",
        "X-Requested-With": "XMLHttpRequest",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    if csrf:
        headers["csrf-token"] = csrf
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def csrf_token(cookies: list[dict]) -> str:
    status, text = raw_request("GET", f"{BASE}/ru/article/new/", cookies)
    if status in (401, 403) or "habrahabr" in text and "login" in text.lower():
        fail("Habr login Cookie is expired; reconnect Habr and retry")
    match = CSRF_RE.search(text)
    if not match:
        fail("Habr editor did not expose a CSRF token; its private web contract may have changed")
    return match.group(1)


def request(
    method: str,
    path: str,
    cookies: list[dict],
    body: dict | None = None,
    write: bool = False,
    csrf_required: bool = False,
    silent: bool = False,
):
    def reject(message: str):
        if silent:
            raise HabrError(message)
        fail(message)

    try:
        csrf = csrf_token(cookies) if write or csrf_required else ""
        status, text = raw_request(method, f"{API}{path}", cookies, body, csrf)
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        if write:
            reject("Habr write result is unknown after a network failure; do not retry. Re-read the draft first.")
        reject(f"network error reaching Habr: {exc}")
    if write and status >= 500:
        reject("Habr write result is unknown after a server error; do not retry. Re-read the draft first.")
    if status in (401, 403):
        reject(f"Habr authentication failed ({status}); reconnect Habr and retry")
    try:
        value = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        if write:
            reject("Habr write result is unknown because its response was malformed; do not retry. Re-read the draft.")
        reject(f"Habr returned non-JSON ({status}); its private web contract may have changed")
    if status >= 400:
        reject(f"Habr web API returned {status}: {value}")
    return value


def read_payload(path: str) -> dict:
    try:
        value = json.loads(open(path, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read payload file: {exc}")
    if not isinstance(value, dict):
        fail("payload file must contain one JSON object")
    return value


def idempotence_key(payload: dict) -> str:
    current = {key: value for key, value in payload.items() if key != "idempotenceKey"}
    canonical = json.dumps(current, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return str(uuid.UUID(bytes=hashlib.sha256(canonical).digest()[:16], version=5))


def find_article_url(value: object) -> str | None:
    if isinstance(value, str):
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname == "habr.com" and re.match(r"^/(?:ru|en)/articles/\d+/?$", parsed.path):
            return value
    if isinstance(value, dict):
        for child in value.values():
            found = find_article_url(child)
            if found:
                return found
    if isinstance(value, list):
        for child in value:
            found = find_article_url(child)
            if found:
                return found
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    drafts = commands.add_parser("drafts")
    drafts.add_argument("--limit", type=int, default=20)
    get = commands.add_parser("get")
    get.add_argument("--id", required=True)
    save = commands.add_parser("save")
    save.add_argument("--id")
    save.add_argument("--payload-file", required=True)
    preview = commands.add_parser("preview")
    preview.add_argument("--payload-file", required=True)
    publish = commands.add_parser("publish")
    publish.add_argument("--id", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--id", required=True)
    return parser


def dry_run(operation: str, request_body: object) -> None:
    output({"dry_run": True, "operation": operation, "request": request_body, "confirm": "append --confirm"})


def main() -> None:
    args = build_parser().parse_args(ARGS)
    cookies = load_cookies()
    if args.command == "drafts":
        limit = max(1, min(args.limit, 100))
        output(request("GET", f"/articles/drafts?draftType=posts&page=1&perPage={limit}", cookies))
        return
    if args.command == "get":
        article_id = urllib.parse.quote(args.id, safe="")
        output(request("GET", f"/publication/post-data/{article_id}", cookies))
        return
    if args.command in {"save", "preview"}:
        payload = read_payload(args.payload_file)
        if args.command == "save":
            payload = {**payload, "idempotenceKey": idempotence_key(payload)}
            suffix = f"/{urllib.parse.quote(args.id, safe='')}" if args.id else ""
            path = f"/publication/save{suffix}"
            if not CONFIRMED:
                dry_run(args.command, payload)
                return
            output(request("POST", path, cookies, payload, write=True))
        else:
            output(request("POST", "/publication/preview", cookies, payload, csrf_required=True))
        return
    article_id = urllib.parse.quote(args.id, safe="")
    if args.command == "verify":
        article = request("GET", f"/articles/{article_id}/", cookies)
        url = find_article_url(article)
        if not url:
            fail("Habr does not expose a verified public URL for this article yet")
        output({"published": True, "url": url, "article": article})
        return
    if not CONFIRMED:
        dry_run("publish", {"article_id": args.id})
        return
    publish_result = request("POST", f"/articles/{article_id}/published", cookies, {}, write=True)
    try:
        article = request("GET", f"/articles/{article_id}/", cookies, silent=True)
    except HabrError:
        fail(
            "Habr accepted the publish request, but verification failed. Do not publish again; "
            f"run verify --id {args.id} to check the existing result."
        )
    url = find_article_url(publish_result) or find_article_url(article)
    if not url:
        fail(
            "Habr accepted the publish request, but no public URL is visible yet. Do not publish again; "
            f"run verify --id {args.id} to check the existing result."
        )
    output({"published": True, "url": url, "article": article})


if __name__ == "__main__":
    main()
