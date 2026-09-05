from pathlib import Path


ROOT = Path(__file__).parents[1]


def read_skill(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_fish_tts_documents_latest_reference_shapes() -> None:
    skill = read_skill("fish-audio")

    assert "`reference_id` | string \\| string[]" in skill
    assert "exactly one object with `audio`" in skill
    assert "Do not send `reference_id` and `references` together." in skill
    assert "not Base64, data URIs, MessagePack, local files, or credentialed URLs" in skill


def test_suno_upload_documents_enhanced_mode_and_mp3_endpoint() -> None:
    skill = read_skill("suno-music")

    assert "| `/suno/mp3` | POST | Retrieve/export MP3 audio for a song |" in skill
    assert '| `mode` | `"standard"` \\| `"enhanced"` |' in skill
    assert "| `name` | string | Required for `enhanced`; 1-100 characters |" in skill
    assert "returns `task_id`/`trace_id`" in skill


def test_ai_chat_includes_latest_claude_fable_model() -> None:
    assert "`claude-fable-5-1`" in read_skill("ai-chat")
