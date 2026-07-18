import importlib.util
import json
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "skills" / "reddit" / "scripts" / "reddit.py"
    spec = importlib.util.spec_from_file_location("reddit_skill", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _cookies():
    return json.dumps(
        [
            {
                "name": "reddit_session",
                "value": "cookie-token",
                "domain": ".reddit.com",
                "path": "/",
            }
        ]
    )


def test_oauth_is_preferred_when_both_credentials_exist(monkeypatch):
    reddit = _module()
    monkeypatch.setenv("REDDIT_TOKEN", "oauth-token")
    monkeypatch.setenv("REDDIT_COOKIES", _cookies())

    client = reddit.RedditClient.from_environment()

    assert client.mode == "oauth"
    assert client.token == "oauth-token"


def test_cookie_remains_the_fallback(monkeypatch):
    reddit = _module()
    monkeypatch.delenv("REDDIT_TOKEN", raising=False)
    monkeypatch.setenv("REDDIT_COOKIES", _cookies())

    client = reddit.RedditClient.from_environment()

    assert client.mode == "cookie"
