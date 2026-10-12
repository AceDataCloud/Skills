# Maintaining existing ClawHub listings

Use the current [ClawHub publishing contract](https://github.com/openclaw/clawhub/blob/main/docs/publishing.md). Skill folders and registry names differ: `skills/suno-music` is `@acedatacloud/suno`; `clawhub/api-guide` is `@acedatacloud/api-guide`. Do not recreate old aliases or publish every source folder. Sora is retired.

Preview one existing listing from committed source:

```bash
bash publish-clawhub.sh --skill suno-music --slug suno \
  --changelog "Describe the reviewed changes."
```

The helper uses CLI 0.23.3 without changing the global installation, checks the canonical owner/name, and sends the exact source commit and path. Preview requires no login and does not upload. Omit `--version` to let ClawHub skip unchanged content; use an explicit version only for a reviewed release that needs it. Modified, untracked, and ignored files inside the selected Skill are rejected so the source pin represents its uploaded contents.

Before adding `--publish`, verify that the existing login has publishing access to `@acedatacloud`, and that the organization has authorized the **MIT-0** license used for ClawHub Skill releases. The repository's Apache-2.0 frontmatter is not evidence of that permission. The helper never changes login, creates a publisher, migrates ownership, or accepts agreements on the user's behalf. ClawHub enforces token access to the explicit owner. A failed request returns a nonzero status without retrying or claiming success.

After an authorized release, inspect its version, files, source information, and scan result. Search and install anonymously using the canonical scoped name. Keep source/PR, submitted release, review, searchable listing, installation, actual host calls, terminal results, billing, and referrals as separate verification stages. Registry downloads and installs do not prove AceDataCloud registration or API use.

The Suno 1.0.1 artifact also contains a `skill-card.md` absent from the source folder. Reconcile that extra file before the next approved release; matching `SKILL.md` alone does not prove the whole bundle is reproducible. Do not issue a new generation merely to check a pending task: query the same task ID.
