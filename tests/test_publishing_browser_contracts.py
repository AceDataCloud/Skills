"""Validate executable browser policy against the runtime facade contract.

This does not certify third-party editor behavior or live publication.
"""
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'jianshu': 'https://www.jianshu.com', 'douyin': 'https://creator.douyin.com', 'netease': 'https://mp.163.com', 'tencentcloud-community': 'https://cloud.tencent.com', 'aliyun-community': 'https://developer.aliyun.com', 'sohu': 'https://mp.sohu.com', 'sspai': 'https://sspai.com', 'infoq': 'https://xie.infoq.cn', 'huaweicloud-blog': 'https://bbs.huaweicloud.com', 'douban': 'https://www.douban.com', 'volcengine-community': 'https://developer.volcengine.com', 'modelscope': 'https://modelscope.cn'}


class PublishingBrowserContractTests(unittest.TestCase):
    def test_browser_skills_project_only_supported_facades(self):
        manifest = json.loads((ROOT / "skills/xiaohongshu/contracts/browser-manifest.compact.json").read_text())
        for slug, origin in EXPECTED.items():
            with self.subTest(slug=slug):
                file = ROOT / "skills" / slug / "SKILL.md"
                data = yaml.safe_load(file.read_text().split("---\n")[1])
                self.assertEqual(data["name"], slug)
                self.assertEqual(data["connections"], [slug])
                browser = data["execution"]["browser"]
                self.assertEqual(browser["provider"], f"{slug}/{slug}")
                self.assertEqual(browser["origins"], [origin])
                url = urlsplit(browser["initial_url"])
                self.assertEqual(f"{url.scheme}://{url.netloc}", origin)
                self.assertNotIn("*", origin)
                projected = set()
                for operation in browser["operations"].values():
                    for name in operation["allowed_tools"]:
                        facade = manifest["facades"][name]
                        command = f"{facade['family']}/{facade['kind']}"
                        self.assertIn(command, operation["allowed_commands"])
                        self.assertIn(facade["policy_capability"], browser["capabilities"])
                        if name in {"browser.click", "browser.fill", "browser.type", "browser.select",
                                    "browser.check", "browser.press", "browser.dialog", "browser.upload"}:
                            # Runtime chooses the least privileged operation for
                            # shared facades. No low-privilege click/fill alias.
                            self.assertEqual(operation["minimum_action_class"], "protected.publish")
                        projected.add(name)
                self.assertEqual(projected, set(data["allowed_tools"]))
                self.assertNotIn("browser.evaluate", projected)
                self.assertNotIn("browser.cookies", projected)
                self.assertEqual(browser["skill_revision"], data["skill_revision"])
                required = browser["operations"]["publish_article"]["preview_schema"]["required"]
                self.assertIn("content_hash", required)
                self.assertIn("visibility", required)

    def test_skills_are_distributable_and_discoverable(self):
        data = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        paths = {path for item in data["plugins"] for path in item.get("skills", [])}
        for slug in [*EXPECTED, "baijiahao"]:
            with self.subTest(slug=slug):
                self.assertIn(f"./skills/{slug}", paths)
                skill = ROOT / "skills" / slug / "SKILL.md"
                meta = yaml.safe_load(skill.read_text().split("---\n")[1])
                self.assertTrue(meta["description"].strip())
                self.assertLessEqual(len(meta["description"]), 1024)
                for mirror in (".agents", ".github"):
                    self.assertEqual((ROOT / mirror / "skills" / slug / "SKILL.md").read_bytes(), skill.read_bytes())


if __name__ == "__main__":
    unittest.main()
