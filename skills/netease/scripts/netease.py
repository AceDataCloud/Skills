#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import urllib.parse
from publishing_http import HTTP, require, identifier, identity, saved, run

BASE = "https://mp.163.com"


class Adapter:
    description = "Netease account and HTML drafts over HTTP."
    command, formats = "draft", ["html"]

    def __init__(self):
        self.http = HTTP("NETEASE_COOKIES", [BASE], BASE + "/subscribe_v4/index.html")

    def whoami(self):
        value = self.http.request(BASE + "/wemedia/navinfo.do")
        require(value.get("code") == 1 and isinstance(value.get("data"), dict))
        self.account = value["data"]
        return identity(self.account.get("wemediaId"), self.account.get("tname"))

    def prepare(self, options, content):
        return {
            "title": options.title,
            "content": content,
            "articleId": "-1",
            "cover": "auto",
            "picUrl": "",
            "operation": "saveDraft",
            "scheduled": "0",
            "original": "0",
        }

    def write(self, options, payload, account):
        query = {"wemediaId": account["user_id"]}
        real = next(
            (
                self.account.get(k)
                for k in ("realUserId", "email", "passport", "userName")
                if self.account.get(k)
            ),
            None,
        )
        if real:
            query["realUserId"] = real
        value = self.http.request(
            BASE
            + "/wemedia/article/status/api/publishV2.do?"
            + urllib.parse.urlencode(query),
            method="POST",
            form={**payload, "wemediaId": account["user_id"]},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        require(value.get("code") in (1, 200), "Draft save was not accepted.")
        data = value.get("data")
        if isinstance(data, str):
            value_id = urllib.parse.parse_qs(data.lstrip("?")).get("docId", [None])[0]
        else:
            require(isinstance(data, dict), "Missing draft result.")
            value_id = data.get("docId") or data.get("articleId") or data.get("id")
        value_id = identifier(value_id)
        return saved(
            value_id, BASE + "/subscribe_v4/index.html#/article-publish/" + value_id
        )


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
