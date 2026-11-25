"""Credential-scoped HTTP and CLI support for standalone publishing skill bundles.

Canonical source: skills/_shared/publishing_http.py. Generated bundle copies
are synchronized by scripts/sync_publishing_http.py. No third-party dependencies.
"""

from __future__ import annotations

import argparse
import http.client
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

LIMIT = 4 * 1024 * 1024


class Error(Exception):
    def __init__(self, message, *, result=None):
        super().__init__(message)
        self.result = result


def require(
    condition, message="Unexpected platform response; check login or account access."
):
    if not condition:
        raise Error(message)


def identifier(value):
    require(
        isinstance(value, (str, int)) and not isinstance(value, bool),
        "Missing result ID.",
    )
    result = str(value)
    require(bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", result)), "Invalid result ID.")
    return result


def identity(value, name=None):
    return {"user_id": identifier(value), "name": str(name or value)[:200]}


def saved(value, url, **extra):
    return {
        "status": "draft",
        "draft_id": identifier(value),
        "edit_url": url,
        "published": False,
        "readback_verified": False,
        **extra,
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HTTP:
    def __init__(self, env, origins, referer, cookies=None):
        self.env = env
        self.origins = set(origins)
        self.referer = referer
        self.cookies = cookies
        self.opener = urllib.request.build_opener(NoRedirect())

    def jar(self):
        if self.cookies is None:
            try:
                self.cookies = json.loads(os.environ.get(self.env, ""))
            except (ValueError, TypeError):
                raise Error(
                    f"{self.env} is missing/invalid; connect this platform in Studio."
                ) from None
        require(
            isinstance(self.cookies, list)
            and bool(self.cookies)
            and all(isinstance(c, dict) for c in self.cookies),
            "Invalid cookie array; reconnect in Studio.",
        )
        return self.cookies

    def matching(self, url):
        parsed = urllib.parse.urlsplit(url)
        require(
            f"{parsed.scheme}://{parsed.netloc}" in self.origins,
            "Off-origin request refused.",
        )
        path = parsed.path or "/"
        pairs = []
        for c in self.jar():
            domain = c.get("domain", "")
            if not isinstance(domain, str) or not domain:
                continue
            domain = domain.lstrip(".").lower()
            if "." not in domain or domain in {"com.cn", "co.uk", "com", "cn", "net"}:
                continue
            host = parsed.hostname
            if host != domain and (
                c.get("hostOnly") or not host.endswith("." + domain)
            ):
                continue
            cp = c.get("path") or "/"
            if not isinstance(cp, str) or not cp.startswith("/"):
                continue
            if path != cp and not path.startswith(cp.rstrip("/") + "/"):
                continue
            expiry = c.get("expirationDate", c.get("expires"))
            if expiry is not None:
                try:
                    expiry = float(expiry)
                except (TypeError, ValueError):
                    raise Error("Invalid cookie expiry; reconnect.") from None
                require(math.isfinite(expiry), "Invalid cookie expiry; reconnect.")
                if expiry >= 0 and expiry <= time.time():
                    continue
            name, value = c.get("name"), c.get("value")
            require(
                isinstance(name, str)
                and re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", name),
                "Invalid cookie name; reconnect.",
            )
            require(isinstance(value, str), "Invalid cookie value; reconnect.")
            # Chrome retains quoted values (e.g. Douban dbcl2) and commas
            # (ap_v). Preserve their wire representation. A comma cannot start
            # another Cookie pair; semicolons and header controls still can.
            inner = value[1:-1] if len(value) >= 2 and value.startswith('"') and value.endswith('"') else value
            require(
                all(33 <= ord(ch) <= 126 and ch not in ';"\\' for ch in inner),
                "Invalid cookie value; reconnect.",
            )
            pairs.append((len(cp), name, value))
        return sorted(pairs, key=lambda row: -row[0])

    def cookie(self, name, url, required=True):
        values = [v for _, n, v in self.matching(url) if n == name]
        if required:
            require(bool(values), "Required session/CSRF cookie is missing; reconnect.")
        return values[0] if values else ""

    def request(
        self,
        url,
        *,
        method="GET",
        data=None,
        form=None,
        headers=None,
        raw=None,
        text=False,
        empty=False,
    ):
        cookies = self.matching(url)
        require(bool(cookies), "No matching login cookies; reconnect in Studio.")
        body = raw
        origin = self.referer.split("/", 3)[:3]
        request_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "identity",
            "Origin": "/".join(origin),
            "Referer": self.referer,
        }
        if data is not None:
            body = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
            request_headers["Content-Type"] = "application/json"
        if form is not None:
            body = urllib.parse.urlencode(form).encode()
            request_headers["Content-Type"] = "application/x-www-form-urlencoded"
        require(body is None or len(body) <= LIMIT, "Encoded request exceeds 4 MiB.")
        request_headers.update(headers or {})
        for value in request_headers.values():
            require(
                isinstance(value, str) and all(32 <= ord(ch) <= 126 for ch in value),
                "Invalid request header.",
            )
        req = urllib.request.Request(
            url, data=body, method=method, headers=request_headers
        )
        req.add_unredirected_header(
            "Cookie", "; ".join(n + "=" + v for _, n, v in cookies)
        )
        try:
            with self.opener.open(req, timeout=30) as response:
                body = response.read(LIMIT + 1)
                require(len(body) <= LIMIT, "Response exceeds read limit.")
                body = body.decode("utf-8")
        except urllib.error.HTTPError as error:
            error.close()
            raise Error(
                f"Platform returned HTTP {error.code}; check login, access or rate limits."
            ) from None
        except (
            OSError,
            ValueError,
            UnicodeError,
            urllib.error.URLError,
            http.client.HTTPException,
        ):
            raise Error("Platform transport failed; no automatic retry.") from None
        if text:
            return body
        if empty and not body.strip():
            return None
        try:
            result = json.loads(body)
        except ValueError:
            raise Error(
                "Platform returned non-JSON data; login or verification may be required."
            ) from None
        require(isinstance(result, (dict, list)), "Unexpected response shape.")
        return result


def read_content(path):
    try:
        with Path(path).open("rb") as f:
            raw = f.read(LIMIT + 1)
        require(len(raw) <= LIMIT, "Content exceeds 4 MiB.")
        content = raw.decode("utf-8")
    except (OSError, UnicodeError):
        raise Error("Cannot read content file as UTF-8.") from None
    require(bool(content.strip()), "Content is empty.")
    return content


def run(adapter_type, argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    confirmed = bool(args) and args[-1] == "--confirm"
    if confirmed:
        args.pop()
    adapter = adapter_type()
    parser = argparse.ArgumentParser(description=adapter.description)
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("whoami")
    if hasattr(adapter, "notebooks"):
        subs.add_parser("notebooks")
    write = subs.add_parser(
        adapter.command, help="Local dry-run; --confirm LAST performs the write."
    )
    write.add_argument("--title", required=True)
    write.add_argument("--content-file", required=True)
    write.add_argument("--format", choices=adapter.formats, default=adapter.formats[0])
    write.add_argument("--account-id")
    write.add_argument("--notebook-id")
    options = parser.parse_args(args)
    try:
        if options.command == "whoami":
            result = adapter.whoami()
        elif options.command == "notebooks":
            result = adapter.notebooks()
        else:
            require(
                bool(options.title.strip()) and len(options.title) <= 200,
                "Title must contain 1–200 characters.",
            )
            content = read_content(options.content_file)
            payload = adapter.prepare(options, content)
            if not confirmed:
                result = {
                    "dry_run": True,
                    "action": adapter.command,
                    "payload": payload,
                    "note": "No network or credentials accessed. Images are not re-hosted; review in the editor.",
                }
            else:
                # Identity and account permission checks happen before the first write.
                account = adapter.whoami()
                try:
                    result = adapter.write(options, payload, account)
                except Error as error:
                    raise Error(
                        str(error)
                        + " Write outcome may be unknown; inspect the original item before retrying.",
                        result=error.result,
                    ) from None
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Error as error:
        print(
            json.dumps(
                {
                    "error": str(error),
                    **({"partial_result": error.result} if error.result else {}),
                },
                ensure_ascii=False,
            )
        )
        return 1
    except (TypeError, KeyError, AttributeError, IndexError, ValueError):
        # Never echo platform responses or tokens in exception text.
        print(
            json.dumps(
                {
                    "error": "Unexpected platform data. If a write started, reconcile the original item before retrying."
                }
            )
        )
        return 1
