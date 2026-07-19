from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "xhs_contract.py"
SPEC = importlib.util.spec_from_file_location("xhs_contract", SCRIPT)
assert SPEC and SPEC.loader
xhs_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(xhs_contract)


def test_validate_image_publish_contract() -> None:
    result = xhs_contract.validate_publish(
        {
            "type": "image",
            "title": "周末城市漫步",
            "content": "一条仅自己可见的验收笔记",
            "media": ["https://cdn.acedata.cloud/xhs/test.png"],
            "tags": ["城市漫步"],
            "visibility": "仅自己可见",
            "is_original": True,
            "schedule_at": "2026-07-20T12:00:00+08:00",
            "now": "2026-07-19T11:00:00+08:00",
        }
    )

    assert result["title_units"] == 6
    assert result["visibility"] == "仅自己可见"
    assert result["schedule_at"] == "2026-07-20T04:00:00+00:00"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"media": []}, "at least one image"),
        ({"media": ["https://example.com/a.png"]}, "Ace Data Cloud CDN"),
        ({"schedule_at": "2026-07-19T11:30:00+08:00"}, "between 1 hour and 14 days"),
        ({"visibility": "好友可见"}, "visibility is unsupported"),
    ],
)
def test_validate_publish_rejects_unsafe_inputs(changes: dict, message: str) -> None:
    payload = {
        "type": "image",
        "title": "验收笔记",
        "content": "body",
        "media": ["https://cdn.acedata.cloud/xhs/test.png"],
        "now": "2026-07-19T11:00:00+08:00",
    }
    payload.update(changes)

    with pytest.raises(xhs_contract.ContractError, match=message):
        xhs_contract.validate_publish(payload)


def test_normalize_search_filters() -> None:
    result = xhs_contract.normalize_filters(
        {"keyword": " 露营 ", "filters": {"sort_by": "最新", "note_type": "图文"}}
    )

    assert result == {
        "keyword": "露营",
        "filters": {
            "sort_by": "最新",
            "note_type": "图文",
            "publish_time": "不限",
            "search_scope": "不限",
            "location": "不限",
        },
    }


def test_parse_feed_snapshot_uses_bounded_card_ranges() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"ref": "r1", "role": "link", "name": "第一篇", "href": "https://www.xiaohongshu.com/explore/abc123"},
            {"ref": "r2", "role": "link", "name": "作者甲", "href": "https://www.xiaohongshu.com/user/profile/user1"},
            {"ref": "r3", "role": "button", "name": "128"},
            {"ref": "r4", "role": "link", "name": "第二篇", "href": "https://www.xiaohongshu.com/explore/def456"},
            {"ref": "r5", "role": "link", "name": "作者乙", "href": "https://www.xiaohongshu.com/user/profile/user2"},
        ],
        "truncated": False,
    }

    result = xhs_contract.parse_feed_snapshot(snapshot)

    assert [item["note_id"] for item in result["notes"]] == ["abc123", "def456"]
    assert result["notes"][0]["author"]["name"] == "作者甲"
    assert result["notes"][0]["visible_engagement"] == ["128"]


def test_parse_feed_snapshot_reports_ambiguous_author() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"ref": "r1", "role": "link", "name": "笔记", "href": "https://www.xiaohongshu.com/explore/abc123"},
            {"ref": "r2", "role": "link", "name": "甲", "href": "https://www.xiaohongshu.com/user/profile/user1"},
            {"ref": "r3", "role": "link", "name": "乙", "href": "https://www.xiaohongshu.com/user/profile/user2"},
        ],
    }

    result = xhs_contract.parse_feed_snapshot(snapshot)

    assert result["notes"][0]["author"] is None
    assert result["notes"][0]["author_state"] == "ambiguous"


def test_parse_feed_snapshot_treats_duplicate_profile_links_as_ambiguous() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"ref": "r1", "role": "link", "name": "笔记", "href": "https://www.xiaohongshu.com/explore/abc123"},
            {"ref": "r2", "role": "link", "name": "作者头像", "href": "https://www.xiaohongshu.com/user/profile/user1"},
            {"ref": "r3", "role": "link", "name": "作者名称", "href": "https://www.xiaohongshu.com/user/profile/user1"},
        ],
    }

    result = xhs_contract.parse_feed_snapshot(snapshot)

    assert result["notes"][0]["author"] is None
    assert result["notes"][0]["author_state"] == "ambiguous"


