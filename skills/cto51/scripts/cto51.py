#!/usr/bin/env python3
"""
cto51 — read & draft on 51CTO 博客 (blog.51cto.com) with the user's own login
cookies (BYOC). Standard-library only (urllib), no third-party deps, so it runs
in the bare sandbox without an image change.

The connector injects the user's cookie jar as a JSON env var ``CTO51_COOKIES``
— a list of ``{name, value, domain, ...}`` dicts captured by the ACE extension.
(The namespace is `cto51`, not `51cto`, because `51CTO_COOKIES` would not be a
valid shell identifier.)

Read commands run directly. ``draft`` is GATED: without a trailing ``--confirm``
it only dry-runs. ``--confirm`` is honored ONLY as the last argument.

NOTE: this creates a DRAFT and returns its editor URL; the user finishes
publishing in the 51CTO editor.

Examples:
  python3 cto51.py whoami
  python3 cto51.py draft --title T --content-file a.md --confirm
"""

from __future__ import annotations

import argparse
import gzip
import http.client
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
PLATFORM = "cto51"
BASE = "https://blog.51cto.com"
PUBLISH_PAGE = f"{BASE}/blogger/publish"
# Cap on the FORM-ENCODED body (urlencode expands CJK ~3x).
MAX_ENCODED_BYTES = 8 * 1024 * 1024

# Bounded quantifiers so a hostile page cannot cause catastrophic backtracking.
_CSRF_RE = re.compile(r'<meta\s{1,10}name="csrf-token"\s{1,10}content="([^"]{1,500})"')
_USER_RE = re.compile(
    r'<li class="more user">\s{0,50}<a[^>]{0,300}href="([^"]{1,300})"[^>]{0,300}>'
    r'\s{0,50}<img[^>]{0,300}src="([^"]{1,300})"'
)

_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects outright.

    add_unredirected_header only protects the Cookie; urllib copies every other
    header (here the `_csrf` form token's companion headers) onto the redirected
    request, so a 30x to a foreign host could hand them over.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect())


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# 51CTO error/WAF pages carry the site chrome, including the csrf-token meta —
# never echo a raw response body without stripping it. Covers both the HTML meta
# form (name="csrf-token" content="…") and any JSON/inline "csrfToken":"…".
_CSRF_LEAK_RES = (
    # name="csrf-token" … content="TOKEN"  (and the reversed attribute order)
    re.compile(r'(name=["\']csrf[-_]?token["\'][^>]{0,400}?content=["\'])([^"\']{0,500})', re.I),
    re.compile(r'(content=["\'])([^"\']{0,500})(["\'][^>]{0,400}?name=["\']csrf[-_]?token)', re.I),
    # "_csrf": "TOKEN" / _csrf=TOKEN / csrfToken: 'TOKEN'  — 51CTO runs Yii, whose
    # CSRF parameter is literally `_csrf`, so `token` must be OPTIONAL here.
    re.compile(r'(_?csrf[-_]?(?:token)?["\']?\s{0,5}[:=]\s{0,5}["\']?)([^"\'&,\s>;]{1,500})', re.I),
)


def _redact(text: str) -> str:
    for rx in _CSRF_LEAK_RES:
        text = rx.sub(
            (lambda mo: mo.group(1) + "<redacted>" + (mo.group(3) if mo.lastindex and mo.lastindex >= 3 else "")),
            text,
        )
    return text



# ── Cookie jar (shared pattern across the cookie-BYOC skills) ────────

def load_cookies() -> list:
    env = f"{PLATFORM.upper()}_COOKIES"
    raw = os.environ.get(env)
    if not raw:
        die(f"{env} is not set — connect 51CTO at "
            f"https://studio.acedata.cloud/console/connectors, then retry.")
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
        # http.client raises ValueError("Invalid header value %r" % value) at
        # send time for CR/LF, and UnicodeEncodeError for non-latin1 — and the
        # exception text carries the WHOLE Cookie header. Reject here, with a
        # message that never echoes a value.
        pair = f"{name}={value}"
        if any(ch in pair for ch in "\r\n\x00"):
            die("a cookie in the jar contains a line break and cannot be sent — "
                "reconnect at https://studio.acedata.cloud/console/connectors.")
        try:
            pair.encode("latin-1")
        except UnicodeEncodeError:
            die("a cookie in the jar contains characters that cannot be sent in "
                "an HTTP header — reconnect at "
                "https://studio.acedata.cloud/console/connectors.")
        parts.append(pair)
    return "; ".join(parts)


