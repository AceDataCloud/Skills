from __future__ import annotations

import importlib.util
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "skills" / "bilibili" / "scripts" / "bilibili.py"
SPEC = importlib.util.spec_from_file_location("bilibili_skill", SCRIPT)
assert SPEC and SPEC.loader
bili = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bili)

JAR = [{"name": "bili_jct", "value": "csrf-token", "domain": ".bilibili.com"},
       {"name": "SESSDATA", "value": "sess", "domain": ".bilibili.com"}]

DRAFT_AID = 373282
ARTICLE_ID = 51827685


def args(**kw) -> SimpleNamespace:
    base = dict(title="T", content="<p>hi</p>", content_file=None, draft_only=False,
                category=None, no_rehost_images=True)
    base.update(kw)
    return SimpleNamespace(**base)


class Recorder:
    """Stands in for bilibili.request, capturing the form each call posted."""

    def __init__(self, submit_data=None, draft_code=0):
        self.calls: list[tuple[str, dict]] = []
        self.submit_data = submit_data if submit_data is not None else {
            "aid": ARTICLE_ID, "state": -2,
        }
        self.draft_code = draft_code

    def __call__(self, method, url, jar, referer=None, form=None):
        self.calls.append((url, form or {}))
        if url.endswith("draft/addupdate"):
            if self.draft_code:
                return 200, json.dumps({"code": self.draft_code, "message": "分类错误"})
            return 200, json.dumps({"code": 0, "data": {"aid": DRAFT_AID}})
        if url.endswith("article/submit"):
            return 200, json.dumps({"code": 0, "data": self.submit_data})
        raise AssertionError(f"unexpected url {url}")

    def form_for(self, suffix: str) -> dict:
        for url, form in self.calls:
            if url.endswith(suffix):
                return form
        raise AssertionError(f"no call to {suffix}")


def publish(monkey_request, publish_args) -> dict:
    original_request, original_confirm = bili.request, bili.CONFIRM
    bili.request, bili.CONFIRM = monkey_request, True
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            bili.cmd_publish(JAR, publish_args)
        return json.loads(buf.getvalue())
    finally:
        bili.request, bili.CONFIRM = original_request, original_confirm


class PublishIdTest(unittest.TestCase):
    def test_url_uses_submit_article_id_not_draft_aid(self):
        # The published article gets a NEW id; cv<draft_aid> 404s.
        rec = Recorder()
        res = publish(rec, args())
        self.assertEqual(res["id"], str(ARTICLE_ID))
        self.assertEqual(res["url"], f"https://www.bilibili.com/read/cv{ARTICLE_ID}")
        self.assertEqual(res["draft_aid"], str(DRAFT_AID))
        self.assertNotIn(str(DRAFT_AID), res["url"])

    def test_pending_review_state_is_surfaced(self):
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": -2}), args())
        self.assertTrue(res["pending_review"])
        self.assertEqual(res["state"], -2)
        self.assertTrue(res["ok"])

    def test_approved_state_has_no_pending_flag(self):
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": 0}), args())
        self.assertNotIn("pending_review", res)
        self.assertTrue(res["ok"])

    def test_rejected_state_is_not_reported_as_pending(self):
        # -1 未通过 will NEVER go live; calling it "pending" makes the agent
        # record a permanently-404 URL as delivered.
        for state in (-1, -3, -4):
            res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": state}),
                          args())
            self.assertNotIn("pending_review", res, f"state {state}")
            self.assertFalse(res["ok"], f"state {state}")
            self.assertFalse(res["published"], f"state {state}")
            self.assertEqual(res["state_desc"], bili._STATES[state])

    def test_non_int_state_does_not_crash_after_the_write(self):
        # The article is already submitted here — a TypeError would destroy the
        # only copy of the returned id.
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": "-2"}), args())
        self.assertEqual(res["id"], str(ARTICLE_ID))

    def test_coercible_string_state_still_warns(self):
        # "-2" must not silently downgrade to "fully published".
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": "-2"}), args())
        self.assertTrue(res["pending_review"])
        self.assertEqual(res["state"], -2)

    def test_unreadable_state_is_flagged_not_swallowed(self):
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": "weird"}),
                      args())
        self.assertTrue(res["state_unknown"])
        self.assertIn("unreadable state", res["note"])
        self.assertNotIn("state", res)

    def test_state_one_is_live_not_abnormal(self):
        # _STATES maps both 0 and 1 to 已发布.
        res = publish(Recorder(submit_data={"aid": ARTICLE_ID, "state": 1}), args())
        self.assertTrue(res["ok"])
        self.assertNotIn("pending_review", res)
        self.assertEqual(res["state_desc"], "已发布")

    def test_missing_article_id_yields_no_url_at_all(self):
        # Falling back to a draft-aid URL is the exact 404 bug being fixed.
        for data in ({}, {"aid": 0}, {"aid": None}, {"aid": "not-a-number"}):
            res = publish(Recorder(submit_data=data), args())
            self.assertTrue(res["id_unverified"], data)
            self.assertIsNone(res["url"], data)
            self.assertIsNone(res["id"], data)
            self.assertNotIn(str(DRAFT_AID), json.dumps(res.get("url") or ""), data)

    def test_unverified_id_warning_survives_pending_review(self):
        # Ground truth: submit always returns -2, so this pairing is the norm.
        res = publish(Recorder(submit_data={"state": -2}), args())
        self.assertTrue(res["id_unverified"])
        self.assertTrue(res["pending_review"])
        self.assertIn("no shareable URL", res["note"])
        self.assertIn("review queue", res["note"])

    def test_publish_reports_the_category_it_used(self):
        res = publish(Recorder(), args())
        self.assertEqual(res["category_id"], "26")
        self.assertEqual(res["category"], "数码")


