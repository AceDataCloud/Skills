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
    # Answers (回答) — the question/answer side of Zhihu, distinct from articles.
    "member_answers": "https://www.zhihu.com/api/v4/members/{token}/answers",
    "answer": "https://www.zhihu.com/api/v4/answers/{id}",
    "question": "https://www.zhihu.com/api/v4/questions/{id}",
    "question_answers": "https://www.zhihu.com/api/v4/questions/{id}/answers",
    "question_draft": "https://www.zhihu.com/api/v4/questions/{id}/draft",
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


# ── Answers (回答) ───────────────────────────────────────────────────
#
# Answers are Zhihu's question/answer side, separate from articles. A user has
# at most ONE answer per question (a second POST returns RepeatedActionException
# 103003 — surface that and point at edit-answer). Writes go through the same
# cookie-only web APIs as articles; no x-zse signature is required.

ZH_ANSWER_LIST_INCLUDE = (
    "data[*].comment_count,created_time,updated_time,question"
)


def _fmt_answer(a: dict) -> dict:
    aid = a.get("id")
    q = a.get("question") or {}
    qid = q.get("id")
    # The member/answers endpoint never returns voteup_count (赞同); it only
    # exposes like_count / favorites under reaction.statistics. The authoritative
    # 赞同 count lives on the single-answer detail endpoint (`answer <id>`).
    react = (a.get("reaction") or {}).get("statistics") or {}
    return {
        "answer_id": str(aid) if aid is not None else None,
        "question_id": str(qid) if qid is not None else None,
        "question_title": q.get("title"),
        "url": (f"https://www.zhihu.com/question/{qid}/answer/{aid}" if (qid and aid) else None),
        "voteup_count": a.get("voteup_count"),
        "like_count": react.get("like_count"),
        "favorite_count": react.get("favorites"),
        "comment_count": a.get("comment_count"),
        "created_time": a.get("created_time"),
        "updated_time": a.get("updated_time"),
    }


def cmd_answers(jar, args):
    me = zh_me(jar)
    token = me.get("url_token")
    if not token:
        die("Zhihu profile has no url_token; cannot list answers.")
    url = ZH["member_answers"].format(token=token)
    q = urllib.parse.urlencode({
        "include": ZH_ANSWER_LIST_INCLUDE,
        "limit": args.limit,
        "offset": args.offset,
    })
    _, data = get_json(f"{url}?{q}", jar, headers=ZH_FETCH)
    items = data.get("data", []) if isinstance(data, dict) else []
    out({
        "total": (data.get("paging") or {}).get("totals") if isinstance(data, dict) else None,
        "count": len(items),
        "answers": [_fmt_answer(a) for a in items],
    })


def cmd_answer(jar, args):
    base = ZH["answer"].format(id=args.id)
    q = urllib.parse.urlencode({
        "include": "content,voteup_count,comment_count,created_time,updated_time,question",
    })
    _, a = get_json(f"{base}?{q}", jar, headers=ZH_FETCH)
    if not isinstance(a, dict) or not a.get("id"):
        die(f"answer {args.id} not found or not accessible: {str(a)[:300]}")
    res = _fmt_answer(a)
    res["content_excerpt"] = (a.get("excerpt") or "")[:200]
    out(res)


def cmd_question(jar, args):
    base = ZH["question"].format(id=args.id)
    q = urllib.parse.urlencode({
        "include": "answer_count,follower_count,visit_count,comment_count,detail",
    })
    _, qd = get_json(f"{base}?{q}", jar, headers=ZH_FETCH)
    if not isinstance(qd, dict) or not (qd.get("id") or qd.get("title")):
        die(f"question {args.id} not found or not accessible: {str(qd)[:300]}")
    # Detect whether the logged-in user already answered this question so the
    # caller knows to use `edit-answer` instead of `answer-question`.
    mine = _my_answer_for_question(jar, args.id)
    out({
        "question_id": str(qd.get("id") or args.id),
        "title": qd.get("title"),
        "url": f"https://www.zhihu.com/question/{args.id}",
        "answer_count": qd.get("answer_count"),
        "follower_count": qd.get("follower_count"),
        "visit_count": qd.get("visit_count"),
        "detail_excerpt": _strip_tags(qd.get("detail") or "")[:300],
        "my_answer_id": mine,
        "already_answered": bool(mine),
    })


