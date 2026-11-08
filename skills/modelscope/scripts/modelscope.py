#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

import json
import uuid
import urllib.parse
from publishing_http import HTTP, Error, require, identifier, saved, run

BASE = "https://modelscope.cn"


class Adapter:
    description = "ModelScope account and body-only article drafts over HTTP; title is completed in editor."
    command, formats = "draft", ["text", "native"]

    def __init__(self):
        self.http = HTTP("MODELSCOPE_COOKIES", [BASE], BASE + "/learn/create")

    def whoami(self):
        value = self.http.request(
            BASE + "/api/v1/users/login/info",
            headers={"x-modelscope-accept-language": "zh_CN"},
        )
        require(
            value.get("Success") is True
            and value.get("Code") == 200
            and isinstance(value.get("Data"), dict)
        )
        name = value["Data"].get("Name") or value["Data"].get("NickName")
        require(
            isinstance(name, str) and bool(name),
            "ModelScope returned no account identity.",
        )
        return {"name": name[:200]}

    def prepare(self, options, content):
        if options.format == "native":
            try:
                document = json.loads(content)
            except ValueError:
                raise Error("Native input must be valid Cangjie JsonML.") from None
        else:
            document = [
                "root",
                {},
                *[
                    [
                        "p",
                        {"uuid": uuid.uuid4().hex},
                        [
                            "span",
                            {"data-type": "text"},
                            ["span", {"data-type": "leaf"}, line],
                        ],
                    ]
                    for line in content.splitlines()
                    if line
                ],
            ]
        require(
            isinstance(document, list)
            and len(document) > 2
            and document[0] == "root"
            and isinstance(document[1], dict),
            "Native input must be a non-empty JsonML root.",
        )
        return {"ContentDraft": json.dumps(document, ensure_ascii=False)}

    def write(self, options, payload, account):
        url = BASE + "/api/v1/articles"
        csrf = self.http.cookie("csrf_token", url, required=False)
        headers = {"X-CSRF-TOKEN": urllib.parse.unquote(csrf)} if csrf else {}
        value = self.http.request(url, method="POST", data=payload, headers=headers)
        require(
            value.get("Success") is True
            and value.get("Code") == 200
            and isinstance(value.get("Data"), dict),
            "Draft save was not accepted; account eligibility may be required.",
        )
        data = value["Data"]
        value_id = data.get("Id") or data.get("id")
        if not value_id and isinstance(data.get("Articles"), list) and data["Articles"]:
            value_id = data["Articles"][0].get("Id")
        value_id = identifier(value_id)
        return saved(
            value_id,
            BASE + "/learn/edit/" + value_id,
            title_saved=False,
            requested_title=options.title,
            next_step="Set the article title and review the body in the editor.",
        )


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
