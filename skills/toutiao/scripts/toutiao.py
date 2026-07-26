#!/usr/bin/env python3
"""
toutiao — read & publish on 今日头条 (mp.toutiao.com) with the user's own login
cookies (BYOC). Standard-library only (urllib), no third-party deps, so it runs
in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var ``TOUTIAO_COOKIES``
— a list of ``{name, value, domain, ...}`` dicts captured by the ACE extension.

头条's creator APIs are cookie-only (no request signing); writes additionally
need the ``csrftoken`` cookie echoed back as the ``X-CSRFToken`` header.

Read commands run directly. ``publish`` is GATED: without a trailing
``--confirm`` it only dry-runs. ``--confirm`` is honored ONLY as the last
argument, so a title/content that merely contains "--confirm" can never silently
go live. ``--draft-only`` stops after saving a private draft.

Examples:
  python3 toutiao.py whoami
  python3 toutiao.py articles --limit 20
  python3 toutiao.py articles --status draft
  python3 toutiao.py article <pgc-id>
  python3 toutiao.py publish --title T --content-file a.md --draft-only --confirm
"""

from __future__ import annotations

import argparse
import gzip
import html as _html
import ipaddress
import json
import os
import random
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PLATFORM = "toutiao"
MP = "https://mp.toutiao.com"

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
        die(f"{env} is not set — connect 今日头条 at "
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

def _headers(jar: list, referer: str) -> dict:
    return {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": referer,
        "Origin": MP,
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def request(method: str, url: str, jar: list, *, referer, headers=None, body=None,
            nonfatal=False):
    hdrs = _headers(jar, referer)
    if headers:
        hdrs.update(headers)
    data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → urllib will NOT re-send these if the API 30x-redirects to a
    # different host (e.g. a login page), so neither the jar nor the CSRF token
    # (which is itself a cookie value) leaks off-site.
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    # Writes are rejected without the csrftoken cookie echoed as a header.
    req.add_unredirected_header("X-CSRFToken", str(cookie_value(jar, "csrftoken") or ""))
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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
        if nonfatal:
            raise RuntimeError(f"network error reaching {url}: {e.reason}")
        die(f"network error reaching {url}: {e.reason}")


def api_envelope(method: str, path: str, jar: list, *, referer=None, body=None, headers=None,
                 nonfatal=False):
    """Call an mp.toutiao.com endpoint and return the raw {code, message, ...}
    envelope, dying on a non-zero code. 头条 answers HTTP 200 even for logical
    failures, so the envelope code is the real status."""
    url = f"{MP}{path}"
    ref = referer or f"{MP}/profile_v4/graphic/articles"
    status, text = request(method, url, jar, referer=ref, body=body, headers=headers,
                           nonfatal=nonfatal)
    if status in (401, 403) or "/auth/page/login" in text:
        msg = (f"auth failed ({status}) on {path} — cookie likely expired. "
               f"Reconnect 今日头条 at https://auth.acedata.cloud/user/connections.")
        if nonfatal:
            raise RuntimeError(msg)
        die(msg)
    try:
        env = json.loads(text)
    except json.JSONDecodeError:
        if nonfatal:
            raise RuntimeError(f"non-JSON response ({status}) from {path}: {text[:200]}")
        die(f"non-JSON response ({status}) from {path}: {text[:300]}")
    if not isinstance(env, dict):
        if nonfatal:
            raise RuntimeError(f"unexpected response from {path}: {text[:200]}")
        die(f"unexpected response from {path}: {text[:300]}")
    # `.get("code", …)` would return a stored None instead of falling back to
    # err_no, so test explicitly.
    code = env.get("code")
    if code is None:
        code = env.get("err_no")
    if code not in (0, None):
        msg = env.get("message") or env.get("reason") or ""
        if code in (401, 403) or "登录" in str(msg):
            auth_msg = (f"auth failed (code={code}: {msg}) — cookie likely expired. "
                        f"Reconnect at https://auth.acedata.cloud/user/connections.")
            if nonfatal:
                raise RuntimeError(auth_msg)
            die(auth_msg)
        if nonfatal:
            raise RuntimeError(f"头条 API error on {path} (code={code}): {msg}")
        die(f"头条 API error on {path} (code={code}): {msg}")
    return env


def api(method: str, path: str, jar: list, **kw):
    """Same as api_envelope but unwraps the `data` payload."""
    return api_envelope(method, path, jar, **kw).get("data")


# ── commands ────────────────────────────────────────────────────────

def media_info(jar):
    d = api("GET", "/mp/agw/media/get_media_info/", jar, referer=f"{MP}/profile_v4/index")
    if not isinstance(d, dict):
        die("could not read 头条号 profile (cookie expired?)")
    return d


def cmd_whoami(jar, _args):
    d = media_info(jar)
    media = d.get("media") or {}
    user = d.get("user") or {}
    _, total = _list_page(jar, "all", 1, 1)
    out({
        "user_id": user.get("id"),
        "media_id": media.get("id"),
        "name": user.get("screen_name") or media.get("display_name"),
        "url": f"https://www.toutiao.com/c/user/token/{media.get('id')}/"
               if media.get("id") else None,
        "articles_total": total,
        "media_level": media.get("article_media_level"),
    })


# status → 头条's own filter value. `all` also returns drafts (is_draft=1).
_STATUS = {"all": "all", "draft": "draft", "published": "published",
           "reviewing": "verifying", "failed": "unpass"}


def _list_page(jar, status, page, size, nonfatal=False):
    q = urllib.parse.urlencode({
        "status": _STATUS.get(status, "all"), "from_time": 0, "start_time": 0,
        "end_time": 0, "search_word": "", "page": page, "size": size,
    })
    d = api("GET", f"/mp/agw/article/list/?{q}", jar, nonfatal=nonfatal) or {}
    return d.get("content") or [], d.get("total")


def _fmt(a: dict) -> dict:
    pgc = a.get("pgc_id") or a.get("item_id") or a.get("id")
    return {
        "pgc_id": str(pgc) if pgc is not None else None,
        "title": a.get("title"),
        "url": a.get("article_url"),
        "is_draft": bool(a.get("is_draft")),
        "status_desc": a.get("status_desc"),
        "impression_count": a.get("impression_count"),
        # go_detail_count_v2 is the read count; show_go_detail_count is a
        # display-toggle BOOLEAN, never a fallback for it.
        "read_count": a.get("go_detail_count_v2"),
        "comment_count": a.get("comment_count"),
        "digg_count": a.get("digg_count"),
        "create_time": a.get("create_time"),
    }


def _iter_articles(jar, status, hard_cap=2000):
    page, seen = 1, 0
    while seen < hard_cap:
        items, total = _list_page(jar, status, page, 50)
        if not items:
            return
        for it in items:
            yield it
            seen += 1
        if total is not None and seen >= total:
            return
        page += 1


def cmd_articles(jar, args):
    items = []
    for it in _iter_articles(jar, args.status):
        items.append(it)
        if len(items) >= args.limit:
            break
    _, total = _list_page(jar, args.status, 1, 1)
    out({"total": total, "count": len(items), "status": args.status,
         "articles": [_fmt(a) for a in items]})


def cmd_article(jar, args):
    # 头条 has no per-article detail endpoint for the creator (article/edit only
    # works within 14 days of publishing), but the list already carries every
    # stat, so resolve by scanning it.
    for it in _iter_articles(jar, "all"):
        if str(it.get("pgc_id")) == str(args.id) or str(it.get("item_id")) == str(args.id):
            res = _fmt(it)
            res["abstract"] = (it.get("abstract") or "")[:200]
            res["word_count"] = it.get("content_word_cnt")
            out(res)
            return
    die(f"article {args.id} not found among your 头条 articles")


# ── image re-host (头条 rejects the whole article if an <img> is external) ──

MAX_IMG_BYTES = 12 * 1024 * 1024
# Two branches. The first is attribute-aware so a `>` inside alt="3 > 2" can't
# tear the tag apart; quoted runs exclude `<` so an unbalanced quote can only
# damage one tag instead of swallowing the rest of the article. The second
# catches malformed tags (odd quote count) that branch 1 rejects — they must
# still be seen, so _SRC_ATTR fails and the publish aborts rather than shipping
# an external image. Excluding `<` also keeps the scan linear.
_HTML_IMG = re.compile(
    r"""<img\b(?:[^<>"']|"[^"<]*"|'[^'<]*')*>|<img\b[^<>]*>""", re.I)
# (?<![-\w]) so `data-src=` / `x_src=` don't masquerade as the real src.
_SRC_ATTR = re.compile(r"""(?<![-\w])src\s*=\s*["']([^"']{0,2000})["']""", re.I)
_ALT_ATTR = re.compile(r"""(?<![-\w])alt\s*=\s*["']([^"']{0,500})["']""", re.I)
_IMG_SKIP = ("toutiao.com", "byteimg.com", "pstatp.com", "toutiaoimg.com")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    # Refuse redirects on image fetches — a 30x could otherwise reach an internal
    # host that _assert_public_url() never saw (SSRF).
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(f"image redirect blocked ({code}) -> {newurl[:80]}")


_IMG_OPENER = urllib.request.build_opener(_NoRedirect)


def _assert_public_url(url):
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
    if len(data) > MAX_IMG_BYTES:
        raise RuntimeError(f"image exceeds {MAX_IMG_BYTES} bytes")
    return data


def _same_or_sub(host, suffix):
    return host == suffix or host.endswith("." + suffix)


def _ext_of(url, default="png"):
    tail = url.rsplit("/", 1)[-1].split("?")[0]
    if "." in tail:
        e = tail.rsplit(".", 1)[-1].lower()
        if e in ("jpg", "jpeg", "png", "gif", "webp"):
            return e
    return default


def _multipart(field, filename, blob, ctype):
    boundary = "----acedata" + "".join(random.choice("0123456789abcdef") for _ in range(20))
    body = b"".join([
        (f'--{boundary}\r\nContent-Disposition: form-data; name="{field}";'
         f' filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n').encode(),
        blob,
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    return body, boundary


def upload_image(jar, src) -> dict:
    """Upload one image to 头条's CDN, returning its {url, web_uri, width, ...}."""
    img = _download_image(src)
    ext = _ext_of(src)
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    # The upload form field MUST be `upfile` — `file`/`image` return 1053.
    body, boundary = _multipart("upfile", f"image.{ext}", img, mime)
    # This endpoint answers with a FLAT envelope (no `data` wrapper), unlike the
    # rest of the creator API, so read the fields off the top level.
    # nonfatal → a per-image failure raises instead of die()ing, so the caller's
    # failure collector (and --drop-failed-images) actually gets to run.
    env = api_envelope("POST", "/mp/agw/article_material/photo/upload_picture/?type=json", jar,
                       referer=f"{MP}/profile_v4/graphic/publish", body=body,
                       headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                       nonfatal=True)
    if not env.get("web_url") or not env.get("web_uri"):
        raise RuntimeError(f"upload returned no image URL: {str(env)[:200]}")
    return env


def _img_tag(info: dict, alt: str) -> str:
    """头条 needs the CDN attributes it returned, not a bare src — a plain
    <img src> (or any external URL) makes publish fail with 7115 图片uri非法."""
    return (
        f'<img src="{_attr_url(info["web_url"])}"'
        f' img_width="{int(info.get("width") or 0)}"'
        f' img_height="{int(info.get("height") or 0)}"'
        f' image_type="{int(info.get("image_type") or 1)}"'
        f' mime_type="{_alt(str(info.get("mime_type") or "image/jpeg"))}"'
        f' web_uri="{_alt(str(info["web_uri"]))}"'
        f' alt="{_alt(alt)}">'
    )


def rehost_images(jar, html, drop_failed=False):
    """Rewrite every <img> in the rendered body to a 头条-hosted one.

    An external <img> is not merely blocked — it makes 头条 reject the WHOLE
    article (7115), so keeping the original is never an option. Default is to
    abort the publish so the user's article is never silently posted without
    its images; ``drop_failed`` opts into dropping them instead.
    """
    failures = []

    def repl(m):
        tag = m.group(0)
        src_m = _SRC_ATTR.search(tag)
        if not src_m:
            # No parseable src (unquoted, or malformed) — count it as a failure
            # rather than dropping it silently.
            failures.append(f"{tag[:80]} (no parseable src attribute)")
            return ""
        src = _html.unescape(src_m.group(1))
        alt_m = _ALT_ATTR.search(tag)
        # Keep alt in its escaped attribute form — unescaping would put raw
        # </>/& back into the body we re-emit (breaking the tag, and undoing
        # md_to_html's escaping).
        alt = alt_m.group(1) if alt_m else ""
        host = (urllib.parse.urlsplit(src).hostname or "").lower()
        if any(_same_or_sub(host, s) for s in _IMG_SKIP) and 'web_uri="' in tag:
            return tag
        try:
            info = upload_image(jar, src)
            sys.stderr.write(f"[img] rehosted {src[:60]} -> {info['web_uri']}\n")
            return _img_tag(info, alt)
        except Exception as e:  # noqa: BLE001 — collected, then reported below
            failures.append(f"{src[:80]} ({e})")
            return ""

    result = _HTML_IMG.sub(repl, html)
    if failures and not drop_failed:
        die("could not upload these images to 头条, and 头条 rejects any article "
            "with an external image, so nothing was published:\n  - "
            + "\n  - ".join(failures)
            + "\nFix the image URLs, or re-run with --drop-failed-images to "
              "publish without them.")
    for f in failures:
        sys.stderr.write(f"[img] DROPPED {f}\n")
    return result


# ── Markdown → HTML (头条's `content` field is rendered HTML, not source) ──

_IMG_RE = re.compile(r"!\[([^\]]{0,500})\]\(([^)\s]{0,2000})\)")
_LINK_RE = re.compile(r"(?<!!)\[([^\]]{0,500})\]\(([^)\s]{0,2000})\)")


def _attr_url(u):
    # Strip C0 controls/space FIRST, then allow only http/https/mailto — otherwise
    # `\x01javascript:` would slip past a literal scheme check yet be re-normalised
    # to javascript: by the browser. Finally neutralise attribute-breaking quotes.
    u = re.sub(r"[\x00-\x20\x7f]", "", u or "")
    m = re.match(r"(?i)([a-z][a-z0-9+.\-]*):", u)
    if m and m.group(1).lower() not in ("http", "https", "mailto"):
        return "#"
    return u.replace('"', "%22").replace("'", "%27")


def _alt(s):
    return (s or "").replace('"', "&quot;").replace("'", "&#x27;")


def _inline_md(t):
    t = _html.escape(t, quote=False).replace("\x00", "")
    # Stash code spans FIRST so emphasis/link/image markup inside `…` stays literal.
    spans = []

    def _stash(m):
        spans.append("<code>" + m.group(1) + "</code>")
        return f"\x00{len(spans) - 1}\x00"

    t = re.sub(r"`([^`]+)`", _stash, t)
    t = _IMG_RE.sub(lambda m: f'<img src="{_attr_url(m.group(2))}" alt="{_alt(m.group(1))}">', t)
    t = _LINK_RE.sub(lambda m: f'<a href="{_attr_url(m.group(2))}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], t)
    return t


def _md_block_to_html(b):
    b = b.strip("\n")
    if not b.strip():
        return None
    f = b.lstrip()
    m = re.match(r"(#{1,6})\s+(.*)", f)
    if m:
        lvl = len(m.group(1))
        return f"<h{lvl}>{_inline_md(m.group(2).strip())}</h{lvl}>"
    if f.startswith(">"):
        inner = re.sub(r"^>\s?", "", b, flags=re.M).replace("\n", " ")
        return "<blockquote><p>" + _inline_md(inner) + "</p></blockquote>"
    if re.match(r"[-*+]\s+", f):
        items = [_inline_md(re.sub(r"^[-*+]\s+", "", ln)) for ln in b.split("\n") if ln.strip()]
        return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"
    if re.match(r"\d+\.\s+", f):
        items = [_inline_md(re.sub(r"^\d+\.\s+", "", ln)) for ln in b.split("\n") if ln.strip()]
        return "<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"
    only = re.fullmatch(r"!\[([^\]]{0,500})\]\(([^)\s]{0,2000})\)", f)
    if only:
        return f'<img src="{_attr_url(only.group(2))}" alt="{_alt(_html.escape(only.group(1), quote=False))}">'
    return "<p>" + _inline_md(b.replace("\n", " ").strip()) + "</p>"


def md_to_html(src):
    """Minimal stdlib Markdown→HTML — 头条's body field is HTML, so raw markdown
    would publish as literal `##` / `![]()` on one collapsed line."""
    src = (src or "").strip()
    res = []
    # Pull fenced code out FIRST (it may itself contain blank lines) so the
    # blank-line block splitter below can never tear a ``` … ``` fence apart.
    for i, part in enumerate(re.split(r"(?ms)^(```.*?(?:\n```[ \t]*$|\Z))", src)):
        if i % 2 == 1:
            code = re.sub(r"\A```[^\n]*\n?", "", part)
            code = re.sub(r"\n?```[ \t]*\Z", "", code)
            res.append("<pre><code>" + _html.escape(code) + "</code></pre>")
            continue
        for b in re.split(r"\n[ \t]*\n", part):
            block = _md_block_to_html(b)
            if block:
                res.append(block)
    return "\n".join(res)


def _looks_like_markdown(s):
    # Three-way classification (no full parser): block-level HTML ⇒ already an
    # HTML document → pass through; else markdown markers ⇒ render; else
    # inline-only HTML ⇒ pass through; else plain text ⇒ render.
    s = s or ""
    if re.search(
        r"</?(?:p|div|h[1-6]|ul|ol|li|table|thead|tbody|tr|td|th|blockquote|"
        r"pre|figure|figcaption|section|article|header|footer|nav|aside|hr|"
        r"main|details|summary)\b", s, re.I,
    ):
        return False
    # ^-anchored (re.M) + bounded {0,N} repeats so the scan can't backtrack
    # across newlines or to EOF (no quadratic scanning).
    if re.search(
        r"^#{1,6}\s|!\[[^\]]{0,500}\]\([^)]{0,2000}\)|^[ \t]*[-*+]\s|^[ \t]*\d+\.\s"
        r"|\[[^\]]{0,500}\]\([^)]{0,2000}\)|`[^`]{1,500}`|\*\*[^*]{1,500}\*\*",
        s, re.M,
    ):
        return True
    inline_html = re.search(
        r"</?(?:a|strong|em|b|i|u|s|span|code|br|img|small|mark|sup|sub|"
        r"video|audio|iframe)\b", s, re.I,
    )
    return not inline_html


# ── publish ─────────────────────────────────────────────────────────

PUBLISH_PATH = "/mp/agw/article/publish/?source=mp&type=article"


def _resolve_url(jar, pgc_id, draft):
    """Look the freshly-written article up in the list to return its real URL
    (preview URL for a draft, public /item/ URL once published).

    Runs AFTER the write succeeded, so it must never fail the command — losing
    the pgc_id would read as a failed publish and invite a duplicate post.
    """
    try:
        items, _ = _list_page(jar, "draft" if draft else "all", 1, 20, nonfatal=True)
        for it in items:
            if str(it.get("pgc_id")) == str(pgc_id):
                return it.get("article_url")
    except (Exception, SystemExit):  # noqa: BLE001 — URL is a nicety
        pass
    if draft:
        return f"{MP}/preview_article/?pgc_id={pgc_id}"
    return f"https://www.toutiao.com/item/{pgc_id}/"


def cmd_publish(jar, args):
    if not args.title:
        die("--title is required")
    # 头条 rejects out-of-range titles server-side; fail early with a clear message.
    if not 2 <= len(args.title) <= 30:
        die(f"头条 titles must be 2–30 characters; got {len(args.title)}")
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
            "dry_run": True, "command": "publish", "platform": "toutiao",
            "title": args.title, "draft_only": args.draft_only,
            "content_bytes": len(content),
            "note": "头条 content is Markdown (converted to HTML for the body). "
                    "Re-run with --confirm as the LAST argument to actually write. "
                    "Without --draft-only it publishes a PUBLIC article on the "
                    "user's real 头条号 and goes through 审核.",
        })
        return

    # Writes need the csrftoken cookie echoed as a header; without it 头条 fails
    # deep in its API with an opaque code instead of "reconnect".
    if not cookie_value(jar, "csrftoken"):
        die("the 今日头条 cookie jar has no `csrftoken` — it is incomplete or "
            "expired. Reconnect at https://auth.acedata.cloud/user/connections.")

    # Render to HTML FIRST, then rewrite <img> tags — 头条 rejects the whole
    # article (7115) if any image isn't hosted on its own CDN with web_uri.
    body_html = md_to_html(content) if _looks_like_markdown(content) else content
    if not args.no_rehost_images:
        body_html = rehost_images(jar, body_html, drop_failed=args.drop_failed_images)

    form = urllib.parse.urlencode({
        "title": args.title,
        "content": body_html,
        # save=1 → draft; save=0 → submit for 审核 and publish.
        "save": "1" if args.draft_only else "0",
        # 0 = no ad. Other values need 广告/自营 permissions most accounts lack.
        "article_ad_type": "0",
    })
    d = api("POST", PUBLISH_PATH, jar, referer=f"{MP}/profile_v4/graphic/publish",
            body=form, headers={"Content-Type": "application/x-www-form-urlencoded"})
    pgc_id = (d or {}).get("pgc_id")
    if not pgc_id:
        die(f"publish returned no pgc_id: {str(d)[:300]}")
    out({
        "ok": True,
        "draft_only": bool(args.draft_only),
        "published": not args.draft_only,
        "pgc_id": str(pgc_id),
        "url": _resolve_url(jar, pgc_id, args.draft_only),
        "note": None if args.draft_only else "头条 reviews new articles (审核); "
                                             "the public URL goes live once it passes.",
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "articles": cmd_articles,
    "article": cmd_article,
    "publish": cmd_publish,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="toutiao.py", description="今日头条 cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in 头条号")
    sp = sub.add_parser("articles", help="list the user's articles + stats")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--status", default="all",
                    choices=["all", "draft", "published", "reviewing", "failed"])
    sp = sub.add_parser("article", help="one article's stats")
    sp.add_argument("id", help="pgc_id / item_id")
    sp = sub.add_parser("publish", help="create/publish an article (GATED by trailing --confirm)")
    sp.add_argument("--title", help="2–30 characters")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--draft-only", action="store_true",
                    help="save a private draft; do NOT go public")
    sp.add_argument("--no-rehost-images", action="store_true",
                    help="keep external image URLs as-is (头条 will reject the article)")
    sp.add_argument("--drop-failed-images", action="store_true",
                    help="publish without any image that fails to upload, "
                         "instead of aborting")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
