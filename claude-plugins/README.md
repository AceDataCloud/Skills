# Independent Claude Code service plugins

These five entries install independently from the Ace-maintained `acedatacloud-skills` marketplace. Each owns a narrow workflow and connects an existing MCP through a separately configured Ace service token. Four use hosted HTTP; GPT Image uses the published five-tool stdio profile via pinned uvx package, with no separate hosted URL. They share the maintained API/MCP backend; no worker, model price or provider fallback is copied here.

| Service | Plugin / illustrated guide |
|---|---|
| Suno | [suno-by-ace-data-cloud](suno-by-ace-data-cloud/README.md) |
| Seedance | [seedance-by-ace-data-cloud](seedance-by-ace-data-cloud/README.md) |
| HappyHorse | [happyhorse-by-ace-data-cloud](happyhorse-by-ace-data-cloud/README.md) |
| GPT Image | [gpt-image-by-ace-data-cloud](gpt-image-by-ace-data-cloud/README.md) |
| Nano Banana | [nano-banana-by-ace-data-cloud](nano-banana-by-ace-data-cloud/README.md) |

The five plugins are published on GitHub `main` at source merge `605e92ed` (2026-10-19), version 0.1.0. Normal public Git marketplace clone and five independent native installations were verified with official Claude Code 2.1.303. This is not an Anthropic official-directory listing or a native chat provider. Current Directory Policy §4.B restricts standalone AI media generation absent express written permission. An existing official listing such as Runway is evidence of that entry, not permission for Ace. [Review gates and per-service submission material](submission/README.md) remain separate from source and local-install checks.

The bundled key screenshots are existing redacted Ace tutorial images, with provenance in [assets-sources.json](assets-sources.json). The historical Suno host image is accurately labeled in every guide. Current Token option UI and ordinary real-host first use are pending shared UI validation; no screenshots are fabricated.

Current manifests and marketplace entries set service-first `displayName` values (for example, Suno by Ace Data Cloud), with an Ace icon and legal/support links. They are strictly validated with official Claude Code 2.1.303; older 2.1.81 rejects newer display fields, so update from the official distribution before installation. Native sensitive options are tested with fake values and local-only transport receivers. Official directory permission, actual service authentication and ordinary public installation remain separate stages. No global branding, credentials or analytics rules are changed.
