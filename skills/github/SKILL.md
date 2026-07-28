---
name: github
description: GitHub issues, pull requests, repos, code search, releases, gists, stars, watching, forks, and Actions via the gh CLI. Use when the user mentions GitHub, an issue/PR number, a repo, a commit, a release, a gist, or code review.
when_to_use: |
  Trigger when the user wants to read or write something on GitHub —
  list / view / create / comment on issues or PRs, star / watch / fork a
  repo, manage releases / gists / labels / milestones, search code, view
  CI runs, etc. Works with either connection method (OAuth authorization
  or a self-supplied Personal Access Token); the commands are the same.
connections: [github]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.2"
---

Use the `gh` CLI for everything. The user's token is exported as an env var
and `gh` reads it automatically — `gh auth status` will say "not logged in"
because gh keeps no config file in the sandbox, but every authenticated
subcommand works regardless. **The commands are identical in both modes**;
only the permission envelope differs, so check which one you're in before
diagnosing a `403`:

```sh
if [ -n "$GITHUB_TOKEN" ]; then echo "mode: pat (user-created token)"; \
elif [ -n "$GH_TOKEN" ]; then echo "mode: oauth"; \
else echo "no GitHub connection — connect at https://auth.acedata.cloud/user/connections"; fi
```

Both are **secret — full account access within their scope. Never echo or
print them.**

`gh --help` and `gh <subcommand> --help` are always current. When unsure,
read the help first instead of guessing flags.

## Granted scopes — what you can and cannot do

**In PAT mode (`$GITHUB_TOKEN`)** the scopes are whatever the user picked
when they created the token, and a fine-grained token may be limited to a
few repositories. You cannot introspect them reliably — treat every `403` /
`404` as a possible permission limit and say so rather than retrying.

**In OAuth mode (`$GH_TOKEN`)** the connection requests exactly five scopes:
`read:user`, `user:email`, `repo`, `read:org`, `gist`. Everything in the
Recipes below fits inside them. These do NOT fit, and will fail no matter
how you phrase the call:

| Want to… | Needs scope | Verdict |
|---|---|---|
| Follow / unfollow a user | `user:follow` (or full `user`) | ✗ we only have `read:user` |
| Block / unblock a user | `user` | ✗ |
| Read / write Projects V2 | `read:project` / `project` | ✗ `INSUFFICIENT_SCOPES` |
| Manage SSH / GPG keys | `admin:public_key` / `admin:gpg_key` | ✗ |
| Manage org membership, teams | `write:org` / `admin:org` | ✗ read-only via `read:org` |
| Manage repo webhooks | `admin:repo_hook` | ✗ |

Users pick scopes at install time and every box is optional, so even the
five above may be partially granted. A `404` on something you know exists,
or a `403`, usually means a missing scope — not a wrong URL. Say so plainly
and point the user at `auth.acedata.cloud/user/connections` to reconnect
with the box ticked (OAuth) or to paste a token with wider permissions (PAT).

## Two ways to call gh — prefer subcommands

### Style A: First-class subcommands — START HERE

`gh issue`, `gh pr`, `gh repo`, `gh search`, `gh release`, `gh workflow`,
`gh run`, `gh status`, `gh label`, `gh secret`, `gh variable`, `gh gist`,
`gh org`, `gh ruleset`. Use these whenever they cover the task; they
output formatted text by default and structured JSON via
`--json <fields> [--jq <expr>]`.

There is no `gh star` / `gh watch` subcommand — those go through
`gh api` (see below). `gh repo fork` does exist.

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
gh issue reopen 123 --repo OWNER/REPO
```

### Edit an issue — labels, assignees, milestone, title, body

```sh
gh issue edit 123 --repo OWNER/REPO --add-label bug --add-assignee @me
gh issue edit 123 --repo OWNER/REPO --remove-label wontfix --milestone "v2.0"
gh issue edit 123 --repo OWNER/REPO --title "New title" --body "Rewritten body"
gh issue lock 123 --repo OWNER/REPO --reason spam
gh issue transfer 123 OWNER/OTHER_REPO --repo OWNER/REPO
```

`--add-project` / `--remove-project` need the `project` scope we do not
have; they will fail. Everything else on this list works.

### List PRs assigned to / authored by me

```sh
gh search prs --assignee=@me --state=open --json number,title,repository,updatedAt
gh search prs --author=@me --state=open
gh search prs --review-requested=@me --state=open
```

### View a PR with diff and CI checks

```sh
gh pr view 456 --repo OWNER/REPO
gh pr diff 456 --repo OWNER/REPO
gh pr checks 456 --repo OWNER/REPO
```

### Create / edit a PR

```sh
gh pr create --repo OWNER/REPO --base main --head feature-branch \
  --title "Add foo" --body "Closes #123" --draft
