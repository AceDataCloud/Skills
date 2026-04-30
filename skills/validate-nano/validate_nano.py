#!/usr/bin/env python3
"""Validate Nano Banana production callback flows and write full reports."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_SOURCE_IMAGE_URL = (
    "https://cdn.turbotext.ru/userfiles/wd6/pro/gemini_edit_image/"
    "2026-04-30/05/55a2eb0a-21cd-4eac-94ab-3a9e99783f93.png"
)

SUCCESS_STATES = {"success", "succeeded", "succeed", "completed", "complete", "finished", "done"}
FAILURE_STATES = {"failed", "fail", "error", "cancelled", "canceled", "timeout"}


@dataclass(frozen=True)
class Case:
    name: str
    purpose: str
    payload: dict[str, Any]


def default_cases(source_image_url: str) -> list[Case]:
    return [
        Case(
            name="generate_1k_square",
            purpose="Basic generation callback smoke test.",
            payload={
                "action": "generate",
                "prompt": "A clean product-style photo of a glass lemon tea on a white table, natural light",
                "model": "nano-banana-2",
                "aspect_ratio": "1:1",
                "resolution": "1K",
                "count": 1,
            },
        ),
        Case(
            name="generate_2k_landscape",
            purpose="2K generation with an explicit supported aspect ratio.",
            payload={
                "action": "generate",
                "prompt": "A realistic mountain observatory at sunrise, crisp details, cinematic landscape",
                "model": "nano-banana-2",
                "aspect_ratio": "16:9",
                "resolution": "2K",
                "count": 1,
            },
        ),
        Case(
            name="edit_2k_arbitrary_ratio_no_aspect",
            purpose="2K edit regression test for arbitrary input ratio with omitted aspect_ratio.",
            payload={
                "action": "edit",
                "prompt": "Make the photo color. Keep the face and original photo size.",
                "model": "nano-banana-2",
                "resolution": "2K",
                "count": 1,
                "image_urls": [source_image_url],
            },
        ),
        Case(
            name="edit_4k_arbitrary_ratio_no_aspect",
            purpose="4K edit regression test for arbitrary input ratio with omitted aspect_ratio.",
            payload={
                "action": "edit",
                "prompt": "Make the photo color. Keep the face and original photo size.",
                "model": "nano-banana-2",
                "resolution": "4K",
                "count": 1,
                "image_urls": [source_image_url],
            },
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Nano Banana callback-mode generation and edit cases.")
    parser.add_argument("--api-base", default="https://api.acedata.cloud")
    parser.add_argument("--callback-url", default="https://api.acedata.cloud/health")
    parser.add_argument("--case", action="append", dest="cases", help="Case name to run. Repeat for multiple cases.")
    parser.add_argument("--source-image-url", default=DEFAULT_SOURCE_IMAGE_URL)
    parser.add_argument("--output-dir", default="artifacts/nano-validation")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--poll-interval", type=int, default=10)
    return parser.parse_args()


def get_token() -> str:
    token = os.environ.get("ACEDATACLOUD_API_TOKEN") or os.environ.get("ACEDATACLOUD_API_KEY")
    if not token:
        raise SystemExit("Set ACEDATACLOUD_API_TOKEN or ACEDATACLOUD_API_KEY before running validation.")
    return token


def post_json(url: str, payload: dict[str, Any], token: str, timeout: int = 60) -> tuple[int, dict[str, Any] | list[Any] | str]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, parse_json(raw)
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return exc.code, parse_json(raw)


def parse_json(raw: str) -> dict[str, Any] | list[Any] | str:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def find_first_key(obj: Any, keys: set[str]) -> Any:
    if isinstance(obj, dict):
        for key in keys:
            if key in obj:
                return obj[key]
        for value in obj.values():
            found = find_first_key(value, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, keys)
            if found is not None:
                return found
    return None


def collect_urls(obj: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"url", "image_url", "image"} and isinstance(value, str) and value.startswith("http"):
                urls.append(value)
            else:
                urls.extend(collect_urls(value))
    elif isinstance(obj, list):
        for item in obj:
            urls.extend(collect_urls(item))
    elif isinstance(obj, str) and obj.startswith("http"):
        lowered = obj.lower().split("?", 1)[0]
        if lowered.endswith((".png", ".jpg", ".jpeg", ".webp")):
            urls.append(obj)
    return list(dict.fromkeys(urls))


def terminal_state(obj: Any) -> str | None:
    state = find_first_key(obj, {"status", "state"})
    if isinstance(state, str):
        return state.lower()
    return None


def has_terminal_output(obj: Any) -> bool:
    if isinstance(obj, dict):
        response = obj.get("response")
        if response and collect_urls(response):
            return True
        if collect_urls(obj):
            return True
        success = obj.get("success")
        if success is True and (obj.get("data") or obj.get("result")):
            return True
    return False


def fetch_head(url: str, timeout: int = 30) -> bytes:
    req = request.Request(url, headers={"Range": "bytes=0-131071", "User-Agent": "validate-nano/1.0"})
    with request.urlopen(req, timeout=timeout) as resp:
        return resp.read(131072)


def image_dimensions(url: str) -> dict[str, Any]:
    try:
        data = fetch_head(url)
        dims = parse_image_dimensions(data)
        if not dims:
            return {"url": url, "error": "could not parse dimensions"}
        width, height = dims
        return {"url": url, "width": width, "height": height, "ratio": round(width / height, 6)}
    except Exception as exc:
        return {"url": url, "error": str(exc)}


def parse_image_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if len(data) >= 10 and data[:2] == b"\xff\xd8":
        return parse_jpeg_dimensions(data)
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 " and len(data) >= 30:
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
            return width, height
        if chunk == b"VP8L" and len(data) >= 25:
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X" and len(data) >= 30:
            width = int.from_bytes(data[24:27] + b"\x00", "little") + 1
            height = int.from_bytes(data[27:30] + b"\x00", "little") + 1
            return width, height
    return None


def parse_jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        while marker == 0xFF and offset < len(data):
            marker = data[offset]
            offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            return None
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height = int.from_bytes(data[offset + 3 : offset + 5], "big")
            width = int.from_bytes(data[offset + 5 : offset + 7], "big")
            return width, height
        offset += length
    return None


def run_case(case: Case, api_base: str, callback_url: str, token: str, timeout: int, poll_interval: int) -> dict[str, Any]:
    trace_id = f"validate-nano-{case.name}-{uuid.uuid4()}"
    payload = {**case.payload, "callback_url": callback_url, "trace_id": trace_id}
    started = time.time()
    submit_status, submit_body = post_json(f"{api_base.rstrip('/')}/nano-banana/images", payload, token, timeout=90)
    task_id = find_first_key(submit_body, {"task_id", "id"})
    result: dict[str, Any] = {
        "case": case.name,
        "purpose": case.purpose,
        "trace_id": trace_id,
        "input": payload,
        "submit": {"http_status": submit_status, "body": submit_body},
        "task_id": task_id,
        "polls": [],
        "success": False,
    }
    if not isinstance(task_id, str) or not task_id:
        result["error"] = "submit response did not include task_id/id"
        result["duration_seconds"] = round(time.time() - started, 3)
        return finalize_case(result)

    deadline = time.time() + timeout
    final_body: Any = None
    while time.time() < deadline:
        poll_status, poll_body = post_json(
            f"{api_base.rstrip('/')}/nano-banana/tasks",
            {"id": task_id},
            token,
            timeout=60,
        )
        state = terminal_state(poll_body)
        poll_record = {"http_status": poll_status, "state": state, "body": poll_body}
        result["polls"].append(poll_record)
        final_body = poll_body
        if state in FAILURE_STATES:
            result["error"] = f"task entered failure state: {state}"
            break
        if state in SUCCESS_STATES or has_terminal_output(poll_body):
            result["success"] = True
            break
        time.sleep(poll_interval)
    else:
        result["error"] = f"timed out after {timeout}s waiting for task result"

    result["final"] = final_body
    result["duration_seconds"] = round(time.time() - started, 3)
    return finalize_case(result)


def finalize_case(result: dict[str, Any]) -> dict[str, Any]:
    input_urls = collect_urls(result.get("input"))
    output_urls = collect_urls(result.get("final"))
    result["input_images"] = [image_dimensions(url) for url in input_urls]
    result["output_images"] = [image_dimensions(url) for url in output_urls]
    if result.get("success") and not output_urls:
        result["success"] = False
        result["error"] = "task completed but no output image URLs were found"
    return result


def write_reports(results: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "success": all(item.get("success") for item in results),
        "results": results,
    }
    (output_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "report.md").write_text(markdown_report(report), encoding="utf-8")


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# Nano Banana Validation Report", "", f"Generated at: `{report['generated_at']}`", "", f"Overall success: `{report['success']}`", ""]
    for item in report["results"]:
        lines.extend(
            [
                f"## {item['case']}",
                "",
                f"Purpose: {item['purpose']}",
                f"Success: `{item.get('success')}`",
                f"Task ID: `{item.get('task_id')}`",
                f"Trace ID: `{item.get('trace_id')}`",
                f"Duration seconds: `{item.get('duration_seconds')}`",
            ]
        )
        if item.get("error"):
            lines.append(f"Error: `{item['error']}`")
        lines.extend(["", "Input images:", "", "```json", json.dumps(item.get("input_images", []), ensure_ascii=False, indent=2), "```"])
        lines.extend(["", "Output images:", "", "```json", json.dumps(item.get("output_images", []), ensure_ascii=False, indent=2), "```"])
        lines.extend(["", "Full input:", "", "```json", json.dumps(item.get("input"), ensure_ascii=False, indent=2), "```"])
        lines.extend(["", "Initial response:", "", "```json", json.dumps(item.get("submit"), ensure_ascii=False, indent=2), "```"])
        lines.extend(["", "Final response:", "", "```json", json.dumps(item.get("final"), ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    token = get_token()
    cases = default_cases(args.source_image_url)
    if args.cases:
        wanted = set(args.cases)
        known = {case.name for case in cases}
        unknown = sorted(wanted - known)
        if unknown:
            raise SystemExit(f"Unknown case(s): {', '.join(unknown)}. Known cases: {', '.join(sorted(known))}")
        cases = [case for case in cases if case.name in wanted]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir) / stamp
    results = []
    for case in cases:
        print(f"running {case.name}...", flush=True)
        result = run_case(case, args.api_base, args.callback_url, token, args.timeout, args.poll_interval)
        results.append(result)
        print(f"  success={result.get('success')} task_id={result.get('task_id')} error={result.get('error')}", flush=True)

    write_reports(results, output_dir)
    print(f"report_json={output_dir / 'report.json'}")
    print(f"report_md={output_dir / 'report.md'}")
    return 0 if all(item.get("success") for item in results) else 1


if __name__ == "__main__":
    sys.exit(main())
