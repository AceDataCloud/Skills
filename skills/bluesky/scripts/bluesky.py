#!/usr/bin/env python3
"""Bluesky (AT Protocol / XRPC) CLI shipped with the `bluesky` skill.

Deps: `requests` + `Pillow` (both preinstalled in the sandbox). One command does
the whole publish flow that previously had to be hand-assembled from curl + jq +
python heredocs (and kept breaking on shell quoting):

- create a session (handle normalized to a full handle on the default PDS)
- auto-compute richtext `facets` (clickable links, #hashtags, @mentions) with
  correct UTF-8 byte offsets
- attach images: download the URL/path, resize/recompress to Bluesky's ~1 MB
  blob limit, `uploadBlob`, and build the `app.bsky.embed.images` embed
- `createRecord`, then print the public post URL

Secrets ($BLUESKY_APP_PASSWORD) are read from the env and never printed.
"""

import argparse
import io
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from PIL import Image

# bsky.social's uploadBlob rejects images over ~1 MB; stay safely under it.
BLOB_LIMIT = 976_560
URL_RE = re.compile(r"https?://[^\s\]\)]+")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_]+)")
# A mention target must be a dotted handle (name.bsky.social / custom domain);
# each dot-separated segment is non-empty so a trailing sentence dot isn't eaten.
MENTION_RE = re.compile(r"(?<!\w)@([A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+)")


def out(o):
    print(json.dumps(o, ensure_ascii=False))


def die(o):
    out(o)
    sys.exit(1)


def env_service():
    return os.environ.get("BLUESKY_SERVICE", "https://bsky.social").rstrip("/")


def normalize_identifier(handle, svc):
    # A dotted handle, an email or a DID is already valid; a bare username needs
    # `.bsky.social` on the default PDS or createSession returns AuthRequired.
    if any(c in handle for c in ".@") or handle.startswith("did:"):
        return handle
    if svc == "https://bsky.social":
        return f"{handle}.bsky.social"
    return handle


def create_session(svc):
    handle = os.environ["BLUESKY_HANDLE"]
    pw = os.environ["BLUESKY_APP_PASSWORD"]
    ident = normalize_identifier(handle, svc)
    try:
        r = requests.post(
            f"{svc}/xrpc/com.atproto.server.createSession",
            json={"identifier": ident, "password": pw},
            timeout=30,
        )
    except requests.RequestException as e:
        die({"error": "session_request_failed", "detail": str(e)})
    data = r.json() if r.content else {}
    if r.status_code != 200 or not data.get("accessJwt"):
        die({
            "error": "session_failed",
            "status": r.status_code,
            "detail": data,
            "hint": "reconnect the Bluesky connector with your FULL handle "
                    "(e.g. name.bsky.social) and a valid App Password",
        })
    return data["accessJwt"], data["did"], ident


def byte_index(text, char_index):
    return len(text[:char_index].encode("utf-8"))


