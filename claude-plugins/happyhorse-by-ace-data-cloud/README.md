# HappyHorse by Ace Data Cloud

[简体中文](readme/README_zh_Hans.md) · Version 0.1.0 · [Install a Claude plugin](https://code.claude.com/docs/en/plugins/install)

HappyHorse by Ace Data Cloud brings video tools into Claude Code as one independently installable plugin. **Ace Data Cloud provides this integration and bills service use. It is not an official plugin from the HappyHorse model vendor or Anthropic.** It connects the existing Ace MCP instead of shipping another API implementation.

## 1. Install this service

The source is the Ace-maintained marketplace. It is **not currently verified as an entry in Anthropic's official directory**. The five plugins were released to the public Git-backed Ace marketplace on 2026-10-19 (source merge `605e92ed`). Add this marketplace once and install only the service you need:

```text
/plugin marketplace add AceDataCloud/Skills
/plugin install happyhorse-by-ace-data-cloud@acedatacloud-skills
```

Or use the equivalent shell commands `claude plugin marketplace add AceDataCloud/Skills` and `claude plugin install happyhorse-by-ace-data-cloud@acedatacloud-skills`. In `/plugin` → Discover for the added marketplace, search **HappyHorse** or **happyhorse-by-ace-data-cloud**. Other Ace services are separate entries; the older media bundle remains optional. If both copies enable the same service, disable the unused copy to avoid duplicate tools.

The public `main` marketplace contains these plugins at version 0.1.0. On 2026-10-19, ordinary `claude plugin marketplace add AceDataCloud/Skills` cloned the public repository, and all five independent plugins installed and exposed the required sensitive Token option schema under official Claude Code 2.1.303. This is the Ace-maintained marketplace, not Anthropic's official directory. Initial manifest/install checks used Claude Code 2.1.81. On 2026-10-19, the SHA256-verified official Claude Code 2.1.303 release also passed strict manifest checks, five independent installs, native sensitive-option configuration/redacted readback, and local-only header/env substitution tests. Those initial local and synthetic-credential checks did not prove public installation or real service authentication. The later ordinary public-main installation check described above passed; real service authentication and paid first use remain separate.

## 2. Get a dedicated Ace API Token

1. [Sign in or register with Ace Data Cloud](https://platform.acedata.cloud/?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=happyhorse_claude_signup). Open [Applications](https://platform.acedata.cloud/console/applications?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=happyhorse_claude_api_key) and select **General application**. Initialize it if the account has none.
2. Check **HappyHorse** access, available balance and [current service pricing](https://platform.acedata.cloud/documents/happyhorse?utm_source=github&utm_medium=referral&utm_campaign=evergreen&utm_content=happyhorse_claude_pricing). A general application's key can access several entitled services. Prefer a separate key for this plugin.
3. Copy the application's key, or choose **Manage Keys → Create**. Name it `HappyHorse Claude Code`. Review expiration, usage limit and **Allowed APIs**; this workflow uses `/happyhorse/videos`, `/happyhorse/tasks`. Restrict it to the operations you need.

![Redacted Ace application API key and Manage Keys controls](assets/get-api-key-en.png)

![Ace Create New Credential controls; the source image uses the example name Dify tutorial](assets/create-api-key-en.png)

Both are existing redacted Ace UI tutorial images from [SunoDify commit 8d3d035](https://github.com/AceDataCloud/SunoDify/tree/8d3d03570e73324220f111f7fe343da0792a8071/_assets/tutorial), reused and visually checked on 2026-10-18. Capture date is not established. The example name **Dify tutorial** is in the original image; enter **HappyHorse Claude Code** here. Copy only the raw token, without `Bearer `, spaces or quotes. A `platform-...` management token, an Anthropic token or the model vendor's key is not an Ace service token.

## 3. Paste it in Claude Code

Enable the plugin. In `/plugin` → **Installed** → **happyhorse-by-ace-data-cloud** → **Configure options**, paste the raw token into **Ace Data Cloud API Token**. Current Claude plugin documentation specifies `userConfig` with `sensitive: true`, stored by the client separately from `settings.json` and substituted into the plugin's MCP configuration. On macOS the current documented store is Keychain, with a `.credentials.json` fallback if Keychain rejects the write; platforms without a supported keychain use that credential file. Protect the client config directory and inspect the actual store used on your platform before entering a real Token. This plugin does not read another application's key or a keychain directly.

The value becomes the header `Authorization: Bearer <your Ace token>` for `https://happyhorse.mcp.acedata.cloud/mcp`. Do not also configure OAuth on this same token-based connection. The MCP connects when Claude loads the enabled plugin; inspect `/mcp` after configuration. Never put a real token in a prompt, Git commit, shared settings file or screenshot. The plugin does not grant service access or top up the account.

With Claude Code 2.1.303 or later, `claude plugin configure happyhorse-by-ace-data-cloud@acedatacloud-skills --json` shows which options are configured without revealing their sensitive values. Its documented `--values-stdin` interface accepts values from a trusted local secret source; do not pass a real Token in shell arguments, prompts or a shared file. The configure command stores plugin options; it does not prove the remote service accepted the credential.

### Existing host screenshot and what it does not prove

![Historical actual Claude Add custom connector dialog, using Suno as the example](assets/claude-custom-connector-historical.png)

This is an **unchanged historical Claude Web/Desktop custom-connector screenshot**, downloaded and visually checked on 2026-10-17. Its capture date/client version are unknown. It shows **Suno** and an unclicked Add button, not this plugin's Token dialog or an approved directory listing. The plugin path above uses `/plugin`; the screenshot illustrates the separate existing custom-connector path only. A fresh screenshot of the real **Configure options** screen is still queued with the shared browser coordinator. No mock UI or successful run is fabricated.

## 4. Verify setup, then use the service

Call `happyhorse_list_models` with no arguments to read local model reference information. It does not submit a paid generation or prove balance/authorization for generation.

Try these prompts (the generation example is a request to prepare, not permission to charge):

- List HappyHorse video models without generating.
- Prepare a HappyHorse first-frame video request; explain the current price before running.
- Retrieve HappyHorse task TASK_ID, using the original ID.

When you explicitly choose to run a paid operation, review its model, parameters, current price and output count. A successful response may contain final media URLs directly. When it contains a pending task ID, poll that same ID with the retrieval tool; do not start a second generation to check status. Record the terminal result, original task/trace ID and usage receipt when checking billing; a connected icon or listed tool alone is not a successful generation.

## FAQ

- **Plugin not found:** add the Ace marketplace first or run `claude plugin marketplace update acedatacloud-skills`, then check the exact service slug. An organization allowlist or a failed Git download may still block installation. Anthropic official-directory search is a separate, unverified channel.
- **401:** check the raw Ace token, expiration, service/Allowed APIs and which application's key you copied. Do not send a management or Anthropic credential.
- **Insufficient balance / 403 / 429:** inspect the service error and permissions or current balance. A reference tool does not prove generation access; respect rate limits and moderation.
- **Task still pending:** poll the original ID at the service's documented interval. Avoid automatic generation retries.
- **Where is the official listing?** Current [Directory Policy §4.B](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy) restricts standalone AI image/video/audio generation unless expressly permitted in writing. This plugin does not claim that permission. A separately approved vendor listing is not approval for Ace.

## Privacy, support and maintenance

The MCP receives the configured Ace credential and the arguments needed for selected tool calls. Generation can send user-provided prompts/reference media to the Ace service and consumes Credits. This plugin registers **no hooks, telemetry, automatic software installer or background generation**. Only use reference media you have selected for this task. See [Ace privacy policy](https://platform.acedata.cloud/privacy), [terms](https://platform.acedata.cloud/terms), and [support](https://platform.acedata.cloud/support); email support@acedata.cloud for service questions. Server-side retention and usage are governed by the service policy, not a promise that this plugin deletes tasks.

The icon in `assets/ace-data-cloud-mark.png` is the Ace mark, not a third-party official logo. The canonical API/Skill reference is [maintained here](https://github.com/AceDataCloud/Skills/tree/main/skills/happyhorse-video); the MCP source is [AceDataCloud/MCPs](https://github.com/AceDataCloud/MCPs/tree/main/happyhorse). Keep exact tool/model behavior there, rather than copying worker or billing code into this plugin.
