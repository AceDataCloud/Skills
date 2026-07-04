#!/usr/bin/env python3
"""
x — read & act on X (Twitter) with the user's own login cookies (BYOC).

Drives X's internal web API through `tweety-ns`
(https://github.com/mahrtayyab/tweety), authenticated by the ``auth_token`` +
``ct0`` cookies the user captured with the ACE extension. This acts as the
user's REAL account, so every state-changing command (post / thread / reply /
quote / like / retweet / follow / delete) is GATED by a trailing ``--confirm``
— without it, the command dry-runs.

The connector injects the cookie jar as a JSON env var ``X_COOKIES`` (a JSON
list of cookie dicts, each with at least ``name`` and ``value``). It is full
account access — NEVER echo or print it.

tweety-ns scrapes X's non-public frontend API: it can drift when X changes its
internal endpoints (though it is actively maintained), and high-frequency use
risks rate-limiting or account suspension under X's ToS. Errors surface as
clear JSON messages rather than silent breakage.

Examples:
  python3 x.py whoami
  python3 x.py search --query "python" --product Latest --limit 20
  python3 x.py search-users --query "openai" --limit 10
  python3 x.py timeline --limit 20
  python3 x.py user-tweets --user elonmusk --type Tweets --limit 20
  python3 x.py tweet --id 1234567890
  python3 x.py trends --limit 20
  python3 x.py post --text "hello world" --confirm
  python3 x.py post --text "look" --media a.jpg,b.jpg --confirm
  python3 x.py thread --text "1/2 first" --text "2/2 second" --confirm
  python3 x.py like --id 1234567890 --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import shutil
import sys
import tempfile

_RAW = sys.argv[1:]
# --confirm is honored ONLY as the last token, and only one is stripped, so a
# tweet body that merely contains "--confirm" can never silently confirm a write.
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)

# State-changing commands — dry-run unless the invocation ends with --confirm.
GATED = {
    "post", "thread", "like", "unlike", "retweet", "unretweet",
    "follow", "unfollow", "delete",
}

_PAGE = 20  # X returns roughly this many items per page; used to size fetches.


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


def load_cookie_dict() -> dict:
    raw = os.environ.get("X_COOKIES")
    if not raw:
        die("X_COOKIES is not set — connect X (Twitter) at "
            "https://auth.acedata.cloud/user/connections, then retry.")
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"X_COOKIES is not valid JSON: {e}")
    if not isinstance(jar, list):
        die(f"X_COOKIES must be a JSON list of cookies, got {type(jar).__name__}")
    cookies = {}
    for c in jar:
        name, value = c.get("name"), c.get("value")
        if name and value is not None:
            cookies[name] = value
    if "auth_token" not in cookies or "ct0" not in cookies:
        die("X_COOKIES is missing auth_token / ct0 — re-capture the cookie on "
            "x.com with the ACE extension, then reconnect at "
            "https://auth.acedata.cloud/user/connections.")
    return cookies


def _proxy() -> str | None:
    return (
        os.environ.get("X_PROXY")
        or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("ALL_PROXY") or os.environ.get("all_proxy")
        or None
    )


def _pages_for(limit: int) -> int:
    # Fetch enough pages to satisfy --limit, capped so a huge limit can't loop
    # X forever. Results are sliced to exactly `limit` afterwards.
    return max(1, min(10, math.ceil(limit / _PAGE)))


# ── formatting ──────────────────────────────────────────────────────

def fmt_user(u) -> dict:
    sn = getattr(u, "username", None) or getattr(u, "screen_name", None)
    return {
        "id": str(getattr(u, "id", None) or getattr(u, "rest_id", "")),
        "name": getattr(u, "name", None),
        "screen_name": sn,
        "url": f"https://x.com/{sn}" if sn else None,
        "followers_count": getattr(u, "followers_count", None),
        "following_count": getattr(u, "friends_count", None),
        "statuses_count": getattr(u, "statuses_count", None),
        "verified": getattr(u, "verified", None),
        "description": (getattr(u, "description", None) or getattr(u, "bio", None) or "")[:200],
    }


def fmt_tweet(t) -> dict:
    author = getattr(t, "author", None)
    sn = (getattr(author, "username", None) or getattr(author, "screen_name", None)) if author else None
    tid = str(getattr(t, "id", ""))
    return {
        "id": tid,
        "text": getattr(t, "text", None) or getattr(t, "tweet_body", None) or "",
        "author": sn,
        "url": getattr(t, "url", None) or (f"https://x.com/{sn}/status/{tid}" if sn and tid else None),
        "created_at": getattr(t, "created_on", None) or getattr(t, "date", None),
        "likes": getattr(t, "likes", None),
        "retweet_count": getattr(t, "retweet_counts", None),
        "reply_count": getattr(t, "reply_counts", None),
        "quote_count": getattr(t, "quote_counts", None),
        "views": getattr(t, "views", None),
        "language": getattr(t, "language", None),
    }


def _limited(iterable, limit: int) -> list:
    items = []
    for it in iterable:
        items.append(it)
        if len(items) >= limit:
            break
    return items


def _quote_id(value: str | None) -> str | None:
    # Accept a tweet id or a full status URL; tweety wants the id. Take ONLY the
    # leading path segment after /status/ (before any ?query, /photo, #frag) so
    # tracking params like ?s=20&t=ab don't get merged into the id.
    if not value:
        return None
    value = value.strip()
    if "/status/" in value:
        seg = value.split("/status/", 1)[1].split("?", 1)[0].split("/", 1)[0].split("#", 1)[0]
        return seg if seg.isdigit() else value
    return value


# ── read commands ───────────────────────────────────────────────────

async def cmd_whoami(app, _args):
    out(fmt_user(app.me))


async def cmd_search(app, args):
    from tweety.filters import SearchFilters
    product = {"Top": None, "Latest": SearchFilters.Latest, "Media": SearchFilters.Media}[args.product]
    results = await app.search(args.query, pages=_pages_for(args.limit), filter_=product)
    items = _limited(results, args.limit)
    out({"query": args.query, "product": args.product,
         "count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_search_users(app, args):
    from tweety.filters import SearchFilters
    results = await app.search(args.query, pages=_pages_for(args.limit), filter_=SearchFilters.Users)
    items = _limited(results, args.limit)
    out({"query": args.query, "count": len(items), "users": [fmt_user(u) for u in items]})


async def cmd_timeline(app, args):
    results = await app.get_home_timeline("HomeLatestTimeline", pages=_pages_for(args.limit))
    items = _limited(results, args.limit)
    out({"count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_user_tweets(app, args):
    user = args.user.lstrip("@")
    if args.type == "Media":
        results = await app.get_user_media(user, pages=_pages_for(args.limit))
    else:
        results = await app.get_tweets(user, pages=_pages_for(args.limit),
                                       replies=(args.type == "Replies"))
    items = _limited(results, args.limit)
    out({"user": user, "type": args.type,
         "count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_tweet(app, args):
    out(fmt_tweet(await app.tweet_detail(args.id)))


async def cmd_trends(app, args):
    trends = await app.get_trends()
    items = list(trends)[: args.limit]
    out({"trends": [{"name": getattr(x, "name", None),
                     "tweet_count": getattr(x, "tweet_count", None),
                     "url": getattr(x, "url", None)} for x in items]})


# ── write commands (GATED — reached only when CONFIRM) ──────────────

def _media_files(media_arg: str | None) -> list | None:
    if not media_arg:
        return None
    files = []
    for path in [p.strip() for p in media_arg.split(",") if p.strip()]:
        if not os.path.isfile(path):
            die(f"media file not found: {path}")
        files.append(path)
    return files or None


async def cmd_post(app, args):
    text = (args.text or "").strip()
    if not text and not args.media:
        die("provide --text and/or --media")
    tweet = await app.create_tweet(
        text=text, files=_media_files(args.media),
        reply_to=args.reply_to, quote=_quote_id(args.quote))
    out({"ok": True, "posted": True, **fmt_tweet(tweet)})


async def cmd_thread(app, args):
    texts = [t for t in (args.text or []) if t and t.strip()]
    if len(texts) < 2:
        die("a thread needs at least two --text segments")
    files = _media_files(args.media)
    posted, reply_to = [], None
    for i, text in enumerate(texts):
        tweet = await app.create_tweet(
            text=text.strip(),
            files=files if i == 0 else None,
            reply_to=reply_to)
        reply_to = tweet.id
        posted.append(fmt_tweet(tweet))
    out({"ok": True, "posted": True, "count": len(posted), "tweets": posted})


async def cmd_like(app, args):
    await app.like_tweet(args.id)
    out({"ok": True, "liked": True, "tweet_id": args.id})


async def cmd_unlike(app, args):
    await app.unlike_tweet(args.id)
    out({"ok": True, "unliked": True, "tweet_id": args.id})


async def cmd_retweet(app, args):
    await app.retweet_tweet(args.id)
    out({"ok": True, "retweeted": True, "tweet_id": args.id})


async def cmd_unretweet(app, args):
    await app.delete_retweet(args.id)
    out({"ok": True, "unretweeted": True, "tweet_id": args.id})


async def cmd_follow(app, args):
    u = await app.get_user_info(args.user.lstrip("@"))
    await app.follow_user(u.id)
    out({"ok": True, "followed": True, "user": getattr(u, "username", None), "user_id": str(u.id)})


async def cmd_unfollow(app, args):
    u = await app.get_user_info(args.user.lstrip("@"))
    await app.unfollow_user(u.id)
    out({"ok": True, "unfollowed": True, "user": getattr(u, "username", None), "user_id": str(u.id)})


async def cmd_delete(app, args):
    await app.delete_tweet(args.id)
    out({"ok": True, "deleted": True, "tweet_id": args.id})


def gated_dry_run(args) -> None:
    """Print what a state-changing command WOULD do, without any network call."""
    cmd = args.command
    if cmd == "post":
        fields = {"text_preview": (args.text or "")[:280], "media": args.media,
                  "reply_to": args.reply_to, "quote": args.quote}
    elif cmd == "thread":
        texts = [t for t in (args.text or []) if t and t.strip()]
        fields = {"segments": len(texts), "preview": [t[:120] for t in texts],
                  "media_on_first": args.media}
    elif cmd in ("follow", "unfollow"):
        fields = {"user": args.user}
    else:  # like / unlike / retweet / unretweet / delete
        fields = {"tweet_id": args.id}
    out({"dry_run": True, "command": cmd, **fields,
         "note": "Re-run with --confirm as the LAST argument to actually run "
                 "this. It acts on the user's REAL X account."})


COMMANDS = {
    "whoami": cmd_whoami, "search": cmd_search, "search-users": cmd_search_users,
    "timeline": cmd_timeline, "user-tweets": cmd_user_tweets, "tweet": cmd_tweet,
    "trends": cmd_trends, "post": cmd_post, "thread": cmd_thread,
    "like": cmd_like, "unlike": cmd_unlike, "retweet": cmd_retweet,
    "unretweet": cmd_unretweet, "follow": cmd_follow, "unfollow": cmd_unfollow,
    "delete": cmd_delete,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="x.py", description="X (Twitter) cookie CLI")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="show the logged-in account")

    sp = sub.add_parser("search", help="search tweets by keyword")
    sp.add_argument("--query", required=True)
    sp.add_argument("--product", choices=["Top", "Latest", "Media"], default="Latest")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("search-users", help="search users by keyword")
    sp.add_argument("--query", required=True)
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("timeline", help="my home timeline (latest)")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("user-tweets", help="a user's tweets")
    sp.add_argument("--user", required=True, help="@screen_name or numeric id")
    sp.add_argument("--type", choices=["Tweets", "Replies", "Media"], default="Tweets")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("tweet", help="single tweet detail")
    sp.add_argument("--id", required=True, help="tweet id or URL")

    sp = sub.add_parser("trends", help="local trending topics")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("post", help="publish a tweet (GATED by trailing --confirm)")
    sp.add_argument("--text", default="")
    sp.add_argument("--media", help="comma-separated image/video file paths")
    sp.add_argument("--reply-to", dest="reply_to", help="tweet id to reply to")
    sp.add_argument("--quote", help="tweet id or URL to quote")

    sp = sub.add_parser("thread", help="publish a thread (GATED by trailing --confirm)")
    sp.add_argument("--text", action="append", help="one per tweet; repeat 2+ times")
    sp.add_argument("--media", help="comma-separated paths, attached to the FIRST tweet")

    for name in ("like", "unlike", "retweet", "unretweet", "delete"):
        sp = sub.add_parser(name, help=f"{name} a tweet (GATED by trailing --confirm)")
        sp.add_argument("--id", required=True)

    for name in ("follow", "unfollow"):
        sp = sub.add_parser(name, help=f"{name} a user (GATED by trailing --confirm)")
        sp.add_argument("--user", required=True, help="@screen_name or numeric id")

    return p


async def run(args) -> None:
    from tweety import TwitterAsync
    # Session file holds the auth cookie; keep it in an ephemeral temp dir and
    # delete it (never CWD) so the credential is not left on disk.
    tmp = tempfile.mkdtemp(prefix="x-sess-")
    try:
        app = TwitterAsync(os.path.join(tmp, "x"), proxy=_proxy())
        await app.load_cookies(load_cookie_dict())
        await COMMANDS[args.command](app, args)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    args = build_parser().parse_args(ARGV)
    # Gated commands dry-run offline (no cookies, no network) unless --confirm.
    if args.command in GATED and not CONFIRM:
        gated_dry_run(args)
        return
    try:
        from tweety.exceptions_ import (
            AuthenticationRequired, InvalidCredentials, DeniedLogin,
            LockedAccount, SuspendedAccount, RateLimitReached,
            ProtectedTweet, UserNotFound, UserProtected,
            InvalidTweetIdentifier, TwitterError,
        )
    except Exception as e:  # tweety not importable
        die(f"tweety-ns is not available: {e}. Install with "
            f"`pip install --user tweety-ns`.")
    try:
        asyncio.run(run(args))
    except (AuthenticationRequired, InvalidCredentials, DeniedLogin) as e:
        die(f"auth failed — cookie likely expired. Reconnect X at "
            f"https://auth.acedata.cloud/user/connections. ({e})")
    except (LockedAccount, SuspendedAccount) as e:
        die(f"account locked/suspended by X: {e}")
    except RateLimitReached as e:
        die(f"rate limited by X — wait and retry, or slow down. ({e})")
    except (UserNotFound, UserProtected, ProtectedTweet, InvalidTweetIdentifier) as e:
        die(f"not found / unavailable: {e}")
    except TwitterError as e:
        die(f"X API error: {e}")
    except Exception as e:
        # tweety-ns scrapes X's non-public API; a bare error here usually means
        # an expired cookie OR that X changed its internal endpoints and tweety
        # needs upgrading (`pip install --user -U tweety-ns`).
        die(f"X request failed ({type(e).__name__}: {e}). Likely an expired "
            f"cookie — reconnect at https://auth.acedata.cloud/user/connections "
            f"— or tweety-ns drift vs X's internal API (try `pip install "
            f"--user -U tweety-ns`).")


if __name__ == "__main__":
    main()