gh pr edit 456 --repo OWNER/REPO --add-reviewer octocat --add-label review-needed
gh pr edit 456 --repo OWNER/REPO --base develop --title "Retitled"
gh pr ready 456 --repo OWNER/REPO          # draft → ready for review
```

### Comment / review / merge a PR

```sh
gh pr comment 456 --repo OWNER/REPO --body "Please rebase on main."
gh pr review 456 --repo OWNER/REPO --approve --body "LGTM"
gh pr review 456 --repo OWNER/REPO --request-changes --body "See nits"
gh pr merge 456 --repo OWNER/REPO --squash --delete-branch
gh pr update-branch 456 --repo OWNER/REPO  # merge base into the PR branch
gh pr close 456 --repo OWNER/REPO
```

`merge`, `close`, and `review --approve` are irreversible or publicly
visible. Confirm with the user before running them unless they clearly
asked for that exact action.

### Star / unstar a repo

No `gh` subcommand exists — use the REST route. A `204` means success,
and `GET` returns `204` when starred / `404` when not.

```sh
gh api -X PUT    user/starred/OWNER/REPO      # star
gh api -X DELETE user/starred/OWNER/REPO      # unstar
gh api           user/starred/OWNER/REPO      # 204 = starred, 404 = not
gh api user/starred --paginate --jq '.[].full_name'   # list my stars
```

### Watch / unwatch a repo (notification subscription)

```sh
gh api -X PUT repos/OWNER/REPO/subscription -F subscribed=true    # watch
gh api -X PUT repos/OWNER/REPO/subscription -F ignored=true       # ignore
gh api -X DELETE repos/OWNER/REPO/subscription                    # unwatch
gh api user/subscriptions --paginate --jq '.[].full_name'
```

Watching is distinct from starring: starring is a public bookmark,
watching only changes what lands in the user's notifications.

### Fork a repo

```sh
gh repo fork OWNER/REPO --clone=false
gh repo fork OWNER/REPO --org MY_ORG --default-branch-only
gh api repos/OWNER/REPO/forks --jq '.[].full_name'
```

Starring and forking are visible on the user's public profile. Confirm
before doing either on someone else's repo unless explicitly asked.

### Notifications

```sh
gh api notifications --jq '.[] | "\(.repository.full_name) \(.subject.type) \(.subject.title)"'
gh api -X PATCH notifications                                # mark all read
gh api -X PATCH notifications/threads/<THREAD_ID>            # mark one read
```

### Create / manage a repo

```sh
gh repo create OWNER/NEW_REPO --private --description "…"
gh repo view OWNER/REPO --json description,url,stargazerCount,defaultBranchRef
gh repo edit OWNER/REPO --description "New desc" --add-topic ai --visibility private
gh repo list OWNER --limit 30 --json name,visibility,updatedAt
gh repo archive OWNER/REPO --yes
```

`gh repo delete` needs `delete_repo`, which is NOT granted — it will fail.
Never reach for it.

### Releases

```sh
gh release list --repo OWNER/REPO --limit 10
gh release view v1.2.0 --repo OWNER/REPO
gh release create v1.2.0 --repo OWNER/REPO --title "v1.2.0" --notes "Changelog…"
gh release create v1.2.0 --repo OWNER/REPO --generate-notes ./dist/app.zip
gh release upload v1.2.0 ./extra-asset.tar.gz --repo OWNER/REPO
gh release download v1.2.0 --repo OWNER/REPO --pattern '*.zip'
```

### Gists

```sh
gh gist list --limit 20
gh gist create ./script.py --public --desc "Handy script"
gh gist view <GIST_ID>
gh gist edit <GIST_ID>
gh gist delete <GIST_ID>
```

### Labels and milestones

```sh
gh label list --repo OWNER/REPO
gh label create urgent --repo OWNER/REPO --color FF0000 --description "Drop everything"
gh label edit bug --repo OWNER/REPO --color 00FF00
gh label clone SOURCE_OWNER/SOURCE_REPO --repo OWNER/REPO

