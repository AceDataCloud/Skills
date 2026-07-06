#!/usr/bin/env python3
"""
x — read & act on X (Twitter) with the user's own login cookies (BYOC).

Drives X's internal web API through `twikit` (https://github.com/d60/twikit),
authenticated by the ``auth_token`` + ``ct0`` cookies the user captured with the
ACE extension. This acts as the user's REAL account, so every state-changing
command (post / thread / reply / quote / like / retweet / follow / delete) is
GATED by a trailing ``--confirm`` — without it, the command dry-runs.

The connector injects the cookie jar as a JSON env var ``X_COOKIES`` (a JSON list
of cookie dicts, each with at least ``name`` and ``value``). It is full account
access — NEVER echo or print it.

twikit is a scraper of X's non-public API: it can drift when X changes its
internal endpoints, and high-frequency use risks rate-limiting or account
suspension under X's ToS. Errors surface as clear messages rather than silent
breakage.

Examples:
  python3 x.py whoami
  python3 x.py search --query "python" --product Latest --limit 20
  python3 x.py timeline --limit 20
  python3 x.py user-tweets --user elonmusk --type Tweets --limit 20
  python3 x.py tweet --id 1234567890
  python3 x.py trends --category trending
  python3 x.py post --text "hello world" --confirm
  python3 x.py post --text "look" --media a.jpg,b.jpg --confirm
  python3 x.py thread --text "1/2 first" --text "2/2 second" --confirm
  python3 x.py like --id 1234567890 --confirm
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from urllib.parse import unquote

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

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


def current_user_id_from_cookies() -> str | None:
    twid = load_cookie_dict().get("twid", "")
    decoded = unquote(twid)
    match = re.search(r"(?:^|[&?])u=(\d+)", decoded) or re.search(r"u=(\d+)", decoded)
    return match.group(1) if match else None


def make_client():
    from twikit import Client
    patch_twikit_transaction_resolver()
    patch_twikit_model_defaults()
    proxy = (
        os.environ.get("X_PROXY")
        or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("ALL_PROXY") or os.environ.get("all_proxy")
        or None
    )
    client = Client("en-US", proxy=proxy, user_agent=UA)
    client.set_cookies(load_cookie_dict())
    return client


def patch_twikit_transaction_resolver() -> None:
    from twikit.x_client_transaction import transaction as tx

    if getattr(tx.ClientTransaction, "_acedata_chunk_patch", False):
        return
    original_get_indices = tx.ClientTransaction.get_indices

    async def get_indices(self, home_page_response, session, headers):
        try:
            return await original_get_indices(self, home_page_response, session, headers)
        except Exception as exc:
            if "KEY_BYTE indices" not in str(exc):
                raise

        response = self.validate_response(home_page_response) or self.home_page_response
        html = str(response)
        chunk_id_match = re.search(r'(\d+):"ondemand\.s"', html)
        if not chunk_id_match:
            raise Exception("Couldn't find ondemand.s chunk id")
        chunk_id = chunk_id_match.group(1)
        hash_match = re.search(rf'{chunk_id}:"([a-f0-9]+)"', html)
        if not hash_match:
            raise Exception("Couldn't find ondemand.s chunk hash")
        url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{hash_match.group(1)}a.js"
        js_response = await session.request(method="GET", url=url, headers=headers)
        indices = [item.group(2) for item in tx.INDICES_REGEX.finditer(str(js_response.text))]
        if not indices:
            raise Exception("Couldn't get KEY_BYTE indices")
        indices = list(map(int, indices))
        return indices[0], indices[1:]

    tx.ClientTransaction.get_indices = get_indices
    tx.ClientTransaction._acedata_chunk_patch = True


def patch_twikit_model_defaults() -> None:
    from twikit.tweet import Tweet
    from twikit.user import User

    if getattr(User, "_acedata_defaults_patch", False):
        return

    user_init = User.__init__
    tweet_init = Tweet.__init__

    def patched_user_init(self, client, data):
        legacy = data.setdefault("legacy", {})
        entities = legacy.setdefault("entities", {})
        entities.setdefault("description", {}).setdefault("urls", [])
        entities.setdefault("url", {}).setdefault("urls", [])
        legacy.setdefault("pinned_tweet_ids_str", [])
        legacy.setdefault("withheld_in_countries", [])
        return user_init(self, client, data)

    def patched_tweet_init(self, client, data, user=None):
        legacy = data.setdefault("legacy", {})
        entities = legacy.setdefault("entities", {})
        entities.setdefault("urls", [])
        entities.setdefault("hashtags", [])
        entities.setdefault("media", [])
        data.setdefault("edit_control", {})
        return tweet_init(self, client, data, user)

    User.__init__ = patched_user_init
    Tweet.__init__ = patched_tweet_init
    User._acedata_defaults_patch = True


# ── formatting ──────────────────────────────────────────────────────

def fmt_user(u) -> dict:
    return {
        "id": str(getattr(u, "id", "")),
        "name": getattr(u, "name", None),
        "screen_name": getattr(u, "screen_name", None),
        "url": f"https://x.com/{getattr(u, 'screen_name', '')}",
        "followers_count": getattr(u, "followers_count", None),
        "following_count": getattr(u, "following_count", None),
        "statuses_count": getattr(u, "statuses_count", None),
        "verified": getattr(u, "verified", None) or getattr(u, "is_blue_verified", None),
        "description": (getattr(u, "description", None) or "")[:200],
    }


def fmt_tweet(t) -> dict:
    author = getattr(t, "user", None)
    sn = getattr(author, "screen_name", None) if author else None
    tid = str(getattr(t, "id", ""))
    return {
        "id": tid,
        "text": (getattr(t, "full_text", None) or getattr(t, "text", None) or "")[:280],
        "author": sn,
        "url": f"https://x.com/{sn}/status/{tid}" if sn and tid else None,
        "created_at": getattr(t, "created_at", None),
        "favorite_count": getattr(t, "favorite_count", None),
        "retweet_count": getattr(t, "retweet_count", None),
        "reply_count": getattr(t, "reply_count", None),
        "quote_count": getattr(t, "quote_count", None),
        "view_count": getattr(t, "view_count", None),
        "lang": getattr(t, "lang", None),
    }


async def resolve_user(client, target: str):
    t = target.lstrip("@").strip()
    if t.isdigit():
        return await client.get_user_by_id(t)
    return await client.get_user_by_screen_name(t)


# ── read commands ───────────────────────────────────────────────────

async def cmd_whoami(client, _args):
    user_id = current_user_id_from_cookies()
    u = await client.get_user_by_id(user_id) if user_id else await client.user()
    out(fmt_user(u))


async def cmd_search(client, args):
    tweets = await client.search_tweet(args.query, args.product, count=args.limit)
    items = list(tweets)[: args.limit]
    out({"query": args.query, "product": args.product,
         "count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_search_users(client, args):
    users = await client.search_user(args.query, count=args.limit)
    items = list(users)[: args.limit]
    out({"query": args.query, "count": len(items),
         "users": [fmt_user(u) for u in items]})


async def cmd_timeline(client, args):
    tweets = await client.get_latest_timeline(count=args.limit)
    items = list(tweets)[: args.limit]
    out({"count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_user_tweets(client, args):
    u = await resolve_user(client, args.user)
    tweets = await client.get_user_tweets(u.id, args.type, count=args.limit)
    items = list(tweets)[: args.limit]
    out({"user": fmt_user(u), "type": args.type,
         "count": len(items), "tweets": [fmt_tweet(t) for t in items]})


async def cmd_tweet(client, args):
    try:
        tweets = await client.get_tweets_by_ids([args.id])
        t = tweets[0] if tweets else None
    except Exception:
        t = None
    if t is None:
        t = await client.get_tweet_by_id(args.id)
    out(fmt_tweet(t))


async def cmd_trends(client, args):
    trends = await client.get_trends(args.category, count=args.limit, retry=False)
    out({"category": args.category,
         "trends": [{"name": getattr(x, "name", None),
                     "tweets_count": getattr(x, "tweets_count", None)}
                    for x in list(trends)[: args.limit]]})


# ── write commands (GATED) ──────────────────────────────────────────

async def _upload_media(client, media_arg: str) -> list:
    media_ids = []
    for path in [p.strip() for p in media_arg.split(",") if p.strip()]:
        if not os.path.isfile(path):
            die(f"media file not found: {path}")
        media_ids.append(await client.upload_media(path, wait_for_completion=True))
    return media_ids


def _quote_note(args) -> dict:
    return {
        "reply_to": getattr(args, "reply_to", None),
        "quote_url": getattr(args, "quote_url", None),
        "media": getattr(args, "media", None),
    }


async def cmd_post(client, args):
    text = (args.text or "").strip()
    if not text and not args.media:
        die("provide --text and/or --media")
    media_ids = await _upload_media(client, args.media) if args.media else None
    tweet = await client.create_tweet(
        text=text, media_ids=media_ids,
        reply_to=args.reply_to, attachment_url=args.quote_url)
    out({"ok": True, "posted": True, **fmt_tweet(tweet)})


async def cmd_thread(client, args):
    texts = [t for t in (args.text or []) if t and t.strip()]
    if len(texts) < 2:
        die("a thread needs at least two --text segments")
    media_ids = await _upload_media(client, args.media) if args.media else None
    posted, reply_to = [], None
    for i, text in enumerate(texts):
        tweet = await client.create_tweet(
            text=text.strip(),
            media_ids=media_ids if i == 0 else None,
            reply_to=reply_to)
        reply_to = tweet.id
        posted.append(fmt_tweet(tweet))
    out({"ok": True, "posted": True, "count": len(posted), "tweets": posted})


async def cmd_like(client, args):
    await client.favorite_tweet(args.id)
    out({"ok": True, "liked": True, "tweet_id": args.id})


async def cmd_unlike(client, args):
    await client.unfavorite_tweet(args.id)
    out({"ok": True, "unliked": True, "tweet_id": args.id})


async def cmd_retweet(client, args):
    await client.retweet(args.id)
    out({"ok": True, "retweeted": True, "tweet_id": args.id})


async def cmd_unretweet(client, args):
    await client.delete_retweet(args.id)
    out({"ok": True, "unretweeted": True, "tweet_id": args.id})


async def cmd_follow(client, args):
    u = await resolve_user(client, args.user)
    await client.follow_user(u.id)
    out({"ok": True, "followed": True, "user": u.screen_name, "user_id": str(u.id)})


async def cmd_unfollow(client, args):
    u = await resolve_user(client, args.user)
    await client.unfollow_user(u.id)
    out({"ok": True, "unfollowed": True, "user": u.screen_name, "user_id": str(u.id)})


async def cmd_delete(client, args):
    await client.delete_tweet(args.id)
    out({"ok": True, "deleted": True, "tweet_id": args.id})


def gated_dry_run(args) -> None:
    """Print what a state-changing command WOULD do, without any network call."""
    cmd = args.command
    fields: dict = {}
    if cmd == "post":
        fields = {"text_preview": (args.text or "")[:280], **_quote_note(args)}
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
    "whoami": cmd_whoami,
    "search": cmd_search,
    "search-users": cmd_search_users,
    "timeline": cmd_timeline,
    "user-tweets": cmd_user_tweets,
    "tweet": cmd_tweet,
    "trends": cmd_trends,
    "post": cmd_post,
    "thread": cmd_thread,
    "like": cmd_like,
    "unlike": cmd_unlike,
    "retweet": cmd_retweet,
    "unretweet": cmd_unretweet,
    "follow": cmd_follow,
    "unfollow": cmd_unfollow,
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
    sp.add_argument("--type", choices=["Tweets", "Replies", "Media", "Likes"],
                    default="Tweets")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("tweet", help="single tweet detail")
    sp.add_argument("--id", required=True)

    sp = sub.add_parser("trends", help="trending topics")
    sp.add_argument("--category",
                    choices=["trending", "for-you", "news", "sports", "entertainment"],
                    default="trending")
    sp.add_argument("--limit", type=int, default=20)

    sp = sub.add_parser("post", help="publish a tweet (GATED by trailing --confirm)")
    sp.add_argument("--text", default="")
    sp.add_argument("--media", help="comma-separated image/video file paths")
    sp.add_argument("--reply-to", dest="reply_to", help="tweet id to reply to")
    sp.add_argument("--quote-url", dest="quote_url", help="tweet URL to quote")

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
    client = make_client()
    await COMMANDS[args.command](client, args)


def main() -> None:
    args = build_parser().parse_args(ARGV)
    # Gated commands dry-run offline (no cookies, no network) unless --confirm.
    if args.command in GATED and not CONFIRM:
        gated_dry_run(args)
        return
    try:
        from twikit.errors import (
            Unauthorized, Forbidden, TooManyRequests, NotFound,
            TweetNotAvailable, UserNotFound, UserUnavailable,
            AccountLocked, AccountSuspended, TwitterException,
        )
    except Exception as e:  # twikit not importable
        die(
            f"twikit is not available in the sandbox image: {e}. "
            "Deploy the sandbox skill dependencies image; do not pip-install it at runtime."
        )
    try:
        asyncio.run(run(args))
    except (Unauthorized,) as e:
        die(f"auth failed — cookie likely expired. Reconnect X at "
            f"https://auth.acedata.cloud/user/connections. ({e})")
    except (AccountLocked, AccountSuspended) as e:
        die(f"account locked/suspended by X: {e}")
    except TooManyRequests as e:
        die(f"rate limited by X — wait and retry, or slow down. ({e})")
    except (NotFound, TweetNotAvailable, UserNotFound, UserUnavailable) as e:
        die(f"not found / unavailable: {e}")
    except Forbidden as e:
        die(f"forbidden by X (content rule, protected account, or ToS): {e}")
    except TwitterException as e:
        die(f"X API error: {e}")
    except Exception as e:
        # twikit scrapes X's non-public API; a bare error here usually means an
        # expired cookie OR that X changed its internal endpoints and twikit
        # needs a compatibility fix.
        if "Couldn't get KEY_BYTE indices" in str(e):
            die(
                "X request failed because twikit cannot derive X's current "
                "transaction-id keys (`Couldn't get KEY_BYTE indices`). This is "
                "upstream drift in X's internal web API, not a missing/expired "
                "cookie. Retry after twikit/X compatibility is fixed."
            )
        die(f"X request failed ({type(e).__name__}: {e}). Likely an expired "
            f"cookie — reconnect at https://auth.acedata.cloud/user/connections "
            f"— or twikit drift vs X's internal API.")


if __name__ == "__main__":
    main()
