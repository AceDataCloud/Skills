import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read_skill(name):
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def json_examples(text):
    for block in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
        yield json.loads(re.sub(r"^POST /[^\n]+\n", "", block))


class SunoProjectsProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = read_skill("suno-music").split("## Studio Projects (Beta)\n", 1)[1]
        cls.text = cls.text.split("## Auxiliary Endpoints\n", 1)[0]

    def test_examples_use_versioned_project_actions(self):
        examples = {example["action"]: example for example in json_examples(self.text)}
        self.assertEqual(
            set(examples),
            {"create", "retrieve", "save", "upload", "add_track", "replace_section", "commit_candidate", "render"},
        )
        self.assertEqual(examples["save"]["state"], {"tracks": [], "timing": {"bps": 2}})
        self.assertNotIn("version_id", examples["save"])
        for action in ("upload", "add_track", "replace_section", "commit_candidate", "render"):
            with self.subTest(action=action):
                self.assertEqual(examples[action]["version_id"], "CURRENT_VERSION_ID")
        self.assertEqual(examples["replace_section"]["model"], "chirp-v6")
        self.assertLess(examples["replace_section"]["start_seconds"], examples["replace_section"]["end_seconds"])
        self.assertNotIn("start_beats", examples["commit_candidate"])
        self.assertNotIn("end_beats", examples["render"])

    def test_timing_and_upload_result_are_unambiguous(self):
        for requirement in (
            "beats per second",
            "must be positive",
            "120 BPM",
            "not audio-analysis bar positions",
            "source-audio seconds",
            "response.data.candidate.audio_id",
            "preserves playback speed",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)

    def test_generation_and_candidate_recovery_are_version_safe(self):
        for requirement in (
            "render_audio_id",
            "stem_control_tags",
            "1–4 (default 2)",
            "shorter than 26 seconds",
            "Never silently switch models",
            "let the user choose",
            "Save an empty destination track **before** generating",
            "preserves the surrounding clips",
            "leaves the project unchanged",
            "Overlap on the destination track returns 400",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)
        self.assertNotIn("`chirp-v3-0`", self.text)

    def test_render_and_retry_require_terminal_evidence(self):
        for requirement in (
            "Muted tracks/clips are excluded",
            "only those tracks participate",
            "empty or inaudible project",
            "Success requires `finished_at` and `response.success=true`",
            "`response.success=false` indicates failure",
            "including failure, without generating again",
            "first confirm the original task failed, then use a new key",
            "Never resubmit while the original is processing or uncertain",
            "`trace_id`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, self.text)


class ClaudeMessagesProcedureTests(unittest.TestCase):
    def test_native_route_and_extensible_parameters(self):
        text = read_skill("ai-chat")
        for requirement in (
            "/v1/messages/count_tokens",
            "/claude/messages/count_tokens",
            "public alias `/claude/messages`",
            "extension fields unchanged",
            "not enforce a frozen per-model enum",
            "not a closed enum",
            "between_tools",
            "budget_tokens",
            "parameter errors are returned to the caller",
            "generates no model output and consumes no quota",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_native_example_uses_bearer_auth_without_metadata_guidance(self):
        text = read_skill("ai-chat")
        native = text.split("## Native Claude Messages\n", 1)[1].split("## Stateful / Agentic Conversations\n", 1)[0]
        payload = json.loads(re.search(r"-d '(\{.*?\})'", native, re.DOTALL).group(1))
        self.assertNotIn("metadata", payload)
        self.assertNotIn("metadata", payload["messages"][0])
        self.assertNotIn("`metadata`", native)
        self.assertNotIn("metadata.user_id", native)
        self.assertNotIn("example-user-001", native)
        self.assertIn('Authorization: Bearer $ACEDATACLOUD_API_TOKEN', native)
        self.assertTrue({"model", "messages", "max_tokens"}.issubset(payload))
        self.assertEqual(payload["model"], "claude-sonnet-5-5")
        self.assertEqual(payload["thinking"], {"type": "adaptive"})
        self.assertEqual(payload["output_config"], {"effort": "high"})

    def test_beta_display_and_signature_preservation(self):
        text = read_skill("ai-chat")
        self.assertIn("anthropic-beta: thinking-display-updates-2026-08-18", text)
        self.assertIn('thinking.display="updates"', text)
        self.assertIn("not rewritten to `summarized`", text)
        self.assertIn("return complete assistant thinking blocks and signatures unchanged", text)
        self.assertIn("Display settings do not disable thinking", text)


class EmbeddingsProcedureTests(unittest.TestCase):
    def test_example_uses_current_model_and_preserves_migration_boundary(self):
        text = read_skill("ai-chat")
        embeddings = text.split("## OpenAI Embeddings\n", 1)[1].split("## Native Claude Messages\n", 1)[0]
        example, = json_examples(embeddings)
        self.assertEqual(example["model"], "text-embedding-3-small")
        self.assertEqual(example["input"], "Hello!")
        self.assertIn("text-embedding-3-large", embeddings)
        for requirement in (
            "POST /openai/embeddings",
            "public alias `/v1/embeddings`",
            "`text-embedding-ada-002` is retired",
            "Rebuild existing indexes",
            "do not mix vectors from different models",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, embeddings)


class BlogReviewProcedureTests(unittest.TestCase):
    def test_peer_review_and_write_safety(self):
        text = read_skill("acedatacloud")
        blog = text.split("### Blog drafts, peer approval and publication (MCP)\n", 1)[1].split("## Write-operation safety\n", 1)[0]
        for tool in (
            "acedatacloud_create_blog_draft",
            "acedatacloud_get_blog_draft",
            "acedatacloud_approve_blog_post",
            "acedatacloud_withdraw_blog_approval",
            "acedatacloud_publish_blog_post",
            "acedatacloud_unpublish_blog_post",
        ):
            with self.subTest(tool=tool):
                self.assertIn(tool, blog)
        for requirement in (
            "`blog:read` + `blog:publish`",
            "`blog:write` + `blog:publish`",
            "creator cannot approve their own draft",
            "publisher must not be the reviewer",
            "current `review_version`",
            "409",
            "reread the full draft",
            "invalidate approval",
            "Unpublish before editing",
            "`confirm=true`",
            "does not implement blog commands",
            "timezone-aware `publish_at`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, blog)

    def test_current_editorial_categories_and_catalog(self):
        text = read_skill("acedatacloud")
        for category in (
            "product-updates", "tech-sharing", "product-recommendations", "industry-insights",
        ):
            self.assertIn(f"`{category}`", text)
        readme = (ROOT / "README.md").read_text()
        self.assertIn("peer-reviewed blog publishing", readme)
        self.assertIn("embeddings", readme)


class MiniMaxPollingProcedureTests(unittest.TestCase):
    def test_success_failure_and_batch_paths(self):
        text = read_skill("minimax-video")
        for requirement in (
            "`queued` or `running`",
            'Only `task.status="succeeded"` is success',
            "`task.content.url`",
            "`failed` or `cancelled`",
            "`task.error.code` / `task.error.message`",
            "never report a URL as final before success",
            "inspect each item in `items` independently",
            "not to cancel generation",
            "mcp-minimax",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)


class HostedMCPSetupTests(unittest.TestCase):
    def test_client_examples_use_environment_token_not_literal_secret(self):
        text = (ROOT / "skills" / "_shared" / "mcp-servers.md").read_text()
        claude, amp = list(json_examples(text))
        for config, key in ((claude, "mcpServers"), (amp, "amp.mcpServers")):
            self.assertEqual(
                config[key]["suno"]["headers"]["Authorization"],
                "Bearer ${ACEDATACLOUD_API_TOKEN}",
            )
        self.assertEqual(claude["mcpServers"]["suno"]["type"], "http")
        for requirement in (
            "do not replace other services",
            "start the client from that same terminal",
            "saving configuration alone is not proof",
            "amp mcp doctor",
            "amp mcp approve suno",
        ):
            self.assertIn(requirement, text)

    def test_catalog_matches_updated_procedures(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn("edit/render versioned multitrack Studio projects", readme)
        self.assertIn("native Claude Messages", readme)
        self.assertIn("Generate MiniMax-H3 videos (768P/2K)", readme)
        config, = json_examples(readme)
        self.assertEqual(
            config["mcpServers"]["suno"]["headers"]["Authorization"],
            "Bearer ${ACEDATACLOUD_API_TOKEN}",
        )


if __name__ == "__main__":
    unittest.main()