class CategoryTest(unittest.TestCase):
    def test_category_field_is_sent_not_just_tid(self):
        # A hardcoded category=0 silently lands every article in 生活.
        rec = Recorder()
        publish(rec, args(category="数码"))
        for suffix in ("draft/addupdate", "article/submit"):
            form = rec.form_for(suffix)
            self.assertEqual(form["category"], "26", suffix)
            self.assertEqual(form["tid"], "26", suffix)

    def test_default_category_is_shuma(self):
        rec = Recorder()
        publish(rec, args())
        self.assertEqual(rec.form_for("draft/addupdate")["category"], "26")

    def test_explicit_category_does_not_fall_back(self):
        # -17 on an explicit choice must fail, not silently pick another 分类.
        rec = Recorder(draft_code=-17)
        original_request, original_confirm = bili.request, bili.CONFIRM
        bili.request, bili.CONFIRM = rec, True
        try:
            buf = io.StringIO()
            with redirect_stdout(buf), self.assertRaises(SystemExit):
                bili.cmd_publish(JAR, args(category="数码"))
        finally:
            bili.request, bili.CONFIRM = original_request, original_confirm
        self.assertEqual(len(rec.calls), 1)

    def test_unknown_category_name_is_rejected(self):
        buf = io.StringIO()
        original_confirm = bili.CONFIRM
        bili.CONFIRM = True
        try:
            with redirect_stdout(buf), self.assertRaises(SystemExit):
                bili.cmd_publish(JAR, args(category="不存在的分类"))
        finally:
            bili.CONFIRM = original_confirm
        self.assertIn("unknown --category", json.loads(buf.getvalue())["error"])

    def test_bad_category_is_caught_in_the_dry_run(self):
        # Must fail in the preview, not after --confirm has uploaded images.
        buf = io.StringIO()
        original_confirm = bili.CONFIRM
        bili.CONFIRM = False
        try:
            with redirect_stdout(buf), self.assertRaises(SystemExit):
                bili.cmd_publish(JAR, args(category="不存在的分类"))
        finally:
            bili.CONFIRM = original_confirm
        self.assertIn("unknown --category", json.loads(buf.getvalue())["error"])

    def test_bad_category_aborts_before_image_upload(self):
        uploads = []
        original = bili.rehost_images
        bili.rehost_images = lambda *a, **k: uploads.append(1) or ""
        original_confirm, bili.CONFIRM = bili.CONFIRM, True
        try:
            buf = io.StringIO()
            with redirect_stdout(buf), self.assertRaises(SystemExit):
                bili.cmd_publish(JAR, args(category="不存在的分类",
                                           no_rehost_images=False))
        finally:
            bili.rehost_images, bili.CONFIRM = original, original_confirm
        self.assertEqual(uploads, [])

    def test_numeric_category_passes_through(self):
        rec = Recorder()
        publish(rec, args(category="34"))
        self.assertEqual(rec.form_for("draft/addupdate")["category"], "34")

    def test_all_category_ids_are_subcategories(self):
        # Parent ids (e.g. 17 科技) are rejected by submit.
        parents = {"1", "2", "3", "16", "17", "28", "29", "41", "43"}
        self.assertFalse(parents & set(bili._CATEGORIES.values()))
        self.assertFalse(parents & set(bili._TID_CANDIDATES))


