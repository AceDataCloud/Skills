#!/usr/bin/env python3
"""Generate machine-owned Skill references from a PlatformBackend bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def skill_targets(bundle: Path) -> dict[str, list[dict[str, Any]]]:
    manifest = load_json(bundle / "manifest.json")
    result: dict[str, list[dict[str, Any]]] = {}
    for service in manifest["services"]:
        contract = load_json(bundle / f"services/{service}.json")
        slugs = {
            artifact.get("skill", {}).get("slug")
            for artifact in contract.get("artifacts", [])
            if artifact.get("kind") == "skill"
        }
        group_skill = contract.get("targets", {}).get("skill")
        if group_skill:
            slugs.add(group_skill)
        for slug in sorted(value for value in slugs if value):
            result.setdefault(slug, []).append(contract)
    return result


def render_json(source_sha: str, contracts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source": {"repository": "AceDataCloud/PlatformBackend", "sha": source_sha},
        "services": [contract["service"]["alias"] for contract in contracts],
        "models": sorted({model for contract in contracts for model in contract.get("models", [])}),
        "apis": [api for contract in contracts for api in contract.get("apis", [])],
        "companions": [artifact for contract in contracts for artifact in contract.get("artifacts", []) if artifact.get("kind") == "mcp"],
    }


def render_markdown(value: dict[str, Any]) -> str:
    lines = [
        "<!-- Generated from PlatformBackend. Do not edit manually. -->",
        "# Platform contract",
        "",
        f"Source: `AceDataCloud/PlatformBackend@{value['source']['sha']}`",
        "",
        "## Services",
        "",
        *[f"- `{service}`" for service in value["services"]],
        "",
        "## Endpoints",
        "",
        *[f"- `{api.get('method', 'POST')}` `{api.get('path', '')}` — {api.get('title') or api.get('name', '')}" for api in value["apis"]],
        "",
    ]
    if value["models"]:
        lines.extend(["## Models", "", *[f"- `{model}`" for model in value["models"]], ""])
    return "\n".join(lines)


def generate(bundle: Path, skills_dir: Path, check: bool = False) -> list[str]:
    manifest = load_json(bundle / "manifest.json")
    targets = skill_targets(bundle)
    changed: list[str] = []
    for slug, contracts in sorted(targets.items()):
        skill_dir = skills_dir / slug
        if not (skill_dir / "SKILL.md").is_file():
            raise ValueError(f"PlatformBackend maps to missing skill: {slug}")
        value = render_json(manifest["source_sha"], contracts)
        outputs = {
            skill_dir / "references/platform.generated.json": json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            skill_dir / "references/platform.generated.md": render_markdown(value),
        }
        for path, content in outputs.items():
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current == content:
                continue
            changed.append(str(path.relative_to(skills_dir.parent)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if check and changed:
        raise RuntimeError(f"generated Skill references are stale: {', '.join(changed)}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--skills-dir", type=Path, default=Path(__file__).parents[1] / "skills")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(generate(args.bundle, args.skills_dir, args.check)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
