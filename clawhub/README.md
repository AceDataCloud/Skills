# Maintaining existing ClawHub listings

Use the current [ClawHub publishing contract](https://github.com/openclaw/clawhub/blob/main/docs/publishing.md). Skill folders and registry names differ: `skills/suno-music` is `@acedatacloud/suno`; `clawhub/api-guide` is `@acedatacloud/api-guide`. Do not recreate old aliases or publish every source folder. Sora is retired.

Preview one existing listing from committed source:

```bash
bash publish-clawhub.sh --skill suno-music --slug suno \
  --changelog "Describe the reviewed changes."
```

The helper uses CLI 0.23.3 without changing the global installation, checks the canonical owner/slug and matching `SKILL.md` frontmatter names, preserves the existing display name, and sends the exact source commit and path. This prevents publishing the Suno folder into the Midjourney listing even though both belong to AceDataCloud. Preview requires no login and does not upload. Omit `--version` to let ClawHub skip unchanged content; use an explicit version only for a reviewed release that needs it. Modified, untracked, and ignored files inside the selected Skill are rejected so the source pin represents its uploaded contents.

Before adding `--publish --accept-mit-0`, verify that the existing login has publishing access to `@acedatacloud`, and that a human has authorized the **MIT-0** terms used for ClawHub Skill releases. The repository's Apache-2.0 frontmatter is not evidence of that permission. A live CLI publish sends `acceptLicenseTerms: true`; the extra flag acknowledges prior authorization and does not grant it. Do not run a live publish without that authorization. The helper never changes login, creates a publisher, or migrates ownership. `whoami` validates the actor's token, but does not prove organization membership; ClawHub enforces token access to the explicit owner. A failed request returns a nonzero status without retrying or claiming success.

After an authorized release, inspect its version, files, source information, and scan result. Search and install anonymously using the canonical scoped name. Keep source/PR, submitted release, review, searchable listing, installation, actual host calls, terminal results, billing, and referrals as separate verification stages. Registry downloads and installs do not prove AceDataCloud registration or API use.

ClawHub generates `skill-card.md` and the CLI excludes it when computing source publishes. Its presence in a downloaded artifact does not require adding it to this repository. Compare authored files against the source and retain registry metadata/hashes for the generated card separately. An unchanged fingerprint does not prove that source-provenance metadata was attached to an old release. Do not issue a new generation merely to check a pending task: query the same task ID.

## Native single-service discovery

See the [Top 5 single-service catalog](readme/README.md) ([中文](readme/README.zh-CN.md)). `scripts/build_clawhub_catalog.py` builds independent Suno, Seedance, HappyHorse, GPT Image and Nano Banana packages from canonical references with native credential metadata and per-service onboarding. This is the service-name discovery track; the existing `publish-clawhub.sh` remains the guarded updater for unchanged canonical source folders. The builder only previews and has no upload option.