class StatusTest(unittest.TestCase):
    # Live-verified: the creative list puts `artlist` at the TOP level.
    ENVELOPE = {
        "code": 0, "message": "OK",
        "artlist": {"articles": [
            {"id": 51827685, "title": "pending one", "state": -2, "reason": "",
             "category": {"id": 26, "name": "数码"}},
            {"id": 51826510, "title": "live one", "state": 0, "reason": "",
             "category": {"id": 15, "name": "生活"}},
            {"id": 51820000, "title": "rejected one", "state": -1,
             "reason": "含违规内容", "category": {"id": 26, "name": "数码"}},
        ]},
    }

    def run_status(self, envelope, limit=10) -> dict:
        original = bili.get_json
        bili.get_json = lambda *a, **k: envelope
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                bili.cmd_status(JAR, SimpleNamespace(limit=limit))
            return json.loads(buf.getvalue())
        finally:
            bili.get_json = original

    def test_parses_top_level_artlist(self):
        res = self.run_status(self.ENVELOPE)
        self.assertEqual(res["count"], 3)
        self.assertEqual(res["articles"][0]["title"], "pending one")

    def test_live_flag_and_state_desc(self):
        rows = self.run_status(self.ENVELOPE)["articles"]
        self.assertEqual([r["live"] for r in rows], [False, True, False])
        self.assertEqual([r["state_desc"] for r in rows],
                         ["待审核", "已发布", "未通过"])
        self.assertEqual(rows[2]["reason"], "含违规内容")

    def test_no_cvnone_url_when_id_missing(self):
        res = self.run_status({"artlist": {"articles": [
            {"title": "no id yet", "state": -2}]}})
        row = res["articles"][0]
        self.assertIsNone(row["url"])
        self.assertIsNone(row["id"])

    def test_no_literal_none_state_desc(self):
        row = self.run_status({"artlist": {"articles": [
            {"id": 51, "title": "no state"}]}})["articles"][0]
        self.assertIsNone(row["state_desc"])
        self.assertFalse(row["live"])

    def test_limit_is_respected(self):
        self.assertEqual(self.run_status(self.ENVELOPE, limit=2)["count"], 2)

    def test_api_error_exits(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
            self.run_status({"code": -101, "message": "账号未登录"})


class CategoriesCommandTest(unittest.TestCase):
    def run_categories(self) -> dict:
        buf = io.StringIO()
        with redirect_stdout(buf):
            bili.cmd_categories(JAR, SimpleNamespace())
        return json.loads(buf.getvalue())

    def test_every_accepted_name_is_listed(self):
        # De-duping by id used to hide aliases like 生活 and 科技, so an agent
        # reading this output would think they were unavailable.
        listed = {n for c in self.run_categories()["categories"] for n in c["names"]}
        self.assertEqual(listed, set(bili._CATEGORIES))

    def test_ids_match_the_lookup_table(self):
        for cat in self.run_categories()["categories"]:
            for name in cat["names"]:
                self.assertEqual(bili._CATEGORIES[name], cat["id"])


class DryRunTest(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        rec = Recorder()
        original_request, original_confirm = bili.request, bili.CONFIRM
        bili.request, bili.CONFIRM = rec, False
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                bili.cmd_publish(JAR, args())
            res = json.loads(buf.getvalue())
        finally:
            bili.request, bili.CONFIRM = original_request, original_confirm
        self.assertTrue(res["dry_run"])
        self.assertEqual(rec.calls, [])

    def test_dry_run_echoes_the_category_name_the_user_typed(self):
        # "26" is not checkable by a human against the 分类 they asked for.
        original_confirm, bili.CONFIRM = bili.CONFIRM, False
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                bili.cmd_publish(JAR, args(category="数码"))
            self.assertEqual(json.loads(buf.getvalue())["category"], "数码")
        finally:
            bili.CONFIRM = original_confirm


class MarkdownTest(unittest.TestCase):
    def test_code_block_renders_to_pre_code(self):
        html = bili.md_to_html('# T\n\n```json\n{"a": 1}\n```\n')
        self.assertIn("<pre><code>", html)
        self.assertIn("&quot;a&quot;", html)


if __name__ == "__main__":
    unittest.main()
