#!/usr/bin/env python3
"""Baijiahao account lookup and HTML drafts. Stdlib only; no public publish.

HTTP contract researched from Wechatsync's baijiahao adapter; independently
implemented here. No upstream implementation is bundled. See SKILL.md.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://baijiahao.baidu.com"
MAX_BYTES = 4 * 1024 * 1024
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class DraftError(Exception):
    """Only locally authored, credential-free messages may leave the client."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def load_cookies():
    try:
        jar = json.loads(os.environ.get("BAIJIAHAO_COOKIES", ""))
    except (ValueError, TypeError):
        raise DraftError("Connect Baijiahao first; BAIJIAHAO_COOKIES must be a JSON cookie array.") from None
    if not isinstance(jar, list) or not jar or any(not isinstance(c, dict) for c in jar):
        raise DraftError("BAIJIAHAO_COOKIES must be a non-empty JSON cookie array.")
    return jar


def cookie_header(jar, url):
    parsed = urllib.parse.urlsplit(url)
    if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN:
        raise DraftError("Request outside the Baijiahao origin refused.")
    host = parsed.hostname
    request_path = parsed.path or "/"
    pairs = []
    for cookie in jar:
        domain = cookie.get("domain", "")
        if not isinstance(domain, str) or not domain:
            continue  # Domainless secrets must not be sent to a guessed host.
        domain = domain.lstrip(".").lower()
        if domain not in {"baidu.com", "baijiahao.baidu.com"}:
            continue
        if cookie.get("hostOnly") and host != domain:
            continue
        path = cookie.get("path") or "/"
        if not isinstance(path, str) or not path.startswith("/"):
            continue
        if request_path != path and not request_path.startswith(path.rstrip("/") + "/"):
            continue
        expires = cookie.get("expirationDate", cookie.get("expires"))
        if expires is not None:
            try:
                # Browser session exports sometimes use -1 for no expiration.
                if float(expires) >= 0 and float(expires) <= time.time():
                    continue
            except (ValueError, TypeError):
                raise DraftError("Invalid cookie expiration; reconnect Baijiahao.") from None
        name, value = cookie.get("name"), cookie.get("value")
        if not isinstance(name, str) or not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name):
            raise DraftError("Invalid cookie name; reconnect Baijiahao.")
        if not isinstance(value, str) or any(ord(c) < 33 or ord(c) > 126 or c in ';,"\\' for c in value):
            raise DraftError("Invalid cookie value; reconnect Baijiahao.")
        pairs.append((len(path), f"{name}={value}"))
    if not pairs:
        raise DraftError("No valid Baijiahao cookies for this request; reconnect.")
    return "; ".join(pair for _, pair in sorted(pairs, key=lambda p: -p[0]))


