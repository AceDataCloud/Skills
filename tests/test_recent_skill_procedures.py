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


class ChatGatewayProcedureTests(unittest.TestCase):
    def test_public_model_selection_and_pricing_boundary(self):
        text = read_skill("ai-chat")
        for requirement in (
            "`gpt-5.6-sol-fast`",
            "exact public model ID on Chat Completions, Responses, Messages",
            "either conversation endpoint",
            "no public model introduction",
            "catalog visibility does not guarantee access",
            "`prompt_tokens` exceeds 272,000 (not at exactly 272,000)",
            "Do not silently substitute `gpt-5.6-sol`",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_aliases_and_dify_append_only_the_endpoint_suffix(self):
        text = read_skill("ai-chat")
        for route in ("/v1/chat/completions", "/v1/responses", "/v1/embeddings"):
            with self.subTest(route=route):
                self.assertIn(f"public alias `{route}`", text)
        dify = text.split("### Dify: OpenAI-API-compatible provider\n", 1)[1].split("## Currently Documented Model Families\n", 1)[0]
        for requirement in (
            "**Base URL** to `https://api.acedata.cloud/v1`",
            "**model** to `gpt-5.5`",
            "**conversation type** Chat",
            "**API type** Chat Completions",
            "Dify appends `/chat/completions` itself",
            "do not use `/openai/v1`",
            "Test the connection",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, dify)
        self.assertIn('base_url="https://api.acedata.cloud/openai"', text)
        self.assertNotIn("not `/v1/*`", text)


class AgentTaskProcedureTests(unittest.TestCase):
    def test_turn_limit_is_per_request_not_history(self):
        text = read_skill("ai-chat")
        for requirement in (
            "Agent iterations per request: 1–500, default 500",
            "not retained history",
            "Each iteration is a model call",
            "`max_turns: 1` requests a single answer without tool calls",
            "not a guarantee that all will run",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("Trim retained turn history", text)

    def test_scheduled_examples_use_action_payloads_and_bounded_template(self):
        text = read_skill("ai-chat").split("## Scheduled Agent Tasks\n", 1)[1].split("## Gotchas\n", 1)[0]
        examples = {example["action"]: example for example in json_examples(text)}
        self.assertEqual(set(examples), {"create", "retrieve_runs", "update"})
        create = examples["create"]
        self.assertEqual(create["schedule"], {"type": "cron", "cron": "0 9 * * *", "tz": "UTC"})
        self.assertGreaterEqual(create["template"]["max_turns"], 1)
        self.assertLessEqual(create["template"]["max_turns"], 500)
        self.assertNotIn("max_turns", create)
        self.assertIn("Do not publish or send messages", create["template"]["question"])
        self.assertEqual(examples["retrieve_runs"]["id"], "TASK_ID")
        self.assertEqual(examples["update"], {"action": "update", "id": "TASK_ID", "state": "disabled"})
        for requirement in (
            "same service Bearer token",
            "not a platform-management-token endpoint",
            "`template.max_turns` is 1–500, default 500",
            "not schedule frequency",
            "preview locally and obtain confirmation",
            "scheduling is not blanket permission",
            "three months after creation",
            "at most 15 minutes",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)

    def test_run_failure_and_handoff_failure_are_distinct(self):
        text = read_skill("ai-chat")
        for requirement in (
            "not evidence of a successful run",
            "AI execution failures **do not auto-pause**",
            "five consecutive handoff failures",
            "not five failed AI runs",
            "`status`, `error_code` and `conversation_id`",
            "`awaiting_user_input`",
            "explicitly pause recurring failures",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("/internal/scheduled-task", text)
        self.assertIn("scheduled agent tasks", (ROOT / "README.md").read_text())


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
        blog = text.split("### Blog drafts, review submission and publication (MCP / REST)\n", 1)[1].split("## Write-operation safety\n", 1)[0]
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

    def test_submission_rejection_and_pending_edit_boundaries(self):
        text = read_skill("acedatacloud")
        for requirement in (
            "current `review_version` and `review_status`",
            "Submit a `draft` or `rejected` article",
            "POST /api/v1/blogs/admin/{id}/submit/",
            '{"expected_version": CURRENT_REVIEW_VERSION}',
            'verify `review_status="pending"`',
            "Pending articles cannot be edited",
            "`DELETE` to the same `/submit/` route",
            "Withdrawal of a pending review is distinct",
            "POST /api/v1/blogs/admin/{id}/approval/",
            "POST /api/v1/blogs/admin/{id}/reject/",
            "nonblank `comment` (at most 2,000 characters)",
            'verify `review_status="rejected"`',
            "Read `review_comment`, revise and resubmit",
            'Only after `review_status="approved"`',
            "409 on submission, withdrawal, approval or rejection",
            "REST review routes above execute immediately and have no dry-run flag",
            "obtain confirmation before sending",
            "do not invent submission/rejection tool names or CLI flags",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertNotIn("acedatacloud_submit_blog", text)
        self.assertNotIn("acedatacloud_reject_blog", text)

    def test_video_drafts_keep_validation_and_review_boundaries(self):
        text = read_skill("acedatacloud")
        for requirement in (
            'Default `content_type="article"` requires a nonblank body and clears `video_url`',
            'For `content_type="video"`',
            "actual HTTPS `video_url`",
            "body may be blank, but title and summary remain required",
            "Never fabricate a media URL",
            "nonblank `cover_alt`",
            "MCP schema lacks video fields",
            "POST /api/v1/blogs/admin/",
            "PATCH /api/v1/blogs/admin/{id}/",
            "watch the actual video",
            "`content_type` or `video_url`) invalidate approval",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, text)
        self.assertIn("article/video drafts and review threads", (ROOT / "README.md").read_text())

    def test_private_threads_use_saved_utf16_anchors_and_root_ids(self):
        text = read_skill("acedatacloud")
        threads = text.split("#### Review threads (authenticated REST)\n", 1)[1].split("All blog writes", 1)[0]
        for requirement in (
            "private editorial feedback, not public blog comments",
            "platform Bearer token",
            "`blog:read` plus either `blog:write` or `blog:publish`",
            "GET /api/v1/blogs/admin/{id}/comments/",
            "POST /api/v1/blogs/admin/{id}/comments/",
            "current `expected_version`",
            'field="overall"` with no offsets or quote',
            'field="title"`, `"summary"` or `"content"`',
            "**UTF-16 code units**",
            "not Python characters or UTF-8 bytes",
            "start is inclusive, end exclusive",
            "at most 2,000 code units",
            "Never anchor to unsaved text",
            "On 409, refresh the draft and recompute",
            "POST /api/v1/blogs/admin/{id}/comments/{comment_id}/replies/",
            "root ID, not a reply ID",
            "replying to a resolved thread reopens it",
            "PATCH /api/v1/blogs/admin/{id}/comments/{comment_id}/",
            '{"resolved":true}',
            '{"resolved":false}',
            "resolution do not require `expected_version`",
            "does not approve or publish",
            "After preview and confirmation",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, threads)

    def test_rejection_can_use_only_current_unresolved_root_feedback(self):
        text = read_skill("acedatacloud")
        self.assertIn("omit `comment` if an unresolved root review thread already exists on the current version", text)
        self.assertIn("Read `review_comment`, revise and resubmit", text)
        self.assertIn("historical feedback does not prove a selection still matches", text)

    def test_current_editorial_categories_and_catalog(self):
        text = read_skill("acedatacloud")
        for category in (
            "product-updates", "tech-sharing", "product-recommendations", "industry-insights",
        ):
            self.assertIn(f"`{category}`", text)
        readme = (ROOT / "README.md").read_text()
        self.assertIn("submitted, peer-reviewed blog publishing via MCP / REST", readme)
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
