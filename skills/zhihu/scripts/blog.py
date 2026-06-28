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
import base64
import gzip
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import formatdate

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


# ── Image re-hosting ────────────────────────────────────────
#
# Zhihu silently drops any <img> whose src is not on its own CDN, so external
# images must be re-hosted first. Primary path: hand Zhihu the remote URL and
# let it fetch (uploaded_images). Fallback: download the bytes and PUT them to
# Zhihu's Aliyun-OSS bucket with an HMAC-SHA1-signed request. Ported from
# PlatformPublisher app/publisher/zhihu.py (proven in production).

ZH_UPLOADED_IMAGES = "https://zhuanlan.zhihu.com/api/uploaded_images"
ZH_IMAGES = "https://api.zhihu.com/images"
OSS_ENDPOINT = "https://zhihu-pics-upload.zhimg.com"
OSS_BUCKET = "zhihu-pics"
_ZHIMG = "zhimg.com"  # a src already on Zhihu's CDN needs no re-upload
_IMG_SRC_RE = re.compile(r'(<img[^>]*?\ssrc=["\'])([^"\']+)(["\'])', re.IGNORECASE)
_MD_IMG_RE = re.compile(r'(!\[[^\]]*\]\()(\s*<?)([^)\s>]+)(>?\s*\))')


def _raw(method, url, jar, *, headers=None, data=None, timeout=60):
    """Low-level request returning (status, raw_bytes); handles gzip + binary."""
    hdrs = {"User-Agent": UA, "Cookie": cookie_header(jar, url)}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            if e.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        except Exception:
            pass
        return e.code, raw
    except urllib.error.URLError:
        return 0, b""


