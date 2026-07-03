#!/usr/bin/env python3
"""
apple-notes — manage Apple Notes on macOS via AppleScript (osascript).

Standard library only. There is no cloud API for Apple Notes, so this drives the
local Notes.app through `osascript`. Dynamic values (titles, bodies, ids, folder
names, queries) are passed as ENVIRONMENT VARIABLES and read inside AppleScript
with `system attribute` — they are never interpolated into the script source, so
note content cannot break the script or inject AppleScript/shell commands.

Read commands run directly. Writes (create / append / move / new-folder /
delete) are GATED by a trailing `--confirm` (honored only as the last arg);
without it they dry-run. `delete` moves the note to Recently Deleted (recoverable).

Examples:
  python3 notes.py folders
  python3 notes.py list --limit 20
  python3 notes.py search "invoice" --limit 10
  python3 notes.py view <note-id>
  python3 notes.py export <note-id> --format md -o note.md
  python3 notes.py create --title "Groceries" --body "milk\neggs" --confirm
"""

from __future__ import annotations

import argparse
import html as _html
import json
import os
import re
import subprocess
import sys
from html.parser import HTMLParser

# Field / record separators used to pack AppleScript output (U+001F / U+001E).
US = "\x1f"
RS = "\x1e"

TIMEOUT = 90  # overridden by --timeout in main()

# GATED-write handling: a trailing "--confirm" arms writes; it is stripped before
# argparse so it is never a real flag (and is honored ONLY as the last argument).
_RAW = sys.argv[1:]
CONFIRM = bool(_RAW) and _RAW[-1] == "--confirm"
ARGV = _RAW[:-1] if CONFIRM else list(_RAW)


