#!/usr/bin/env python3
"""Read and submit Reddit posts with OAuth or the user's login cookies.

Cookie mode uses Reddit's first-party web JSON endpoints and the ``modhash``
returned by ``/api/me.json``. OAuth mode uses ``oauth.reddit.com``. The helper
automatically selects ``REDDIT_TOKEN`` first, then ``REDDIT_COOKIES``.

State-changing commands are dry-runs unless ``--confirm`` is the final argv
token. Credentials, cookie values and modhashes are never emitted.
"""

from __future__ import annotations

import argparse
import contextlib
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WEB_BASE = "https://www.reddit.com"
OAUTH_BASE = "https://oauth.reddit.com"
USER_AGENT = "web:cloud.acedata.reddit:v2.0 (by /u/acedatacloud)"
GATED_COMMANDS = {"submit-text", "submit-link", "comment"}
SUBREDDIT_RE = re.compile(r"^[A-Za-z0-9_]{2,21}$")
COOKIE_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
# Only a comment (t1_) or a post (t3_) can be replied to.
THING_ID_RE = re.compile(r"^t[13]_[A-Za-z0-9]{2,16}$")
VERIFY_ATTEMPTS = 2
VERIFY_RETRY_SECONDS = 3
VERIFY_CLOCK_SKEW_SECONDS = 15


