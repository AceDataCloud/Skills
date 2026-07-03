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
import ipaddress
import json
import mimetypes
import os
import random
import re
import socket
import sys
import time
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


def api(method, url, jar, *, body=None, _retried=False):
    status, text = request(method, url, jar, body=body)
    # Medium sits behind Cloudflare, which intermittently 403s/429s an otherwise
    # valid session; one retry after a short pause clears the transient block.
    # Only retry idempotent GETs — never replay a POST (new-story/deltas/publish),
    # which could duplicate a write if the origin already processed it.
    if status in (403, 429) and method == "GET" and not _retried:
        time.sleep(1.5)
        return api(method, url, jar, body=body, _retried=True)
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


def prime_xsrf(jar) -> None:
    """Ensure the jar carries an ``xsrf`` cookie. Captured jars frequently lack
    it, but Medium hands one out on any GET of the site; without it the
    ``x-xsrf-token`` header is absent and every write fails ('Missing xsrf token')."""
    if cookie_value(jar, "xsrf"):
        return
    url = BASE + "/"
    hdrs = {"User-Agent": UA, "Accept": "text/html",
            "X-Requested-With": "XMLHttpRequest"}
    req = urllib.request.Request(url, headers=hdrs, method="GET")
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            set_cookies = resp.headers.get_all("Set-Cookie") or []
    except urllib.error.HTTPError as e:
        set_cookies = e.headers.get_all("Set-Cookie") or []
    except urllib.error.URLError:
        return
    for sc in set_cookies:
        m = re.match(r"\s*xsrf=([^;]+)", sc)
        if m:
            jar.append({"name": "xsrf", "value": m.group(1).strip('"'),
                        "domain": ".medium.com", "path": "/"})
            return


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


# ── image upload (Medium has no markdown image; upload bytes → image
#    paragraph delta type 4) ─────────────────────────────────────────

_MD_IMG = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")


def _rand_hex(n):
    return "".join(random.choice("0123456789abcdef") for _ in range(n))


MAX_IMG_BYTES = 12 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Refuse redirects on image fetches — a 30x could reach an internal host the
    # _assert_public_url() check never saw (SSRF).
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(f"image redirect blocked ({code}) -> {newurl[:80]}")


_IMG_OPENER = urllib.request.build_opener(_NoRedirect)


