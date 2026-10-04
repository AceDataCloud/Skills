import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/sync_from_platformbackend.py"
SPEC = importlib.util.spec_from_file_location("sync_from_platformbackend", SCRIPT)
assert SPEC and SPEC.loader
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class SyncFromPlatformBackendTests(unittest.TestCase):
    def test_generates_sidecars_without_touching_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bundle = root / "bundle"
            skills = root / "skills"
            (skills / "ai-chat").mkdir(parents=True)
            skill = skills / "ai-chat/SKILL.md"
            skill.write_text("---\nname: ai-chat\n---\nCurated\n")
            write_json(bundle / "manifest.json", {"source_sha": "a" * 40, "services": ["openai", "claude"]})
            for service in ("openai", "claude"):
                write_json(bundle / f"services/{service}.json", {"service": {"alias": service}, "apis": [{"method": "POST", "path": f"/{service}/chat", "title": "Chat"}], "models": [f"{service}-model"], "artifacts": [{"kind": "skill", "skill": {"slug": "ai-chat"}}, {"kind": "mcp", "id": f"{service}-mcp"}]})
            changed = sync.generate(bundle, skills)
            assert skill.read_text() == "---\nname: ai-chat\n---\nCurated\n"
            assert len(changed) == 2
            sidecar = json.loads((skills / "ai-chat/references/platform.generated.json").read_text())
            assert sidecar["services"] == ["openai", "claude"]
            assert sidecar["source"]["sha"] == "a" * 40
            assert sync.generate(bundle, skills, check=True) == []
    

    def test_missing_skill_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_json(root / "bundle/manifest.json", {"source_sha": "b" * 40, "services": ["suno"]})
            write_json(root / "bundle/services/suno.json", {"service": {"alias": "suno"}, "artifacts": [{"kind": "skill", "skill": {"slug": "missing"}}]})
            with self.assertRaisesRegex(ValueError, "missing skill"):
                sync.generate(root / "bundle", root / "skills")
