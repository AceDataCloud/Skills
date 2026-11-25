#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import json
from publishing_http import HTTP, Error, require, identifier, identity, saved, run

BASE = "https://xie.infoq.cn"


class Adapter:
    description = "InfoQ author lookup and native ProseMirror drafts over HTTP."
    command, formats = "draft", ["text", "native"]

    def __init__(self):
        self.http = HTTP("INFOQ_COOKIES", [BASE], BASE + "/")

    def api(self, path, payload):
        value = self.http.request(BASE + path, method="POST", data=payload)
        require(
            value.get("code") == 0,
            "InfoQ rejected the request; check author access or draft capacity.",
        )
        return value.get("data")

    def whoami(self):
        self.user = self.api("/public/v1/user/get_user", {})
        require(isinstance(self.user, dict))
        return {
            **identity(self.user.get("uid"), self.user.get("nickname")),
            "is_author": self.user.get("is_author", 0),
        }

    def prepare(self, options, content):
        if options.format == "native":
            try:
                document = json.loads(content)
            except ValueError:
                raise Error("Native input must be valid ProseMirror JSON.") from None
        else:
            document = {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "attrs": {
                            "indent": 0,
                            "number": 0,
                            "align": None,
                            "origin": None,
                        },
                        "content": [{"type": "text", "text": line}],
                    }
                    for line in content.splitlines()
                    if line
                ],
            }
        require(
            isinstance(document, dict)
            and document.get("type") == "doc"
            and isinstance(document.get("content"), list)
            and bool(document["content"]),
            "Native input must be a non-empty ProseMirror doc.",
        )
        return {
            "title": options.title,
            "cover": "",
            "summary": "",
            "is_force": 1,
            "content": json.dumps(document, ensure_ascii=False),
        }

    def write(self, options, payload, account):
        require(
            isinstance(account["is_author"], int) and account["is_author"] >= 2,
            "InfoQ author access is not enabled.",
        )
        created = self.api("/api/v1/draft/create", {})
        require(isinstance(created, dict), "No draft was returned.")
        draft_id = identifier(created.get("id"))
        result = saved(draft_id, BASE + "/draft/" + draft_id)
        try:
            self.api(
                "/api/v1/draft/pushFull", {"id": int(draft_id), "version": 0, **payload}
            )
        except Error as error:
            raise Error(
                str(error), result={**result, "status": "partial", "body_saved": False}
            ) from None
        return {**result, "body_saved": True}


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