def resolve_handle(svc, handle):
    try:
        r = requests.get(
            f"{svc}/xrpc/com.atproto.identity.resolveHandle",
            params={"handle": handle},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("did")
    except requests.RequestException:
        pass
    return None


def build_facets(text, svc):
    """Compute link / hashtag / mention facets with UTF-8 byte offsets."""
    facets = []
    url_spans = []  # char ranges already claimed by a link facet
    for m in URL_RE.finditer(text):
        uri = m.group(0).rstrip(".,;:)]}'\"")  # drop trailing punctuation
        c_start, c_end = m.start(), m.start() + len(uri)
        url_spans.append((c_start, c_end))
        facets.append({
            "index": {"byteStart": byte_index(text, c_start),
                      "byteEnd": byte_index(text, c_end)},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": uri}],
        })

    def inside_url(pos):
        # Skip #frag / @x that live inside a URL (e.g. https://x.com/#a) so
        # facets never overlap — atproto rejects overlapping richtext ranges.
        return any(s <= pos < e for s, e in url_spans)

    for m in TAG_RE.finditer(text):
        if inside_url(m.start()):
            continue
        facets.append({
            "index": {"byteStart": byte_index(text, m.start()),
                      "byteEnd": byte_index(text, m.end())},
            "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}],
        })
    for m in MENTION_RE.finditer(text):
        if inside_url(m.start()):
            continue
        did = resolve_handle(svc, m.group(1))
        if did:
            facets.append({
                "index": {"byteStart": byte_index(text, m.start()),
                          "byteEnd": byte_index(text, m.end())},
                "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
            })
    return facets


def fetch_bytes(src):
    if re.match(r"^https?://", src):
        r = requests.get(src, timeout=120, headers={"User-Agent": "Mozilla/5.0 (bluesky-skill)"})
        r.raise_for_status()
        return r.content
    with open(src, "rb") as f:
        return f.read()


def compress_to_limit(raw):
    """Return (bytes, mime) within BLOB_LIMIT, recompressing/resizing if needed."""
    known = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "GIF": "image/gif"}
    try:
        fmt = Image.open(io.BytesIO(raw)).format
    except Exception:
        die({"error": "image_decode_failed", "detail": "could not read the image bytes"})
    # Small AND a format Bluesky handles as-is → upload untouched (keeps PNG
    # transparency / animated GIF). Otherwise fall through and re-encode to JPEG
    # so the blob's bytes always match its declared mimeType.
    if len(raw) <= BLOB_LIMIT and fmt in known:
        return raw, known[fmt]

    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    max_side = max(img.size)
    buf = io.BytesIO()
    for target_side in (max_side, 2048, 1600, 1280, 1024, 800, 640):
        if target_side < max_side:
            ratio = target_side / max_side
            work = img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))))
        else:
            work = img
        for quality in (90, 85, 80, 70, 60, 50, 40):
            buf = io.BytesIO()
            work.save(buf, format="JPEG", quality=quality, optimize=True)
            if buf.tell() <= BLOB_LIMIT:
                return buf.getvalue(), "image/jpeg"
    # Couldn't get under the limit; return the smallest attempt and let the API decide.
    return buf.getvalue(), "image/jpeg"


def upload_blob(svc, jwt, raw, mime):
    r = requests.post(
        f"{svc}/xrpc/com.atproto.repo.uploadBlob",
        data=raw,
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": mime},
        timeout=120,
    )
    data = r.json() if r.content else {}
    if r.status_code != 200 or "blob" not in data:
        die({"error": "uploadBlob_failed", "status": r.status_code, "detail": data})
    return data["blob"]


def read_text(a):
    if a.text_file:
        with open(a.text_file, encoding="utf-8") as f:
            return f.read().rstrip("\n")
    if a.text == "-":
        return sys.stdin.read().rstrip("\n")
    if a.text is not None:
        return a.text
    return ""  # no text source; caller allows this when images are attached


def cmd_post(a):
    svc = env_service()
    text = read_text(a)
    images = a.image or []
    if len(images) > 4:
        die({"error": "too_many_images", "detail": "Bluesky allows at most 4 images per post"})
    if not text and not images:
        die({"error": "empty_post", "detail": "a post needs --text/--text-file or at least one --image"})
    jwt, did, ident = create_session(svc)
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "langs": [a.lang],
    }
    facets = build_facets(text, svc)
    if facets:
        record["facets"] = facets

    if images:
        alts = a.alt or []
        embed_images = []
        for i, src in enumerate(images):
            try:
                raw = fetch_bytes(src)
            except (requests.RequestException, OSError) as e:
                die({"error": "image_fetch_failed", "src": src, "detail": str(e)})
            blob_bytes, mime = compress_to_limit(raw)
            blob = upload_blob(svc, jwt, blob_bytes, mime)
            # Missing alt defaults to empty (never reuse another image's alt).
            alt = alts[i] if i < len(alts) else ""
            embed_images.append({"alt": alt, "image": blob})
        record["embed"] = {"$type": "app.bsky.embed.images", "images": embed_images}

    r = requests.post(
        f"{svc}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
        timeout=60,
    )
    data = r.json() if r.content else {}
    if r.status_code != 200 or "uri" not in data:
        die({"error": "createRecord_failed", "status": r.status_code, "detail": data})
    rkey = data["uri"].rsplit("/", 1)[-1]
    out({
        "posted": True,
        "uri": data["uri"],
        "cid": data.get("cid"),
        "url": f"https://bsky.app/profile/{ident}/post/{rkey}",
        "images": len(images),
        "facets": len(facets),
    })


