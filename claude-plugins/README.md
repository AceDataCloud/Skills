# Independent Claude Code service plugins

These five entries install independently from the Ace-maintained `acedatacloud-skills` marketplace. Each owns a narrow workflow and connects the existing MCP server through a separately configured Ace service token. They share the maintained API/MCP backend; no worker, model price or provider fallback is copied here.

| Service | Plugin / illustrated guide |
|---|---|
| Suno | [suno-by-ace-data-cloud](suno-by-ace-data-cloud/README.md) |
| Seedance | [seedance-by-ace-data-cloud](seedance-by-ace-data-cloud/README.md) |
| HappyHorse | [happyhorse-by-ace-data-cloud](happyhorse-by-ace-data-cloud/README.md) |
| GPT Image | [gpt-image-by-ace-data-cloud](gpt-image-by-ace-data-cloud/README.md) |
| Nano Banana | [nano-banana-by-ace-data-cloud](nano-banana-by-ace-data-cloud/README.md) |

The source PR must be merged before GitHub `main` installs work. This is not an Anthropic official-directory listing or a native chat provider. Current Directory Policy §4.B restricts standalone AI media generation absent express written permission. An existing official listing such as Runway is evidence of that entry, not permission for Ace. [Review gates and per-service submission material](submission/README.md) remain separate from source and local-install checks.

The bundled key screenshots are existing redacted Ace tutorial images, with provenance in [assets-sources.json](assets-sources.json). The historical Suno host image is accurately labeled in every guide. Current Token option UI and ordinary real-host first use are pending shared UI validation; no screenshots are fabricated.

`displayName`, directory-only icon fields and `userConfig` UI support vary by Claude Code version. The source uses a brand-explicit install slug and description rather than a `displayName` rejected by the tested 2.1.81 validator. An Ace icon and human-readable title are prepared in each plugin for a future permitted listing. We do not change global branding, credentials or analytics rules.
