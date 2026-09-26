#!/usr/bin/env python3
"""List uploaded YouTube videos while preserving pagination evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib import error, parse, request

API_ROOT = "https://www.googleapis.com/youtube/v3"


def api_get(path: str, token: str, params: dict[str, str]) -> dict[str, Any]:
    url = f"{API_ROOT}/{path}?{parse.urlencode(params)}"
    req = request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube API HTTP {exc.code}: {body}") from exc


def list_uploads(token: str, *, max_pages: int = 20) -> dict[str, Any]:
    channel = api_get("channels", token, {"part": "contentDetails", "mine": "true"})
    items = channel.get("items") or []
    if not items:
        raise RuntimeError("YouTube channel not found for the connected account")
    uploads = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos: list[dict[str, Any]] = []
    page_token = ""
    pages = 0
    while pages < max_pages:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads,
            "maxResults": "50",
        }
        if page_token:
            params["pageToken"] = page_token
        payload = api_get("playlistItems", token, params)
        pages += 1
        for item in payload.get("items") or []:
            videos.append(
                {
                    "videoId": item.get("contentDetails", {}).get("videoId"),
                    "title": item.get("snippet", {}).get("title"),
                    "published": item.get("snippet", {}).get("publishedAt"),
                }
            )
        page_token = str(payload.get("nextPageToken") or "")
        if not page_token:
            break

    return {
        "uploads_playlist": uploads,
        "pages_fetched": pages,
        "complete": not page_token,
        "next_page_token": page_token or None,
        "items": videos,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()
    token = os.environ.get("GOOGLE_YOUTUBE_TOKEN", "")
    if not token:
        print(json.dumps({"error": "GOOGLE_YOUTUBE_TOKEN is not set"}))
        return 2
    try:
        print(json.dumps(list_uploads(token, max_pages=max(1, min(args.max_pages, 100))), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
