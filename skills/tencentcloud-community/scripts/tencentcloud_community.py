#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import json
import re
from publishing_http import HTTP, require, identifier, identity, saved, run

BASE = "https://cloud.tencent.com"


class Adapter:
    description = "Tencent developer community identity and Markdown drafts over HTTP."
    command, formats = "draft", ["markdown"]

    def __init__(self):
        self.http = HTTP("TENCENTCLOUDCOMMUNITY_COOKIES", [BASE], BASE + "/developer/")

    def whoami(self):
        value = self.http.request(
            BASE + "/developer/api/user/session",
            method="POST",
            raw=b"",
            headers={"Content-Type": "application/json"},
        )
        require(value.get("code", 0) in (0, "0", "ok"), "Community session rejected.")
        data = value.get("data") or value.get("result") or value.get("user") or value
        require(
            isinstance(data, dict) and data.get("isLogin") not in (False, 0, "false"),
            "Community login is required.",
        )
        user_id = (
            data.get("userId")
            or data.get("user_id")
            or data.get("uid")
            or data.get("id")
        )
        name = (
            data.get("nickName")
            or data.get("nickname")
            or data.get("userName")
            or data.get("name")
        )
        if user_id:
            return identity(user_id, name)
        # Read-only fallback for deployments whose session response contains no identity.
        page = self.http.request(BASE + "/developer/creator", text=True)
        match = re.search(r'qct-uid="(\d{1,32})"', page)
        require(
            match is not None and '"isLogin":false' not in page,
            "Community identity could not be verified.",
        )
        return identity(match[1], name)

    def prepare(self, options, content):
        require(
            "data:image/" not in content.lower(),
            "Upload base64 images in the platform editor first.",
        )
        plain = re.sub(r"\s+", " ", content).strip()
        result = {
            "articleId": 0,
            "title": options.title,
            "content": "<!--markdown-->\n" + content + "\n<!--/markdown-->",
            "plain": plain[:4000],
            "sourceType": 0,
            "classifyIds": [],
            "tagIds": [],
            "longtailTag": [],
            "columnIds": [],
            "openComment": 1,
            "closeTextLink": 0,
            "userSummary": "",
            "pic": "",
            "sourceDetail": {},
            "zoneName": "",
            "summary": plain[:120],
        }
        require(
            len(json.dumps(result, ensure_ascii=False).encode()) <= 900000,
            "Draft exceeds the 900 kB local cap.",
        )
        return result

    def write(self, options, payload, account):
        value = self.http.request(
            BASE + "/developer/api/article/addArticleDraft", method="POST", data=payload
        )
        require(value.get("code", 0) in (0, "0"), "Draft save was not accepted.")
        value_id = identifier(value.get("draftId"))
        return saved(
            value_id, BASE + "/developer/article/write-new?draftId=" + value_id
        )


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