def out(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def die(msg: str, code: int = 1) -> None:
    out({"error": msg})
    sys.exit(code)


def _int(s) -> int:
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return 0


# ── AppleScript ─────────────────────────────────────────────────────

# ISO-8601 date helpers (locale-independent: build the string from integers).
_HANDLERS = r"""
on isoDate(d)
  return (pad(year of d, 4)) & "-" & (pad((month of d) as integer, 2)) & "-" & (pad(day of d, 2)) & "T" & (pad(hours of d, 2)) & ":" & (pad(minutes of d, 2)) & ":" & (pad(seconds of d, 2))
end isoDate
on pad(n, w)
  set s to ((n as integer) as string)
  repeat while (length of s) < w
    set s to "0" & s
  end repeat
  return s
end pad
"""

_EMIT = (
    '      set fol to ""\n'
    "      try\n"
    "        set fol to name of container of n\n"
    "      end try\n"
    "      set outText to outText & (id of n) & US & (name of n) & US & fol"
    " & US & (my isoDate(modification date of n)) & US & (my isoDate(creation date of n)) & RS\n"
)

_SCRIPT_FOLDERS = r"""
set US to (character id 31)
set RS to (character id 30)
set outText to ""
tell application "Notes"
  repeat with f in folders
    set outText to outText & (name of f) & US & ((count of notes of f) as string) & RS
  end repeat
end tell
return outText
"""

_SCRIPT_LIST = _HANDLERS + (
    'set US to (character id 31)\n'
    'set RS to (character id 30)\n'
    'set folderName to system attribute "ANOTE_FOLDER"\n'
    'set outText to ""\n'
    'tell application "Notes"\n'
    '  if folderName is "" then\n'
    '    set theNotes to every note\n'
    '  else\n'
    '    set theNotes to every note of folder folderName\n'
    '  end if\n'
    '  repeat with n in theNotes\n'
    + _EMIT +
    '  end repeat\n'
    'end tell\n'
    'return outText\n'
)

_SCRIPT_SEARCH = _HANDLERS + (
    'set US to (character id 31)\n'
    'set RS to (character id 30)\n'
    'set q to system attribute "ANOTE_QUERY"\n'
    'set folderName to system attribute "ANOTE_FOLDER"\n'
    'set outText to ""\n'
    'tell application "Notes"\n'
    '  if folderName is "" then\n'
    '    set theNotes to (every note whose (name contains q) or (body contains q))\n'
    '  else\n'
    '    set theNotes to (every note of folder folderName whose (name contains q) or (body contains q))\n'
    '  end if\n'
    '  repeat with n in theNotes\n'
    + _EMIT +
    '  end repeat\n'
    'end tell\n'
    'return outText\n'
)

_SCRIPT_VIEW = _HANDLERS + (
    'set US to (character id 31)\n'
    'set theId to system attribute "ANOTE_ID"\n'
    'tell application "Notes"\n'
    '  set n to first note whose id is theId\n'
    '  set fol to ""\n'
    '  try\n'
    '    set fol to name of container of n\n'
    '  end try\n'
    '  set outText to (id of n) & US & (name of n) & US & fol & US'
    ' & (my isoDate(creation date of n)) & US & (my isoDate(modification date of n)) & US & (body of n)\n'
    'end tell\n'
    'return outText\n'
)

_SCRIPT_CREATE = r"""
set theBody to system attribute "ANOTE_BODY"
set folderName to system attribute "ANOTE_FOLDER"
tell application "Notes"
  if folderName is "" then
    set newNote to make new note with properties {body:theBody}
  else
    tell folder folderName
      set newNote to make new note with properties {body:theBody}
    end tell
  end if
  return id of newNote
end tell
"""

_SCRIPT_APPEND = r"""
set theId to system attribute "ANOTE_ID"
set extra to system attribute "ANOTE_BODY"
tell application "Notes"
  set n to first note whose id is theId
  set body of n to (body of n) & extra
  return id of n
end tell
"""

_SCRIPT_MOVE = r"""
set theId to system attribute "ANOTE_ID"
set destFolder to system attribute "ANOTE_FOLDER"
tell application "Notes"
  set n to first note whose id is theId
  move n to folder destFolder
  return id of n
end tell
"""

_SCRIPT_NEWFOLDER = r"""
set folderName to system attribute "ANOTE_FOLDER"
tell application "Notes"
  make new folder with properties {name:folderName}
end tell
return folderName
"""

_SCRIPT_DELETE = r"""
set theId to system attribute "ANOTE_ID"
tell application "Notes"
  set n to first note whose id is theId
  delete n
end tell
return theId
"""


def _map_error(err: str) -> None:
    low = err.lower()
    if "-1743" in err or "not authoriz" in low or "not allowed to send" in low:
        die(
            "Not authorized to control Notes. Grant Automation access under "
            "System Settings \u203a Privacy & Security \u203a Automation \u203a "
            "(your terminal/agent) \u203a Notes, then retry."
        )
    if "-1728" in err or "can\u2019t get" in low or "can't get" in low or "-2753" in err:
        die("Not found \u2014 check the note id or folder name (run `list` / `folders` for valid values).")
    if "-600" in err or "isn\u2019t running" in low or "not running" in low:
        die("Notes.app could not launch.")
    die("AppleScript error: " + err if err else "osascript failed with no error message.")


def osa(script: str, **env: str) -> str:
    full = dict(os.environ)
    for key, value in env.items():
        full[key] = "" if value is None else str(value)
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=full,
            timeout=TIMEOUT,
        )
    except FileNotFoundError:
        die("osascript not found \u2014 this skill requires macOS.")
    except subprocess.TimeoutExpired:
        die(f"osascript timed out after {TIMEOUT}s \u2014 narrow with --folder / --limit.")
    if proc.returncode != 0:
        _map_error((proc.stderr or "").strip())
    return proc.stdout


# ── content helpers ─────────────────────────────────────────────────

def text_to_html(title: str, body: str) -> str:
    """Plain text -> Notes-safe HTML (one <div> per line). Input is escaped."""
    parts = []
    if title:
        parts.append("<div>" + _html.escape(title) + "</div>")
    for line in (body or "").split("\n"):
        parts.append("<div><br></div>" if line.strip() == "" else "<div>" + _html.escape(line) + "</div>")
    return "".join(parts)


