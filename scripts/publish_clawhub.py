#!/usr/bin/env python3
"""Preview or update one existing AceDataCloud ClawHub skill."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
OWNER = "acedatacloud"
CLI = ["npx", "--yes", "clawhub@0.23.3"]


def run(args, cwd=REPO):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or
                           f"Command failed with exit code {result.returncode}")
    return result.stdout.strip()


def manifest_name(content):
    """Read a plain top-level name without executing or expanding YAML tags."""
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise RuntimeError("SKILL.md must declare a top-level frontmatter name")
    for line in lines[1:]:
        if line == "---":
            break
        match = re.fullmatch(r"name:\s*([a-z0-9-]+|'[a-z0-9-]+'|\"[a-z0-9-]+\")\s*", line)
        if match:
            return match.group(1).strip("'\"")
    raise RuntimeError("SKILL.md must declare a plain top-level frontmatter name")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="Source folder name, e.g. suno-music or api-guide")
    parser.add_argument("--slug", required=True, help="Existing canonical ClawHub name, e.g. suno")
    parser.add_argument("--version", help="Explicit semver; otherwise ClawHub skips unchanged content")
    parser.add_argument("--changelog", required=True, help="Reviewed release notes")
    parser.add_argument("--publish", action="store_true", help="Upload after publisher access and MIT-0 permission are confirmed")
    parser.add_argument("--accept-mit-0", action="store_true", help="Acknowledge existing human authorization for ClawHub's MIT-0 terms; required with --publish")
    args = parser.parse_args(argv)
    if args.publish and not args.accept_mit_0:
        parser.error("--publish requires --accept-mit-0 after human authorization; the CLI accepts these terms during upload")
    name_pattern = r"[a-z0-9]+(?:-[a-z0-9]+)*"
    if not re.fullmatch(name_pattern, args.skill) or not re.fullmatch(name_pattern, args.slug):
        parser.error("--skill and --slug must be unscoped folder names")
    if args.skill == "sora-video" or args.slug == "sora":
        parser.error("Sora is retired; do not republish it")
    if args.version and not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?", args.version):
        parser.error("--version must be semver")
    paths = [REPO / "skills" / args.skill, REPO / "clawhub" / args.skill]
    sources = [p for p in paths if (p / "SKILL.md").is_file()]
    if len(sources) != 1:
        parser.error("Choose exactly one existing source folder containing SKILL.md")
    source = sources[0]
    relative = source.relative_to(REPO).as_posix()
    commit = run(["git", "rev-parse", "HEAD"])
    changed = run(["git", "status", "--porcelain", "--untracked-files=all", "--", relative])
    ignored = run(["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--", relative])
    if changed or ignored:
        raise RuntimeError("The selected skill contains modified, untracked, or ignored files; commit reviewed source first")
    # Never recreate a legacy alias or publish into the logged-in user's namespace.
    listing = json.loads(run(CLI + ["--no-input", "inspect", f"@{OWNER}/{args.slug}",
                                    "--file", "SKILL.md", "--json"]))
    if listing.get("owner", {}).get("handle") != OWNER or listing.get("skill", {}).get("slug") != args.slug:
        raise RuntimeError("The existing listing must resolve to the exact @acedatacloud canonical name")
    remote_content = (listing.get("file") or {}).get("content")
    if not isinstance(remote_content, str):
        raise RuntimeError("Cannot verify the existing listing's SKILL.md identity")
    local_name = manifest_name((source / "SKILL.md").read_text())
    if local_name != manifest_name(remote_content):
        raise RuntimeError("Source and target SKILL.md names differ; refusing to overwrite another skill")
    display_name = listing["skill"].get("displayName")
    if not isinstance(display_name, str) or not display_name.strip():
        raise RuntimeError("Cannot preserve the existing listing's display name")
    command = CLI + ["--no-input", "skill", "publish", str(source),
                     "--owner", OWNER, "--slug", args.slug, "--name", display_name,
                     "--changelog", args.changelog, "--json",
                     "--source-repo", "AceDataCloud/Skills",
                     "--source-commit", commit, "--source-ref", commit,
                     "--source-path", relative]
    if args.version:
        command += ["--version", args.version]
    if not args.publish:
        command += ["--dry-run"]
    else:
        # Validate the current token; the registry enforces publisher membership.
        run(CLI + ["--no-input", "whoami"])
    result = json.loads(run(command))
    if result.get("ok") is not True:
        raise RuntimeError("ClawHub did not confirm success: " + json.dumps(result))
    print(json.dumps({"mode": "publish" if args.publish else "preview",
                      "owner": OWNER, "source": {"repo": "AceDataCloud/Skills",
                      "commit": commit, "path": relative}, "result": result}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
