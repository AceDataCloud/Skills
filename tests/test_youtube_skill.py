import unittest
from pathlib import Path


SKILL = Path(__file__).parents[1] / "skills" / "youtube" / "SKILL.md"


def body() -> str:
    return SKILL.read_text()


class YouTubeSkillContractTests(unittest.TestCase):
    def test_publish_artifact_remains_available_after_skill_load(self) -> None:
        self.assertIn("allowed_tools: [Bash, publish_artifact]", body())

    def test_upload_metadata_is_built_with_jq_arguments(self) -> None:
        text = body()
        self.assertIn('META=$(jq -n --arg title "$TITLE" --arg description "$DESC"', text)
        self.assertNotIn("read -r -d '' META", text)

    def test_resumable_init_preserves_diagnostics_and_guards_put(self) -> None:
        text = body()
        self.assertIn('INIT_HEADERS=$(mktemp)', text)
        self.assertIn('INIT_BODY=$(mktemp)', text)
        self.assertIn("-w '%{http_code}'", text)
        self.assertIn('tolower($1) == "location:"', text)
        self.assertIn('if [ -z "$UPLOAD_URL" ]; then', text)
        self.assertIn('upload init failed: HTTP $INIT_HTTP', text)
        self.assertLess(
            text.index('if [ -z "$UPLOAD_URL" ]; then'),
            text.index('-X PUT --upload-file "$FILE" "$UPLOAD_URL"'),
        )

    def test_success_records_only_a_real_youtube_url(self) -> None:
        text = body()
        self.assertIn("call `publish_artifact` exactly", text)
        self.assertIn('`channel="youtube"`', text)
        self.assertIn("https://www.youtube.com/watch?v=<id>", text)
        self.assertIn("never fabricate a URL", text)

    def test_upload_example_defaults_to_unlisted(self) -> None:
        self.assertIn('privacyStatus: "unlisted"', body())


if __name__ == "__main__":
    unittest.main()