def cmd_list(a):
    svc = env_service()
    jwt, did, _ = create_session(svc)
    r = requests.get(
        f"{svc}/xrpc/app.bsky.feed.getAuthorFeed",
        params={"actor": did, "limit": a.limit, "filter": a.filter},
        headers={"Authorization": f"Bearer {jwt}"},
        timeout=30,
    )
    data = r.json() if r.content else {}
    if r.status_code != 200:
        die({"error": "getAuthorFeed_failed", "status": r.status_code, "detail": data})
    out([
        {
            "uri": it["post"]["uri"],
            "text": it["post"]["record"].get("text", ""),
            "reposts": it["post"].get("repostCount", 0),
            "likes": it["post"].get("likeCount", 0),
            "replies": it["post"].get("replyCount", 0),
            "at": it["post"].get("indexedAt"),
        }
        for it in data.get("feed", [])
    ])


def cmd_delete(a):
    svc = env_service()
    jwt, did, _ = create_session(svc)
    rkey = a.uri.rsplit("/", 1)[-1]
    r = requests.post(
        f"{svc}/xrpc/com.atproto.repo.deleteRecord",
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        json={"repo": did, "collection": "app.bsky.feed.post", "rkey": rkey},
        timeout=30,
    )
    if r.status_code != 200:
        die({"error": "deleteRecord_failed", "status": r.status_code,
             "detail": r.json() if r.content else {}})
    out({"deleted": True, "rkey": rkey})


def cmd_whoami(a):
    svc = env_service()
    jwt, did, ident = create_session(svc)
    out({"did": did, "handle": ident, "service": svc, "session": bool(jwt)})


def main():
    p = argparse.ArgumentParser(prog="bluesky", description="Bluesky AT Protocol CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("post", help="publish a post (text + optional images + auto facets)")
    pp.add_argument("--text", help='post text (use "-" to read from stdin)')
    pp.add_argument("--text-file", help="read post text from a file (safest for multi-line/emoji)")
    pp.add_argument("--image", action="append", help="image URL or local path (repeatable, max 4)")
    pp.add_argument("--alt", action="append", help="alt text per image (repeatable, paired by order)")
    pp.add_argument("--lang", default="en", help="BCP-47 language tag (default: en)")
    pp.set_defaults(func=cmd_post)

    pl = sub.add_parser("list", help="list my recent posts with engagement")
    pl.add_argument("--limit", type=int, default=20)
    pl.add_argument("--filter", default="posts_no_replies",
                    help="posts_no_replies | posts_with_replies | posts_with_media | posts_and_author_threads")
    pl.set_defaults(func=cmd_list)

    pd = sub.add_parser("delete", help="delete one of my posts by its at:// uri")
    pd.add_argument("--uri", required=True)
    pd.set_defaults(func=cmd_delete)

    pw = sub.add_parser("whoami", help="verify the session and show did/handle")
    pw.set_defaults(func=cmd_whoami)

    a = p.parse_args()
    try:
        a.func(a)
    except SystemExit:
        raise
    except Exception as e:
        die({"error": f"{type(e).__name__}", "detail": str(e)})


if __name__ == "__main__":
    main()
