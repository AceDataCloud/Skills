#!/usr/bin/env python3
"""Independent HTTP client; protocol evidence is linked in SKILL.md."""

from publishing_http import HTTP, Error, require, identifier, saved, run

BASE = "https://www.jianshu.com"
HEADERS = {"X-Requested-With": "XMLHttpRequest"}


class Adapter:
    description = "Jianshu account, notebooks and Markdown drafts over HTTP."
    command, formats = "draft", ["markdown"]

    def __init__(self):
        self.http = HTTP("JIANSHU_COOKIES", [BASE], BASE + "/writer")

    def whoami(self):
        value = self.http.request(BASE + "/settings/basic.json", headers=HEADERS)
        user = value.get("data", value)
        require(isinstance(user, dict) and (user.get("nickname") or user.get("name")))
        return {"name": user.get("nickname") or user["name"]}

    def notebooks(self):
        rows = self.http.request(BASE + "/author/notebooks", headers=HEADERS)
        require(isinstance(rows, list), "Notebook listing failed.")
        return [
            {"id": identifier(r.get("id")), "name": str(r.get("name", ""))[:200]}
            for r in rows
        ]

    def prepare(self, options, content):
        require(
            options.notebook_id is not None,
            "Choose --notebook-id from the notebooks command.",
        )
        return {
            "title": options.title,
            "content": content,
            "notebook_id": int(identifier(options.notebook_id)),
        }

    def write(self, options, payload, account):
        require(
            str(payload["notebook_id"]) in {r["id"] for r in self.notebooks()},
            "Requested notebook is not in this account.",
        )
        created = self.http.request(
            BASE + "/author/notes",
            method="POST",
            data={
                "at_bottom": False,
                "notebook_id": payload["notebook_id"],
                "title": payload["title"],
            },
            headers=HEADERS,
        )
        note_id = identifier(created.get("id"))
        result = saved(
            note_id,
            f"{BASE}/writer#/notebooks/{payload['notebook_id']}/notes/{note_id}",
        )
        version = created.get("autosave_control", 0)
        try:
            require(
                isinstance(version, int)
                and not isinstance(version, bool)
                and version >= 0,
                "Invalid draft version.",
            )
            response = self.http.request(
                BASE + "/author/notes/" + note_id,
                method="PUT",
                headers=HEADERS,
                empty=True,
                data={
                    "id": int(note_id),
                    "title": payload["title"],
                    "content": payload["content"],
                    "autosave_control": version + 1,
                },
            )
            require(
                response is None
                or (isinstance(response, dict) and not response.get("error")),
                "Draft body update rejected.",
            )
        except Error as error:
            raise Error(
                str(error), result={**result, "status": "partial", "body_saved": False}
            ) from None
        return {**result, "body_saved": True}


if __name__ == "__main__":
    raise SystemExit(run(Adapter))