class _Converter(HTMLParser):
    """Minimal Notes-HTML -> Markdown/plain-text converter (stdlib only)."""

    def __init__(self, markdown: bool = True) -> None:
        super().__init__(convert_charrefs=True)
        self.md = markdown
        self.buf: list[str] = []
        self._href: str | None = None
        self._list: list = []

    def _nl(self) -> None:
        if self.buf and not self.buf[-1].endswith("\n"):
            self.buf.append("\n")

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "br":
            self.buf.append("\n")
        elif tag in ("div", "p"):
            self._nl()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._nl()
            if self.md:
                self.buf.append("#" * int(tag[1]) + " ")
        elif tag in ("b", "strong") and self.md:
            self.buf.append("**")
        elif tag in ("i", "em") and self.md:
            self.buf.append("*")
        elif tag == "ul":
            self._list.append("ul")
            self._nl()
        elif tag == "ol":
            self._list.append(["ol", 0])
            self._nl()
        elif tag == "li":
            self._nl()
            if self.md and self._list:
                top = self._list[-1]
                if top == "ul":
                    self.buf.append("- ")
                else:
                    top[1] += 1
                    self.buf.append(f"{top[1]}. ")
        elif tag == "a":
            self._href = dict(attrs).get("href")
            if self.md and self._href:
                self.buf.append("[")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("b", "strong") and self.md:
            self.buf.append("**")
        elif tag in ("i", "em") and self.md:
            self.buf.append("*")
        elif tag in ("div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li"):
            self._nl()
        elif tag in ("ul", "ol"):
            if self._list:
                self._list.pop()
            self._nl()
        elif tag == "a":
            if self.md and self._href:
                self.buf.append(f"]({self._href})")
            self._href = None

    def handle_data(self, data: str) -> None:
        self.buf.append(data)

    def result(self) -> str:
        text = re.sub(r"\n{3,}", "\n\n", "".join(self.buf))
        return text.strip() + "\n"


def _convert(body_html: str, markdown: bool) -> str:
    conv = _Converter(markdown=markdown)
    conv.feed(body_html or "")
    return conv.result()


def _read_body(args) -> str:
    body_file = getattr(args, "body_file", None)
    if body_file:
        try:
            with open(body_file, "r", encoding="utf-8") as fh:
                return fh.read()
        except OSError as exc:
            die(f"cannot read --body-file: {exc}")
    body = getattr(args, "body", None)
    if body is None:
        return ""
    return body.replace("\\n", "\n").replace("\\t", "\t")


def _parse_notes(raw: str) -> list:
    items = []
    for rec in raw.split(RS):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = rec.split(US)
        if len(parts) < 5:
            continue
        items.append(
            {"id": parts[0], "title": parts[1], "folder": parts[2], "modified": parts[3], "created": parts[4]}
        )
    return items


# ── commands ────────────────────────────────────────────────────────

def cmd_folders(args) -> None:
    raw = osa(_SCRIPT_FOLDERS)
    items = []
    for rec in raw.split(RS):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = rec.split(US)
        if len(parts) < 2:
            continue
        items.append({"folder": parts[0], "count": _int(parts[1])})
    out({"folders": items, "count": len(items)})


def cmd_list(args) -> None:
    items = _parse_notes(osa(_SCRIPT_LIST, ANOTE_FOLDER=args.folder or ""))
    items.sort(key=lambda x: x.get("modified") or "", reverse=True)
    if args.limit and args.limit > 0:
        items = items[: args.limit]
    out({"notes": items, "count": len(items)})


def cmd_search(args) -> None:
    query = (args.query or "").strip()
    if not query:
        die("search needs a non-empty query.")
    items = _parse_notes(osa(_SCRIPT_SEARCH, ANOTE_QUERY=args.query, ANOTE_FOLDER=args.folder or ""))
    items.sort(key=lambda x: x.get("modified") or "", reverse=True)
    if args.limit and args.limit > 0:
        items = items[: args.limit]
    out({"query": args.query, "notes": items, "count": len(items)})


def _fetch(note_id: str) -> dict:
    raw = osa(_SCRIPT_VIEW, ANOTE_ID=note_id)
    # maxsplit=5 so the HTML body (last field) keeps any US/RS chars it contains
    parts = raw.split(US, 5)
    if len(parts) < 6:
        die("unexpected osascript output while reading the note.")
    body = parts[5]
    if body.endswith("\n"):
        body = body[:-1]
    return {
        "id": parts[0],
        "title": parts[1],
        "folder": parts[2],
        "created": parts[3],
        "modified": parts[4],
        "body_html": body,
    }


def cmd_view(args) -> None:
    note = _fetch(args.note_id)
    if args.format == "html":
        print(note["body_html"])
        return
    if args.format == "text":
        print(_convert(note["body_html"], markdown=False))
        return
    note["text"] = _convert(note["body_html"], markdown=False)
    out(note)


def cmd_export(args) -> None:
    note = _fetch(args.note_id)
    if args.format == "html":
        content = note["body_html"]
    else:
        content = _convert(note["body_html"], markdown=(args.format == "md"))
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(content if content.endswith("\n") else content + "\n")
        except OSError as exc:
            die(f"cannot write output: {exc}")
        out(
            {
                "exported": args.output,
                "title": note["title"],
                "format": args.format,
                "bytes": len(content.encode("utf-8")),
            }
        )
    else:
        print(content)


