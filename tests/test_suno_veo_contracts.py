from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1] / "skills"


class SunoVeoContractTests(unittest.TestCase):
    def test_discord_documents_proxy_health_and_idempotent_send(self) -> None:
        content = (ROOT / "discord" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`/health` and `/readyz` require no token", content)
        self.assertIn('{"status":"ready","gateway_ready":true}', content)
        self.assertIn("`Idempotency-Key`", content)
        self.assertIn("`POST /api/dms/send`", content)

    def test_telegram_documents_proxy_health_and_supported_operations(self) -> None:
        content = (ROOT / "telegram" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`/health` and `/readyz` are unauthenticated", content)
        self.assertIn("`login_state:\"authenticated\"`", content)
        self.assertIn("`POST /api/auth/qr`", content)
        self.assertIn("$BASE/api/chats/$TARGET/read", content)

    def test_suno_documents_current_conversion_and_constraints(self) -> None:
        content = (ROOT / "suno-music" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`/suno/mp3`", content)
        self.assertIn("| `lyric_prompt` | string |", content)
        self.assertIn("`weirdness` | number (0–1)", content)
        self.assertIn("`style_influence` | number (0–1)", content)
        self.assertIn("`audio_weight` | number (0–1)", content)
        self.assertIn("`vocal_start` (≥ 0), and `vocal_end` (> 0)", content)

    def test_veo_task_retrieval_has_required_action(self) -> None:
        content = (ROOT / "veo-video" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('{"action": "retrieve", "id": "..."}', content)
        self.assertIn('{"action": "retrieve", "id": "<task_id from above>"}', content)
        self.assertIn('action: "retrieve_batch"', content)
        self.assertIn('action: "list"', content)


if __name__ == "__main__":
    unittest.main()