def request(method: str, url: str, jar: list, *, headers=None, form=None,
            write: bool = False):
    # 51CTO's WAF 567s a bare request; it needs a full browser fingerprint
    # (same treatment the csdn skill needs).
    hdrs = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Origin": BASE,
        "Referer": PUBLISH_PAGE,
    }
    if headers:
        hdrs.update(headers)
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → the cookie is not re-sent if the API 30x-redirects to a
    # different host (e.g. a login page), so the jar never leaks off-site.
    req.add_unredirected_header("Cookie", cookie_header(jar, url))
    try:
        with _OPENER.open(req, timeout=30) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return resp.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            die("51CTO redirected the request — not followed, so no credential "
                "left 51cto.com. You are most likely logged out; reconnect at "
                "https://studio.acedata.cloud/console/connectors."
                + (" This was a WRITE: its outcome is UNKNOWN — check your "
                   "drafts before retrying." if write else ""))
        # Draining the error body can itself raise (IncompleteRead / reset).
        # Degrade to an empty body so a truncated 5xx still flows into the
        # normal non-JSON path, which carries the write-UNKNOWN wording.
        try:
            raw = e.read()
            if e.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
        except Exception:
            raw = b""
        return e.code, raw.decode("utf-8", "replace")
    # URLError subclasses OSError, so it must come first. The receive phase
    # (getresponse) raises TimeoutError/HTTPException OUTSIDE urllib's own
    # OSError wrapper, so a write whose reply never lands would otherwise
    # escape as a bare traceback with no JSON at all.
    except (urllib.error.URLError, TimeoutError, socket.timeout,
            http.client.HTTPException, gzip.BadGzipFile, OSError) as e:
        if write:
            die(f"51CTO write did not return a result ({type(e).__name__}: {e}); "
                f"the outcome is UNKNOWN. Check your 51CTO drafts before "
                f"retrying so you do not create a duplicate.")
        die(f"network error reaching {url}: {type(e).__name__}: {e}")


def publish_page(jar: list) -> tuple[str, dict]:
    """Fetch the publish page — it carries both the identity and the CSRF token."""
    status, html = request("GET", PUBLISH_PAGE, jar)
    if status in (401, 403):
        die("auth failed — cookie expired or invalid. Reconnect at "
            "https://studio.acedata.cloud/console/connectors.")
    if status != 200:
        die(f"unexpected status {status} loading the 51CTO publish page")
    m = _USER_RE.search(html)
    if not m:
        # The csrf-token meta also appears on logged-out pages, so it is not a
        # session signal. Distinguish "definitely logged out" from "markup
        # changed" instead of always blaming the cookie.
        if "/user/login" in html or "home.51cto.com/login" in html:
            die("not logged in to 51CTO — reconnect at "
                "https://studio.acedata.cloud/console/connectors.")
        die("could not confirm the 51CTO session from the publish page — either "
            "the cookie expired or 51CTO changed its markup. Try reconnecting "
            "at https://studio.acedata.cloud/console/connectors; if that does not "
            "help, this skill needs updating.")
    link, avatar = m.group(1), m.group(2)
    csrf_m = _CSRF_RE.search(html)
    if not csrf_m:
        die("could not read the 51CTO CSRF token from the publish page; "
            "reconnect and retry.")
    uid = link.rstrip("/").split("/")[-1]
    return csrf_m.group(1), {"user_id": uid, "url": link, "avatar": avatar}


# ── commands ────────────────────────────────────────────────────────

def cmd_whoami(jar, _args):
    _csrf, who = publish_page(jar)
    out({"platform": PLATFORM, **who})


