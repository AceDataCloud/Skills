#!/usr/bin/env python3
"""
hashnode — read & publish on Hashnode with the user's own login cookies (BYOC).
Standard-library only (urllib), no third-party deps.

Hashnode moved its **public GraphQL API behind a paid Pro plan** (2026-05-13), so
this skill does NOT use ``gql-beta.hashnode.com`` / a Personal Access Token.
Instead it drives the **same first-party REST endpoints the web editor uses**
(``https://hashnode.com/api/...``), authenticated by the login session cookie —
which is free and needs no Pro plan.

The connector injects the cookie jar as a JSON env var ``HASHNODE_COOKIES`` (a
JSON list of cookie dicts; the session cookie is ``hashnode-session``). It is
full account access — NEVER echo or print it.

⚠️ Non-Pro publications are subject to Hashnode **automoderation**: overtly
promotional posts (hypey language, repeated identical CTA links, "free credits!!")
are auto-removed within seconds of publishing, so the post 404s even though the
publish call returned success. Write **editorial / how-to** content (a helpful
guide that happens to feature the product, with at most a couple of tasteful
links) and it stays live. ``publish`` re-fetches the live URL and warns if the
post was moderated away.

Read commands run directly. ``publish`` / ``delete`` are GATED by a trailing
``--confirm`` (honored only as the LAST arg). ``draft`` saves a private draft.

Examples:
  python3 hashnode.py publications
  python3 hashnode.py draft   --title T --content-file a.md --cover https://x/y.jpg --tags ai,apis
  python3 hashnode.py publish --title T --content-file a.md --cover https://x/y.jpg --tags ai,apis --confirm
  python3 hashnode.py delete  --id <draftOrPostId> --confirm
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BASE = "https://hashnode.com"

_RAW = sys.argv[1:]
# --confirm is honored ONLY as the last token, so body text containing
# "--confirm" can never silently trigger a write.
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)

# State-changing commands — dry-run unless the invocation ends with --confirm.
GATED = {"publish", "delete"}


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


# ── Cookie jar ──────────────────────────────────────────────────────

def load_cookies() -> list:
    raw = os.environ.get("HASHNODE_COOKIES")
    if not raw:
        die("HASHNODE_COOKIES is not set — connect Hashnode at "
            "https://auth.acedata.cloud/user/connections, then retry.")
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"HASHNODE_COOKIES is not valid JSON: {e}")
    if not isinstance(jar, list):
        die(f"HASHNODE_COOKIES must be a JSON list of cookies, got {type(jar).__name__}")
    if not any(c.get("name") == "hashnode-session" for c in jar):
        die("HASHNODE_COOKIES is missing the 'hashnode-session' cookie — re-capture "
            "on hashnode.com with the ACE extension, then reconnect at "
            "https://auth.acedata.cloud/user/connections.")
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
            # A domain-less cookie only rides along when at least one scoped
            # cookie already matched this host (never leak it to a stray host).
            continue
        parts.append(f"{name}={value}")
    return "; ".join(parts)


# ── HTTP ────────────────────────────────────────────────────────────

def request(method, path, jar, *, body=None):
    url = BASE + path
    hdrs = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": BASE,
        "Referer": BASE + "/",
        "X-Requested-With": "XMLHttpRequest",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    # Unredirected → the cookie is not re-sent if the API 30x-redirects to a
    # different host, so the jar never leaks off-site.
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


def api(method, path, jar, *, body=None, _retried=False):
    status, text = request(method, path, jar, body=body)
    # Hashnode sits behind Cloudflare, which intermittently 403/429s an
    # otherwise valid session; retry idempotent GETs once. Never replay a
    # write (POST/PUT/DELETE) — it could duplicate a publish.
    if status in (403, 429) and method == "GET" and not _retried:
        time.sleep(1.5)
        return api(method, path, jar, body=body, _retried=True)
    if status in (401, 403):
        die(f"auth failed ({status}) on {path} — cookie likely expired. "
            f"Reconnect at https://auth.acedata.cloud/user/connections.")
    # A hashnode.com/api path that 404s with an HTML body means the route/id is
    # wrong; a JSON {success:false} is a real API error.
    stripped = text.lstrip()
    if stripped.startswith("<"):
        die(f"unexpected non-JSON ({status}) from {path} — the route or id is "
            f"likely wrong.")
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        die(f"non-JSON response ({status}) from {path}: {text[:300]}")
    if isinstance(d, dict) and d.get("success") is False:
        die(f"Hashnode API error ({status}) on {path}: {d.get('error')}")
    return d


# ── helpers ─────────────────────────────────────────────────────────

def resolve_publication(jar, wanted: str | None) -> dict:
    d = api("GET", "/api/publications", jar)
    pubs = d.get("publications") or []
    if not pubs:
        die("no publications on this account — create a blog on hashnode.com first.")
    if wanted:
        for p in pubs:
            if wanted in (p.get("_id"), p.get("title"), p.get("displayTitle")):
                return p
        die(f"publication {wanted!r} not found; have: "
            + ", ".join(f'{p.get("title")}({p.get("_id")})' for p in pubs))
    if len(pubs) > 1:
        die("multiple publications — pass --publication <id>. Have: "
            + ", ".join(f'{p.get("title")}({p.get("_id")})' for p in pubs))
    return pubs[0]


def resolve_tags(jar, slugs_csv: str | None) -> list:
    if not slugs_csv:
        return []
    tags = []
    for slug in [s.strip() for s in slugs_csv.split(",") if s.strip()]:
        d = api("GET", f"/api/tags/search?q={urllib.parse.quote(slug)}", jar)
        cands = d.get("tags") or []
        pick = next((t for t in cands if t.get("slug") == slug), None) \
            or (max(cands, key=lambda t: t.get("numPosts", 0)) if cands else None)
        if pick:
            tags.append({"_id": pick["_id"], "name": pick["name"], "slug": pick["slug"]})
    return tags[:5]


def read_content(args) -> str:
    if args.content_file:
        if not os.path.isfile(args.content_file):
            die(f"content file not found: {args.content_file}")
        with open(args.content_file, encoding="utf-8") as fh:
            return fh.read()
    if args.content:
        return args.content
    die("provide --content-file or --content")


def build_save(args, pub_id, jar) -> dict:
    body = {
        "title": (args.title or "").strip(),
        "contentMarkdown": read_content(args),
        "publicationId": pub_id,
    }
    if not body["title"]:
        die("provide --title")
    if args.subtitle:
        body["subtitle"] = args.subtitle
    if args.cover:
        body["coverImage"] = args.cover
        body["ogImage"] = args.cover
    if args.slug:
        body["slug"] = args.slug
    tags = resolve_tags(jar, args.tags)
    if tags:
        body["tags"] = tags
    return body


def create_and_save(args, jar) -> tuple[str, dict]:
    pub = resolve_publication(jar, args.publication)
    d = api("POST", "/api/drafts", jar, body={"publicationId": pub["_id"]})
    did = d.get("draftId")
    if not did:
        die(f"draft creation returned no draftId: {d}")
    save = build_save(args, pub["_id"], jar)
    api("PUT", f"/api/drafts/{did}", jar, body=save)
    return did, pub


# ── commands ────────────────────────────────────────────────────────

def cmd_publications(jar, _args):
    d = api("GET", "/api/publications", jar)
    out({"publications": [
        {"id": p.get("_id"), "title": p.get("title"),
         "url": p.get("url") or p.get("domain")} for p in d.get("publications") or []]})


def cmd_draft(jar, args):
    did, pub = create_and_save(args, jar)
    out({"ok": True, "draft_id": did, "publication": pub.get("title"),
         "editor_url": f"https://hashnode.com/draft/{did}",
         "note": "Private draft saved. Review it, then run `publish ... --confirm` to go live."})


def cmd_publish(jar, args):
    did, pub = create_and_save(args, jar)
    d = api("POST", f"/api/drafts/{did}/publish", jar, body={})
    post = d.get("post") or {}
    url = post.get("url")
    result = {"ok": True, "posted": True, "id": post.get("id"),
              "title": post.get("title"), "url": url, "publication": pub.get("title")}
    # Verify the post is actually live — non-Pro blogs auto-moderate promo posts.
    if url:
        time.sleep(4)
        try:
            code = _url_status(url)
            if code == 404:
                result["ok"] = False
                result["warning"] = (
                    "The publish call succeeded but the live URL returns 404 — "
                    "Hashnode automoderation removed the post (common for overtly "
                    "promotional content on a non-Pro blog). Rewrite it in an "
                    "editorial / how-to style with fewer repeated CTA links and "
                    "republish.")
        except Exception:
            pass
    out(result)


def _url_status(url: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def cmd_delete(jar, args):
    d = api("DELETE", f"/api/drafts/{args.id}", jar)
    out({"ok": True, "deleted": True, "id": d.get("deletedDraftId") or args.id})


COMMANDS = {
    "publications": cmd_publications,
    "draft": cmd_draft,
    "publish": cmd_publish,
    "delete": cmd_delete,
}


def gated_dry_run(args) -> None:
    out({"dry_run": True, "command": args.command,
         "title": getattr(args, "title", None), "id": getattr(args, "id", None),
         "note": "Re-run with --confirm as the LAST argument to actually run this "
                 "on the user's REAL Hashnode blog."})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Hashnode via login cookies (no Pro).")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("publications", help="list my blogs (publications)")

    def add_write_args(sp):
        sp.add_argument("--title", required=True)
        sp.add_argument("--subtitle")
        sp.add_argument("--content-file", dest="content_file", help="path to a Markdown file")
        sp.add_argument("--content", help="inline Markdown (use --content-file for长文)")
        sp.add_argument("--cover", help="cover image URL (also used as OG image)")
        sp.add_argument("--tags", help="comma-separated tag slugs, e.g. ai,apis")
        sp.add_argument("--slug", help="custom URL slug (optional)")
        sp.add_argument("--publication", help="publication id (needed only if >1 blog)")

    add_write_args(sub.add_parser("draft", help="save a PRIVATE draft (safe, non-public)"))
    add_write_args(sub.add_parser("publish", help="publish a post (GATED by trailing --confirm)"))

    sp = sub.add_parser("delete", help="delete a draft or post (GATED by trailing --confirm)")
    sp.add_argument("--id", required=True)
    return p


def main() -> None:
    args = build_parser().parse_args(ARGV)
    if args.command in GATED and not CONFIRM:
        gated_dry_run(args)
        return
    jar = load_cookies()
    COMMANDS[args.command](jar, args)


if __name__ == "__main__":
    main()