_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(html: str) -> str:
    return _TAG_RE.sub("", html or "").strip()


def _my_answer_for_question(jar, question_id: str):
    """Return the logged-in user's answer id for a question, or None.

    Scans the *user's own* answers (bounded by their answer count) and matches
    on question id. This is reliable even for popular questions — unlike walking
    the question's own answer list, which may have thousands of entries. For an
    account with more answers than the scan cap this is best-effort.
    """
    me = zh_me(jar)
    token = me.get("url_token")
    if not token:
        return None
    url = ZH["member_answers"].format(token=token)
    qid = str(question_id)
    offset = 0
    for _ in range(15):  # up to 300 of the user's own answers
        q = urllib.parse.urlencode({
            "include": "data[*].question",
            "limit": 20,
            "offset": offset,
        })
        status, data = request("GET", f"{url}?{q}", jar, headers=ZH_FETCH)
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return None
        items = data.get("data", []) if isinstance(data, dict) else []
        for a in items:
            if str((a.get("question") or {}).get("id")) == qid:
                return str(a.get("id"))
        if (data.get("paging") or {}).get("is_end", True) or not items:
            return None
        offset += 20
    return None



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
# A src already on Zhihu's own CDN needs no re-upload. uploaded_images hands back
# a pic-private.zhihu.com URL for draft-scoped images, so skip those too.
_ZHIMG_HOSTS = ("zhimg.com", "pic-private.zhihu.com")
_IMG_SRC_RE = re.compile(r'(<img[^>]*?\ssrc=["\'])([^"\']+)(["\'])', re.IGNORECASE)
_MD_IMG_RE = re.compile(r'(!\[[^\]]*\]\()(\s*<?)([^)\s>]+)(>?\s*\))')
# uploaded_images returns a DRAFT-SCOPED signed pic-private URL whose auth_key
# expires; reduce any Zhihu image URL to the durable public form Zhihu serves
# after publish (picx.zhimg.com/v2-<hash>.<ext>).
_ZH_IMG_HASH = re.compile(r'(v2-[0-9a-f]+)(?:~[^."?\']*)?\.(png|jpe?g|gif|webp)', re.IGNORECASE)


def _on_zhihu_cdn(src: str) -> bool:
    # Match on the parsed host (not a substring) so an external host that merely
    # contains "zhimg.com" (e.g. my-zhimg.com) isn't wrongly treated as hosted.
    host = (urllib.parse.urlsplit(src).hostname or "") if src else ""
    return any(host == h or host.endswith("." + h) for h in _ZHIMG_HOSTS)


def _canonical_zhimg(url):
    if not url:
        return url
    m = _ZH_IMG_HASH.search(url)
    return f"https://picx.zhimg.com/{m.group(1)}.{m.group(2).lower()}" if m else url


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
            return _canonical_zhimg(d["src"])
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
        return _canonical_zhimg(f"https://pic4.zhimg.com/{object_key}") if object_key else None
    object_key = upload_file.get("object_key", "")
    if not object_key or not _oss_put(object_key, data, upload_token):
        return None
    if data[:6] in (b"GIF87a", b"GIF89a"):
        object_key += ".gif"
    return _canonical_zhimg(f"https://pic4.zhimg.com/{object_key}")


def _download_image(src: str):
    # Route through _raw so a gzip-encoded response is decompressed (otherwise we
    # would upload gzipped bytes and Zhihu would reject/garble the image). jar=[]
    # so no cookie is ever sent to a third-party image host.
    status, raw = _raw("GET", src, [], headers={"User-Agent": UA}, timeout=30)
    return raw if status and status < 400 and raw else None


