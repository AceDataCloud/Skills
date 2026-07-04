# Recording produced outputs (`publish_artifact`)

Write/publish-capable Skills should record their concrete deliverable so the
user can later find and aggregate everything the agent produced (in the "My
Outputs" view at `/chatgpt/artifacts`).

After a publish/send/generate action **succeeds and you have the live result
URL**, call the built-in `publish_artifact` tool exactly ONCE for that
deliverable:

```
publish_artifact(
  kind="article",          # article | image | video | audio | document | email | message | dataset | link | other
  channel="<platform>",    # e.g. zhihu, csdn, medium, x, mastodon
  title="<human title>",
  url="<the REAL returned URL>",
  status="delivered"       # delivered | draft | failed
)
```

Rules:

- Use the **real URL returned by the publish step** — never fabricate a URL.
- Call it once per distinct deliverable, right after delivery is confirmed.
- Do NOT call it for intermediate steps, drafts you didn't submit, or narration.
- If publishing failed, either skip it or record `status="failed"`.

The tool is non-interactive and works in unattended (scheduled-task) runs.
