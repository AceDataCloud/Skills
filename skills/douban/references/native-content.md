# Draft.js input

Save the document itself as UTF-8 JSON, then pass `--format native`. The client encodes it inside the platform request; do not pre-double-encode it.

```json
{
  "blocks": [
    {
      "key": "p1",
      "text": "Article paragraph",
      "type": "unstyled",
      "depth": 0,
      "inlineStyleRanges": [],
      "entityRanges": [],
      "data": {}
    }
  ],
  "entityMap": {}
}
```

Style ranges use UTF-16 offsets; avoid guessing offsets for emoji. Image entities require platform-uploaded image metadata. Use text input if formatting cannot be represented faithfully; disclose the change before writing.

The root shape is validated locally; the platform validates the complete schema. Do not retry if a content write fails after item creation; reconcile its returned ID.