def test_parse_feed_snapshot_canonicalizes_and_deduplicates_note_urls() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {
                "ref": "r1",
                "role": "link",
                "name": "同一笔记",
                "href": "https://www.xiaohongshu.com/explore/abc123?xsec_token=secret",
            },
            {
                "ref": "r2",
                "role": "link",
                "name": "同一笔记重复链接",
                "href": "https://www.xiaohongshu.com/explore/abc123#comments",
            },
        ],
    }

    result = xhs_contract.parse_feed_snapshot(snapshot)

    assert len(result["notes"]) == 1
    assert result["notes"][0]["url"] == "https://www.xiaohongshu.com/explore/abc123"


def test_parse_feed_snapshot_ignores_non_string_names() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"ref": "bad", "role": "link", "name": {"text": "伪造笔记"}, "href": "https://www.xiaohongshu.com/explore/bad123"},
            {"ref": "good", "role": "link", "name": "真实笔记", "href": "https://www.xiaohongshu.com/explore/good123"},
            {"ref": "metric", "role": "button", "name": 128},
        ],
    }

    result = xhs_contract.parse_feed_snapshot(snapshot)

    assert [item["note_id"] for item in result["notes"]] == ["good123"]
    assert result["notes"][0]["visible_engagement"] == []


def test_sanitized_home_fixture_matches_parser_contract() -> None:
    fixture = Path(__file__).parent / "fixtures" / "home.json"

    result = xhs_contract.parse_feed_snapshot(json.loads(fixture.read_text(encoding="utf-8")))

    assert result == {
        "notes": [
            {
                "note_id": "abc123",
                "title": "周末城市漫步",
                "url": "https://www.xiaohongshu.com/explore/abc123",
                "author": {
                    "user_id": "user123",
                    "name": "示例作者",
                    "url": "https://www.xiaohongshu.com/user/profile/user123",
                },
                "author_state": "available",
                "visible_engagement": ["128"],
            }
        ],
        "truncated": False,
    }


def test_parse_note_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "note.json"
    result = xhs_contract.parse_note_snapshot(
        json.loads(fixture.read_text(encoding="utf-8")),
        "https://www.xiaohongshu.com/explore/abc123?tracking=removed",
    )

    assert result["canonical_url"] == "https://www.xiaohongshu.com/explore/abc123"
    assert result["title"] == "示例笔记"
    assert result["author_state"] == "available"
    assert result["profile_url"] == "https://www.xiaohongshu.com/user/profile/user123"
    assert result["visible_engagement"] == ["赞：128"]
    assert result["comments"] == ["示例评论"]


def test_parse_note_ignores_generic_list_items_before_author() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"role": "heading", "name": "示例笔记"},
            {"role": "listitem", "name": "导航项"},
            {
                "role": "link",
                "name": "示例作者",
                "href": "https://www.xiaohongshu.com/user/profile/user123",
            },
        ],
    }

    result = xhs_contract.parse_note_snapshot(
        snapshot, "https://www.xiaohongshu.com/explore/abc123"
    )

    assert result["author_state"] == "available"
    assert result["comments"] == []


def test_parse_note_refuses_to_guess_between_pre_comment_profiles() -> None:
    snapshot = {
        "origin": "https://www.xiaohongshu.com",
        "nodes": [
            {"role": "heading", "name": "示例笔记"},
            {
                "role": "link",
                "name": "赞过的人",
                "href": "https://www.xiaohongshu.com/user/profile/liker999",
            },
            {
                "role": "link",
                "name": "示例作者",
                "href": "https://www.xiaohongshu.com/user/profile/user123",
            },
        ],
    }

    result = xhs_contract.parse_note_snapshot(
        snapshot, "https://www.xiaohongshu.com/explore/abc123"
    )

    assert result["author"] is None
    assert result["author_state"] == "ambiguous"


def test_parse_profile_fixture() -> None:
    fixture = Path(__file__).parent / "fixtures" / "profile.json"
    result = xhs_contract.parse_profile_snapshot(
        json.loads(fixture.read_text(encoding="utf-8")),
        "https://www.xiaohongshu.com/user/profile/user123?tracking=removed",
    )

    assert result["canonical_url"] == "https://www.xiaohongshu.com/user/profile/user123"
    assert result["display_name"] == "示例作者"
    assert result["visible_metrics"] == ["粉丝 128"]
    assert result["visible_counts"] == ["999", "5678"]
    assert result["notes"] == [
        {"note_id": "abc123", "title": "最近笔记", "url": "https://www.xiaohongshu.com/explore/abc123"}
    ]