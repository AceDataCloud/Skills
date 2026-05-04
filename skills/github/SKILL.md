---
name: github
description: GitHub issues, pull requests, repos, code search, and Actions via the gh CLI. Use when the user mentions GitHub, an issue/PR number, a repo, a commit, or code review.
when_to_use: |
  Trigger when the user wants to read or write something on GitHub —
  list / view / create / comment on issues or PRs, search code, view
  a repo, view CI runs, etc.
connections: [github]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Use the `gh` CLI for everything. The user's OAuth access token is exported
as `$GH_TOKEN`; `gh` reads it automatically — `gh auth status` will say
"not logged in" because gh keeps no config file in the sandbox, but every
authenticated subcommand works regardless.

`gh --help` and `gh <subcommand> --help` are always current. When unsure,
read the help first instead of guessing flags.

## Two ways to call gh — prefer subcommands

### Style A: First-class subcommands — START HERE

`gh issue`, `gh pr`, `gh repo`, `gh search`, `gh release`, `gh workflow`,
`gh run`, `gh status`, `gh project`, `gh label`, `gh secret`,
`gh variable`, `gh gist`. Use these whenever they cover the task; they
output formatted text by default and structured JSON via
`--json <fields> [--jq <expr>]`.

### Style B: Raw REST / GraphQL via `gh api`

`gh api <endpoint>` for REST, `gh api graphql -f query='…'` for GraphQL.
Useful when no first-class subcommand exists. Notable flags:

- `-X POST|PATCH|PUT|DELETE` — override method (default `GET`, becomes
  `POST` automatically when `-f`/`-F` is set).
- `-f key=value` — string field; `-F key=value` — JSON-typed field
  (`true`/`123`/`@file.json`); both URL-encode for `GET` and JSON-encode
  for body methods.
- `-q '<jq>'` — same as `--jq`. With a primitive top-level value (string
  / number) it prints the raw value (no quotes).
- `-H 'Accept: application/vnd.github.raw'` — fetch a file's raw bytes
  instead of the JSON wrapper.
- `--paginate` — auto-walk `Link: rel="next"`.

## Recipes

### Triage what's on my plate (issues + PRs + reviews + mentions)

```sh
gh status
```

### List recent issues in a repo

```sh
gh issue list --repo OWNER/REPO --limit 20
gh issue list --repo OWNER/REPO --state all --limit 20 \
  --json number,title,state,author,updatedAt,labels --jq '.[]'
```

### View an issue with comments

```sh
gh issue view 123 --repo OWNER/REPO --comments
gh issue view 123 --repo OWNER/REPO --json title,body,comments \
  --jq '{title, body, comments: [.comments[] | {author: .author.login, body, createdAt}]}'
```

### Create / comment / close an issue

```sh
gh issue create --repo OWNER/REPO --title "Bug: foo" --body "Repro steps…" --label bug
gh issue comment 123 --repo OWNER/REPO --body "LGTM"
gh issue close 123 --repo OWNER/REPO --comment "Fixed in #456"
```

### List PRs assigned to / authored by me

```sh
gh search prs --assignee=@me --state=open --json number,title,repository,updatedAt
gh search prs --author=@me --state=open
```

### View a PR with diff and CI checks

```sh
gh pr view 456 --repo OWNER/REPO
gh pr diff 456 --repo OWNER/REPO
gh pr checks 456 --repo OWNER/REPO
```

### Comment / review / merge a PR

```sh
gh pr comment 456 --repo OWNER/REPO --body "Please rebase on main."
gh pr review 456 --repo OWNER/REPO --approve --body "LGTM"
gh pr review 456 --repo OWNER/REPO --request-changes --body "See nits"
gh pr merge 456 --repo OWNER/REPO --squash --delete-branch
```

### Search code across GitHub

```sh
gh search code 'someFunction language:typescript' --limit 20 \
  --json repository,path,url --jq '.[] | "\(.repository.nameWithOwner) \(.path)"'
```

### Read a file from a repo (raw bytes, no base64 dance)

```sh
gh api "repos/OWNER/REPO/contents/path/to/file.ts" \
  -H 'Accept: application/vnd.github.raw'
```

### List recent commits on the default branch

```sh
gh api "repos/OWNER/REPO/commits?per_page=20" \
  --jq '.[] | "\(.sha[0:7]) \(.commit.author.date) \(.commit.message | split("\n")[0])"'
```

### Trigger / inspect Actions workflows

```sh
gh workflow list --repo OWNER/REPO
gh workflow run ci.yaml --repo OWNER/REPO --ref main -f key=value
gh run list --repo OWNER/REPO --workflow ci.yaml --limit 5
gh run view <RUN_ID> --repo OWNER/REPO --log-failed
```

### View a repo's metadata

```sh
gh repo view OWNER/REPO
gh repo view OWNER/REPO --json description,url,stargazerCount,defaultBranchRef
```

### GraphQL for things REST can't do (e.g. project board items)

```sh
gh api graphql -f query='
  query($owner: String!, $repo: String!, $num: Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $num) {
        title
        timelineItems(first: 50) {
          nodes { __typename ... on CrossReferencedEvent { source { ... on PullRequest { number title state } } } }
        }
      }
    }
  }' -f owner=OWNER -f repo=REPO -F num=123
```

## Notes

- For private repos the user MUST have granted `repo` scope when they
  authorized the connection at `auth.acedata.cloud/user/connections`.
  A 404 on a repo you know exists usually means missing scope, not a
  wrong URL.
- When `--json` rejects a field name, gh prints the full list of valid
  fields — re-read the error and pick from there.
- `gh issue list --search` and `gh search issues` use the GitHub search
  syntax (`is:open`, `assignee:@me`, `repo:owner/name`, etc.). Use
  `gh search issues` / `gh search prs` for cross-repo queries; use
  `gh issue list` for one repo.
- `gh api --paginate` only works on endpoints that emit a `Link` header;
  for cursor-paginated endpoints you have to follow `pagination.next`
  yourself.
