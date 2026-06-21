#!/usr/bin/env python3
"""
zhihu — read & publish on Zhihu (知乎) with the user's own
login cookies (BYOC). Standard-library only (urllib), no third-party deps,
so it runs in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var named
``<PLATFORM>_COOKIES`` (e.g. ``ZHIHU_COOKIES``) — a list of
``{name, value, domain, path, ...}`` dicts captured by the ACE extension.

Read commands run directly. ``publish`` is GATED: without a trailing
``--confirm`` it only dry-runs (prints what it would do, changes nothing).
``--confirm`` is honored ONLY as the last argument, so a title/content that
merely contains "--confirm" can never silently go live.

Quick examples:
  python3 $SKILL_DIR/scripts/blog.py whoami
  python3 $SKILL_DIR/scripts/blog.py articles --limit 20
  python3 $SKILL_DIR/scripts/blog.py article <article-id>
  python3 $SKILL_DIR/scripts/blog.py drafts
  python3 $SKILL_DIR/scripts/blog.py publish --title "T" --content-file a.html --draft-only --confirm
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

# --confirm is only honored as the LAST token so a value that merely
# contains "--confirm" can never silently confirm a write.
_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# ── Cookie jar (from env) ───────────────────────────────────────────

def load_cookies(platform: str) -> list[dict]:
    env = f"{platform.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(
            f"{env} is not set — connect the {platform} account at "
            f"https://auth.acedata.cloud/user/connections, then retry."
        )
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"{env} is not valid JSON: {e}")
    if not isinstance(jar, list):
        die(f"{env} must be a JSON list of cookies, got {type(jar).__name__}")
    return jar


def _domain_matches(host: str, domain: str) -> bool:
    # Browser-style domain match: a cookie scoped to ".zhihu.com" / "zhihu.com"
    # is sent to zhihu.com and any subdomain; a host-only cookie matches exactly.
    d = domain.lstrip(".").lower()
    h = host.lower()
    return not d or h == d or h.endswith("." + d)


def cookie_header(jar: list[dict], url: str) -> str:
    # Only send a cookie to a host inside its domain scope, so a jar is never
    # replayed outside the platform it was captured for (defense in depth — all
    # request URLs here are first-party, but this future-proofs multi-platform).
    host = urllib.parse.urlsplit(url).hostname or ""
    # A domainless cookie has no scope of its own; only send it to a host the
    # jar's domain-scoped cookies already cover (i.e. this jar's own platform),
    # never fail-open to an arbitrary host.
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


# ── HTTP (stdlib urllib) ────────────────────────────────────────────

def request(method: str, url: str, jar: list[dict], *, headers=None, body=None):
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Cookie": cookie_header(jar, url),
    }
    if headers:
        hdrs.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
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


def get_json(url: str, jar: list[dict], **kw):
    status, text = request("GET", url, jar, **kw)
    if status == 401 or status == 403:
        die(
            f"auth failed ({status}) on {url} — the cookie is likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections."
        )
    try:
        return status, json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {text[:300]}")


# ── Zhihu ───────────────────────────────────────────────────────────

ZH = {
    "me": "https://www.zhihu.com/api/v4/me",
    "articles": "https://www.zhihu.com/api/v4/members/{token}/articles",
    "article": "https://www.zhihu.com/api/v4/articles/{id}",
    "create_draft": "https://zhuanlan.zhihu.com/api/articles/drafts",
}
ZH_FETCH = {"x-requested-with": "fetch"}


def zh_me(jar):
    _, data = get_json(ZH["me"], jar, headers=ZH_FETCH)
    if not data.get("id"):
        die(f"could not read Zhihu profile (cookie expired?): {str(data)[:300]}")
    return data


def cmd_whoami(jar, _args):
    me = zh_me(jar)
    out({
        "id": str(me.get("id", "")),
        "name": me.get("name"),
        "url_token": me.get("url_token"),
        "headline": me.get("headline"),
        "articles_count": me.get("articles_count"),
        "voteup_count": me.get("voteup_count"),
    })


# Zhihu omits stats unless asked via `include`. This pulls the counts the
# user actually cares about onto each article in the list/detail responses.
ZH_ARTICLE_INCLUDE = "data[*].comment_count,voteup_count,created,updated,title,url"


def _https(url):
    if isinstance(url, str) and url.startswith("http://"):
        return "https://" + url[len("http://"):]
    return url


def _fmt_article(a: dict) -> dict:
    aid = a.get("id")
    # Prefer the canonical public reader URL built from the id — the API's own
    # `url` field is inconsistent (zhuanlan in the list, api.zhihu.com in detail).
    return {
        "id": str(aid) if aid is not None else None,
        "title": a.get("title"),
        "url": (f"https://zhuanlan.zhihu.com/p/{aid}" if aid else _https(a.get("url"))),
        "voteup_count": a.get("voteup_count"),
        "comment_count": a.get("comment_count"),
        "created": a.get("created"),
        "updated": a.get("updated"),
    }


def cmd_articles(jar, args):
    me = zh_me(jar)
    token = me.get("url_token")
    if not token:
        die("Zhihu profile has no url_token; cannot list articles.")
    url = ZH["articles"].format(token=token)
    q = urllib.parse.urlencode({
        "include": ZH_ARTICLE_INCLUDE,
        "limit": args.limit,
        "offset": args.offset,
    })
    _, data = get_json(f"{url}?{q}", jar, headers=ZH_FETCH)
    items = data.get("data", []) if isinstance(data, dict) else []
    out({
        "total": (data.get("paging") or {}).get("totals") if isinstance(data, dict) else None,
        "count": len(items),
        "articles": [_fmt_article(a) for a in items],
    })


def cmd_article(jar, args):
    base = ZH["article"].format(id=args.id)
    q = urllib.parse.urlencode({"include": "comment_count,voteup_count"})
    _, a = get_json(f"{base}?{q}", jar, headers=ZH_FETCH)
    if not isinstance(a, dict) or not a.get("id"):
        die(f"article {args.id} not found or not accessible: {str(a)[:300]}")
    res = _fmt_article(a)
    res["content_excerpt"] = (a.get("excerpt") or "")[:200]
    out(res)


def cmd_publish(jar, args):
    if not args.title:
        die("--title is required")
    if not args.content_file and args.content is None:
        die("provide --content-file <path> or --content <html>")
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")

    if not CONFIRM:
        out({
            "dry_run": True,
            "command": "publish",
            "platform": "zhihu",
            "title": args.title,
            "draft_only": args.draft_only,
            "content_bytes": len(content or ""),
            "note": "re-run with --confirm as the LAST argument to actually write. "
                    "Without --draft-only this publishes a PUBLIC article on the user's real account.",
        })
        return

    # 1. create empty draft
    status, text = request(
        "POST", ZH["create_draft"], jar, headers=ZH_FETCH,
        body={"title": args.title, "content": "", "delta_time": 0},
    )
    try:
        created = json.loads(text)
    except json.JSONDecodeError:
        die(f"create-draft returned non-JSON ({status}): {text[:300]}")
    draft_id = created.get("id")
    if not draft_id:
        die(f"create-draft failed ({status}): {str(created)[:300]}")

    # 2. set draft content
    status, text = request(
        "PATCH", f"https://zhuanlan.zhihu.com/api/articles/{draft_id}/draft", jar,
        headers=ZH_FETCH, body={"title": args.title, "content": content},
    )
    if status >= 400:
        die(f"update-draft failed ({status}) for {draft_id}: {text[:300]}")

    if args.draft_only:
        out({
            "ok": True,
            "draft_only": True,
            "draft_id": str(draft_id),
            "edit_url": f"https://zhuanlan.zhihu.com/write?draftId={draft_id}",
        })
        return

    # 3. publish (go live)
    status, text = request(
        "PUT", f"https://zhuanlan.zhihu.com/api/articles/{draft_id}/publish", jar,
        headers=ZH_FETCH, body={},
    )
    if status >= 400:
        die(f"publish failed ({status}) for {draft_id}; it remains a draft: {text[:300]}")
    out({
        "ok": True,
        "published": True,
        "article_id": str(draft_id),
        "url": f"https://zhuanlan.zhihu.com/p/{draft_id}",
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="blog.py", description="zhihu cookie CLI")
    p.add_argument("--platform", default="zhihu", choices=["zhihu"],
                   help="content platform (only zhihu is implemented today)")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="show the logged-in account")

    sp = sub.add_parser("articles", help="list the user's published articles + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--offset", type=int, default=0)

    sp = sub.add_parser("article", help="one article's details + stats")
    sp.add_argument("id")

    sp = sub.add_parser("publish", help="create/publish an article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="HTML content inline")
    sp.add_argument("--content-file", help="path to an HTML file")
    sp.add_argument("--draft-only", action="store_true",
                    help="create a draft only; do NOT go public")

    args = p.parse_args(ARGV)
    jar = load_cookies(args.platform)
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
