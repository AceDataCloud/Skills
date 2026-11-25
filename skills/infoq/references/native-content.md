# ProseMirror input

Save the document itself as UTF-8 JSON, then pass `--format native`. The client encodes it inside the platform request; do not pre-double-encode it.

```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "attrs": {
        "indent": 0,
        "number": 0,
        "align": null,
        "origin": null
      },
      "content": [
        {
          "type": "text",
          "text": "Article paragraph"
        }
      ]
    }
  ]
}
```

Use `heading` with attrs `level` and text content, or `codeblock` with attrs `lang`; use only schema nodes observed in the platform. Preserve each paragraph and its order.

The root shape is validated locally; the platform validates the complete schema. Do not retry if a content write fails after item creation; reconcile its returned ID.
