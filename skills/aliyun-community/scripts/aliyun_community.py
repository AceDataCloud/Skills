#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import urllib.parse
from publishing_http import HTTP, require, identifier, identity, saved, run

BASE = "https://developer.aliyun.com"


class Adapter:
    description = "Aliyun developer community account and Markdown drafts over HTTP."
    command, formats = "draft", ["markdown"]

    def __init__(self):
        self.http = HTTP("ALIYUNCOMMUNITY_COOKIES", [BASE], BASE + "/article/new")

    def whoami(self):
        value = self.http.request(BASE + "/developer/api/my/user/getUser")
        require(value.get("success") is True and isinstance(value.get("data"), dict))
        data = value["data"]
        return identity(data.get("aliyunPK") or data.get("uccId"), data.get("nickname"))

    def prepare(self, options, content):
        return {"title": options.title, "content": content}

    def write(self, options, payload, account):
        url = BASE + "/developer/api/articleDraft/putDraft"
        csrf = self.http.cookie("c_csrf", url)
        value = self.http.request(
            url + "?" + urllib.parse.urlencode({"p_csrf": csrf}),
            method="POST",
            data=payload,
            headers={"h_csrf": csrf, "X-XSRF-TOKEN": csrf},
        )
        require(
            value.get("success") is True and isinstance(value.get("data"), dict),
            "Draft save was not accepted.",
        )
        aid = identifier(value["data"].get("aid"))
        return saved(aid, BASE + "/article/new?edit=" + aid)


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
