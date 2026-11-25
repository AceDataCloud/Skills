#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import json
from publishing_http import HTTP, require, identifier, identity, saved, run

BASE = "https://developer.volcengine.com"


class Adapter:
    description = "Volcengine community account and Markdown drafts over HTTP."
    command, formats = "draft", ["markdown"]

    def __init__(self):
        self.http = HTTP("VOLCENGINECOMMUNITY_COOKIES", [BASE], BASE + "/")

    def whoami(self):
        value = self.http.request(
            BASE + "/proxy_tech_api/v1/user/get", method="POST", data={}
        )
        require(value.get("err_no", 0) == 0 and isinstance(value.get("data"), dict))
        data = value["data"]
        return identity(
            data.get("xid") or data.get("employee_id"),
            data.get("volc_name") or data.get("name") or data.get("full_name"),
        )

    def prepare(self, options, content):
        value = {
            "article_info": {
                "title": options.title,
                "content": content,
                "en_title": "",
                "en_content": "",
            }
        }
        require(
            "data:image/" not in content.lower(),
            "Upload inline/base64 images in the platform editor first.",
        )
        require(
            len(json.dumps(value, ensure_ascii=False).encode()) < 400 * 1024,
            "Draft exceeds the 400 KiB local cap.",
        )
        return value

    def write(self, options, payload, account):
        value = self.http.request(
            BASE + "/proxy_tech_api/v1/draft/publish", method="POST", data=payload
        )
        require(
            value.get("err_no", 0) == 0 and isinstance(value.get("data"), dict),
            "Draft save was not accepted.",
        )
        data = value["data"].get("article_info")
        require(isinstance(data, dict), "Missing draft result.")
        value_id = identifier(
            data.get("draft_id") or data.get("article_id") or data.get("id")
        )
        return saved(value_id, BASE + "/articles/draft/" + value_id)


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