# Milestones have no gh subcommand — use the API
gh api repos/OWNER/REPO/milestones --jq '.[] | "\(.number) \(.title) \(.open_issues) open"'
gh api -X POST repos/OWNER/REPO/milestones -f title="v2.0" -f due_on="2026-12-31T23:59:59Z"
```

### Branches, commits, and comparing

```sh
gh api repos/OWNER/REPO/branches --jq '.[].name'
gh api "repos/OWNER/REPO/commits?per_page=20" \
  --jq '.[] | "\(.sha[0:7]) \(.commit.author.date) \(.commit.message | split("\n")[0])"'
gh api repos/OWNER/REPO/compare/main...feature-branch \
  --jq '{ahead: .ahead_by, behind: .behind_by, files: [.files[].filename]}'
gh api -X DELETE repos/OWNER/REPO/git/refs/heads/stale-branch
```

### Read / write a file in a repo

```sh
# Read raw bytes, no base64 dance
gh api "repos/OWNER/REPO/contents/path/to/file.ts" \
  -H 'Accept: application/vnd.github.raw'

# Write requires base64 content + the current blob sha when replacing
SHA=$(gh api repos/OWNER/REPO/contents/README.md --jq .sha)
gh api -X PUT repos/OWNER/REPO/contents/README.md \
  -f message="docs: update readme" \
  -f content="$(base64 < ./README.md | tr -d '\n')" \
  -f sha="$SHA"
```

### Search across GitHub

```sh
gh search code 'someFunction language:typescript' --limit 20 \
  --json repository,path,url --jq '.[] | "\(.repository.nameWithOwner) \(.path)"'
gh search repos 'topic:mcp stars:>100' --limit 20 --json fullName,stargazersCount
gh search commits 'fix memory leak' --repo OWNER/REPO --limit 10
gh search issues 'is:open label:bug' --owner OWNER --limit 20
```

### Trigger / inspect Actions workflows

```sh
gh workflow list --repo OWNER/REPO
gh workflow run ci.yaml --repo OWNER/REPO --ref main -f key=value
gh run list --repo OWNER/REPO --workflow ci.yaml --limit 5
gh run view <RUN_ID> --repo OWNER/REPO --log-failed
gh run rerun <RUN_ID> --repo OWNER/REPO --failed
gh run cancel <RUN_ID> --repo OWNER/REPO
gh run watch <RUN_ID> --repo OWNER/REPO
```

### Actions secrets and variables

```sh
gh secret list --repo OWNER/REPO
gh secret set MY_TOKEN --repo OWNER/REPO --body "value"
gh variable list --repo OWNER/REPO
gh variable set MY_VAR --repo OWNER/REPO --body "value"
```

Secret values are write-only — you can set and list names, never read a
value back. Never echo a secret the user gives you into a comment, issue,
or commit.

### Organizations (read-only under `read:org`)

```sh
gh org list
gh api user/orgs --jq '.[].login'
gh api orgs/ORG/members --jq '.[].login'
gh api orgs/ORG/repos --paginate --jq '.[].full_name'
```

### GraphQL for things REST can't do

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

Projects V2 lives only in GraphQL and needs `read:project` — not granted,
so those queries return `INSUFFICIENT_SCOPES`. Don't build recipes on it.

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
- Write endpoints that take no body (star, follow, watch-delete) return
  `204 No Content` on success — an empty response is the success case,
  not a failure.
- This connection can run unattended in a scheduled task. Public actions
  (star, fork, issue/PR comments, reviews, merges) leave a permanent,
  publicly attributable trace on the user's account. In an unattended run,
  stick to exactly what the task authorized.