def output(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def die(message: str, code: int = 1) -> None:
    output({"error": message})
    raise SystemExit(code)


def split_confirmation(argv: list[str]) -> tuple[list[str], bool]:
    confirmed = bool(argv) and argv[-1] == "--confirm"
    return (argv[:-1] if confirmed else list(argv), confirmed)


def parse_cookie_jar(raw: str) -> list[dict]:
    try:
        jar = json.loads(raw)
    except json.JSONDecodeError as error:
        die(f"REDDIT_COOKIES is not valid JSON: {error}")
    if not isinstance(jar, list):
        die(f"REDDIT_COOKIES must be a JSON list of cookies, got {type(jar).__name__}")
    normalized = []
    for item in jar:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if not isinstance(name, str) or not COOKIE_NAME_RE.fullmatch(name) or not isinstance(value, str):
            continue
        if any(character == ";" or ord(character) < 0x20 or ord(character) == 0x7F for character in value):
            continue
        domain = item.get("domain")
        if not isinstance(domain, str) or not reddit_cookie_domain(domain):
            continue
        path = str(item.get("path") or "/")
        if not path.startswith("/"):
            continue
        expiration = item.get("expirationDate")
        if expiration not in (None, ""):
            try:
                if float(expiration) <= time.time():
                    continue
            except (TypeError, ValueError):
                continue
        normalized.append(
            dict(
                item,
                name=name,
                value=value,
                domain=domain,
                path=path,
                secure=bool(item.get("secure")),
            )
        )
    if not any(
        cookie.get("name") == "reddit_session"
        and cookie.get("value")
        and cookie_applies(cookie, WEB_BASE + "/api/me.json")
        for cookie in normalized
    ):
        die(
            "REDDIT_COOKIES is missing a valid reddit_session — log in on reddit.com, "
            "re-capture with the ACE extension, then reconnect at "
            "https://studio.acedata.cloud/console/connectors."
        )
    return normalized


def reddit_cookie_domain(domain: str) -> bool:
    normalized_domain = domain.strip().lstrip(".").lower()
    return normalized_domain == "reddit.com" or normalized_domain.endswith(".reddit.com")


def domain_matches(host: str, domain: str) -> bool:
    raw_domain = domain.strip().lower()
    normalized_domain = raw_domain.lstrip(".")
    normalized_host = host.lower()
    if not normalized_domain:
        return False
    if raw_domain.startswith("."):
        return normalized_host == normalized_domain or normalized_host.endswith("." + normalized_domain)
    return normalized_host == normalized_domain


def cookie_domain_matches(cookie: dict, host: str) -> bool:
    domain = str(cookie.get("domain") or "")
    if cookie.get("hostOnly") is True:
        return host.lower() == domain.lstrip(".").lower()
    if cookie.get("hostOnly") is False:
        normalized = domain.lstrip(".")
        return bool(normalized) and (
            host.lower() == normalized.lower() or host.lower().endswith("." + normalized.lower())
        )
    return domain_matches(host, domain)


def path_matches(request_path: str, cookie_path: str) -> bool:
    if request_path == cookie_path:
        return True
    if not request_path.startswith(cookie_path):
        return False
    return cookie_path.endswith("/") or request_path[len(cookie_path) :].startswith("/")


def cookie_applies(cookie: dict, url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    domain = str(cookie.get("domain") or "")
    path = str(cookie.get("path") or "/")
    if not reddit_cookie_domain(domain) or not cookie_domain_matches(cookie, host):
        return False
    if not path.startswith("/") or not path_matches(parsed.path or "/", path):
        return False
    if cookie.get("secure") and parsed.scheme != "https":
        return False
    expiration = cookie.get("expirationDate")
    if expiration not in (None, ""):
        try:
            if float(expiration) <= time.time():
                return False
        except (TypeError, ValueError):
            return False
    return True


def cookie_header(jar: list[dict], url: str) -> str:
    host = urllib.parse.urlsplit(url).hostname or ""
    if not reddit_cookie_domain(host):
        return ""
    applicable = [
        (index, cookie)
        for index, cookie in enumerate(jar)
        if cookie_applies(cookie, url)
    ]
    applicable.sort(key=lambda item: (-len(str(item[1].get("path") or "/")), item[0]))
    parts = []
    seen = set()
    for _, cookie in applicable:
        identity = (
            cookie.get("name"),
            cookie.get("domain"),
            cookie.get("path") or "/",
        )
        if identity in seen:
            continue
        seen.add(identity)
        parts.append(f"{cookie['name']}={cookie['value']}")
    return "; ".join(parts)


def normalize_subreddit(value: str) -> str:
    subreddit = value.strip().strip("/")
    if subreddit.lower().startswith("r/"):
        subreddit = subreddit[2:]
    if not SUBREDDIT_RE.fullmatch(subreddit):
        die("subreddit must contain only letters, numbers or underscores (2-21 characters)")
    return subreddit


def validate_title(value: str) -> str:
    title = value.strip()
    if not title:
        die("title cannot be empty")
    if len(title) > 300:
        die("title exceeds Reddit's 300-character limit")
    return title


def validate_link(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        die("url must be an http(s) URL without embedded credentials")
    return value.strip()


def normalize_thing_id(value: str) -> str:
    """Accept a fullname (t3_abc123) or a reddit permalink and return a fullname."""
    candidate = value.strip()
    if THING_ID_RE.fullmatch(candidate):
        return candidate
    parsed = urllib.parse.urlsplit(candidate)
    if parsed.scheme in {"http", "https"}:
        if not parsed.hostname or not reddit_cookie_domain(parsed.hostname):
            die("parent URL must point at reddit.com")
        # /r/<sub>/comments/<post_id>/<slug>/<comment_id>
        segments = [segment for segment in (parsed.path or "").split("/") if segment]
        if "comments" in segments:
            index = segments.index("comments")
            if len(segments) > index + 3 and re.fullmatch(r"[A-Za-z0-9]{2,16}", segments[index + 3]):
                return "t1_" + segments[index + 3]
            if len(segments) > index + 1 and re.fullmatch(r"[A-Za-z0-9]{2,16}", segments[index + 1]):
                return "t3_" + segments[index + 1]
    die("parent must be a post (t3_xxxxxx), a comment (t1_xxxxxx) or a reddit.com permalink")


def validate_comment_body(text: str) -> str:
    body = text.strip()
    if not body:
        die("comment body cannot be empty")
    if len(body) > 10_000:
        die("comment exceeds Reddit's 10,000-character limit")
    return body


def validate_query(value: str) -> str:
    query = value.strip()
    if not query:
        die("query cannot be empty")
    if len(query) > 512:
        die("query exceeds Reddit's 512-character search limit")
    return query


def read_text(args: argparse.Namespace) -> str:
    if args.text_file:
        try:
            with open(args.text_file, encoding="utf-8") as file_handle:
                text = file_handle.read()
        except OSError as error:
            die(f"cannot read text file {args.text_file}: {error}")
    else:
        text = args.text or ""
    if len(text) > 40_000:
        die("text exceeds Reddit's 40,000-character limit")
    return text


def read_body(args: argparse.Namespace) -> str:
    """Read a comment body from --body or --body-file."""
    if getattr(args, "body_file", None):
        try:
            with open(args.body_file, encoding="utf-8") as file_handle:
                text = file_handle.read()
        except OSError as error:
            die(f"cannot read body file {args.body_file}: {error}")
    else:
        text = args.body or ""
    return validate_comment_body(text)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Return 30x responses to the caller instead of replaying credentials."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def open_request(request: urllib.request.Request):
    return urllib.request.build_opener(NoRedirect()).open(request, timeout=30)


class RedditClient:
    def __init__(self, mode: str, *, cookies: list[dict] | None = None, token: str = ""):
        self.mode = mode
        self.cookies = cookies or []
        self.token = token
        self.modhash = ""
        self.username = ""

    @classmethod
    def from_environment(cls) -> "RedditClient":
        token = os.environ.get("REDDIT_TOKEN", "").strip()
        if token:
            if "\r" in token or "\n" in token:
                die("REDDIT_TOKEN contains invalid characters")
            return cls("oauth", token=token)
        raw_cookies = os.environ.get("REDDIT_COOKIES", "").strip()
        if raw_cookies:
            return cls("cookie", cookies=parse_cookie_jar(raw_cookies))
        die(
            "No Reddit credential is available — connect Reddit with Cookie or OAuth at "
            "https://studio.acedata.cloud/console/connectors."
        )

    @property
    def base_url(self) -> str:
        return WEB_BASE if self.mode == "cookie" else OAUTH_BASE

    def request(self, method: str, path: str, *, query: dict | None = None, form: dict | None = None, write_kind: str = "post"):
        is_write = method.upper() == "POST"
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        if self.mode == "oauth":
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            headers.update({"Origin": WEB_BASE, "Referer": WEB_BASE + "/", "X-Requested-With": "XMLHttpRequest"})

        data = None
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        if self.mode == "cookie":
            request.add_unredirected_header("Cookie", cookie_header(self.cookies, url))

        try:
            with open_request(request) as response:
                status = response.status
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
        except urllib.error.HTTPError as error:
            try:
                status = error.code
                raw = error.read()
                if error.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            except Exception:
                if is_write:
                    die_unknown_write_outcome("The Reddit HTTP error response for the write request could not be read", kind=write_kind)
                die("The Reddit HTTP error response could not be read; authenticated response content was omitted.")
            finally:
                with contextlib.suppress(Exception):
                    error.close()
        except urllib.error.URLError as error:
            if is_write:
                die_unknown_write_outcome("A network error interrupted the Reddit write request", kind=write_kind)
            die(f"network error reaching Reddit: {error.reason}")
        except Exception:
            if is_write:
                die_unknown_write_outcome("The Reddit write response could not be read or decompressed", kind=write_kind)
            die("The Reddit response could not be read or decompressed; authenticated response content was omitted.")

        text = raw.decode("utf-8", "replace")
        if 300 <= status < 400:
            if is_write:
                die_unknown_write_outcome("Reddit redirected the write request; credentials were not forwarded", kind=write_kind)
            die("Reddit returned an unexpected redirect; credentials were not forwarded. Reconnect before retrying the read.")
        if status in {401, 403}:
            die(
                f"Reddit authentication failed ({status}) — the credential may be expired or blocked. "
                "Reconnect at https://studio.acedata.cloud/console/connectors."
            )
        if status == 429:
            die("Reddit rate limit reached (429). Wait before retrying; do not loop-retry.")
        if status >= 400:
            if is_write and status >= 500:
                die_unknown_write_outcome(f"Reddit returned HTTP {status} for the write request", kind=write_kind)
            die(f"Reddit returned HTTP {status}; authenticated response content was omitted.")
        if text.lstrip().startswith("<"):
            if is_write:
                die_unknown_write_outcome("Reddit returned HTML for the write request", kind=write_kind)
            die("Reddit returned HTML instead of JSON — the session expired or the web endpoint changed.")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if is_write:
                die_unknown_write_outcome("Reddit returned invalid JSON for the write request", kind=write_kind)
            die(f"Reddit returned non-JSON data ({status}); authenticated response content was omitted.")

    def me(self) -> dict:
        if self.mode == "cookie":
            payload = self.request("GET", "/api/me.json", query={"raw_json": 1})
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
                die("Reddit returned a malformed identity response; authenticated response content was omitted.")
            data = payload["data"]
            self.modhash = str(data.get("modhash") or "")
        else:
            data = self.request("GET", "/api/v1/me")
            if not isinstance(data, dict):
                die("Reddit returned a malformed identity response; authenticated response content was omitted.")
        self.username = str(data.get("name") or "")
        if not self.username:
            die("Reddit did not return an authenticated username — reconnect the account.")
        return data

    def submissions(self, limit: int) -> list[dict]:
        username = self.username or str(self.me().get("name") or "")
        suffix = ".json" if self.mode == "cookie" else ""
        payload = self.request(
            "GET",
            f"/user/{urllib.parse.quote(username, safe='')}/submitted{suffix}",
            query={"limit": limit, "raw_json": 1},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            die("Reddit returned a malformed submissions response; authenticated response content was omitted.")
        children = payload["data"].get("children")
        if not isinstance(children, list) or any(
            not isinstance(child, dict)
            or not valid_submission_data(child.get("data"))
            for child in children
        ):
            die("Reddit returned a malformed submissions response; authenticated response content was omitted.")
        return [child["data"] for child in children]

    def submit(self, *, subreddit: str, title: str, kind: str, text: str = "", url: str = "") -> dict:
        if self.mode == "cookie" and not self.modhash:
            self.me()
        form = {
            "api_type": "json",
            "kind": kind,
            "sr": subreddit,
            "title": title,
            "resubmit": "true",
            "sendreplies": "true",
            "raw_json": "1",
        }
        if kind == "self":
            form["text"] = text
        else:
            form["url"] = url
        if self.mode == "cookie":
            if not self.modhash:
                die("Reddit did not return a modhash; the Cookie session cannot perform writes.")
            form["uh"] = self.modhash

        payload = self.request("POST", "/api/submit", form=form)
        if not isinstance(payload, dict) or not isinstance(payload.get("json"), dict):
            die_unknown_post_response()
        json_payload = payload["json"]
        errors = json_payload.get("errors")
        if not isinstance(errors, list):
            die_unknown_post_response()
        if errors:
            die(
                "Reddit rejected the post. Check subreddit rules, account eligibility, "
                "flair requirements and rate limits; authenticated error details were omitted."
            )
        post = json_payload.get("data")
        if not isinstance(post, dict):
            die_unknown_post_response()
        post_url = post.get("url") or post.get("permalink")
        if not isinstance(post_url, str) or not post_url:
            die_unknown_post_response()
        if post_url.startswith("/"):
            post_url = WEB_BASE + post_url
        parsed_post_url = urllib.parse.urlsplit(post_url)
        if parsed_post_url.scheme != "https" or not parsed_post_url.hostname or not reddit_cookie_domain(
            parsed_post_url.hostname
        ):
            die_unknown_post_response()
        return {"ok": True, "posted": True, "id": post.get("id"), "name": post.get("name"), "url": post_url}


    def verify_recent_comment(
        self, parent: str, body: str, written_at: float, seen_ids: set | None = None
    ) -> dict:
        """Resolve an unparsable write by finding the comment we just posted.

        Matching on body alone would let a stale duplicate vouch for a rejected
        write, so the hit must also belong to this thread and be newly created.
        """
        wanted = body.strip()
        recent = []
        for attempt in range(VERIFY_ATTEMPTS):
            if attempt:
                # The user-comments listing is a read replica and lags a write.
                time.sleep(VERIFY_RETRY_SECONDS)
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    recent = self.comments(25)
            except SystemExit:
                recent = []
            match = self.match_written_comment(recent, parent, wanted, written_at, seen_ids)
            if match:
                formatted = format_comment(match)
                return {
                    "ok": True,
                    "commented": True,
                    "id": formatted["id"],
                    "name": None,
                    "url": formatted["url"],
                    "note": "Reddit returned an unrecognized response; the comment was confirmed via `comments`.",
                }
        die(
            "Reddit returned an unrecognized comment response and the comment could not be "
            "confirmed in this account's recent comments. It may have been rejected, or the "
            "listing may still be catching up. Re-check with `comments` before resending; "
            "do not replay automatically."
        )

    @staticmethod
    def match_written_comment(
        recent: list, parent: str, wanted: str, written_at: float, seen_ids: set | None = None
    ) -> dict | None:
        """Find the comment this write created — never merely a lookalike.

        Body alone is not proof: the same text can already exist on the same
        thread, so an id present before the write can never vouch for it.
        """
        thread = parent[3:] if parent.startswith("t3_") else ""
        for item in recent:
            if str(item.get("body") or "").strip() != wanted:
                continue
            if seen_ids is not None and str(item.get("id") or "") in seen_ids:
                continue
            created = item.get("created_utc")
            if not isinstance(created, (int, float)) or created < written_at - VERIFY_CLOCK_SKEW_SECONDS:
                continue
            # Reply target must match: same parent, not merely the same thread.
            parent_id = str(item.get("parent_id") or "")
            if parent_id and parent_id != parent:
                continue
            if thread:
                link_id = item.get("link_id")
                if isinstance(link_id, str) and link_id.startswith("t3_"):
                    if link_id[3:] != thread:
                        continue
                elif f"/comments/{thread}/" not in str(item.get("permalink") or ""):
                    continue
            elif not parent_id:
                # A t1_ reply we cannot attribute to its parent is not proof.
                continue
            return item
        return None

    def comments(self, limit: int) -> list[dict]:
        """List my own recent comments — used to verify an ambiguous write."""
        username = self.username or str(self.me().get("name") or "")
        suffix = ".json" if self.mode == "cookie" else ""
        payload = self.request(
            "GET",
            f"/user/{urllib.parse.quote(username, safe='')}/comments{suffix}",
            query={"limit": limit, "raw_json": 1},
        )
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            die("Reddit returned a malformed comments response; authenticated response content was omitted.")
        children = payload["data"].get("children")
        # Fail closed: a silently-empty list reads as "the write did not land"
        # and invites the duplicate reply this command exists to prevent.
        if not isinstance(children, list) or any(
            not isinstance(child, dict) or not valid_comment_data(child.get("data")) for child in children
        ):
            die("Reddit returned a malformed comments response; authenticated response content was omitted.")
        return [child["data"] for child in children]

    def search(self, *, query: str, subreddit: str = "", sort: str = "relevance", limit: int = 10, time_filter: str = "month") -> list[dict]:
        suffix = ".json" if self.mode == "cookie" else ""
        path = f"/r/{subreddit}/search{suffix}" if subreddit else f"/search{suffix}"
        params = {"q": query, "sort": sort, "limit": limit, "t": time_filter, "raw_json": 1, "type": "link"}
        if subreddit:
            params["restrict_sr"] = "true"
        payload = self.request("GET", path, query=params)
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            die("Reddit returned a malformed search response; authenticated response content was omitted.")
        children = payload["data"].get("children")
        if not isinstance(children, list):
            die("Reddit returned a malformed search response; authenticated response content was omitted.")
        return [child["data"] for child in children if isinstance(child, dict) and valid_submission_data(child.get("data"))]

    def subreddit_about(self, subreddit: str) -> dict:
        suffix = ".json" if self.mode == "cookie" else ""
        payload = self.request("GET", f"/r/{subreddit}/about{suffix}", query={"raw_json": 1})
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
            die("Reddit returned a malformed subreddit response; authenticated response content was omitted.")
        about = payload["data"]
        rules = self.request("GET", f"/r/{subreddit}/about/rules{suffix}", query={"raw_json": 1})
        rule_items = rules.get("rules") if isinstance(rules, dict) else None
        return {
            "subreddit": about.get("display_name"),
            "subscribers": about.get("subscribers"),
            "over18": about.get("over18"),
            "submission_type": about.get("submission_type"),
            "description": (about.get("public_description") or "")[:600],
            "rules": [
                {
                    "short_name": rule.get("short_name"),
                    "description": (rule.get("description") or "")[:400],
                }
                for rule in (rule_items or [])
                if isinstance(rule, dict)
            ],
        }

    def comment(self, *, parent: str, body: str) -> dict:
        if self.mode == "cookie" and not self.modhash:
            self.me()
        form = {"api_type": "json", "thing_id": parent, "text": body, "raw_json": "1"}
        if self.mode == "cookie":
            if not self.modhash:
                die("Reddit did not return a modhash; the Cookie session cannot perform writes.")
            form["uh"] = self.modhash

        written_at = time.time()
        payload = self.request("POST", "/api/comment", form=form, write_kind="comment")
        # Cookie mode can answer in jQuery form with no `json` object at all.
        if not isinstance(payload, dict) or not isinstance(payload.get("json"), dict):
            return self.verify_recent_comment(parent, body, written_at)
        json_payload = payload["json"]
        errors = json_payload.get("errors")
        if not isinstance(errors, list):
            return self.verify_recent_comment(parent, body, written_at)
        if errors:
            die(
                "Reddit rejected the comment. Check subreddit rules, account age/karma "
                "requirements, whether the thread is locked or archived, and rate limits; "
                "authenticated error details were omitted."
            )
        things = (json_payload.get("data") or {}).get("things")
        created = things[0].get("data") if isinstance(things, list) and things and isinstance(things[0], dict) else None
        if not isinstance(created, dict):
            # Cookie mode returns shapes this parser does not model. Never guess:
            # look for the comment we just wrote before reporting any outcome.
            return self.verify_recent_comment(parent, body, written_at)
        comment_name = created.get("name")
        comment_id = created.get("id")
        if not isinstance(comment_id, str) or not comment_id:
            # `name` is the fullname (t1_<id>), so it carries the id too.
            comment_id = comment_name[3:] if isinstance(comment_name, str) and comment_name.startswith("t1_") else ""

        # A permalink alone proves creation — accept it even without an id.
        permalink = created.get("permalink")
        if isinstance(permalink, str) and permalink.startswith("/"):
            return {"ok": True, "commented": True, "id": comment_id or None, "name": comment_name, "url": WEB_BASE + permalink}

        if not comment_id:
            return self.verify_recent_comment(parent, body, written_at)

        # link_id is the thread even when replying to a comment (t1_ parent).
        link_id = created.get("link_id")
        thread = link_id[3:] if isinstance(link_id, str) and link_id.startswith("t3_") else ""
        if not thread and parent.startswith("t3_"):
            thread = parent[3:]
        if not thread:
            # Created for sure (we hold its id) but the thread is unknown; never
            # report this as a failed write — that is what invites a duplicate.
            return {
                "ok": True,
                "commented": True,
                "id": comment_id,
                "name": comment_name,
                "url": None,
                "note": "Reddit did not return a permalink. Run `comments` to locate it; do not resend.",
            }
        return {"ok": True, "commented": True, "id": comment_id, "name": comment_name, "url": derive_comment_url(thread, comment_id)}


def format_profile(data: dict, mode: str) -> dict:
    return {
        "auth_mode": mode,
        "id": data.get("id"),
        "name": data.get("name"),
        "total_karma": data.get("total_karma"),
        "link_karma": data.get("link_karma"),
        "comment_karma": data.get("comment_karma"),
        "created_utc": data.get("created_utc"),
    }


def valid_submission_data(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    required_strings = ("id", "title", "subreddit", "permalink")
    return all(isinstance(item.get(key), str) and item.get(key) for key in required_strings) and str(
        item["permalink"]
    ).startswith("/")


def die_unknown_write_outcome(reason: str, *, kind: str = "post") -> None:
    where = (
        "Open the parent thread and look for your reply"
        if kind == "comment"
        else "Check recent submissions"
    )
    die(
        f"{reason}; authenticated response content was omitted and the {kind} outcome is unknown. "
        f"{where} before taking any further action and do not replay automatically."
    )


def die_unknown_post_response() -> None:
    die_unknown_write_outcome("Reddit returned a malformed write response")


COMMENT_ID_RE = re.compile(r"^[A-Za-z0-9]{2,16}$")


def derive_comment_url(thread_id: str, comment_id: str) -> str:
    """Build Reddit's slug-less permalink when the write response omits one."""
    if not COMMENT_ID_RE.fullmatch(thread_id) or not COMMENT_ID_RE.fullmatch(comment_id):
        die_unknown_comment_response()
    return f"{WEB_BASE}/comments/{thread_id}/_/{comment_id}/"


def valid_comment_data(item: object) -> bool:
    if not isinstance(item, dict):
        return False
    if not isinstance(item.get("id"), str) or not item["id"]:
        return False
    return isinstance(item.get("body"), str) and isinstance(item.get("permalink"), (str, type(None)))


def die_unknown_comment_response() -> None:
    die_unknown_write_outcome("Reddit returned a malformed comment response", kind="comment")


def format_comment(item: dict) -> dict:
    permalink = item.get("permalink")
    return {
        "id": item.get("id"),
        "body": str(item.get("body") or "")[:300],
        "link_title": item.get("link_title"),
        "subreddit": item.get("subreddit"),
        "url": WEB_BASE + permalink if isinstance(permalink, str) and permalink.startswith("/") else None,
        "score": item.get("score"),
        "created_utc": item.get("created_utc"),
    }


def format_search_hit(item: dict) -> dict:
    permalink = item.get("permalink")
    return {
        "fullname": item.get("name"),
        "title": item.get("title"),
        "subreddit": item.get("subreddit"),
        "author": item.get("author"),
        "url": WEB_BASE + permalink if isinstance(permalink, str) and permalink.startswith("/") else item.get("url"),
        "score": item.get("score"),
        "num_comments": item.get("num_comments"),
        "created_utc": item.get("created_utc"),
        "over_18": item.get("over_18"),
        "link_flair_text": item.get("link_flair_text"),
        "selftext_excerpt": (item.get("selftext") or "")[:500],
    }


def format_submission(item: dict) -> dict:
    permalink = item.get("permalink")
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "subreddit": item.get("subreddit"),
        "url": WEB_BASE + permalink if isinstance(permalink, str) and permalink.startswith("/") else item.get("url"),
        "score": item.get("score"),
        "num_comments": item.get("num_comments"),
        "created_utc": item.get("created_utc"),
    }


def dry_run(args: argparse.Namespace) -> None:
    note = "No request was sent. Re-run with --confirm as the final argument after explicit user approval."
    if args.command == "comment":
        body = read_body(args)
        output(
            {
                "dry_run": True,
                "command": args.command,
                "parent": normalize_thing_id(args.parent),
                "body_length": len(body),
                "body_preview": body[:280],
                "note": note,
            }
        )
        return
    value = {
        "dry_run": True,
        "command": args.command,
        "subreddit": normalize_subreddit(args.subreddit),
        "title": validate_title(args.title),
        "note": note,
    }
    if args.command == "submit-text":
        value["text_length"] = len(read_text(args))
    else:
        value["url"] = validate_link(args.url)
    output(value)


def positive_limit(value: str) -> int:
    parsed = int(value)
    if parsed < 1 or parsed > 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reddit via OAuth or login cookies")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("whoami", help="show the connected Reddit identity")

    submissions = commands.add_parser("submissions", help="list my recent submissions")
    submissions.add_argument("--limit", type=positive_limit, default=10)

    text_post = commands.add_parser("submit-text", help="submit a text post (gated)")
    text_post.add_argument("--subreddit", "-r", required=True)
    text_post.add_argument("--title", required=True)
    text_source = text_post.add_mutually_exclusive_group(required=True)
    text_source.add_argument("--text")
    text_source.add_argument("--text-file", dest="text_file")

    link_post = commands.add_parser("submit-link", help="submit a link post (gated)")
    link_post.add_argument("--subreddit", "-r", required=True)
    link_post.add_argument("--title", required=True)
    link_post.add_argument("--url", required=True)

    my_comments = commands.add_parser("comments", help="list my recent comments (verify an ambiguous write)")
    my_comments.add_argument("--limit", type=positive_limit, default=10)

    search = commands.add_parser("search", help="search public posts to find threads worth replying to")
    search.add_argument("--query", "-q", required=True)
    search.add_argument("--subreddit", "-r", default="")
    search.add_argument("--sort", choices=["relevance", "new", "top", "comments"], default="relevance")
    search.add_argument("--time", dest="time_filter", choices=["hour", "day", "week", "month", "year", "all"], default="month")
    search.add_argument("--limit", type=positive_limit, default=10)

    about = commands.add_parser("subreddit-info", help="read a subreddit's rules and posting requirements")
    about.add_argument("--subreddit", "-r", required=True)

    reply = commands.add_parser("comment", help="reply to a post or comment (gated)")
    reply.add_argument("--parent", required=True, help="fullname (t3_xxx / t1_xxx) or a reddit.com permalink")
    body_source = reply.add_mutually_exclusive_group(required=True)
    body_source.add_argument("--body")
    body_source.add_argument("--body-file", dest="body_file")
    return parser


def main(argv: list[str] | None = None) -> None:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parsed_argv, confirmed = split_confirmation(raw_argv)
    args = build_parser().parse_args(parsed_argv)

    if args.command in GATED_COMMANDS and not confirmed:
        dry_run(args)
        return

    client = RedditClient.from_environment()
    if args.command == "whoami":
        output(format_profile(client.me(), client.mode))
        return
    if args.command == "submissions":
        items = client.submissions(args.limit)
        output({"auth_mode": client.mode, "count": len(items), "submissions": [format_submission(item) for item in items]})
        return
    if args.command == "comments":
        items = client.comments(args.limit)
        output({"auth_mode": client.mode, "count": len(items), "comments": [format_comment(item) for item in items]})
        return
    if args.command == "search":
        hits = client.search(
            query=validate_query(args.query),
            subreddit=normalize_subreddit(args.subreddit) if args.subreddit else "",
            sort=args.sort,
            limit=args.limit,
            time_filter=args.time_filter,
        )
        output({"auth_mode": client.mode, "count": len(hits), "results": [format_search_hit(item) for item in hits]})
        return
    if args.command == "subreddit-info":
        output(client.subreddit_about(normalize_subreddit(args.subreddit)))
        return
    if args.command == "comment":
        output(client.comment(parent=normalize_thing_id(args.parent), body=read_body(args)))
        return

    subreddit = normalize_subreddit(args.subreddit)
    title = validate_title(args.title)
    if args.command == "submit-text":
        output(client.submit(subreddit=subreddit, title=title, kind="self", text=read_text(args)))
    elif args.command == "submit-link":
        output(client.submit(subreddit=subreddit, title=title, kind="link", url=validate_link(args.url)))


if __name__ == "__main__":
    main()