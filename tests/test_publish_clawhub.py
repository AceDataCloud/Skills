import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("publish_clawhub", Path(__file__).resolve().parents[1] / "scripts/publish_clawhub.py")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


class PublishClawHubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        source = self.repo / "skills/suno-music"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("---\nname: suno-music\n---\n")
        self.calls = []
        self.owner, self.slug = "acedatacloud", "suno"
        self.dirty, self.ignored = "", ""
        self.publish_error = False
        self.result = {"ok": True, "status": "unchanged", "version": "1.0.1"}

    def fake_run(self, args, **kwargs):
        self.calls.append(args)
        if args[:2] == ["git", "rev-parse"]:
            return "a" * 40
        if args[:2] == ["git", "status"]:
            return self.dirty
        if args[:2] == ["git", "ls-files"]:
            return self.ignored
        if "inspect" in args:
            return json.dumps({"owner": {"handle": self.owner}, "skill": {"slug": self.slug}})
        if "whoami" in args:
            return "Germey"
        if "publish" in args:
            if self.publish_error:
                raise RuntimeError("Rate limit exceeded")
            return json.dumps(self.result)
        self.fail(f"Unexpected command: {args}")

    def invoke(self, extra=()):
        with patch.object(publisher, "REPO", self.repo), patch.object(publisher, "run", self.fake_run), contextlib.redirect_stdout(io.StringIO()) as output:
            publisher.main(["--skill", "suno-music", "--slug", "suno", "--changelog", "Reviewed notes", *extra])
            return json.loads(output.getvalue())

    def test_default_previews_one_existing_listing_and_pins_source(self):
        result = self.invoke()
        upload = next(c for c in self.calls if "publish" in c)
        self.assertIn("--dry-run", upload)
        self.assertEqual(upload[upload.index("--owner") + 1], "acedatacloud")
        self.assertEqual(upload[upload.index("--source-commit") + 1], "a" * 40)
        self.assertEqual(upload[upload.index("--source-path") + 1], "skills/suno-music")
        self.assertFalse(any("whoami" in c for c in self.calls))
        self.assertEqual(result["mode"], "preview")

    def test_wrong_owner_and_legacy_alias_stop_before_publish(self):
        for owner, slug in [("Germey", "suno"), ("acedatacloud", "acedatacloud-suno-music")]:
            self.calls.clear()
            self.owner, self.slug = owner, slug
            with self.assertRaisesRegex(RuntimeError, "canonical"):
                self.invoke()
            self.assertFalse(any("publish" in c for c in self.calls))

    def test_dirty_or_ignored_source_cannot_claim_commit_pin(self):
        for dirty, ignored in [(" M skills/suno-music/SKILL.md", ""), ("", "skills/suno-music/.env")]:
            self.calls.clear()
            self.dirty, self.ignored = dirty, ignored
            with self.assertRaisesRegex(RuntimeError, "commit reviewed"):
                self.invoke()
            self.assertFalse(any("inspect" in c or "publish" in c for c in self.calls))

    def test_explicit_publish_checks_token_and_preserves_version(self):
        self.invoke(["--publish", "--version", "1.0.2"])
        upload = next(c for c in self.calls if "publish" in c)
        self.assertNotIn("--dry-run", upload)
        self.assertEqual(upload[upload.index("--version") + 1], "1.0.2")
        self.assertTrue(any("whoami" in c for c in self.calls))

    def test_failed_publish_is_not_reported_as_success_or_retried(self):
        self.publish_error = True
        with self.assertRaisesRegex(RuntimeError, "Rate limit"):
            self.invoke(["--publish"])
        self.assertEqual(sum("publish" in c for c in self.calls), 1)

    def test_false_ok_is_a_failure(self):
        self.result = {"ok": False}
        with self.assertRaisesRegex(RuntimeError, "confirm success"):
            self.invoke()

    def test_retired_sora_is_rejected_before_any_command(self):
        with patch.object(publisher, "run", self.fake_run), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            publisher.main(["--skill", "sora-video", "--slug", "sora", "--changelog", "notes"])
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
