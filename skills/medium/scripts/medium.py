#!/usr/bin/env python3
"""
medium — read & publish on Medium (medium.com) with the user's own login cookies
(BYOC). Standard-library only (urllib), no third-party deps.

Medium retired its public write API in 2023, so this drives the same internal
endpoints the website uses, authenticated by the session cookies (``sid``,
``uid``, ``xsrf``). State-changing calls must echo the ``xsrf`` cookie as the
``x-xsrf-token`` header. Internal ``/_/api`` responses are prefixed with
``])}while(1);</x>`` which is stripped before parsing.

The connector injects the cookie jar as a JSON env var ``MEDIUM_COOKIES``.

Read commands run directly. ``publish`` is GATED by a trailing ``--confirm``
(honored only as the last arg). ``--draft-only`` stops at a private draft.
Publishing uses Medium's multi-step editor flow (new-story → deltas → publish).

Examples:
  python3 medium.py whoami
  python3 medium.py articles --limit 20
  python3 medium.py article <post-id>
  python3 medium.py publish --title T --content-file a.md --draft-only --confirm
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
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "medium"
BASE = "https://medium.com"
_PREFIX = re.compile(r"^\s*\]\)\}while\(1\);(?:</x>)?")

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
        die(f"{env} is not set — connect Medium at "
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


# ── HTTP ────────────────────────────────────────────────────────────

def request(method, url, jar, *, headers=None, body=None, accept="application/json"):
    hdrs = {
        "User-Agent": UA,
        "Accept": accept,
        "Origin": BASE,
        "Referer": BASE + "/",
        "X-Requested-With": "XMLHttpRequest",
    }
    xsrf = cookie_value(jar, "xsrf")
    if xsrf and method != "GET":
        hdrs["x-xsrf-token"] = xsrf
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


def api(method, url, jar, *, body=None):
    status, text = request(method, url, jar, body=body)
    if status in (401, 403):
        die(f"auth failed ({status}) on {url} — cookie likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections.")
    clean = _PREFIX.sub("", text)
    try:
        d = json.loads(clean)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {clean[:300]}")
    if isinstance(d, dict) and d.get("success") is False:
        die(f"Medium API error ({status}) on {url}: {d.get('error')}")
    return d


# ── commands ────────────────────────────────────────────────────────

def md_me(jar):
    uid = cookie_value(jar, "uid")
    if not uid:
        die("no uid cookie — reconnect Medium at "
            "https://auth.acedata.cloud/user/connections.")
    d = api("GET", f"{BASE}/_/api/users/{uid}", jar)
    val = (d.get("payload") or {}).get("value") or {}
    if not val.get("userId"):
        die(f"could not read Medium profile (cookie expired?): {str(d)[:200]}")
    return val


def cmd_whoami(jar, _args):
    me = md_me(jar)
    out({
        "user_id": me.get("userId"),
        "name": me.get("name"),
        "username": me.get("username"),
        "url": f"{BASE}/@{me.get('username')}",
        "bio": me.get("bio"),
    })


_USER_POSTS_QUERY = (
    "query UserProfileQuery($username: ID, $homepagePostsLimit: PaginationLimit) "
    "{ userResult(username: $username) { __typename ... on User { id name "
    "homepagePostsConnection(paging: {limit: $homepagePostsLimit}) { posts { "
    "id title clapCount postResponses { count } readingTime "
    "firstPublishedAt } } } } }"
)


def gql(jar, operation, variables):
    status, text = request("POST", f"{BASE}/_/graphql", jar,
                           headers={"graphql-operation": operation},
                           body={"operationName": operation, "variables": variables,
                                 "query": _USER_POSTS_QUERY})
    if status in (401, 403):
        die(f"auth failed ({status}) on GraphQL — cookie likely expired.")
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON GraphQL response ({status}): {text[:300]}")
    if d.get("errors"):
        die(f"GraphQL error: {str(d['errors'])[:300]}")
    return d.get("data") or {}


def cmd_articles(jar, args):
    me = md_me(jar)
    data = gql(jar, "UserProfileQuery",
               {"username": me.get("username"), "homepagePostsLimit": args.limit})
    posts = (((data.get("userResult") or {}).get("homepagePostsConnection")) or {}).get("posts") or []
    out({"count": len(posts), "articles": [{
        "id": p.get("id"),
        "title": p.get("title"),
        "url": f"{BASE}/p/{p.get('id')}",
        "claps": p.get("clapCount"),
        "responses": (p.get("postResponses") or {}).get("count"),
        "reading_time_min": round(p.get("readingTime"), 1) if p.get("readingTime") else None,
        "first_published_at": p.get("firstPublishedAt"),
    } for p in posts]})


def cmd_article(jar, args):
    d = api("GET", f"{BASE}/_/api/posts/{args.id}", jar)
    val = (d.get("payload") or {}).get("value") or {}
    if not val.get("id"):
        die(f"post {args.id} not found or not accessible")
    vc = val.get("virtuals") or {}
    out({
        "id": val.get("id"),
        "title": val.get("title"),
        "url": val.get("mediumUrl") or f"{BASE}/p/{val.get('id')}",
        "claps": vc.get("totalClapCount"),
        "reading_time": vc.get("readingTime"),
        "word_count": vc.get("wordCount"),
        "created_at": val.get("createdAt"),
    })


def _markdown_to_deltas(title: str, content: str) -> list:
    """Minimal Markdown → Medium paragraph deltas. Title is a type-3 paragraph;
    body blocks split on blank lines; ``#``/``##``/``###`` map to h1/h2/h3,
    ``>`` to blockquote, ``` ``` to code, everything else to body text."""
    paras = [{"type": 3, "text": title}]
    blocks = re.split(r"\n\s*\n", content.strip())
    in_code = False
    code_buf = []
    for block in blocks:
        b = block.strip("\n")
        if not b.strip():
            continue
        first = b.lstrip()
        if first.startswith("```"):
            # toggle / inline fenced block
            body = re.sub(r"^```[^\n]*\n?|\n?```$", "", b)
            paras.append({"type": 8, "text": body})
            continue
        if first.startswith("# "):
            paras.append({"type": 12, "text": first[2:].strip()})
        elif first.startswith("## "):
            paras.append({"type": 2, "text": first[3:].strip()})
        elif first.startswith("### "):
            paras.append({"type": 3, "text": first[4:].strip()})
        elif first.startswith("> "):
            paras.append({"type": 6, "text": first[2:].strip()})
        else:
            paras.append({"type": 1, "text": b.replace("\n", " ").strip()})
    deltas = []
    for i, p in enumerate(paras):
        deltas.append({"type": 1, "index": i,
                       "paragraph": {"type": p["type"], "text": p["text"], "markups": []}})
    return deltas


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
            "dry_run": True, "command": "publish", "platform": "medium",
            "title": args.title, "draft_only": args.draft_only,
            "content_bytes": len(content),
            "note": "Medium content is Markdown (converted to paragraph deltas). "
                    "Re-run with --confirm as the LAST argument to write. Without "
                    "--draft-only it publishes a PUBLIC story on the user's account.",
        })
        return

    # 1. create empty draft
    d = api("POST", f"{BASE}/new-story", jar, body={})
    payload = d.get("payload") or {}
    post_id = payload.get("id") or (payload.get("value") or {}).get("id")
    if not post_id:
        die(f"new-story did not return a post id: {str(d)[:200]}")

    # 2. read the draft for the base revision
    d2 = api("GET", f"{BASE}/_/api/posts/{post_id}/draft", jar)
    val = (d2.get("payload") or {}).get("value") or {}
    base_rev = val.get("latestRev")
    if base_rev is None:
        base_rev = 0

    # 3. write the body as paragraph deltas
    deltas = _markdown_to_deltas(args.title, content)
    api("POST", f"{BASE}/p/{post_id}/deltas", jar,
        body={"baseRev": base_rev, "deltas": deltas})

    if args.draft_only:
        out({"ok": True, "draft_only": True, "post_id": post_id,
             "edit_url": f"{BASE}/p/{post_id}/edit"})
        return

    # 4. publish (go public)
    api("POST", f"{BASE}/p/{post_id}/publish", jar, body={})
    out({"ok": True, "published": True, "post_id": post_id,
         "url": f"{BASE}/p/{post_id}"})


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="medium.py", description="medium cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("articles", help="list the user's posts + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("article", help="one post's details + stats")
    sp.add_argument("id")
    sp = sub.add_parser("publish", help="create/publish a story (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--draft-only", action="store_true", help="create a draft only; do NOT go public")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
