---
name: postman-publisher
description: Validate and sync a curated Postman Collection to an owned public workspace on the Postman API Network. Use for API distribution, not for reading a customer's Postman workspace.
when_to_use: |
  Use when publishing or updating the user's own public API collection. The
  existing Postman remote MCP connector is for browsing and running requests;
  this skill is the separate outbound publisher.
connections: [postmanpublisher]
allowed_tools: [Bash, publish_artifact]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Postman public API publisher

The connected account supplies `$POSTMANPUBLISHER_API_KEY` and
`$POSTMANPUBLISHER_WORKSPACE_ID`. Prepare a **curated** Postman Collection v2.1
JSON file with working examples. Do not copy production keys, customer data, or
secret headers into the collection. Use `{{api_key}}` with an empty default.

```bash
SCRIPT="$SKILL_DIR/scripts/postman_publisher.py"
python3 "$SCRIPT" sync --collection-file collection.json
# After reviewing the complete collection and target public workspace:
python3 "$SCRIPT" sync --collection-file collection.json --confirm
# Future updates use the collection ID returned by the first sync:
python3 "$SCRIPT" sync --collection-file collection.json --collection-id UUID --confirm
```

Dry-run validation makes no network request. A confirmed sync first reads the
workspace and refuses to write unless its type is `public`. It then creates or
replaces one collection and reads it back. A successful API readback means the
collection is in the public workspace; verify the actual anonymous public URL
before claiming API Network discoverability or recording an artifact.

Official references: [publish a public API](https://learning.postman.com/docs/postman-api-network/showcase/publish/public-apis), [create a collection](https://learning.postman.com/api-docs/api-reference/collections/create-collection), [replace a collection](https://learning.postman.com/api-docs/api-reference/collections/put-collection).