def read_content(args) -> str:
    content = args.content
    if args.content_file:
        try:
            with open(args.content_file, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            die(f"cannot read --content-file: {e}")
    if content is None:
        die("provide --content-file <path.md> or --content <markdown>")
    # The body is form-urlencoded, which expands each CJK byte to %XX (~3x), so
    # cap the ENCODED size — a raw-byte cap would let a 10 MiB Chinese article
    # become a ~30 MB POST that 51CTO rejects opaquely mid-write.
    encoded = len(urllib.parse.quote_plus(content))
    if encoded > MAX_ENCODED_BYTES:
        die(f"content is too large: {encoded} bytes once form-encoded "
            f"(limit {MAX_ENCODED_BYTES}). Split the article or trim it.")
    return content


def cmd_draft(jar, args):
    if not args.title:
        die("--title is required")
    content = read_content(args)
    tags = ",".join(t.strip() for t in (args.tags or "").split(",") if t.strip())

    if not CONFIRM:
        out({
            "dry_run": True, "command": "draft", "platform": PLATFORM,
            "title": args.title, "tags": tags,
            "abstract": args.abstract or "",
            "content_characters": len(content),
            "note": "51CTO content is Markdown (is_old=0). Re-run with --confirm "
                    "as the LAST argument to actually create the draft. This "
                    "creates a DRAFT — finish publishing in the 51CTO editor.",
        })
        return

    csrf, _who = publish_page(jar)
    # We hold the exact token, so scrub it by value too — airtight regardless of
    # how 51CTO frames it in an error page (the patterns are defence in depth).
    def scrub(text: str) -> str:
        return _redact(text.replace(csrf, "<redacted>") if csrf else text)
    form = {
        "title": args.title,
        "content": content,
        "cate_id": "",
        "custom_id": "0",
        "tag": tags,
        "abstract": args.abstract or "",
        "banner_type": "0",
        "blog_type": "1",
        "copy_code": "1",
        "is_hide": "0",
        "top_time": "0",
        "is_comment": "0",
        "is_old": "0",  # 0 = Markdown
        "blog_id": "",
        "pid": "",
        "did": "",
        "work_id": "",
        "class_id": "",
        "subjectId": "",
        "import_type": "-1",
        "invite_code": "",
        "raffle": "",
        "orig": "",
        "_csrf": csrf,
    }
    status, text = request("POST", f"{BASE}/blogger/draft", jar, write=True, form=form,
                           headers={
                               "X-Requested-With": "XMLHttpRequest",
                               "Accept": "application/json, text/javascript, */*; q=0.01",
                               "Sec-Fetch-Dest": "empty",
                               "Sec-Fetch-Mode": "cors",
                           })
    try:
        res = json.loads(text)
    except json.JSONDecodeError:
        die(f"51CTO write returned a non-JSON response ({status}); the outcome "
            f"is UNKNOWN. Check your drafts before retrying. "
            f"Body: {scrub(text)[:200]}")
    # The endpoint really does answer `"data": []` (a list) for the logged-out
    # case, so never dereference it without checking the shape first.
    if not isinstance(res, dict):
        die(f"51CTO write returned an unexpected response shape ({status}); the "
            f"outcome is UNKNOWN. Check your drafts before retrying.")
    data = res.get("data")
    if res.get("status") != 1 or not isinstance(data, dict):
        # Normalize to JSON, never repr(): a dict/list `msg` rendered with
        # repr() uses single quotes, which _redact's double-quote-anchored
        # patterns cannot match.
        raw_msg = res.get("msg")
        detail = (raw_msg if isinstance(raw_msg, str)
                  else json.dumps(raw_msg if raw_msg is not None else res,
                                  ensure_ascii=False))
        die(f"draft creation failed: {scrub(detail)[:200]}")
    # Only an ASCII-numeric id is a real draft handle. str.isdigit() alone is
    # Unicode-wide ('١٢٣', '²' all pass) and would build a plausible-but-wrong
    # edit_url while reporting ok=true.
    did = str(data.get("did") or "").strip()
    if not re.fullmatch(r"[0-9]{1,20}", did):
        # Redact BEFORE slicing so a token can never be half-exposed by the cut.
        die(f"draft creation returned an unusable id {scrub(did)[:80]!r}; the "
            f"outcome is UNKNOWN — check your 51CTO drafts before retrying. "
            f"{scrub(json.dumps(res, ensure_ascii=False))[:200]}")
    out({
        "ok": True,
        "draft_only": True,
        "draft_id": str(did),
        "edit_url": f"{BASE}/blogger/draft/{did}",
        "note": "Draft saved. Open edit_url to review and publish.",
    })


COMMANDS = {
    "whoami": cmd_whoami,
    "draft": cmd_draft,
}


def main() -> None:
    p = argparse.ArgumentParser(prog="cto51.py", description="51CTO 博客 cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show the logged-in account")
    sp = sub.add_parser("draft", help="create a draft article (GATED by trailing --confirm)")
    sp.add_argument("--title")
    sp.add_argument("--content", help="Markdown content inline")
    sp.add_argument("--content-file", help="path to a Markdown file")
    sp.add_argument("--tags", help="comma-separated tag names")
    sp.add_argument("--abstract", help="short summary shown in listings")
    args = p.parse_args(ARGV)
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    # The agent consuming this CLI parses stdout as JSON — never let an
    # unexpected exception escape as a bare traceback with empty stdout.
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001
        die(f"unexpected {type(exc).__name__}: {_redact(str(exc))[:200]}")
