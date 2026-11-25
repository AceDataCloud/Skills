#!/usr/bin/env python3
"""Bundle the shared HTTP helper so each imported skill remains standalone."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUGS = (
    "jianshu",
    "netease",
    "infoq",
    "tencentcloud-community",
    "aliyun-community",
    "volcengine-community",
    "modelscope",
    "sohu",
    "douban",
)
source = (ROOT / "skills/_shared/publishing_http.py").read_bytes()
for slug in SLUGS:
    destination = ROOT / "skills" / slug / "scripts"
    destination.mkdir(exist_ok=True)
    (destination / "publishing_http.py").write_bytes(source)
