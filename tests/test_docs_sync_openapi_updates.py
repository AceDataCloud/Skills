from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


def skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text()


class DocsSyncOpenApiUpdateTests(unittest.TestCase):
    def test_producer_numeric_controls_do_not_claim_defaults(self) -> None:
        body = skill("producer-music")

        self.assertIn("| `lyrics_strength` | number (0-1) | Lyrics adherence |", body)
        self.assertIn("| `sound_strength` | number (0.2-1) | Sound quality weight |", body)
        self.assertIn("| `weirdness` | number (0-1) | Creative randomness |", body)
        self.assertNotIn("Lyrics adherence (default:", body)
        self.assertNotIn("Sound quality weight (default:", body)
        self.assertNotIn("Creative randomness (default:", body)

    def test_shorturl_content_is_required_uri_string(self) -> None:
        body = skill("short-url")

        self.assertIn("| `content` | Yes | URI string", body)
        self.assertIn("valid URI string", body)

    def test_tiktok_user_lookup_accepts_unique_id_or_user_id(self) -> None:
        body = skill("tiktok")

        self.assertIn("POST https://api.acedata.cloud/tiktok/user", body)
        self.assertIn("either `unique_id` or `user_id`", body)
        self.assertIn("do not send an empty identifier", body)

    def test_x_retweets_uses_note_id_not_post_id(self) -> None:
        body = skill("x")

        self.assertIn("POST https://api.acedata.cloud/x/retweets", body)
        self.assertIn("`note_id`", body)
        self.assertIn("not the older `post_id`", body)


if __name__ == "__main__":
    unittest.main()