def _img_content_type(data: bytes) -> str:
    if data[:8].startswith(b"\x89PNG"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def _upload_image_url(jar, src: str):
    """Primary path: Zhihu fetches the remote URL server-side and hosts it."""
    body = urllib.parse.urlencode({"url": src, "source": "article"}).encode("utf-8")
    status, raw = _raw(
        "POST", ZH_UPLOADED_IMAGES, jar,
        headers={"x-requested-with": "fetch", "Content-Type": "application/x-www-form-urlencoded"},
        data=body,
    )
    if status and status < 400:
        try:
            d = json.loads(raw.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            return None
        if isinstance(d, dict) and d.get("src"):
            return d["src"]
    return None


def _oss_put(object_key: str, data: bytes, token: dict) -> bool:
    access_id = token.get("access_id", "")
    access_key = token.get("access_key", "")
    access_token = token.get("access_token", "")
    if not (access_id and access_key and object_key):
        return False
    ctype = _img_content_type(data)
    oss_date = formatdate(usegmt=True)
    oss_ua = "aliyun-sdk-js/6.8.0"
    oss_headers = {
        "x-oss-date": oss_date,
        "x-oss-security-token": access_token,
        "x-oss-user-agent": oss_ua,
    }
    canon = "\n".join(f"{k}:{oss_headers[k]}" for k in sorted(oss_headers))
    string_to_sign = f"PUT\n\n{ctype}\n{oss_date}\n{canon}\n/{OSS_BUCKET}/{object_key}"
    sig = base64.b64encode(
        hmac.new(access_key.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")
    status, _ = _raw(
        "PUT", f"{OSS_ENDPOINT}/{object_key}", [],
        headers={
            "Content-Type": ctype,
            "Authorization": f"OSS {access_id}:{sig}",
            "x-oss-date": oss_date,
            "x-oss-security-token": access_token,
            "x-oss-user-agent": oss_ua,
        },
        data=data,
    )
    return bool(status) and status < 400


def _wait_image_ready(jar, image_id: str) -> str:
    for _ in range(10):
        status, raw = _raw("GET", f"https://api.zhihu.com/images/{image_id}", jar, headers=ZH_FETCH)
        try:
            d = json.loads(raw.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            d = {}
        if d.get("status") == "completed" or d.get("original_hash"):
            return d.get("original_hash", "")
        time.sleep(1.0)
    return ""


def _upload_image_binary(jar, data: bytes):
    """Fallback: MD5 -> request OSS token -> (dedup or) signed PUT to OSS."""
    image_hash = hashlib.md5(data).hexdigest()
    status, raw = _raw(
        "POST", ZH_IMAGES, jar,
        headers={"x-requested-with": "fetch", "Content-Type": "application/json"},
        data=json.dumps({"image_hash": image_hash, "source": "article"}).encode("utf-8"),
    )
    if not status or status >= 400:
        return None
    try:
        token_data = json.loads(raw.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return None
    upload_file = token_data.get("upload_file") or {}
    upload_token = token_data.get("upload_token") or {}
    if upload_file.get("state") == 1:  # already on Zhihu — just resolve its hash
        object_key = _wait_image_ready(jar, upload_file.get("image_id", ""))
        return f"https://pic4.zhimg.com/{object_key}" if object_key else None
    object_key = upload_file.get("object_key", "")
    if not object_key or not _oss_put(object_key, data, upload_token):
        return None
    if data[:6] in (b"GIF87a", b"GIF89a"):
        object_key += ".gif"
    return f"https://pic4.zhimg.com/{object_key}"


def _download_image(src: str):
    # Route through _raw so a gzip-encoded response is decompressed (otherwise we
    # would upload gzipped bytes and Zhihu would reject/garble the image). jar=[]
    # so no cookie is ever sent to a third-party image host.
    status, raw = _raw("GET", src, [], headers={"User-Agent": UA}, timeout=30)
    return raw if status and status < 400 and raw else None


def count_images(content: str) -> int:
    srcs = {m.group(2) for m in _IMG_SRC_RE.finditer(content or "")}
    srcs |= {m.group(3) for m in _MD_IMG_RE.finditer(content or "")}
    return sum(1 for s in srcs if _ZHIMG not in s)


def rehost_images(jar, content: str):
    """Replace every non-Zhihu image URL (HTML <img> + markdown ![]()) with a
    Zhihu-CDN URL. Returns (new_content, stats)."""
    cache: dict = {}
    stats = {"found": 0, "rehosted": 0, "failed": 0}

    def resolve(src: str) -> str:
        if not src or _ZHIMG in src:
            return src
        if src in cache:
            return cache[src]
        stats["found"] += 1
        new = None
        if src.startswith("data:"):
            try:
                new = _upload_image_binary(jar, base64.b64decode(src.split(",", 1)[1]))
            except Exception:
                new = None
        else:
            new = _upload_image_url(jar, src)
            if not new:
                data = _download_image(src)
                if data:
                    new = _upload_image_binary(jar, data)
        if new:
            stats["rehosted"] += 1
            cache[src] = new
            return new
        stats["failed"] += 1
        cache[src] = src  # leave as-is; don't corrupt the doc if upload fails
        return src

    content = _IMG_SRC_RE.sub(lambda m: m.group(1) + resolve(m.group(2)) + m.group(3), content or "")
    content = _MD_IMG_RE.sub(lambda m: m.group(1) + m.group(2) + resolve(m.group(3)) + m.group(4), content)
    return content, stats


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
            "images_found": count_images(content or ""),
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

    # 2. re-host external images to Zhihu's CDN (Zhihu strips foreign <img>)
    image_stats = {"found": 0, "rehosted": 0, "failed": 0}
    if not args.no_images:
        content, image_stats = rehost_images(jar, content)

    # 3. set draft content
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
            "images": image_stats,
            "edit_url": f"https://zhuanlan.zhihu.com/write?draftId={draft_id}",
        })
        return

    # 4. publish (go live)
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
        "images": image_stats,
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
    sp.add_argument("--no-images", action="store_true",
                    help="skip re-hosting external images to Zhihu's CDN")

    args = p.parse_args(ARGV)
    jar = load_cookies(args.platform)
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
