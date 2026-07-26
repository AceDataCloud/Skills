#!/usr/bin/env python3
"""
oschina — read & publish on 开源中国 (my.oschina.net) with the user's own login
cookies (BYOC). Standard-library only (urllib), no third-party deps, so it runs
in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var ``OSCHINA_COOKIES``
— a list of ``{name, value, domain, ...}`` dicts captured by the ACE extension.

Read commands run directly. ``publish`` is GATED: without a trailing
``--confirm`` it only dry-runs. ``--confirm`` is honored ONLY as the last
argument, so a title/content that merely contains "--confirm" can never silently
go live.

NOTE: 开源中国 exposes no public "publish" API — only draft creation. This CLI
creates a draft and returns its editor URL; the user finishes publishing in the
开源中国 editor.

Examples:
  python3 oschina.py whoami
  python3 oschina.py draft --title T --content-file a.md --confirm
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
PLATFORM = "oschina"
API = "https://apiv1.oschina.net/oschinapi"
ORIGIN = "https://my.oschina.net"
MAX_CONTENT_BYTES = 10 * 1024 * 1024

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects outright.

    add_unredirected_header only protects the Cookie; urllib copies every other
    header onto the redirected request, so a 30x to a foreign host could hand
    over any auth header we add later.
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
        die(f"{env} is not set — connect 开源中国 at "
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
        "Origin": ORIGIN,
        "Referer": f"{ORIGIN}/",
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
            die(f"开源中国 redirected {method} {url} — not followed, so no "
                f"credential left oschina.net. You are most likely logged out; "
                f"reconnect at https://auth.acedata.cloud/user/connections."
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
            die(f"开源中国 write {method} {url} did not return a result "
                f"({e.reason}); the outcome is UNKNOWN. Check your 开源中国 "
                f"drafts before retrying so you do not create a duplicate.")
        die(f"network error reaching {url}: {e.reason}")


def api_call(method: str, path: str, jar: list, *, body=None, write: bool = False):
    """Unwrap the {success, message, code, result} envelope, dying on failure.
    开源中国 returns HTTP 200 even for logical errors."""
    url = f"{API}{path}"
    status, text = request(method, url, jar, body=body, write=write)
    try:
        env = json.loads(text)
    except json.JSONDecodeError:
        if write:
            die(f"开源中国 write to {path} returned a non-JSON response ({status}); "
                f"the outcome is UNKNOWN. Check your drafts before retrying. "
                f"Body: {text[:200]}")
        die(f"non-JSON response ({status}) from {path}: {text[:300]}")
    if not isinstance(env, dict):
        die(f"unexpected response from {path}: {text[:300]}")
    if not env.get("success"):
        msg = str(env.get("message") or "")
        code = env.get("code")
        if code in (40001, 401, 403) or "未登录" in msg or "登录" in msg:
            die(f"auth failed (code={code}: {msg}) — cookie likely expired. "
                f"Reconnect at https://auth.acedata.cloud/user/connections.")
        die(f"开源中国 API error on {path} (code={code}): {msg}")
    return env.get("result")


# ── commands ────────────────────────────────────────────────────────

def os_me(jar) -> dict:
    me = api_call("GET", "/user/myDetails", jar)
    if not isinstance(me, dict) or not me.get("userId"):
        die("could not read 开源中国 profile (cookie expired?)")
    return me


def cmd_whoami(jar, _args):
    me = os_me(jar)
    vo = me.get("userVo") or {}
    uid = me.get("userId")
    out({
        "user_id": str(uid),
        "name": vo.get("name"),
        "url": f"{ORIGIN}/u/{uid}",
        "avatar": vo.get("portraitUrl"),
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


def cmd_draft(jar, args):
    if not args.title:
        die("--title is required")
    content = read_content(args)

    if not CONFIRM:
        out({
            "dry_run": True, "command": "draft", "platform": PLATFORM,
            "title": args.title, "catalog": args.catalog,
            "private": not args.public,
            "content_characters": len(content),
            "note": "开源中国 content is Markdown. Re-run with --confirm as the LAST "
                    "argument to actually create the draft. 开源中国 exposes no "
                    "publish API — finish publishing in the 开源中国 editor.",
        })
        return

    me = os_me(jar)
    uid = me.get("userId")
    result = api_call("POST", "/api/draft/save_draft", jar, write=True, body={
        "title": args.title,
        "user": int(uid),
        "content": content,
        "contentType": 1,  # 1 = Markdown, 2 = HTML
        "catalog": args.catalog,
        "originUrl": "",
        "privacy": not args.public,
        "disableComment": False,
    })
    draft_id = result.get("id") if isinstance(result, dict) else None
    if not draft_id:
        die(f"draft creation failed: {str(result)[:300]}")
    out({
        "ok": True,
        "draft_only": True,
        "draft_id": str(draft_id),
        "edit_url": f"{ORIGIN}/u/{uid}/blog/write/draft/{draft_id}",
        "note": "Draft saved. 开源中国 has no publish API — open edit_url to publish.",
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "draft": cmd_draft,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="oschina.py", description="开源中国 cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("draft", help="create a draft article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--catalog", type=int, default=0, help="开源中国 catalog id (0 = default)")
    sp.add_argument("--public", action="store_true",
                    help="mark the draft non-private; it still needs publishing in the editor")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
