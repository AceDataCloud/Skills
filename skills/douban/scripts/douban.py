#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import json
import re
from publishing_http import HTTP, Error, require, identifier, identity, run

BASE = "https://www.douban.com"
POST = "https://m.douban.com/rexxar/api/v2/topic/post"


class Adapter:
    description = "Douban identity and private note creation over HTTP. A private post is not a draft."
    command, formats = "post-private", ["text", "native"]

    def __init__(self):
        self.http = HTTP(
            "DOUBAN_COOKIES",
            [BASE, "https://m.douban.com"],
            BASE + "/topic/create?subtype=note",
        )

    def whoami(self):
        page = self.http.request(BASE + "/topic/create?subtype=note", text=True)
        match = re.search(r'user:\s{0,30}\{\s{0,30}"id":\s{0,30}"(\d{1,32})"', page)
        require(match is not None, "Douban login or verification is required.")
        self.http.cookie("ck", POST)
        return identity(match[1])

    def prepare(self, options, content):
        if options.format == "native":
            try:
                document = json.loads(content)
            except ValueError:
                raise Error("Native input must be valid Draft.js JSON.") from None
        else:
            document = {
                "blocks": [
                    {
                        "key": f"b{i}",
                        "text": line,
                        "type": "unstyled",
                        "depth": 0,
                        "inlineStyleRanges": [],
                        "entityRanges": [],
                        "data": {},
                    }
                    for i, line in enumerate(content.splitlines())
                ],
                "entityMap": {},
            }
        require(
            isinstance(document, dict)
            and isinstance(document.get("blocks"), list)
            and bool(document["blocks"])
            and isinstance(document.get("entityMap"), dict),
            "Native input must contain Draft.js blocks and entityMap.",
        )
        return {
            "title": options.title,
            "content": json.dumps(document, ensure_ascii=False),
            "image_ids": "",
            "topic_tag_ids": "",
            "interest_tags": "",
            "is_event": False,
            "subtype": "note",
            "accessible": "private",
            "explanation_types": "",
            "send_status": True,
            "original": False,
            "is_activity_rule": False,
            "enable_item_tag": False,
        }

    def write(self, options, payload, account):
        value = self.http.request(
            POST,
            method="POST",
            data=payload,
            headers={"X-CSRF-TOKEN": self.http.cookie("ck", POST)},
        )
        value_id = identifier(value.get("id"))
        url = value.get("url")
        require(
            isinstance(url, str) and url.startswith(BASE + "/topic/"),
            "Private post response has no trusted topic URL.",
        )
        return {
            "status": "private_post",
            "post_id": value_id,
            "url": url,
            "visibility": "private",
            "published_publicly": False,
            "readback_verified": False,
        }


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
