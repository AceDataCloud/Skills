# Cangjie JsonML input

Save the document itself as UTF-8 JSON, then pass `--format native`. The client encodes it inside the platform request; do not pre-double-encode it.

```json
[
  "root",
  {},
  [
    "p",
    {
      "uuid": "paragraph-1"
    },
    [
      "span",
      {
        "data-type": "text"
      },
      [
        "span",
        {
          "data-type": "leaf"
        },
        "Article paragraph"
      ]
    ]
  ]
]
```

Each block needs its own stable UUID. For code, use a `code` node with `syntax`, `theme`, `code` and `uuid` attributes. This endpoint saves only the body; do not claim the title was stored.

The root shape is validated locally; the platform validates the complete schema. Do not retry if a content write fails after item creation; reconcile its returned ID.