def count_images(content: str) -> int:
    srcs = {m.group(2) for m in _IMG_SRC_RE.finditer(content or "")}
    srcs |= {m.group(3) for m in _MD_IMG_RE.finditer(content or "")}
    return sum(1 for s in srcs if not _on_zhihu_cdn(s))


def rehost_images(jar, content: str):
    """Replace every non-Zhihu image URL (HTML <img> + markdown ![]()) with a
    Zhihu-CDN URL. Returns (new_content, stats)."""
    cache: dict = {}
    stats = {"found": 0, "rehosted": 0, "failed": 0}

    def resolve(src: str) -> str:
        if not src or _on_zhihu_cdn(src):
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


def _read_content(args) -> str:
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    if content is None:
        die("provide --content-file <path> or --content <html>")
    return content


def _reshipment(value):
    # Zhihu accepts "allowed" / "disallowed" for 转载授权 (repost permission).
    return value if value in ("allowed", "disallowed") else None


def cmd_answer_question(jar, args):
    """Post a NEW answer to a question (GATED). --draft-only saves a private draft."""
    qid = args.question
    if not qid:
        die("--question <question-id> is required")
    content = _read_content(args)
    # Fetch the question title so the dry-run shows what is being answered.
    title = None
    try:
        _, qd = get_json(
            f"{ZH['question'].format(id=qid)}?{urllib.parse.urlencode({'include': 'title'})}",
            jar, headers=ZH_FETCH,
        )
        title = qd.get("title") if isinstance(qd, dict) else None
    except SystemExit:
        raise
    except Exception:
        pass

    reship = _reshipment(args.repost) or "disallowed"

    if not CONFIRM:
        out({
            "dry_run": True,
            "command": "answer-question",
            "platform": "zhihu",
            "question_id": str(qid),
            "question_title": title,
            "draft_only": args.draft_only,
            "reshipment_settings": reship,
            "content_bytes": len(content),
            "images_found": count_images(content),
            "note": "re-run with --confirm as the LAST argument to actually write. "
                    "Without --draft-only this publishes a PUBLIC answer on the user's real "
                    "account. One answer per question — if you already answered, use edit-answer.",
        })
        return

    image_stats = {"found": 0, "rehosted": 0, "failed": 0}
    if not args.no_images:
        content, image_stats = rehost_images(jar, content)

    if args.draft_only:
        # Private autosave draft on the question — nothing goes public.
        status, text = request(
            "PUT", ZH["question_draft"].format(id=qid), jar,
            headers=ZH_FETCH, body={"content": content, "delta_time": 5},
        )
        if status >= 400:
            die(f"save-draft failed ({status}) for question {qid}: {text[:300]}")
        out({
            "ok": True,
            "draft_only": True,
            "question_id": str(qid),
            "images": image_stats,
            "review_url": f"https://www.zhihu.com/question/{qid}",
            "note": "Private draft saved. Open the question to review, then re-run "
                    "without --draft-only (and --confirm) to publish.",
        })
        return

    status, text = request(
        "POST", ZH["question_answers"].format(id=qid), jar,
        headers=ZH_FETCH, body={"content": content, "reshipment_settings": reship},
    )
    try:
        res = json.loads(text)
    except json.JSONDecodeError:
        res = {}
    if status >= 400:
        # Zhihu's `error` is usually a dict {code, name, message} but can be a
        # bare string; guard both. `code` may arrive as int or str.
        err = res.get("error") if isinstance(res, dict) and isinstance(res.get("error"), dict) else {}
        if str(err.get("code")) == "103003":
            die(
                f"you already answered question {qid}; Zhihu allows one answer per "
                f"question. Find your answer id with `answers` and use "
                f"`edit-answer --id <answer-id>` instead."
            )
        die(f"publish answer failed ({status}) for question {qid}: {text[:300]}")
    aid = res.get("id") if isinstance(res, dict) else None
    if not aid:
        die(f"publish answer returned no id ({status}): {text[:300]}")
    out({
        "ok": True,
        "published": True,
        "question_id": str(qid),
        "answer_id": str(aid),
        "images": image_stats,
        "url": f"https://www.zhihu.com/question/{qid}/answer/{aid}",
    })