def _dry(action: str, **fields) -> None:
    payload = {"dry_run": True, "action": action}
    payload.update(fields)
    payload["hint"] = "re-run with --confirm as the LAST argument to apply"
    out(payload)


def cmd_create(args) -> None:
    body = _read_body(args)
    if not CONFIRM:
        preview = args.title + (("\n" + body) if body else "")
        _dry("create", title=args.title, folder=args.folder or "(default)", preview=preview)
        return
    note_id = osa(_SCRIPT_CREATE, ANOTE_BODY=text_to_html(args.title, body), ANOTE_FOLDER=args.folder or "").strip()
    out({"created": True, "id": note_id, "title": args.title, "folder": args.folder or "(default)"})


def cmd_append(args) -> None:
    body = _read_body(args)
    if not body.strip():
        die("nothing to append (empty body).")
    if not CONFIRM:
        _dry("append", note_id=args.note_id, preview=body)
        return
    note_id = osa(_SCRIPT_APPEND, ANOTE_ID=args.note_id, ANOTE_BODY=text_to_html("", body)).strip()
    out({"appended": True, "id": note_id})


def cmd_move(args) -> None:
    if not CONFIRM:
        _dry("move", note_id=args.note_id, to_folder=args.folder)
        return
    note_id = osa(_SCRIPT_MOVE, ANOTE_ID=args.note_id, ANOTE_FOLDER=args.folder).strip()
    out({"moved": True, "id": note_id, "folder": args.folder})


def cmd_new_folder(args) -> None:
    if not CONFIRM:
        _dry("new-folder", name=args.name)
        return
    name = osa(_SCRIPT_NEWFOLDER, ANOTE_FOLDER=args.name).strip()
    out({"created_folder": True, "name": name})


def cmd_delete(args) -> None:
    if not CONFIRM:
        _dry("delete", note_id=args.note_id, note="moves the note to Recently Deleted (recoverable)")
        return
    note_id = osa(_SCRIPT_DELETE, ANOTE_ID=args.note_id).strip()
    out({"deleted": True, "id": note_id, "note": "moved to Recently Deleted (recoverable ~30 days)"})


def main() -> None:
    if sys.platform != "darwin":
        die("apple-notes is macOS-only (it drives Notes.app via AppleScript).")

    parser = argparse.ArgumentParser(prog="notes.py", description="Manage Apple Notes via AppleScript.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--timeout", type=int, default=90, help="osascript timeout in seconds (default 90)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("folders", parents=[common], help="list folders with note counts").set_defaults(func=cmd_folders)

    p = sub.add_parser("list", parents=[common], help="list notes (newest first)")
    p.add_argument("--folder")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search", parents=[common], help="search notes by title + body")
    p.add_argument("query")
    p.add_argument("--folder")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("view", parents=[common], help="show one note")
    p.add_argument("note_id")
    p.add_argument("--format", choices=["json", "text", "html"], default="json")
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("export", parents=[common], help="export one note")
    p.add_argument("note_id")
    p.add_argument("--format", choices=["md", "html", "text"], default="md")
    p.add_argument("-o", "--output")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("create", parents=[common], help="create a note (GATED)")
    p.add_argument("--title", required=True)
    grp = p.add_mutually_exclusive_group()
    grp.add_argument("--body")
    grp.add_argument("--body-file")
    p.add_argument("--folder")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("append", parents=[common], help="append text to a note (GATED)")
    p.add_argument("note_id")
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--body")
    grp.add_argument("--body-file")
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("move", parents=[common], help="move a note to a folder (GATED)")
    p.add_argument("note_id")
    p.add_argument("--folder", required=True)
    p.set_defaults(func=cmd_move)

    p = sub.add_parser("new-folder", parents=[common], help="create a folder (GATED)")
    p.add_argument("name")
    p.set_defaults(func=cmd_new_folder)

    p = sub.add_parser("delete", parents=[common], help="move a note to Recently Deleted (GATED)")
    p.add_argument("note_id")
    p.set_defaults(func=cmd_delete)

    args = parser.parse_args(ARGV)
    global TIMEOUT
    TIMEOUT = args.timeout
    args.func(args)


if __name__ == "__main__":
    main()
