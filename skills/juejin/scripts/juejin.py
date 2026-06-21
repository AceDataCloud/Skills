#!/usr/bin/env python3
"""
juejin — read & publish on 掘金 (juejin.cn) with the user's own login cookies
(BYOC). Standard-library only (urllib), no third-party deps, so it runs in the
bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var ``JUEJIN_COOKIES``
— a list of ``{name, value, domain, ...}`` dicts captured by the ACE extension.

Read commands run directly. ``publish`` is GATED: without a trailing
``--confirm`` it only dry-runs. ``--confirm`` is honored ONLY as the last
argument, so a title/content that merely contains "--confirm" can never silently
go live. ``--draft-only`` stops after creating a private draft.

Examples:
  python3 juejin.py whoami
  python3 juejin.py articles --limit 20
  python3 juejin.py article <article-id>
  python3 juejin.py publish --title T --content-file a.md --draft-only --confirm
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
PLATFORM = "juejin"
API = "https://api.juejin.cn"

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


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
        die(f"{env} is not set — connect 掘金 at "
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


def request(method: str, url: str, jar: list, *, headers=None, body=None):
    hdrs = {
        "User-Agent": UA,
        "Accept": "*/*",
        "Origin": "https://juejin.cn",
        "Referer": "https://juejin.cn/",
    }
    if headers:
        hdrs.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
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


def api_env(method: str, path: str, jar: list, *, body=None) -> dict:
    """Return the full {err_no, data, cursor, has_more, ...} envelope, dying on
    a non-zero err_no. Juejin returns HTTP 200 even on logical errors."""
    url = f"{API}{path}"
    status, text = request(method, url, jar, body=body)
    try:
        env = json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {path}: {text[:300]}")
    if not isinstance(env, dict):
        die(f"unexpected response from {path}: {text[:300]}")
    err = env.get("err_no")
    if err and err != 0:
        msg = env.get("err_msg", "")
        if err in (401, 403) or "登录" in str(msg):
            die(f"auth failed (err_no={err}: {msg}) — cookie likely expired. "
                f"Reconnect at https://auth.acedata.cloud/user/connections.")
        die(f"juejin API error on {path} (err_no={err}): {msg}")
    return env


def api_call(method: str, path: str, jar: list, *, body=None):
    return api_env(method, path, jar, body=body).get("data")


# ── commands ────────────────────────────────────────────────────────

def jj_me(jar):
    me = api_call("GET", "/user_api/v1/user/get", jar)
    if not isinstance(me, dict) or not me.get("user_id"):
        die(f"could not read 掘金 profile (cookie expired?): {str(me)[:300]}")
    return me


def cmd_whoami(jar, _args):
    me = jj_me(jar)
    out({
        "user_id": me.get("user_id"),
        "name": me.get("user_name"),
        "url": f"https://juejin.cn/user/{me.get('user_id')}",
        "post_article_count": me.get("post_article_count"),
        "got_view_count": me.get("got_view_count"),
        "got_digg_count": me.get("got_digg_count"),
        "follower_count": me.get("follower_count"),
    })


def _fmt_article(item: dict) -> dict:
    info = item.get("article_info") or {}
    aid = item.get("article_id") or info.get("article_id")
    return {
        "id": str(aid) if aid is not None else None,
        "title": info.get("title"),
        "url": f"https://juejin.cn/post/{aid}" if aid else None,
        "view_count": info.get("view_count"),
        "digg_count": info.get("digg_count"),
        "comment_count": info.get("comment_count"),
        "collect_count": info.get("collect_count"),
        "audit_status": info.get("audit_status"),
        "ctime": info.get("ctime"),
    }


def _iter_my_articles(jar, uid):
    cursor = "0"
    for _ in range(50):  # hard cap so a bad has_more can't loop forever
        env = api_env("POST", "/content_api/v1/article/query_list", jar,
                      body={"user_id": str(uid), "cursor": cursor, "sort_type": 2})
        items = env.get("data") or []
        for it in items:
            yield it
        if not items or not env.get("has_more"):
            break
        cursor = env.get("cursor") or "0"


def cmd_articles(jar, args):
    me = jj_me(jar)
    items = []
    for it in _iter_my_articles(jar, me.get("user_id")):
        items.append(it)
        if len(items) >= args.limit:
            break
    out({"count": len(items), "articles": [_fmt_article(a) for a in items]})


def cmd_article(jar, args):
    # The detail endpoint is finicky for own cross-posted articles; the user's
    # own list already carries the stats, so fall back to scanning it.
    me = jj_me(jar)
    for it in _iter_my_articles(jar, me.get("user_id")):
        if str(it.get("article_id")) == str(args.id):
            res = _fmt_article(it)
            res["brief"] = ((it.get("article_info") or {}).get("brief_content") or "")[:200]
            out(res)
            return
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

    if not CONFIRM:
        out({
            "dry_run": True, "command": "publish", "platform": "juejin",
            "title": args.title, "draft_only": args.draft_only,
            "content_bytes": len(content or ""),
            "note": "掘金 content is Markdown. Re-run with --confirm as the LAST "
                    "argument to actually write. Publishing (without --draft-only) "
                    "needs a category + tag and goes through 审核.",
        })
        return

    # 1. create draft
    draft = api_call("POST", "/content_api/v1/article_draft/create", jar, body={
        "category_id": args.category_id or "0",
        "tag_ids": [t for t in (args.tag_ids or "").split(",") if t],
        "link_url": "", "cover_image": "",
        "title": args.title, "brief_content": (content or "")[:100],
        "edit_type": 10, "html_content": "deprecated", "mark_content": content or "",
        "theme_ids": [],
    })
    draft_id = draft.get("id") if isinstance(draft, dict) else None
    if not draft_id:
        die(f"create-draft failed: {str(draft)[:300]}")

    if args.draft_only:
        out({"ok": True, "draft_only": True, "draft_id": str(draft_id),
             "edit_url": f"https://juejin.cn/editor/drafts/{draft_id}"})
        return

    # 2. publish (needs valid category + >=1 tag for 审核)
    pub = api_call("POST", "/content_api/v1/article/publish", jar,
                   body={"draft_id": str(draft_id), "sync_to_org": False,
                         "column_ids": [], "theme_ids": []})
    aid = pub.get("article_id") if isinstance(pub, dict) else None
    if not aid:
        die(f"publish failed (draft saved as {draft_id}): {str(pub)[:300]}")
    out({"ok": True, "published": True, "article_id": str(aid),
         "url": f"https://juejin.cn/post/{aid}"})


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="juejin.py", description="juejin cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("articles", help="list the user's published articles + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("article", help="one article's details + stats")
    sp.add_argument("id")
    sp = sub.add_parser("publish", help="create/publish an article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--draft-only", action="store_true", help="create a draft only; do NOT go public")
    sp.add_argument("--category-id", help="掘金 category id (required to actually publish)")
    sp.add_argument("--tag-ids", help="comma-separated tag ids (required to actually publish)")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
