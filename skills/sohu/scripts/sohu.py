#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import time
import uuid
from publishing_http import HTTP, require, identifier, saved, run

BASE = "https://mp.sohu.com"


class Adapter:
    description = "Sohu subaccount listing and HTML drafts over HTTP."
    command, formats = "draft", ["html"]

    def __init__(self):
        self.http = HTTP("SOHU_COOKIES", [BASE], BASE + "/")

    def whoami(self):
        value = self.http.request(BASE + "/mpbp/bp/account/list")
        require(value.get("code") == 2000000 and isinstance(value.get("data"), dict))
        groups = value["data"].get("data")
        require(isinstance(groups, list), "No accessible Sohu accounts.")
        accounts = [
            {"id": identifier(a.get("id")), "name": str(a.get("nickName", ""))[:200]}
            for group in groups
            for a in group.get("accounts", [])
        ]
        require(bool(accounts), "No accessible Sohu accounts.")
        return {"accounts": accounts}

    def prepare(self, options, content):
        require(
            options.account_id is not None,
            "Select --account-id from whoami; no implicit subaccount selection.",
        )
        return {
            "title": options.title,
            "content": content,
            "accountId": int(identifier(options.account_id)),
            "brief": "",
            "channelId": 24,
            "categoryId": -1,
            "id": 0,
            "userColumnId": 0,
            "columnNewsIds": [],
            "businessCode": 0,
            "declareOriginal": False,
            "cover": "",
            "topicIds": [],
            "isAd": 0,
            "userLabels": "[]",
            "reprint": False,
            "customTags": "",
            "infoResource": 0,
            "sourceUrl": "",
            "visibleToLoginedUsers": 0,
            "attrIds": [],
            "auto": True,
        }

    def write(self, options, payload, account):
        require(
            str(payload["accountId"]) in {a["id"] for a in account["accounts"]},
            "Subaccount is not available in this connection.",
        )
        url = (
            BASE
            + "/mpbp/bp/news/v4/news/draft/v2?accountId="
            + str(payload["accountId"])
        )
        fingerprint = (
            self.http.cookie("mp-cv", url, required=False)
            or f"100-{int(time.time() * 1000)}-{uuid.uuid4().hex}"
        )
        value = self.http.request(
            url,
            method="POST",
            data=payload,
            headers={
                "dv-id": uuid.uuid4().hex,
                "sp-cm": fingerprint,
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        require(value.get("success") is True, "Draft save was not accepted.")
        value_id = identifier(value.get("data"))
        return saved(
            value_id,
            BASE
            + "/mpfe/v4/contentManagement/news/addarticle?contentStatus=2&id="
            + value_id,
        )


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
