#!/usr/bin/env python3
"""
csdn — read & publish on CSDN (blog.csdn.net) with the user's own login cookies
(BYOC). Standard-library only (urllib + hmac/hashlib for the editor signature),
no third-party deps, so it runs in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var ``CSDN_COOKIES``.

CSDN fronts its APIs with a WAF that 403s requests lacking a full browser
fingerprint, so every request sends the complete header set. Reads
(get-business-list) are cookie-only; the editor's saveArticle is on bizapi and
needs an HMAC ``x-ca-*`` signature (the key/secret are baked into CSDN's web JS).

Read commands run directly. ``publish`` is GATED by a trailing ``--confirm``
(honored only as the last arg). ``--draft-only`` saves a private draft (status=2).

Examples:
  python3 csdn.py whoami
  python3 csdn.py articles --limit 20
  python3 csdn.py article <article-id>
  python3 csdn.py publish --title T --content-file a.md --draft-only --confirm
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "csdn"
# x-ca signing constants — hard-coded in CSDN's editor web bundle (public).
CA_KEY = "203803574"
CA_SECRET = b"9znpamsyl2c7cdrr9sas0le9vbc3r6ba"

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# ── Cookie jar ──────────────────────────────────────────────────────

def load_cookies() -> list:
    env = f"{PLATFORM.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(f"{env} is not set — connect CSDN at "
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


# ── HTTP with a full browser fingerprint (CSDN WAF needs it) ────────

def _browser_headers(jar: list, url: str, referer: str, origin: str) -> dict:
    return {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
        "Origin": origin,
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def request(method: str, url: str, jar: list, *, referer, origin, headers=None, body=None):
    hdrs = _browser_headers(jar, url, referer, origin)
    if headers:
        hdrs.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → urllib will NOT re-send the cookie if the API 30x-redirects
    # to a different host (e.g. a login page), so the jar never leaks off-site.
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


def get_json(url: str, jar: list, *, referer, origin):
    status, text = request("GET", url, jar, referer=referer, origin=origin)
    if "WAF" in text and "403" in text:
        die("CSDN WAF blocked the request (403). The cookie may be expired or "
            "the account needs to re-pass CSDN's captcha; reconnect at "
            "https://auth.acedata.cloud/user/connections.")
    if status in (401, 403):
        die(f"auth failed ({status}) on {url} — cookie likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {text[:300]}")


def ca_sign(method: str, path_with_query: str, content_type: str) -> dict:
    """Aliyun-API-Gateway style HMAC-SHA256 signature CSDN's bizapi requires."""
    nonce = str(uuid.uuid4())
    string_to_sign = (
        f"{method}\n*/*\n\n{content_type}\n\n"
        f"x-ca-key:{CA_KEY}\nx-ca-nonce:{nonce}\n{path_with_query}"
    )
    sig = base64.b64encode(
        hmac.new(CA_SECRET, string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode()
    return {
        "x-ca-key": CA_KEY,
        "x-ca-nonce": nonce,
        "x-ca-signature": sig,
        "x-ca-signature-headers": "x-ca-key,x-ca-nonce",
    }


# ── commands ────────────────────────────────────────────────────────

BLOG = "https://blog.csdn.net"
BIZ = "https://bizapi.csdn.net"


def csdn_username(jar):
    u = cookie_value(jar, "UserName")
    if not u:
        die("no UserName cookie — reconnect CSDN at "
            "https://auth.acedata.cloud/user/connections.")
    return u


def _list_page(jar, username, page, size):
    url = f"{BLOG}/community/home-api/v1/get-business-list?" + urllib.parse.urlencode(
        {"page": page, "size": size, "businessType": "blog", "username": username})
    d = get_json(url, jar, referer=f"{BLOG}/{username}?type=blog", origin=BLOG)
    if d.get("code") != 200:
        die(f"CSDN list error ({d.get('code')}): {d.get('message')}")
    data = d.get("data") or {}
    return data.get("list") or [], data.get("total")


def cmd_whoami(jar, _args):
    username = csdn_username(jar)
    nick = cookie_value(jar, "UserNick")
    if nick:
        nick = urllib.parse.unquote(str(nick))
    # verify the session is live + surface the article total
    _, total = _list_page(jar, username, 1, 1)
    out({
        "username": username,
        "nickname": nick,
        "url": f"{BLOG}/{username}",
        "articles_total": total,
    })


def _fmt(a: dict) -> dict:
    return {
        "id": str(a.get("articleId")) if a.get("articleId") is not None else None,
        "title": a.get("title"),
        "url": a.get("url"),
        "view_count": a.get("viewCount"),
        "digg_count": a.get("diggCount"),
        "comment_count": a.get("commentCount"),
        "collect_count": a.get("collectCount"),
        "post_time": a.get("postTime") or a.get("formatTime"),
    }


def cmd_articles(jar, args):
    username = csdn_username(jar)
    collected, page, total = [], 1, None
    while len(collected) < args.limit:
        items, total = _list_page(jar, username, page, min(100, args.limit))
        if not items:
            break
        collected.extend(items)
        if total is not None and len(collected) >= total:
            break
        page += 1
    items = collected[: args.limit]
    out({"total": total, "count": len(items), "articles": [_fmt(a) for a in items]})


def cmd_article(jar, args):
    username = csdn_username(jar)
    page = 1
    while True:
        items, total = _list_page(jar, username, page, 100)
        if not items:
            break
        for a in items:
            if str(a.get("articleId")) == str(args.id):
                out(_fmt(a))
                return
        page += 1
        if total is not None and page * 100 > total:
            break
    die(f"article {args.id} not found among your published articles")


def cmd_publish(jar, args):
    if not args.title:
        die("--title is required")
    if not args.content_file and args.content is None:
        die("provide --content-file <path.md> or --content <markdown>")
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    content = content or ""

    if not CONFIRM:
        out({
            "dry_run": True, "command": "publish", "platform": "csdn",
            "title": args.title, "draft_only": args.draft_only,
            "content_bytes": len(content),
            "note": "CSDN content is Markdown. Re-run with --confirm as the LAST "
                    "argument to actually write. Without --draft-only it publishes "
                    "a PUBLIC article on the user's real account.",
        })
        return

    path = "/blog-console-api/v3/mdeditor/saveArticle"
    url = f"{BIZ}{path}"
    status_code = 2 if args.draft_only else 0
    body = {
        "title": args.title,
        "markdowncontent": content,
        "content": content,
        "readType": "public",
        "status": status_code,
        "categories": "",
        "tags": args.tags or "",
        "type": "original",
        "original_link": "",
        "authorized_status": False,
        "Description": content[:200],
        "not_auto_saved": "1",
        "source": "pc_mdeditor",
        "cover_images": [],
        "cover_type": 0,
        "is_new": 1,
        "vote_id": 0,
        "pubStatus": "draft" if args.draft_only else "publish",
    }
    sign = ca_sign("POST", path, "application/json")
    # The signature signs Accept=*/* and Content-Type=application/json verbatim,
    # so the request must send exactly those (override the browser default Accept).
    sign["Accept"] = "*/*"
    status, text = request("POST", url, jar, referer="https://editor.csdn.net/",
                           origin="https://editor.csdn.net", headers=sign, body=body)
    try:
        res = json.loads(text)
    except json.JSONDecodeError:
        die(f"saveArticle returned non-JSON ({status}): {text[:300]}")
    if res.get("code") != 200:
        die(f"saveArticle failed (code={res.get('code')}): {res.get('msg') or res.get('message')}")
    data = res.get("data") or {}
    aid = data.get("id")
    if args.draft_only:
        out({"ok": True, "draft_only": True, "article_id": str(aid),
             "edit_url": f"https://editor.csdn.net/md/?articleId={aid}"})
    else:
        out({"ok": True, "published": True, "article_id": str(aid),
             "url": data.get("url") or f"{BLOG}/{csdn_username(jar)}/article/details/{aid}"})


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="csdn.py", description="csdn cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("articles", help="list the user's published articles + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("article", help="one article's stats")
    sp.add_argument("id")
    sp = sub.add_parser("publish", help="create/publish an article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--draft-only", action="store_true", help="save a private draft; do NOT go public")
    sp.add_argument("--tags", help="comma-separated article tags")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