class Client:
    def __init__(self, cookies):
        self.cookies = cookies
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, path, *, fields=None, token=None):
        url = ORIGIN + path
        headers = {"User-Agent": UA, "Accept": "application/json, text/html", "Origin": ORIGIN,
                   "Referer": ORIGIN + "/builder/rc/edit", "Accept-Encoding": "identity"}
        body = None
        if fields is not None:
            body = urllib.parse.urlencode(fields).encode("utf-8")
            if len(body) > 16 * 1024 * 1024:
                raise DraftError("Encoded article is too large (maximum 16 MiB).")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if token:
            if not re.fullmatch(r"[\x21-\x7e]{1,2048}", token):
                raise DraftError("Unexpected editor token format; reconnect.")
            headers["token"] = token
        request = urllib.request.Request(url, data=body, headers=headers)
        request.add_unredirected_header("Cookie", cookie_header(self.cookies, url))
        try:
            with self.opener.open(request, timeout=30) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise DraftError("Upstream response exceeds the read limit.")
                return raw.decode("utf-8")
        except urllib.error.HTTPError as error:
            raise DraftError(f"Baijiahao returned HTTP {error.code}; check login, access or rate limits.") from None
        except (OSError, ValueError, UnicodeError, urllib.error.URLError, http.client.HTTPException):
            raise DraftError("Baijiahao request failed; check the connection and account.") from None

    def whoami(self):
        response = parse_response(self.request("/builder/app/appinfo"))
        user = response.get("data", {}).get("user") if isinstance(response.get("data"), dict) else None
        if response.get("errno") != 0 or not isinstance(user, dict) or not user.get("userid") or not user.get("name"):
            raise DraftError("Account lookup failed; reconnect Baijiahao or check account access.")
        return {"user_id": str(user["userid"]), "name": user["name"]}

    def draft(self, fields):
        account = self.whoami()
        editor = self.request("/builder/rc/edit")
        match = re.search(r"window\.__BJH__INIT__AUTH__\s{0,30}=\s{0,30}['\"]([^'\"\r\n]{1,2048})['\"]", editor)
        if not match:
            raise DraftError("Editor authorization is unavailable; reconnect or open the editor manually.")
        try:
            response = parse_response(self.request("/pcui/article/save?callback=bjhdraft", fields=fields, token=match[1]))
            result = response.get("ret")
            article_id = result.get("article_id") if isinstance(result, dict) else None
            if response.get("errno") != 0 or not isinstance(article_id, (str, int)) or isinstance(article_id, bool):
                raise DraftError("Draft save did not return a confirmed article ID.")
            article_id = str(article_id)
            if not re.fullmatch(r"[0-9A-Za-z_-]{1,100}", article_id):
                raise DraftError("Draft save returned an unexpected article ID.")
        except DraftError as error:
            raise DraftError(f"{error} Draft outcome may be unknown. Inspect the editor/draft list before retrying; do not resubmit automatically.") from None
        return {"status": "draft", "account": account, "draft_id": article_id,
                "edit_url": ORIGIN + "/builder/rc/edit?" + urllib.parse.urlencode({"type": "news", "article_id": article_id}),
                "published": False}


def parse_response(text):
    text = text.strip()
    if text.startswith("bjhdraft("):
        match = re.fullmatch(r"bjhdraft\((.*)\)\s*;?", text, re.DOTALL)
        if not match:
            raise DraftError("Invalid Baijiahao response; inspect the editor manually.")
        text = match[1]
    try:
        data = json.loads(text)
    except ValueError:
        raise DraftError("Baijiahao returned a non-JSON response; login or verification may be required.") from None
    if not isinstance(data, dict):
        raise DraftError("Unexpected Baijiahao response shape.")
    return data


def draft_fields(title, content):
    if not title.strip() or not content.strip():
        raise DraftError("Title and HTML content must be non-empty.")
    if len(title) > 200 or len(content.encode("utf-8")) > MAX_BYTES:
        raise DraftError("Title or HTML content exceeds the local input limit.")
    return {"title": title, "content": content, "type": "news", "feed_cat": "1",
            "len": str(len(content.encode("utf-16-le")) // 2), "activity_list": "[]",
            "source_reprinted_allow": "0", "original_status": "0", "original_handler_status": "1",
            "isBeautify": "false", "subtitle": "", "bjhtopic_id": "", "bjhtopic_info": ""}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    confirmed = bool(args) and args[-1] == "--confirm"
    if confirmed:
        args.pop()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("whoami")
    draft = commands.add_parser("draft", help="Dry-run HTML draft; add --confirm LAST to save it.")
    draft.add_argument("--title", required=True)
    draft.add_argument("--content-file", required=True, help="UTF-8 HTML fragment, not Markdown.")
    options = parser.parse_args(args)
    try:
        if options.command == "whoami":
            result = Client(load_cookies()).whoami()
        else:
            try:
                with Path(options.content_file).open("rb") as handle:
                    raw = handle.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise DraftError("HTML content exceeds 4 MiB.")
                content = raw.decode("utf-8")
            except (OSError, UnicodeError):
                raise DraftError("Cannot read content-file as UTF-8 HTML.") from None
            fields = draft_fields(options.title, content)
            result = Client(load_cookies()).draft(fields) if confirmed else {
                "dry_run": True, "status": "draft", "published": False, "payload": fields,
                "note": "External images are not re-hosted. Review images and formatting in the editor before publishing."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except DraftError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