def cmd_edit_answer(jar, args):
    """Edit an EXISTING answer's content (GATED). The answer stays public."""
    aid = args.id
    if not aid:
        die("--id <answer-id> is required")
    content = _read_content(args)
    # Read the current answer to preserve its repost setting and show context.
    cur = {}
    try:
        _, cur = get_json(
            f"{ZH['answer'].format(id=aid)}?{urllib.parse.urlencode({'include': 'reshipment_settings,question'})}",
            jar, headers=ZH_FETCH,
        )
    except SystemExit:
        raise
    except Exception:
        cur = {}
    if not isinstance(cur, dict):
        cur = {}
    # Keep the answer's current repost setting; if it couldn't be read and the
    # user gave no override, fall back to the conservative "disallowed" rather
    # than silently granting repost rights.
    reship = _reshipment(args.repost) or cur.get("reshipment_settings") or "disallowed"
    q = cur.get("question") or {}

    if not CONFIRM:
        out({
            "dry_run": True,
            "command": "edit-answer",
            "platform": "zhihu",
            "answer_id": str(aid),
            "question_title": q.get("title"),
            "reshipment_settings": reship,
            "content_bytes": len(content),
            "images_found": count_images(content),
            "note": "re-run with --confirm as the LAST argument to actually overwrite. "
                    "This replaces the live, public answer's content on the user's real account.",
        })
        return

    image_stats = {"found": 0, "rehosted": 0, "failed": 0}
    if not args.no_images:
        content, image_stats = rehost_images(jar, content)

    status, text = request(
        "PUT", ZH["answer"].format(id=aid), jar,
        headers=ZH_FETCH, body={"content": content, "reshipment_settings": reship},
    )
    if status >= 400:
        die(f"edit answer failed ({status}) for {aid}: {text[:300]}")
    qid = q.get("id")
    out({
        "ok": True,
        "edited": True,
        "answer_id": str(aid),
        "images": image_stats,
        "url": (f"https://www.zhihu.com/question/{qid}/answer/{aid}" if qid else None),
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
    "answers": cmd_answers,
    "answer": cmd_answer,
    "question": cmd_question,
    "answer-question": cmd_answer_question,
    "edit-answer": cmd_edit_answer,
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

    sp = sub.add_parser("answers", help="list the user's published answers + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--offset", type=int, default=0)

    sp = sub.add_parser("answer", help="one answer's details + stats")
    sp.add_argument("id")

    sp = sub.add_parser("question", help="a question's info + whether you already answered it")
    sp.add_argument("id")

    sp = sub.add_parser("answer-question",
                        help="post a NEW answer to a question (GATED by trailing --confirm)")
    sp.add_argument("--question", help="question id to answer")
    sp.add_argument("--content", help="HTML content inline")
    sp.add_argument("--content-file", help="path to an HTML file")
    sp.add_argument("--draft-only", action="store_true",
                    help="save a private draft on the question; do NOT go public")
    sp.add_argument("--repost", choices=["allowed", "disallowed"],
                    help="转载授权: allow or disallow reposting (default disallowed)")
    sp.add_argument("--no-images", action="store_true",
                    help="skip re-hosting external images to Zhihu's CDN")

    sp = sub.add_parser("edit-answer",
                        help="overwrite an existing answer's content (GATED by trailing --confirm)")
    sp.add_argument("--id", help="answer id to edit")
    sp.add_argument("--content", help="HTML content inline")
    sp.add_argument("--content-file", help="path to an HTML file")
    sp.add_argument("--repost", choices=["allowed", "disallowed"],
                    help="转载授权: override repost permission (default keeps current)")
    sp.add_argument("--no-images", action="store_true",
                    help="skip re-hosting external images to Zhihu's CDN")

    args = p.parse_args(ARGV)
    jar = load_cookies(args.platform)
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