def _assert_public_url(url):
    """SSRF guard — block non-http(s) and private/loopback/link-local hosts."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise RuntimeError(f"unsupported image URL: {url[:80]}")
    try:
        addrs = socket.getaddrinfo(parts.hostname, None)
    except OSError as e:
        raise RuntimeError(f"cannot resolve {parts.hostname}: {e}")
    for info in addrs:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise RuntimeError(f"blocked non-public image host: {parts.hostname}")


def _download_image(url):
    _assert_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _IMG_OPENER.open(req, timeout=30) as r:
        data = r.read(MAX_IMG_BYTES + 1)
        ct = (r.headers.get("Content-Type") or "image/png").split(";")[0].strip()
    if len(data) > MAX_IMG_BYTES:
        raise RuntimeError(f"image exceeds {MAX_IMG_BYTES} bytes")
    return data, (ct if ct.startswith("image/") else "image/png")


def medium_upload_image(jar, post_id, img_bytes, content_type):
    """POST the bytes to Medium's /_/upload and return (fileId, w, h)."""
    ext = (mimetypes.guess_extension(content_type) or ".png").lstrip(".")
    boundary = "----acedata" + _rand_hex(20)
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="uploadedFile";'
        f' filename="image.{ext}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
        + img_bytes + f"\r\n--{boundary}--\r\n".encode()
    )
    xsrf = cookie_value(jar, "xsrf")
    hdrs = {
        "User-Agent": UA, "Accept": "application/json, text/plain, */*",
        "Origin": BASE, "Referer": f"{BASE}/p/{post_id}/edit",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    if xsrf:
        hdrs["x-xsrf-token"] = xsrf
    url = f"{BASE}/_/upload?is2x=true"
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8", "replace")
    val = (json.loads(_PREFIX.sub("", text)).get("payload") or {}).get("value") or {}
    if not val.get("fileId"):
        raise RuntimeError(f"upload returned no fileId: {text[:200]}")
    return val["fileId"], val.get("imgWidth"), val.get("imgHeight")


# Inline markdown → Medium markups. Groups: 1/2 link, 3 bold, 4 code, 5 italic.
_INLINE = re.compile(
    r"\[([^\]]+)\]\((https?://[^)\s]+)\)"
    r"|\*\*([^*]+)\*\*"
    r"|`([^`]+)`"
    r"|(?<![\w*])\*([^*\n]+)\*(?![\w*])"
)
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
_LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+(.*)$")


def _u16(s: str) -> int:
    """Length in UTF-16 code units — Medium indexes markup offsets like JS."""
    return len(s.encode("utf-16-le")) // 2


def _inline(text: str):
    """Parse inline markdown → (plain_text, markups). Emits Medium markups for
    links (type 3), bold (1), italic (2) and inline code (10) so they render as
    real formatting instead of literal ``**`` / ``[..](..)`` characters. Bold,
    italic and link labels are parsed recursively so nested markup (e.g. a link
    inside bold) is preserved as overlapping markups rather than dropped."""
    plain: list[str] = []
    markups: list[dict] = []
    pos = 0
    off = 0  # running UTF-16 offset into the assembled plain text

    def _nest(inner: str, start: int):
        sub_plain, sub_mk = _inline(inner)
        plain.append(sub_plain)
        for x in sub_mk:
            markups.append({**x, "start": x["start"] + start, "end": x["end"] + start})
        return _u16(sub_plain)

    for m in _INLINE.finditer(text):
        if m.start() > pos:
            seg = text[pos:m.start()]
            plain.append(seg)
            off += _u16(seg)
        start = off
        if m.group(1) is not None:            # link
            off += _nest(m.group(1), start)
            markups.append({"type": 3, "start": start, "end": off,
                            "href": m.group(2), "title": "", "rel": "", "anchorType": 0})
        elif m.group(3) is not None:          # bold
            off += _nest(m.group(3), start)
            markups.append({"type": 1, "start": start, "end": off})
        elif m.group(4) is not None:          # inline code — literal, no recursion
            inner = m.group(4)
            plain.append(inner); off += _u16(inner)
            markups.append({"type": 10, "start": start, "end": off})
        elif m.group(5) is not None:          # italic
            off += _nest(m.group(5), start)
            markups.append({"type": 2, "start": start, "end": off})
        pos = m.end()
    if pos < len(text):
        plain.append(text[pos:])
    return "".join(plain), markups


def _is_table(lines):
    return (len(lines) >= 2 and "|" in lines[0]
            and "-" in lines[1] and _TABLE_SEP.match(lines[1]) is not None)


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def _render_table(lines):
    """Markdown table → aligned monospace text (rendered as a PRE code block, the
    closest faithful representation since Medium's editor has no table element)."""
    rows = [_split_row(ln) for i, ln in enumerate(lines) if i != 1]
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    widths = [max(len(r[c]) for r in rows) for c in range(ncol)]
    def fmt(r):
        return " | ".join(r[c].ljust(widths[c]) for c in range(ncol)).rstrip()
    sep = "-+-".join("-" * widths[c] for c in range(ncol))
    body = [fmt(rows[0]), sep] + [fmt(r) for r in rows[1:]]
    return "\n".join(body)


def _is_list(lines):
    ls = [ln for ln in lines if ln.strip()]
    return bool(ls) and all(_LIST_ITEM.match(ln) for ln in ls)


def _build_deltas(jar, post_id, title, content, rehost=True):
    """Markdown → Medium paragraph deltas. Handles standalone ``![alt](url)``
    images (uploaded → type-4 image paragraph), headings, quotes, fenced code,
    tables (→ aligned code block), bullet/ordered lists, and inline markups
    (links/bold/italic/code) on ordinary text."""
    paras = [{"type": 3, "text": title}]
    for block in re.split(r"\n\s*\n", content.strip()):
        b = block.strip("\n")
        if not b.strip():
            continue
        lines = b.split("\n")
        first = b.lstrip()
        m = _MD_IMG.fullmatch(first)
        if m:
            alt, src = m.group(1), m.group(2)
            if rehost:
                try:
                    data, ct = _download_image(src)
                    fid, w, h = medium_upload_image(jar, post_id, data, ct)
                    sys.stderr.write(f"[img] uploaded {src} -> {fid}\n")
                    meta = {"id": fid}
                    if w:
                        meta["originalWidth"] = w
                    if h:
                        meta["originalHeight"] = h
                    paras.append({"type": 4, "text": alt or "", "layout": 1, "metadata": meta})
                    continue
                except Exception as e:  # noqa: BLE001 — degrade to a link
                    sys.stderr.write(f"[img] link-only {src} (upload failed: {e})\n")
            paras.append({"type": 1, "text": f"{alt or 'image'}: {src}"})
            continue
        if first.startswith("```"):
            paras.append({"type": 8, "text": re.sub(r"^```[^\n]*\n?|\n?```$", "", b)})
        elif _is_table(lines):
            paras.append({"type": 8, "text": _render_table(lines)})
        elif _is_list(lines):
            for ln in lines:
                lm = _LIST_ITEM.match(ln)
                if not lm:
                    continue
                ptype = 10 if lm.group(1).endswith(".") else 9
                txt, mk = _inline(lm.group(2).strip())
                paras.append({"type": ptype, "text": txt, "markups": mk})
        elif first.startswith("# "):
            txt, mk = _inline(first[2:].strip())
            paras.append({"type": 2, "text": txt, "markups": mk})
        elif first.startswith("## "):
            txt, mk = _inline(first[3:].strip())
            paras.append({"type": 2, "text": txt, "markups": mk})
        elif first.startswith("### "):
            txt, mk = _inline(first[4:].strip())
            paras.append({"type": 3, "text": txt, "markups": mk})
        elif first.startswith("> "):
            txt, mk = _inline(first[2:].strip())
            paras.append({"type": 6, "text": txt, "markups": mk})
        else:
            txt, mk = _inline(b.replace("\n", " ").strip())
            paras.append({"type": 1, "text": txt, "markups": mk})
    out_deltas = []
    for i, p in enumerate(paras):
        para = {"type": p["type"], "text": p["text"], "markups": p.get("markups") or []}
        if "layout" in p:
            para["layout"] = p["layout"]
        if "metadata" in p:
            para["metadata"] = p["metadata"]
        out_deltas.append({"type": 1, "index": i, "paragraph": para})
    return out_deltas


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

    # Captured jars often lack an xsrf cookie; mint one so writes don't 400.
    prime_xsrf(jar)
    if not cookie_value(jar, "xsrf"):
        die("could not obtain an xsrf token from Medium (cookie may be expired) — "
            "reconnect at https://auth.acedata.cloud/user/connections.")

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

    # 3. write the body as paragraph deltas (images uploaded to Medium inline)
    deltas = _build_deltas(jar, post_id, args.title, content,
                           rehost=not args.no_rehost_images)
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
    sp.add_argument("--no-rehost-images", action="store_true",
                    help="don't upload images to Medium (degrade to link-only paragraphs)")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
