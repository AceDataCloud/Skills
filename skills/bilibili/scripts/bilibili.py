#!/usr/bin/env python3
"""
bilibili — read & publish 专栏 articles on Bilibili (bilibili.com) with the
user's own login cookies (BYOC). Standard-library only (urllib + hashlib for
WBI signing), no third-party deps.

The connector injects the cookie jar as a JSON env var ``BILIBILI_COOKIES``.
Reads use the login cookies; the article-list endpoint needs WBI signing
(keys come from the nav response). Writes need ``csrf`` = the ``bili_jct`` cookie.

Read commands run directly. ``publish`` is GATED by a trailing ``--confirm``
(honored only as the last arg). ``--draft-only`` saves a draft (no submit).
Note: Bilibili 专栏 content is HTML. The publish *submit* step is often
rate-limited (HTTP 412) by risk-control; the draft is the reliable result.

Examples:
  python3 bilibili.py whoami
  python3 bilibili.py articles --limit 20
  python3 bilibili.py article <cvid>
  python3 bilibili.py publish --title T --content-file a.html --draft-only --confirm
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import ipaddress
import json
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "bilibili"
API = "https://api.bilibili.com"

# Fixed permutation table for WBI mixin-key derivation (from bilibili web JS).
MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

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
        die(f"{env} is not set — connect Bilibili at "
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

def request(method, url, jar, *, referer=None, headers=None, body=None, form=None):
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
    }
    if referer:
        hdrs["Referer"] = referer
    if headers:
        hdrs.update(headers)
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    elif body is not None:
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


def get_json(url, jar, *, referer=None):
    status, text = request("GET", url, jar, referer=referer)
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {url}: {text[:300]}")
    return d


# ── WBI signing (for x/space/wbi/article) ───────────────────────────

def _wbi_keys(jar):
    nav = get_json(f"{API}/x/web-interface/nav", jar)
    data = nav.get("data") or {}
    img = ((data.get("wbi_img") or {}).get("img_url") or "")
    sub = ((data.get("wbi_img") or {}).get("sub_url") or "")
    img_key = img.rsplit("/", 1)[-1].split(".")[0]
    sub_key = sub.rsplit("/", 1)[-1].split(".")[0]
    return nav, img_key, sub_key


def _mixin_key(img_key, sub_key):
    orig = img_key + sub_key
    return "".join(orig[i] for i in MIXIN_KEY_ENC_TAB if i < len(orig))[:32]


def _wbi_sign(params: dict, img_key, sub_key) -> dict:
    mixin = _mixin_key(img_key, sub_key)
    params = dict(params)
    params["wts"] = int(time.time())
    params = {k: params[k] for k in sorted(params)}
    # bilibili drops these chars from values before signing
    cleaned = {k: "".join(ch for ch in str(v) if ch not in "!'()*") for k, v in params.items()}
    query = urllib.parse.urlencode(cleaned)
    params["w_rid"] = hashlib.md5((query + mixin).encode()).hexdigest()
    return params


# ── commands ────────────────────────────────────────────────────────

def bili_nav(jar):
    nav = get_json(f"{API}/x/web-interface/nav", jar)
    data = nav.get("data") or {}
    if not data.get("isLogin"):
        die("not logged in (cookie expired?) — reconnect at "
            "https://auth.acedata.cloud/user/connections.")
    return data


def cmd_whoami(jar, _args):
    d = bili_nav(jar)
    out({
        "mid": d.get("mid"),
        "name": d.get("uname"),
        "url": f"https://space.bilibili.com/{d.get('mid')}",
        "level": (d.get("level_info") or {}).get("current_level"),
        "vip": (d.get("vipStatus") or d.get("vip", {}).get("status")),
    })


def _fmt(a: dict) -> dict:
    st = a.get("stats") or {}
    cvid = a.get("id")
    return {
        "id": str(cvid) if cvid is not None else None,
        "title": a.get("title"),
        "url": f"https://www.bilibili.com/read/cv{cvid}" if cvid else None,
        "view": st.get("view"),
        "like": st.get("like"),
        "reply": st.get("reply"),
        "favorite": st.get("favorite"),
        "coin": st.get("coin"),
        "publish_time": a.get("publish_time"),
    }


def cmd_articles(jar, args):
    nav, img_key, sub_key = _wbi_keys(jar)
    mid = (nav.get("data") or {}).get("mid")
    if not mid:
        die("could not resolve your mid from nav (cookie expired?).")
    collected, pn = [], 1
    while len(collected) < args.limit:
        signed = _wbi_sign({"mid": mid, "pn": pn, "ps": 30, "sort": "publish_time"},
                           img_key, sub_key)
        url = f"{API}/x/space/wbi/article?" + urllib.parse.urlencode(signed)
        # WBI endpoints penalize a Referer header — omit it.
        d = get_json(url, jar)
        if d.get("code") != 0:
            die(f"article list error (code={d.get('code')}): {d.get('message')}")
        data = d.get("data") or {}
        items = data.get("articles") or []
        if not items:
            break
        collected.extend(items)
        total = data.get("count")
        if total is not None and len(collected) >= total:
            break
        pn += 1
    items = collected[: args.limit]
    out({"count": len(items), "articles": [_fmt(a) for a in items]})


def cmd_article(jar, args):
    cvid = str(args.id).lstrip("cv")
    d = get_json(f"{API}/x/article/viewinfo?id={cvid}", jar)
    if d.get("code") != 0:
        die(f"article {args.id} not found (code={d.get('code')}): {d.get('message')}")
    data = d.get("data") or {}
    st = data.get("stats") or {}
    out({
        "id": cvid,
        "title": data.get("title"),
        "url": f"https://www.bilibili.com/read/cv{cvid}",
        "author": data.get("author_name"),
        "view": st.get("view"), "like": st.get("like"), "reply": st.get("reply"),
        "favorite": st.get("favorite"), "coin": st.get("coin"),
    })


# tid = cover layout; a wrong one returns code -17 / "分类". Try common ones.
_TID_CANDIDATES = ["4", "3", "6", "7", "2", "17", "28", "41"]


# ── image upload (Bilibili hotlink-blocks external imgs; re-host via
#    upcover, mirroring our PlatformPublisher bilibili.py) ────────────

_IMG_SKIP = ("hdslb.com", "bilibili.com", "biliimg.com")
# matches both HTML <img src="..."> and markdown ![alt](...)
# <img ... src = "..."> / '...'  (tolerates spaces and either quote style)
_HTML_IMG = re.compile(r"""(<img\b[^>]*?\bsrc\s*=\s*)(["'])(https?://[^"']+)(\2)""", re.IGNORECASE)
_MD_IMG = re.compile(r"!\[([^\]]*)\]\((https?://[^)\s]+)\)")
UPCOVER = "https://api.bilibili.com/x/article/creative/article/upcover"


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


def _same_or_sub(host, suffix):
    return host == suffix or host.endswith("." + suffix)


def _get_bytes(url):
    _assert_public_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*"})
    with _IMG_OPENER.open(req, timeout=30) as r:
        data = r.read(MAX_IMG_BYTES + 1)
    if len(data) > MAX_IMG_BYTES:
        raise RuntimeError(f"image exceeds {MAX_IMG_BYTES} bytes")
    return data


def _is_webp(data):
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _download_image(url):
    # Bilibili's upcover rejects webp. Many of our images live on Tencent COS
    # (cdn.acedata.cloud) which can transcode server-side, so on a webp body
    # retry with the COS format param to get a png Bilibili accepts.
    data = _get_bytes(url)
    if _is_webp(data):
        sep = "&" if "?" in url else "?"
        try:
            conv = _get_bytes(f"{url}{sep}imageMogr2/format/png")
            if not _is_webp(conv):
                return conv
        except Exception:  # noqa: BLE001 — fall through with original bytes
            pass
    return data


def _sniff_image(data):
    """Real (ext, mime) from magic bytes — a URL's extension or the CDN's
    Content-Type can lie (e.g. a `.png` URL serving webp bytes), and Bilibili
    rejects a filename/format mismatch."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", "image/png"
    if data[:2] == b"\xff\xd8":
        return "jpg", "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif", "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    return "jpg", "image/jpeg"


def bili_upload_image(jar, csrf, src):
    img = _download_image(src)
    ext, ct = _sniff_image(img)
    boundary = "----acedata" + _rand_hex(20)
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="binary";'
        f' filename="image.{ext}"\r\nContent-Type: {ct}\r\n\r\n'.encode()
        + img + f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="csrf"'
        f"\r\n\r\n{csrf}\r\n--{boundary}--\r\n".encode()
    )
    hdrs = {"User-Agent": UA, "Origin": "https://member.bilibili.com",
            "Referer": "https://member.bilibili.com/",
            "Content-Type": f"multipart/form-data; boundary={boundary}"}
    req = urllib.request.Request(UPCOVER, data=body, headers=hdrs, method="POST")
    req.add_unredirected_header("Cookie", cookie_header(jar, UPCOVER))
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    if d.get("code") == 0 and (d.get("data") or {}).get("url"):
        return d["data"]["url"]
    raise RuntimeError(f"upcover failed (code={d.get('code')}): {d.get('message')}")


def rehost_images(jar, csrf, content):
    """Re-host external images (both <img src> and markdown) on Bilibili's CDN.
    An image that can't be uploaded is DROPPED (not kept as an external link) —
    Bilibili rejects the whole article with code 37130 if any external image
    link remains. Rate-limited to dodge code -1."""
    def _one(src):
        host = (urllib.parse.urlsplit(src).hostname or "").lower()
        if any(_same_or_sub(host, s) for s in _IMG_SKIP):
            return "keep", src
        try:
            new = bili_upload_image(jar, csrf, src)
            sys.stderr.write(f"[img] rehosted {src} -> {new}\n")
            time.sleep(0.3)
            return "ok", new
        except Exception as e:  # noqa: BLE001 — drop the image rather than fail
            sys.stderr.write(f"[img] dropped {src} (upload failed: {e})\n")
            return "drop", None

    def html_repl(m):
        # groups: 1=<img ... src= , 2=quote, 3=url, 4=closing quote (backref)
        st, new = _one(m.group(3))
        if st == "drop":
            return ""
        return m.group(1) + m.group(2) + (new or m.group(3)) + m.group(2)

    def md_repl(m):
        st, new = _one(m.group(2))
        return "" if st == "drop" else f"![{m.group(1)}]({new or m.group(2)})"

    content = _HTML_IMG.sub(html_repl, content)
    content = _MD_IMG.sub(md_repl, content)
    return content


def cmd_publish(jar, args):
    if not args.title:
        die("--title is required")
    if not args.content_file and args.content is None:
        die("provide --content-file <path.html> or --content <html>")
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    content = content or ""
    csrf = cookie_value(jar, "bili_jct")
    if not csrf:
        die("no bili_jct cookie (CSRF token) — reconnect Bilibili.")

    if not CONFIRM:
        out({
            "dry_run": True, "command": "publish", "platform": "bilibili",
            "title": args.title, "draft_only": args.draft_only,
            "content_bytes": len(content),
            "note": "Bilibili 专栏 content is HTML. Re-run with --confirm as the "
                    "LAST argument to write. The submit step is often 412-limited; "
                    "the saved draft is the reliable result.",
        })
        return

    # Bilibili hotlink-blocks external images → re-host them on its CDN first.
    if not args.no_rehost_images:
        content = rehost_images(jar, csrf, content)

    ref = "https://member.bilibili.com/"
    base = {
        "title": args.title, "content": content, "csrf": csrf,
        "category": "0", "list_id": "0", "reprint": "0", "original": "1",
        "media_id": "0", "spoiler": "0", "save": "0", "pgc_id": "0",
    }
    # 1. save draft, retrying tid until the category is accepted
    aid, last = None, None
    for tid in _TID_CANDIDATES:
        body = dict(base, tid=tid)
        status, text = request("POST", f"{API}/x/article/creative/draft/addupdate",
                               jar, referer=ref, form=body)
        try:
            r = json.loads(text)
        except json.JSONDecodeError:
            last = f"non-JSON ({status}): {text[:200]}"
            continue
        if r.get("code") == 0:
            aid = (r.get("data") or {}).get("aid")
            chosen_tid = tid
            break
        last = f"code={r.get('code')} {r.get('message')}"
        if "分类" not in str(r.get("message", "")) and r.get("code") != -17:
            break  # a non-category error won't be fixed by another tid
    if not aid:
        die(f"save-draft failed: {last}")

    if args.draft_only:
        out({"ok": True, "draft_only": True, "aid": str(aid),
             "edit_url": f"https://member.bilibili.com/article-text/home?aid={aid}"})
        return

    # 2. submit (publish) — may be 412 risk-controlled; report draft if so
    body = dict(base, tid=chosen_tid, aid=aid)
    status, text = request("POST", f"{API}/x/article/creative/article/submit",
                           jar, referer=ref, form=body)
    try:
        r = json.loads(text)
    except json.JSONDecodeError:
        r = None
    if r and r.get("code") == 0:
        out({"ok": True, "published": True, "aid": str(aid),
             "url": f"https://www.bilibili.com/read/cv{aid}"})
    else:
        out({"ok": False, "published": False, "draft_saved": True, "aid": str(aid),
             "edit_url": f"https://member.bilibili.com/article-text/home?aid={aid}",
             "note": f"submit blocked ({status}); the draft is saved — finish in the "
                     f"web editor. Detail: {(r or {}).get('message') if r else text[:200]}"})


def _drafts_of(d: dict) -> list:
    al = (d.get("data") or {}).get("artlist") or d.get("artlist") or {}
    return al.get("drafts") or []


def cmd_drafts(jar, args):
    # 专栏 drafts are capped at 999; this lists them so they can be pruned.
    d = get_json(f"{API}/x/article/creative/draft/list?pn={args.page}&ps={args.limit}",
                 jar, referer="https://member.bilibili.com/")
    if d.get("code"):  # 0 = ok; anything truthy is an auth/API error
        die(f"draft list error (code={d.get('code')}): {d.get('message')} — "
            f"cookie may be expired; reconnect at https://auth.acedata.cloud/user/connections.")
    items = _drafts_of(d)
    out({"page": args.page, "count": len(items), "drafts": [{
        "aid": x.get("id"),
        "title": x.get("title"),
        "edit_url": f"https://member.bilibili.com/article-text/home?aid={x.get('id')}",
    } for x in items]})


def cmd_delete_draft(jar, args):
    if not args.aids:
        die("provide one or more draft aids: delete-draft <aid> [<aid> ...] --confirm")
    bad = [a for a in args.aids if not str(a).isdigit()]
    if bad:
        die(f"invalid draft aid(s) — must be numeric: {bad}")
    csrf = cookie_value(jar, "bili_jct")
    if not csrf:
        die("no bili_jct cookie (CSRF token) — reconnect Bilibili.")
    if not CONFIRM:
        out({"dry_run": True, "command": "delete-draft", "platform": "bilibili",
             "aids": args.aids, "note": "Deletion is PERMANENT. Re-run with --confirm "
             "as the LAST argument to actually delete these draft(s)."})
        return
    results = []
    for aid in args.aids:
        _, text = request("POST", f"{API}/x/article/creative/draft/delete", jar,
                          referer="https://member.bilibili.com/", form={"aid": aid, "csrf": csrf})
        try:
            code = json.loads(text).get("code")
        except json.JSONDecodeError:
            code = None
        results.append({"aid": aid, "deleted": code == 0, "code": code})
    out({"command": "delete-draft", "deleted": sum(1 for r in results if r["deleted"]),
         "results": results})


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
    "drafts": cmd_drafts,
    "delete-draft": cmd_delete_draft,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="bilibili.py", description="bilibili 专栏 cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("articles", help="list the user's 专栏 articles + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp = sub.add_parser("article", help="one article's stats (by cvid)")
    sp.add_argument("id")
    sp = sub.add_parser("publish", help="create/publish a 专栏 article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="HTML content inline")
    sp.add_argument("--content-file", help="path to an HTML file")
    sp.add_argument("--draft-only", action="store_true", help="save a draft; do NOT submit")
    sp.add_argument("--no-rehost-images", action="store_true",
                    help="keep external image URLs as-is (skip Bilibili CDN re-host)")
    sp = sub.add_parser("drafts", help="list 专栏 drafts (id+title); use to prune the 999-draft cap")
    sp.add_argument("--limit", type=int, default=50)
    sp.add_argument("--page", type=int, default=1)
    sp = sub.add_parser("delete-draft", help="delete draft(s) by aid (GATED by trailing --confirm)")
    sp.add_argument("aids", nargs="*", help="one or more draft aids to delete")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
