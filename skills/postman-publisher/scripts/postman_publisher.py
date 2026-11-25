#!/usr/bin/env python3
"""Validate and sync one Postman Collection to an owned public workspace."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


API = "https://api.postman.com"
SCHEMA = "collection/v2.1.0/collection.json"
SENSITIVE = re.compile(r"(?:token|api[_-]?key|password|secret|authorization)", re.I)
SECRET_AUTH_KEYS = {
    "value",
    "token",
    "password",
    "accesstoken",
    "clientsecret",
    "apikey",
}


def validate_collection(document: dict) -> dict:
    collection = document.get("collection", document)
    if not isinstance(collection, dict):
        raise ValueError("collection must be a JSON object")
    info = collection.get("info") or {}
    if not isinstance(info.get("name"), str) or not info["name"].strip():
        raise ValueError("collection.info.name is required")
    if SCHEMA not in str(info.get("schema", "")):
        raise ValueError("collection must use the Postman Collection v2.1 schema")
    if not isinstance(collection.get("item"), list) or not collection["item"]:
        raise ValueError("collection.item must contain at least one request")
    for variable in collection.get("variable", []):
        validate_key_value(variable)
    for item in iter_items(collection["item"]):
        request = item.get("request", {})
        if not isinstance(request, dict):
            continue
        for header in request.get("header", []):
            validate_key_value(header)
    for auth in iter_auth(collection):
        for values in auth.values():
            if isinstance(values, list):
                for entry in values:
                    if (
                        isinstance(entry, dict)
                        and str(entry.get("key", "")).lower() in SECRET_AUTH_KEYS
                    ):
                        validate_placeholder(str(entry.get("value", "")), "auth value")
    return collection


def validate_placeholder(value: str, label: str) -> None:
    if value and not re.fullmatch(r"(?:Bearer )?\{\{[A-Za-z0-9_-]+\}\}", value):
        raise ValueError(f"{label} must have an empty or placeholder value")


def validate_key_value(entry: dict) -> None:
    if isinstance(entry, dict) and SENSITIVE.search(str(entry.get("key", ""))):
        validate_placeholder(str(entry.get("value", "")), str(entry.get("key")))


def iter_items(items):
    for item in items:
        if isinstance(item, dict):
            yield item
            if isinstance(item.get("item"), list):
                yield from iter_items(item["item"])


def iter_auth(value):
    if isinstance(value, dict):
        if isinstance(value.get("auth"), dict):
            yield value["auth"]
        for child in value.values():
            yield from iter_auth(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_auth(child)


def request_signatures(collection):
    result = []
    for item in iter_items(collection.get("item", [])):
        request_body = item.get("request")
        if not isinstance(request_body, dict):
            continue
        url = request_body.get("url", "")
        if isinstance(url, dict):
            url = url.get("raw", "")
        result.append(
            (
                item.get("name", ""),
                str(request_body.get("method", "")).upper(),
                str(url),
            )
        )
    return result


def request(method: str, path: str, api_key: str, params=None, payload=None) -> dict:
    url = API + path + ("?" + urlencode(params) if params else "")
    headers = {"x-api-key": api_key, "Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").replace(api_key, "[redacted]")
        raise RuntimeError(f"Postman API {exc.code}: {body[:1000]}") from None
    except URLError as exc:
        raise RuntimeError(f"Postman API request failed: {exc.reason}") from None


def sync(
    collection: dict,
    collection_id: str | None,
    confirm: bool,
    api_key: str,
    workspace_id: str,
) -> dict:
    collection = validate_collection(collection)
    name = collection["info"]["name"]
    count = sum(
        1
        for item in iter_items(collection["item"])
        if isinstance(item.get("request"), dict)
    )
    if not confirm:
        return {
            "dry_run": True,
            "name": name,
            "request_count": count,
            "operation": "replace" if collection_id else "create",
        }
    if not api_key or not workspace_id:
        raise ValueError("connect the Postman publisher API key and workspace ID first")
    workspace = request(
        "GET", f"/workspaces/{quote(workspace_id, safe='')}", api_key
    ).get("workspace", {})
    if workspace.get("type") != "public":
        raise ValueError(
            "target workspace is not public; make it public in Postman before syncing"
        )
    if collection_id:
        response = request(
            "PUT",
            f"/collections/{quote(collection_id, safe='')}",
            api_key,
            payload={"collection": collection},
        )
    else:
        response = request(
            "POST",
            "/collections",
            api_key,
            {"workspace": workspace_id},
            {"collection": collection},
        )
    meta = response.get("collection", {})
    identifier = meta.get("uid") or meta.get("id") or collection_id
    if not identifier:
        raise RuntimeError(
            "Postman accepted the write but returned no collection ID; inspect the workspace before retrying"
        )
    readback = request(
        "GET", f"/collections/{quote(str(identifier), safe='')}", api_key
    ).get("collection", {})
    read_collection = readback.get("collection", readback)
    verified = read_collection.get("info", {}).get(
        "name"
    ) == name and request_signatures(read_collection) == request_signatures(collection)
    return {
        "synced": True,
        "verified": verified,
        "collection_id": identifier,
        "workspace_id": workspace_id,
        "workspace_type": "public",
        "name": name,
        "request_count": count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["sync"])
    parser.add_argument("--collection-file", type=Path, required=True)
    parser.add_argument("--collection-id")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    try:
        document = json.loads(args.collection_file.read_text(encoding="utf-8"))
        result = sync(
            document,
            args.collection_id,
            args.confirm,
            os.environ.get("POSTMANPUBLISHER_API_KEY", ""),
            os.environ.get("POSTMANPUBLISHER_WORKSPACE_ID", ""),
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
