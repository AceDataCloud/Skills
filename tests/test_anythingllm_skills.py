"""Exercise the two independently installed AnythingLLM native skills."""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1] / "platforms" / "anythingllm"
SKILLS = ROOT / "skills"


class AnythingLLMSkillTests(unittest.TestCase):
    def test_native_manifests_use_separate_identities_and_password_settings(self):
        expected = {
            "acedatacloud-google-search": "Google Search",
            "acedatacloud-suno": "Suno",
        }
        self.assertEqual({folder.name for folder in SKILLS.iterdir()}, set(expected))
        for name, title in expected.items():
            with self.subTest(skill=name):
                folder = SKILLS / name
                manifest = json.loads((folder / "plugin.json").read_text())
                self.assertEqual(manifest["hubId"], name)
                self.assertEqual(manifest["name"], title)
                self.assertEqual(manifest["schema"], "skill-1.0.0")
                self.assertEqual(manifest["license"], "Apache-2.0")
                self.assertFalse(manifest["active"])
                self.assertTrue(manifest["imported"])
                setup = manifest["setup_args"]["ACEDATACLOUD_API_TOKEN"]
                self.assertTrue(setup["required"])
                self.assertEqual(setup["input"]["type"], "password")
                self.assertNotIn("value", setup)
                self.assertEqual(manifest["entrypoint"]["file"], "handler.js")
                params = manifest["entrypoint"]["params"]
                for example in manifest["examples"]:
                    self.assertLessEqual(json.loads(example["call"]).keys(), params.keys())
                self.assertEqual({p.name for p in folder.iterdir()}, {"handler.js", "plugin.json", "README.md", "LICENSE.txt"})

    def test_hub_and_github_acquisition_links_use_separate_attribution(self):
        docs = [(ROOT / "README.md", "github")]
        docs.extend((path, "anythingllm") for path in SKILLS.glob("*/README.md"))
        for doc, source in docs:
            with self.subTest(file=doc):
                text = doc.read_text()
                urls = re.findall(r"https://platform\.acedata\.cloud/[^)\s]+", text)
                self.assertTrue(urls)
                for url in urls:
                    query = parse_qs(urlsplit(url).query)
                    self.assertEqual(query["utm_source"], [source])
                    self.assertEqual(query["utm_medium"], ["referral"])
                    self.assertEqual(query["utm_campaign"], ["evergreen"])
                    self.assertNotIn("token", query)
                if source == "anythingllm":
                    self.assertIn("_assets/icon.", text)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required to exercise the JavaScript handlers")
    def test_handlers_use_one_scoped_request_and_preserve_task_state(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for path in SKILLS.glob("*/handler.js"):
                shutil.copyfile(path, temp / f"{path.parent.name}.cjs")
            subprocess.run(["node", "-e", NODE_CASES], cwd=temp, check=True, timeout=30)


NODE_CASES = r"""
const assert = require('node:assert/strict');
const google = require('./acedatacloud-google-search.cjs').runtime.handler;
const suno = require('./acedatacloud-suno.cjs').runtime.handler;
const context = {runtimeArgs: {ACEDATACLOUD_API_TOKEN: 'offline-fixture'}};
const taskId = '00000000-0000-4000-8000-000000000001';
const requests = [];
let data, status = 200;
global.fetch = async (url, options) => {
  requests.push([url, JSON.parse(options.body), options]);
  return new Response(JSON.stringify(data), {status});
};

async function run() {
  assert.ok(JSON.parse(await google.call(context, {query: ' '})).error);
  assert.ok(JSON.parse(await google.call({}, {query: 'anything'})).error);
  assert.ok(JSON.parse(await suno.call(context, {task_id: 'not-an-id'})).error);
  assert.equal(requests.length, 0);
  data = {organic: [
    {title: 'Official guide', link: 'https://example.test/guide', snippet: 'Guide'},
    {title: 'Bad scheme', link: 'javascript:example'},
  ]};
  assert.deepEqual(JSON.parse(await google.call(context, {query: ' docs ', country: 'JP', language: 'ja'})), {
    query: 'docs', results: [{title: 'Official guide', link: 'https://example.test/guide', snippet: 'Guide'}],
  });
  assert.deepEqual(requests[0].slice(0, 2), ['https://api.acedata.cloud/serp/google', {
    query: 'docs', type: 'search', country: 'jp', language: 'ja', number: 5,
  }]);
  status = 429;
  data = {error: 'offline-fixture'};
  const rateLimited = await google.call(context, {query: 'docs'});
  assert.match(rateLimited, /HTTP 429/);
  assert.ok(!rateLimited.includes('offline-fixture'));
  assert.equal(requests.length, 2);

  status = 200;
  data = {id: taskId, started_at: 1700000000, response: {success: true, data: [{audio_url: 'https://example.test/partial.mp3'}]}};
  assert.deepEqual(JSON.parse(await suno.call(context, {task_id: taskId})), {task_id: taskId, status: 'running'});
  assert.deepEqual(requests[2].slice(0, 2), ['https://api.acedata.cloud/suno/tasks', {id: taskId, action: 'retrieve'}]);
  data = {id: taskId, finished_at: 1700000001, response: JSON.stringify({success: true, task_id: taskId,
    data: [{id: 'track-id', title: 'Title', audio_url: 'https://example.test/audio.mp3', private: 'omit'}]})};
  assert.deepEqual(JSON.parse(await suno.call(context, {task_id: taskId})), {task_id: taskId, status: 'succeeded',
    outputs: [{id: 'track-id', title: 'Title', audio_url: 'https://example.test/audio.mp3'}]});
  data = {id: taskId, finished_at: 1700000001, response: {success: false, error: 'private upstream response'}};
  assert.deepEqual(JSON.parse(await suno.call(context, {task_id: taskId})), {task_id: taskId, status: 'failed'});
  data = {id: '00000000-0000-4000-8000-000000000002'};
  assert.match(JSON.parse(await suno.call(context, {task_id: taskId})).error, /different task/);
  assert.equal(requests.length, 6);
  assert.ok(requests.every(([, , request]) => request.method === 'POST' && request.redirect === 'error' &&
    request.headers.Authorization === 'Bearer offline-fixture' && request.signal instanceof AbortSignal));
}
run().catch((error) => { console.error(error); process.exitCode = 1; });
"""
