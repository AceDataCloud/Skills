# Single-service Skills for ClawHub

Each entry is one service maintained by **Ace Data Cloud**. Users search the service name, install only that service, and provide their own Ace service API key through OpenClaw's native Skill credential configuration. The optional OpenClaw model-provider/plugin suite is a separate distribution; these Skills do not require it.

| Service name | Canonical source | ClawHub install name | Public state checked 2026-10-18 |
|---|---|---|---|
| Suno by Ace Data Cloud | `skills/suno-music` | `@acedatacloud/suno` | Existing 1.0.1; new branded bundle is a preview |
| Seedance by Ace Data Cloud | `skills/seedance-video` | `@acedatacloud/seedance` | Existing 1.0.1; new branded bundle is a preview |
| HappyHorse by Ace Data Cloud | `skills/happyhorse-video` | `@acedatacloud/happyhorse` | No public text Skill verified; prepared candidate |
| GPT Image by Ace Data Cloud | `skills/gpt-image-2-5` | `@acedatacloud/gpt-image` | No public text Skill verified; prepared candidate |
| Nano Banana by Ace Data Cloud | `skills/nano-banana-image` | `@acedatacloud/nano-banana` | Existing 1.0.1; new branded bundle is a preview |

Do not create duplicate aliases, accounts or per-service source repositories. [ClawHub policy](https://github.com/openclaw/clawhub/blob/main/docs/acceptable-usage.md#disallowed-marketplace-behavior) allows differentiated maintained catalogs and prohibits duplicative listings, impersonation and artificial engagement. Service-name-first titles state the Ace integration's maintainer; they do not claim model-brand or OpenClaw endorsement.

**Code plugins are a separate live option.** All five services already have public ClawHub code-plugin entries maintained in [OpenClawProvider](https://github.com/AceDataCloud/OpenClawProvider/pull/18): `@acedatacloud/<service>-openclaw` (Suno 0.1.2, the other four 0.1.1 as checked 2026-10-18). For example, [HappyHorse](https://clawhub.ai/acedatacloud/plugins/happyhorse-openclaw) and [GPT Image](https://clawhub.ai/acedatacloud/plugins/gpt-image-openclaw) can be found as plugins even though the text Skill candidates above are not published. This table describes Skills only; it must not be read as saying those services are missing from ClawHub entirely.

## Build and review

```sh
python3 scripts/build_clawhub_catalog.py --service all --output /tmp/ace-clawhub-review
# Optional free registry dry-run; use another empty output folder:
python3 scripts/build_clawhub_catalog.py --service all --output /tmp/ace-clawhub-preview --preview
```

The builder has **no upload option**. It generates five separate folders from canonical API references plus one maintained onboarding template. It does not modify shared `skills/` files or the skills.sh onboarding PR. `build.json` records source hashes, commit, build command, exact output hashes and each read-only publication command. Registry source-path is the repository root because reproduction needs the catalog, builder and canonical references together. Registry previews reject uncommitted changes to these inputs; build only from reviewed committed source before release provenance can be claimed.

Each generated `SKILL.md`, English README and Chinese README includes:

1. The exact scoped native install command and publisher identity.
2. Register/sign in → Applications → General application → copy/create a dedicated API key, check current access, balance, restrictions and price.
3. Existing pinned real API-key tutorial screenshots, dated as reused references, and OpenClaw's native `skills.entries.<skill-name>.apiKey` configuration. No fabricated configuration screenshot.
4. A user prompt, canonical request examples, same-task polling, output expectations and 401/403/429/timeout troubleshooting. No automatic new billable retry or model fallback.

Each bundle also includes a byte-identical historical real ClawHub Suno installation screenshot and its provenance in `assets/`. This is a directory-entry reference for Skill 1.0.1 dated 2026-10-17, not evidence of a new candidate installation or successful API call. The native Key-configuration screenshot is still pending; no fake interface is substituted.

ClawHub runtime metadata declares `curl`, `ACEDATACLOUD_API_TOKEN`, `primaryEnv`, a service-specific emoji and a homepage. Skill emoji is not a claim to a model owner's official logo. Code-plugin `assets/icon.png` rules do not apply to these text Skills. The existing registry `icon` fields are empty, so no new uploaded icon is claimed.

Native `apiKey` is injected into the host agent turn. Sandboxes need their own environment configuration; consult [OpenClaw Skills config](https://docs.openclaw.ai/tools/skills-config). Each README explains this boundary. Use a dedicated service key; never put it in a chat or a screenshot.

The current Backend acquisition contract allows `agent_skill/referral`; it does not define a `clawhub` source. These generated ClawHub-specific documents use the existing source and a distinct `<service>_clawhub_<placement>` content tag with all four UTM fields. This identifies the surface without changing the shared global contract or promising measured growth.

## Publication gates

The preview may suggest 1.0.2 for an existing entry and 1.0.0 for an unrecognized entry. A missing public result does not prove there is no hidden or pending owner listing: inspect the existing publisher dashboard before creating one. No duplicate upload should bypass review.

A real Skill publish accepts ClawHub's MIT-0 terms. The source retains its Apache-2.0 license; it is not evidence of authorization to relicense. Obtain explicit human permission and verify the current actor's existing `@acedatacloud` publisher access before any upload. This branch neither accepts terms nor uploads. Source PR, published version, approval, search, normal installation, agent execution, terminal media and billing are separate checks.
