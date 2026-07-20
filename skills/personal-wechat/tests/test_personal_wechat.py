from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "personal_wechat.py"
SPEC = importlib.util.spec_from_file_location("personal_wechat_skill_script", SCRIPT)
assert SPEC and SPEC.loader
sys.path.insert(0, str(SCRIPT.parent))
personal_wechat = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(personal_wechat)


def test_wait_task_returns_successful_result() -> None:
    with patch.object(
        personal_wechat,
        "request",
        return_value={"status": "succeeded", "result": {"sent": True}},
    ):
        result = personal_wechat.wait_task("task-1", timeout=0.1)

    assert result == {"sent": True}
