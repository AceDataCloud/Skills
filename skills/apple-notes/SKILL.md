---
name: apple-notes
description: Manage Apple Notes on macOS — list, search, read, create, append, move, delete, and export notes, and manage folders. Use when the user mentions Apple Notes / 备忘录, "add a note", "my notes", searching their notes, organizing folders, or exporting a note to Markdown/HTML. macOS-only; runs locally against Notes.app — no cloud API, no token.
when_to_use: |
  Trigger for anything on the user's local Apple Notes (Notes.app on macOS):
  list / search / read / export a note, create a new one, append to an existing
  one, move it between folders, or manage folders. There is no cloud API for
  Apple Notes, so this runs on the user's own Mac (Claude Code on macOS, or
  driven remotely through a CodingBridge node). Writes act on the user's REAL
  notes, so create / append / move / delete are GATED behind an explicit
  confirmation.
allowed_tools: [Bash]
license: Apache-2.0
compatibility: macOS-only. No API token, no connector — Apple Notes has no cloud API. Drives the local Notes.app via AppleScript (osascript); zero external dependencies (Python 3 standard library only). Requires granting Automation access to Notes.app on first run. Does not call api.acedata.cloud.
metadata:
  author: acedatacloud
  version: "1.0"
---

# apple-notes — manage Apple Notes locally via AppleScript

Drives the user's **real** Apple Notes through `Notes.app` on macOS. Apple never
shipped a cloud API for Notes, so there is nothing to OAuth into and no token to
inject — this skill runs **on the user's own Mac** and talks to Notes.app with
AppleScript (`osascript`). It works when Claude Code runs on macOS directly, or
remotely through a CodingBridge node running on the user's Mac.

The skill ships [`scripts/notes.py`](scripts/notes.py) — self-contained, Python
**standard library only** (it shells out to `osascript`; no `pip install`, no
`brew`). Dynamic values are passed as environment variables, never interpolated
into the AppleScript source, so note content can't break the script or inject
commands.

## Requirements

- **macOS** with the Notes app. `python3` (system Python is fine).
- **Automation permission.** The first call triggers a macOS prompt: *"Terminal
  wants to control Notes."* Approve it, or enable it under **System Settings ›
  Privacy & Security › Automation ›** (your terminal / agent) **› Notes**. On an
  authorization error the CLI tells the user exactly this — do **not** loop-retry.
- Referencing Notes launches the app in the background (no window is forced open).

```sh
NOTES="${SKILL_DIR:-.}/scripts/notes.py"   # run from this skill's directory
python3 "$NOTES" folders                    # smoke-test the connection
```

## Commands

| Command | Read/Write | Purpose |
| --- | --- | --- |
| `folders` | read | List folders with note counts |
| `list [--folder F] [--limit N]` | read | List notes (newest first): id, title, folder, dates |
| `search QUERY [--folder F] [--limit N]` | read | Case-insensitive substring match on title + body |
| `view NOTE_ID [--format json\|text\|html]` | read | Show one note (metadata + body) |
| `export NOTE_ID [--format md\|html\|text] [-o FILE]` | read | Export one note to Markdown/HTML/text |
| `create --title T [--body B \| --body-file F] [--folder F]` | **write** | Create a note |
| `append NOTE_ID [--body B \| --body-file F]` | **write** | Append text to an existing note |
| `move NOTE_ID --folder F` | **write** | Move a note to another folder |
| `new-folder NAME` | **write** | Create a folder |
| `delete NOTE_ID` | **write** | Move a note to *Recently Deleted* (recoverable) |

Most commands print JSON (and errors are always JSON: `{"error": ...}`). The
exceptions print raw note content to stdout: `view --format text|html` and
`export` without `-o`. `NOTE_ID` is the opaque `x-coredata://…` id returned by
`list` / `search` — always fetch a fresh id first; do not guess one.

## Read examples

```sh
python3 "$NOTES" folders
python3 "$NOTES" list --limit 20
python3 "$NOTES" list --folder "Work" --limit 50
python3 "$NOTES" search "invoice" --limit 20
python3 "$NOTES" view "x-coredata://…/p42"
python3 "$NOTES" export "x-coredata://…/p42" --format md -o note.md
```

## Writes are GATED (dry-run unless trailing `--confirm`)

`create`, `append`, `move`, `new-folder`, and `delete` change the user's real
notes. Without a trailing `--confirm` they **dry-run** and print what they would
do. `--confirm` is honored **only as the very last argument**. Always show the
dry-run, get an explicit "yes", then re-run with `--confirm` appended.

```sh
# Create — dry-run, then confirm
python3 "$NOTES" create --title "Groceries" --body "milk\neggs"                # preview
python3 "$NOTES" create --title "Groceries" --body "milk\neggs" --confirm      # writes

# Create in a folder, body from a file
python3 "$NOTES" create --title "Spec" --body-file draft.md --folder "Work" --confirm

# Append to an existing note
python3 "$NOTES" append "x-coredata://…/p42" --body "one more line" --confirm

# Move / organize
python3 "$NOTES" new-folder "Archive" --confirm
python3 "$NOTES" move "x-coredata://…/p42" --folder "Archive" --confirm

# Delete → goes to Recently Deleted (recoverable ~30 days)
python3 "$NOTES" delete "x-coredata://…/p42" --confirm
```

Content is treated as **plain text** (each line becomes a paragraph; the
`--title` is the note's first line, which Notes shows as the title). HTML in the
input is escaped, so it can't inject markup. Use `\n` for line breaks in
`--body`, or pass a file with `--body-file`.

## Gotchas

- **This is the user's real Notes account.** Confirm before any write.
- **`list` scans the whole library** — for large accounts it can take a few
  seconds. Narrow with `--folder`, and cap with `--limit` (default 50). `search`
  filters inside Notes and is faster.
- **Attachments / images:** notes containing images or attachments can be read
  and exported as text, but `append` may not preserve embedded attachments —
  avoid editing attachment notes here; open them in Notes instead.
- **Export → Markdown** converts common Notes formatting (headings, bold/italic,
  lists, links, line breaks). Rich objects (tables, drawings, scanned docs)
  degrade to plain text.
- **`move` stays within one account** (e.g. iCloud). Cross-account moves fail.
- **Never assume a `NOTE_ID`** — ids are store-specific; always get them from
  `list` / `search` first.
- On a persistent authorization error, the Automation permission is missing —
  tell the user to grant it (see Requirements) and stop; do not retry in a loop.
