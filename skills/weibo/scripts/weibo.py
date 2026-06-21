#!/usr/bin/env python3
"""
weibo — read & post on 微博 (weibo.com) with the user's own login cookies (BYOC).
Standard-library only (urllib), no third-party deps.

Drives Weibo's web ``ajax`` API (the same one weibo.com's SPA uses), authenticated
by the login cookies. State-changing calls send the ``XSRF-TOKEN`` cookie both as
the ``x-xsrf-token`` header and as the ``st`` form field.

The connector injects the cookie jar as a JSON env var ``WEIBO_COOKIES``.

⚠️ NOT YET E2E-VERIFIED: unlike the other cookie skills, this one was built from
the documented web API but could not be tested against a live account (no 微博
connection was present at build time). Treat the first live run as the
verification — if an endpoint shape drifted, it will surface as a clear error.

Weibo posts are short-form (a 微博), so there is no draft step and no private
mode — a confirmed post is immediately public. ``post`` is GATED by a trailing
``--confirm`` (honored only as the last arg); without it, it dry-runs.

Examples:
  python3 weibo.py whoami
  python3 weibo.py posts --limit 20
  python3 weibo.py post --content "hello" --confirm
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
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "weibo"
BASE = "https://weibo.com"

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


def load_cookies() -> list:
    env = f"{PLATFORM.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(f"{env} is not set — connect 微博 at "
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


def cookie_value(jar: list, name: str):
    for c in jar:
        if c.get("name") == name:
            return c.get("value")
    return None


def request(method, url, jar, *, headers=None, form=None):
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": BASE + "/",
    }
    if headers:
        hdrs.update(headers)
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → the cookie is not re-sent if the API 30x-redirects to a
    # different host (e.g. a login page), so the jar never leaks off-site.
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return resp.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            if e.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        except Exception:
            pass
        return e.code, raw.decode("utf-8", "replace")
    except urllib.error.URLError as e:
        die(f"network error reaching {url}: {e.reason}")


def get_json(url, jar):
    status, text = request("GET", url, jar)
    if status in (401, 403):
        die(f"auth failed ({status}) on {url} — cookie likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {text[:300]}")


def st_token(jar):
    tok = cookie_value(jar, "XSRF-TOKEN")
    if not tok:
        die("no XSRF-TOKEN cookie — reconnect 微博 at "
            "https://auth.acedata.cloud/user/connections.")
    return tok


# ── commands ────────────────────────────────────────────────────────

def wb_uid(jar):
    cfg = get_json(f"{BASE}/ajax/setting/getConfig", jar)
    data = cfg.get("data") or {}
    uid = data.get("uid")
    if not uid:
        die("not logged in or uid unavailable (cookie expired?) — reconnect 微博 "
            "at https://auth.acedata.cloud/user/connections.")
    return uid


def cmd_whoami(jar, _args):
    uid = wb_uid(jar)
    info = get_json(f"{BASE}/ajax/profile/info?uid={uid}", jar)
    u = (info.get("data") or {}).get("user") or {}
    out({
        "uid": str(uid),
        "name": u.get("screen_name"),
        "url": f"{BASE}/u/{uid}",
        "followers_count": u.get("followers_count"),
        "friends_count": u.get("friends_count"),
        "statuses_count": u.get("statuses_count"),
    })


def _fmt(m: dict) -> dict:
    mid = m.get("mblogid") or m.get("id")
    return {
        "id": str(m.get("id")),
        "mblogid": m.get("mblogid"),
        "text": (m.get("text_raw") or m.get("text") or "")[:140],
        "url": f"{BASE}/{m.get('user', {}).get('idstr', '')}/{mid}" if mid else None,
        "reposts_count": m.get("reposts_count"),
        "comments_count": m.get("comments_count"),
        "attitudes_count": m.get("attitudes_count"),
        "created_at": m.get("created_at"),
    }


def cmd_posts(jar, args):
    uid = wb_uid(jar)
    collected, page = [], 1
    while len(collected) < args.limit:
        url = f"{BASE}/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0"
        d = get_json(url, jar)
        items = (d.get("data") or {}).get("list") or []
        if not items:
            break
        collected.extend(items)
        page += 1
    items = collected[: args.limit]
    out({"count": len(items), "posts": [_fmt(m) for m in items]})


def cmd_post(jar, args):
    if not args.content and not args.content_file:
        die("provide --content <text> or --content-file <path>")
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    content = (content or "").strip()
    if not content:
        die("content is empty")

    if not CONFIRM:
        out({
            "dry_run": True, "command": "post", "platform": "weibo",
            "content_preview": content[:140],
            "note": "Re-run with --confirm as the LAST argument to actually post. "
                    "This posts a PUBLIC 微博 on the user's real account (微博 has no "
                    "draft; a confirmed post is immediately public).",
        })
        return

    tok = st_token(jar)
    form = {"content": content, "st": tok, "visible": 0,
            "pic_id": "", "pdetail": "", "media": "", "vote": ""}
    status, text = request("POST", f"{BASE}/ajax/statuses/update", jar,
                           headers={"x-xsrf-token": tok, "Origin": BASE}, form=form)
    try:
        r = json.loads(text)
    except json.JSONDecodeError:
        die(f"post returned non-JSON ({status}): {text[:300]}")
    data = r.get("data") or {}
    if r.get("ok") == 1 or data.get("id"):
        mid = data.get("mblogid") or data.get("id")
        out({"ok": True, "posted": True, "id": str(data.get("id")),
             "url": f"{BASE}/detail/{mid}" if mid else None})
    else:
        die(f"post failed ({status}): {str(r)[:300]}")


COMMANDS = {
    "whoami": cmd_whoami,
    "posts": cmd_posts,
    "post": cmd_post,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="weibo.py", description="weibo cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("posts", help="list the user's recent 微博 + engagement")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("post", help="publish a 微博 (GATED by trailing --confirm)")
    sp.add_argument("--content", help="post text inline")
    sp.add_argument("--content-file", help="path to a text file")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
