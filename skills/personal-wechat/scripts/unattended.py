"""Unattended scheduled-task confirmation guard bundled with this Skill."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterable


def unattended_confirm_allowed(skill_slugs: Iterable[str]) -> tuple[bool, str]:
    """Return whether the active Skill is pre-authorized for unattended writes."""

    if os.environ.get("AICHAT_UNATTENDED_MODE") != "true":
        return False, "not running in AceDataCloud unattended scheduled-task mode"

    active_skill = os.environ.get("AICHAT_ACTIVE_SKILL", "")
    allowed_skill_slugs = set(skill_slugs)
    if active_skill not in allowed_skill_slugs:
        return False, f"active skill {active_skill or '<empty>'!r} is not one of {sorted(allowed_skill_slugs)!r}"

    raw_allowed = os.environ.get("AICHAT_UNATTENDED_ALLOWED_SKILLS", "[]")
    try:
        allowed = json.loads(raw_allowed)
    except json.JSONDecodeError:
        return False, "AICHAT_UNATTENDED_ALLOWED_SKILLS is not valid JSON"
    if not isinstance(allowed, list) or active_skill not in allowed:
        return False, f"skill {active_skill!r} is not pre-authorized for unattended confirmation"

    expires_raw = os.environ.get("AICHAT_UNATTENDED_EXPIRES_AT", "")
    if expires_raw:
        try:
            expires_at = int(expires_raw)
        except ValueError:
            return False, "AICHAT_UNATTENDED_EXPIRES_AT is invalid"
        if expires_at < int(time.time()):
            return False, "unattended authorization has expired"

    return True, "ok"