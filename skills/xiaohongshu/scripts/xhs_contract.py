#!/usr/bin/env python3
"""Deterministic contracts for the Xiaohongshu browser skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Match, Optional, Pattern
from urllib.parse import urlparse


ALLOWED_ORIGINS = {"https://www.xiaohongshu.com", "https://creator.xiaohongshu.com"}
ALLOWED_VISIBILITY = {"公开可见", "仅自己可见", "仅互关好友可见"}
FILTER_VALUES = {
    "sort_by": {"综合", "最新", "最多点赞", "最多评论", "最多收藏"},
    "note_type": {"不限", "视频", "图文"},
    "publish_time": {"不限", "一天内", "一周内", "半年内"},
    "search_scope": {"不限", "已看过", "未看过", "已关注"},
    "location": {"不限", "同城", "附近"},
}
MAX_MEDIA = 20
NOTE_PATH = re.compile(r"^/explore/([A-Za-z0-9]+)$")
PROFILE_PATH = re.compile(r"^/user/profile/([A-Za-z0-9]+)$")
TITLE_UNIT = re.compile(r"[\u3400-\u9fff]|[A-Za-z0-9]+")


class ContractError(ValueError):
    pass


def _read_json() -> dict:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        raise ContractError(f"invalid JSON input: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError("input must be a JSON object")
    return value


def _iso_datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("schedule_at must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ContractError("schedule_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _validate_media_url(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError("media URLs must be non-empty strings")
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ContractError("media URLs must use credential-free HTTPS")
    if host != "cdn.acedata.cloud" and not host.endswith(".cdn.acedata.cloud"):
        raise ContractError("automatic media upload requires an Ace Data Cloud CDN URL")
    return value


def validate_publish(payload: dict) -> dict:
    post_type = payload.get("type")
    if post_type not in {"image", "video", "long_article"}:
        raise ContractError("type must be image, video, or long_article")
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ContractError("title is required")
    title_units = TITLE_UNIT.findall(title)
    if len(title_units) > 20:
        raise ContractError("title exceeds 20 CJK characters or English words")
    content = payload.get("content")
    if not isinstance(content, str):
        raise ContractError("content must be a string")

    media = payload.get("media", [])
    if not isinstance(media, list):
        raise ContractError("media must be an array")
    if len(media) > MAX_MEDIA:
        raise ContractError(f"media cannot contain more than {MAX_MEDIA} files")
    normalized_media = [_validate_media_url(item) for item in media]
    if post_type == "image" and not normalized_media:
        raise ContractError("image posts require at least one image")
    if post_type == "video" and len(normalized_media) != 1:
        raise ContractError("video posts require exactly one video")
    if post_type == "long_article" and normalized_media:
        raise ContractError("long_article media must be selected in the visible editor")

    tags = payload.get("tags", [])
    products = payload.get("products", [])
    if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
        raise ContractError("tags must be an array of non-empty strings")
    if not isinstance(products, list) or not all(isinstance(item, str) and item.strip() for item in products):
        raise ContractError("products must be an array of non-empty strings")
    visibility = payload.get("visibility", "公开可见")
    if visibility not in ALLOWED_VISIBILITY:
        raise ContractError("visibility is unsupported")
    if post_type != "image" and payload.get("is_original") not in (None, False):
        raise ContractError("is_original is supported only for image posts")

    schedule_at = payload.get("schedule_at")
    normalized_schedule = None
    if schedule_at:
        if not isinstance(schedule_at, str):
            raise ContractError("schedule_at must be a string")
        now_value = payload.get("now")
        now = _iso_datetime(now_value) if isinstance(now_value, str) else datetime.now(timezone.utc)
        scheduled = _iso_datetime(schedule_at)
        if scheduled < now + timedelta(hours=1) or scheduled > now + timedelta(days=14):
            raise ContractError("schedule_at must be between 1 hour and 14 days from now")
        normalized_schedule = scheduled.isoformat()

    return {
        "type": post_type,
        "title": title.strip(),
        "title_units": len(title_units),
        "content": content,
        "media": normalized_media,
        "tags": [item.strip() for item in tags],
        "visibility": visibility,
        "is_original": bool(payload.get("is_original", False)),
        "products": [item.strip() for item in products],
        "schedule_at": normalized_schedule,
    }


def normalize_filters(payload: dict) -> dict:
    keyword = payload.get("keyword")
    if not isinstance(keyword, str) or not keyword.strip():
        raise ContractError("keyword is required")
    filters = payload.get("filters", {})
    if not isinstance(filters, dict):
        raise ContractError("filters must be an object")
    unknown = set(filters) - set(FILTER_VALUES)
    if unknown:
        raise ContractError(f"unsupported filters: {', '.join(sorted(unknown))}")
    normalized = {}
    for key, allowed in FILTER_VALUES.items():
        value = filters.get(key, "不限" if key != "sort_by" else "综合")
        if value not in allowed:
            raise ContractError(f"unsupported {key}: {value}")
        normalized[key] = value
    return {"keyword": keyword.strip(), "filters": normalized}


def _path_match(href: object, pattern: Pattern[str]) -> Optional[Match[str]]:
    if not isinstance(href, str):
        return None
    parsed = urlparse(href)
    if f"{parsed.scheme}://{parsed.netloc}" != "https://www.xiaohongshu.com":
        return None
    return pattern.fullmatch(parsed.path.rstrip("/"))


def parse_feed_snapshot(snapshot: dict) -> dict:
    if snapshot.get("origin") != "https://www.xiaohongshu.com":
        raise ContractError("feed snapshots require the www.xiaohongshu.com origin")
    nodes = snapshot.get("nodes")
    if not isinstance(nodes, list):
        raise ContractError("snapshot nodes must be an array")

    starts = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict) or node.get("role") != "link":
            continue
        node_name = node.get("name")
        if not isinstance(node_name, str) or not node_name.strip():
            continue
        match = _path_match(node.get("href"), NOTE_PATH)
        if match:
            starts.append((index, match.group(1)))

    notes = []
    seen_note_ids = set()
    for position, (start, note_id) in enumerate(starts):
        node = nodes[start]
        if note_id in seen_note_ids:
            continue
        seen_note_ids.add(note_id)
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        end = starts[position + 1][0] if position + 1 < len(starts) else len(nodes)
        profile_candidates = []
        visible_engagement = []
        for candidate in nodes[start + 1 : end]:
            if not isinstance(candidate, dict):
                continue
            profile = _path_match(candidate.get("href"), PROFILE_PATH)
            raw_name = candidate.get("name")
            name = raw_name.strip() if isinstance(raw_name, str) else ""
            if profile and name:
                profile_candidates.append(
                    {"user_id": profile.group(1), "name": name, "url": candidate["href"]}
                )
            if candidate.get("role") in {"button", "section"} and name:
                visible_engagement.append(name)
        author = profile_candidates[0] if len(profile_candidates) == 1 else None
        notes.append(
            {
                "note_id": note_id,
                "title": node["name"].strip(),
                "url": url,
                "author": author,
                "author_state": "available" if author else ("unavailable" if not profile_candidates else "ambiguous"),
                "visible_engagement": visible_engagement,
            }
        )
    return {"notes": notes, "truncated": bool(snapshot.get("truncated", False))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate-publish", "normalize-filters", "parse-feed-snapshot"))
    args = parser.parse_args()
    try:
        payload = _read_json()
        if args.command == "validate-publish":
            result = validate_publish(payload)
        elif args.command == "normalize-filters":
            result = normalize_filters(payload)
        else:
            result = parse_feed_snapshot(payload)
    except ContractError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2) from exc
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))


if __name__ == "__main__":
    main()