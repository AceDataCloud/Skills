#!/usr/bin/env python3
"""
segmentfault — read & publish on SegmentFault 思否 (segmentfault.com) with the
user's own login cookies (BYOC). Standard-library only (urllib), no third-party
deps, so it runs in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var
``SEGMENTFAULT_COOKIES`` — a list of ``{name, value, domain, ...}`` dicts
captured by the ACE extension.

Read commands run directly. ``draft`` is GATED: without a trailing ``--confirm``
it only dry-runs. ``--confirm`` is honored ONLY as the last argument, so a
title/content that merely contains "--confirm" can never silently go live.

NOTE: SegmentFault's write API creates a DRAFT. This CLI returns the draft's
editor URL; the user finishes publishing in the SegmentFault editor.

Examples:
  python3 segmentfault.py whoami
  python3 segmentfault.py draft --title T --content-file a.md --confirm
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
PLATFORM = "segmentfault"
BASE = "https://segmentfault.com"
MAX_CONTENT_BYTES = 10 * 1024 * 1024

# Bounded so a hostile/huge page cannot cause catastrophic backtracking.
_TOKEN_RE = re.compile(r'serverData"\s*:\s*\{\s*"Token"\s*:\s*"([^"]{1,500})"')

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects outright.

    add_unredirected_header only protects the Cookie; urllib still copies every
    other header (including the per-session ``token``) onto the redirected
    request, so a 30x to an attacker host would hand over the write token.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# ── Cookie jar (shared pattern across the cookie-BYOC skills) ────────

def load_cookies() -> list:
    env = f"{PLATFORM.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(f"{env} is not set — connect SegmentFault at "
            f"https://auth.acedata.cloud/user/connections, then retry.")
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"{env} is not valid JSON: {e}")
    if not isinstance(jar, list):
        die(f"{env} must be a JSON list of cookies, got {type(jar).__name__}")
    return jar


def _domain_matches(host: str, domain: str) -> bool:
    d = domain.lstrip(".").lower()
    h = host.lower()
    return not d or h == d or h.endswith("." + d)


def cookie_header(jar: list, url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    host_in_scope = any(
        c.get("domain") and _domain_matches(host, str(c["domain"])) for c in jar
    )
    parts = []
    for c in jar:
        name, value = c.get("name"), c.get("value")
        if not name or value is None:
            continue
        domain = c.get("domain")
        if domain:
            if not _domain_matches(host, str(domain)):
                continue
        elif not host_in_scope:
            continue
        parts.append(f"{name}={value}")
    return "; ".join(parts)


def request(method: str, url: str, jar: list, *, headers=None, body=None, write: bool = False):
    hdrs = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Origin": BASE,
        "Referer": f"{BASE}/",
    }
    if headers:
        hdrs.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → the cookie is not re-sent if the API 30x-redirects to a
    # different host (e.g. a login page), so the jar never leaks off-site.
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    try:
        with _OPENER.open(req, timeout=30) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return resp.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            die(f"SegmentFault redirected {method} {url} — not followed, so no "
                f"credential left segmentfault.com. You are most likely logged "
                f"out; reconnect at https://auth.acedata.cloud/user/connections."
                + (" This was a WRITE: its outcome is UNKNOWN — check your "
                   "drafts before retrying." if write else ""))
        raw = e.read()
        try:
            if e.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "replace")
    except urllib.error.URLError as e:
        if write:
            die(f"SegmentFault write {method} {url} did not return a result "
                f"({e.reason}); the outcome is UNKNOWN. Check your SegmentFault "
                f"drafts before retrying so you do not create a duplicate.")
        die(f"network error reaching {url}: {e.reason}")


def _auth_died(status: int, text: str) -> None:
    if status in (401, 403) or text.strip('"') == "Unauthorized":
        die("auth failed — cookie expired or invalid. Reconnect at "
            "https://auth.acedata.cloud/user/connections.")


def session_token(jar: list) -> str:
    """The write API needs a per-session token embedded in the /write page."""
    status, html = request("GET", f"{BASE}/write", jar)
    _auth_died(status, html)
    m = _TOKEN_RE.search(html)
    if not m:
        die("could not find the SegmentFault session token on /write — you are "
            "probably logged out. Reconnect at "
            "https://auth.acedata.cloud/user/connections.")
    return m.group(1)


# ── commands ────────────────────────────────────────────────────────

def cmd_whoami(jar, _args):
    status, html = request("GET", f"{BASE}/user/settings", jar)
    _auth_died(status, html)
    if status != 200:
        die(f"unexpected status {status} reading the profile")
    name = re.search(r'name="name"[^>]{0,300}?value="([^"]{1,200})"', html)
    avatar = re.search(
        r'src="(https://avatar-static\.segmentfault\.com/[^"]{1,300})"', html
    )
    if not name and "登录" in html:
        die("not logged in — cookie expired. Reconnect at "
            "https://auth.acedata.cloud/user/connections.")
    out({
        "platform": PLATFORM,
        "name": name.group(1) if name else None,
        "avatar": avatar.group(1) if avatar else None,
        "settings_url": f"{BASE}/user/settings",
    })


def read_content(args) -> str:
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    if content is None:
        die("provide --content-file <path.md> or --content <markdown>")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        die("content exceeds the 10 MiB safety limit")
    return content


def _extract_draft_id(text: str):
    """SegmentFault answers either [0, {...}] / [1, "error"] or a bare object."""
    try:
        res = json.loads(text)
    except json.JSONDecodeError:
        return None, f"non-JSON response: {text[:200]}"
    if isinstance(res, list):
        if res and res[0] == 1:
            return None, str(res[1] if len(res) > 1 else "unknown error")
        if len(res) > 1 and isinstance(res[1], dict) and res[1].get("id"):
            return res[1]["id"], None
        return None, f"unexpected list response: {text[:200]}"
    if isinstance(res, dict):
        if res.get("id"):
            return res["id"], None
        msg = res.get("message") or res.get("msg") or res.get("error") or res.get("errMsg")
        return None, str(msg or text[:200])
    return None, f"unexpected response: {text[:200]}"


def cmd_draft(jar, args):
    if not args.title:
        die("--title is required")
    content = read_content(args)
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]

    if not CONFIRM:
        out({
            "dry_run": True, "command": "draft", "platform": PLATFORM,
            "title": args.title, "tags": tags,
            "content_characters": len(content),
            "note": "SegmentFault content is Markdown. Re-run with --confirm as "
                    "the LAST argument to actually create the draft. The write "
                    "API creates a DRAFT — finish publishing in the SegmentFault "
                    "editor.",
        })
        return

    token = session_token(jar)
    status, text = request("POST", f"{BASE}/gateway/draft", jar,
                           headers={"token": token}, write=True,
                           body={"title": args.title, "tags": tags,
                                 "text": content, "object_id": "",
                                 "type": "article"})
    _auth_died(status, text)
    for marker in ("禁言", "锁定"):
        if marker in text:
            die(f"SegmentFault rejected the write ({marker}); the account is "
                f"restricted.")
    draft_id, err = _extract_draft_id(text)
    if not draft_id:
        die(f"draft creation failed (status {status}): {err}")
    out({
        "ok": True,
        "draft_only": True,
        "draft_id": str(draft_id),
        "edit_url": f"{BASE}/write?draftId={draft_id}",
        "note": "Draft saved. Open edit_url to review and publish.",
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "draft": cmd_draft,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="segmentfault.py",
                                description="SegmentFault 思否 cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("draft", help="create a draft article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--tags", help="comma-separated tag names")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
