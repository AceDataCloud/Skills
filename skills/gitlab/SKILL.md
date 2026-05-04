---
name: gitlab
description: GitLab issues, merge requests, repositories, CI pipelines, and code search via the glab CLI. Use when the user mentions GitLab, an MR/issue number, a project on gitlab.com, or a self-hosted GitLab instance.
when_to_use: |
  Trigger when the user wants to read or write something on GitLab —
  list / view / create / comment on issues or MRs, browse a project,
  view CI pipelines, etc.
connections: [gitlab]
allowed_tools: [Bash]
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

Use the `glab` CLI for everything. The user's OAuth access token is
exported as `$GITLAB_TOKEN`; `glab` reads it automatically (the token
is also accepted via `GITLAB_ACCESS_TOKEN` and `OAUTH_TOKEN` for tooling
compatibility). Default host is `gitlab.com` — for self-hosted set
`GITLAB_HOST` or pass `--hostname <host>` per command.

`glab --help` and `glab <subcommand> --help` are always current.

## Two ways to call glab — prefer subcommands

### Style A: First-class subcommands — START HERE

`glab issue`, `glab mr`, `glab repo`, `glab ci`, `glab job`, `glab pipeline`,
`glab release`, `glab snippet`, `glab variable`, `glab label`,
`glab milestone`, `glab schedule`. These print formatted text by default
and JSON via `--output json`.

### Style B: Raw REST / GraphQL via `glab api`

`glab api <path>` for REST, `glab api graphql -f query='…'` for GraphQL.
Notable flags:

- `-X POST|PATCH|PUT|DELETE` — override method (default `GET`, becomes
  `POST` when `--field` / `--raw-field` is set).
- `-f key=value` — magic-typed (literals `true` / `false` / `null` /
  integers become JSON types, leading `@filename` reads from a file).
- `-F key=value` — same as `-f` but always treats the value as a string.
- `--paginate` — auto-walk `Link: rel="next"`.
- `--hostname <host>` — target a different GitLab host than default.
- Path placeholders: when run inside a git checkout, `:fullpath` /
  `:branch` / `:user` are auto-populated from the repo. From a generic
  shell, encode the path manually (see recipes).

## Recipes

### List open issues on a project

```sh
glab issue list --repo OWNER/PROJECT --opened --output json
glab issue list --repo OWNER/PROJECT --assignee=@me --output json
```

### View an issue with comments

```sh
glab issue view 42 --repo OWNER/PROJECT --comments
glab issue view 42 --repo OWNER/PROJECT --output json
```

### Create / comment / close an issue

```sh
glab issue create --repo OWNER/PROJECT --title "Bug: foo" --description "Repro steps…" --label bug
glab issue note 42 --repo OWNER/PROJECT --message "Acknowledged."
glab issue close 42 --repo OWNER/PROJECT
```

### List MRs assigned to / authored by me

```sh
glab mr list --repo OWNER/PROJECT --assignee=@me --opened --output json
glab mr list --repo OWNER/PROJECT --author=@me --opened
```

### View an MR with diff and CI pipeline

```sh
glab mr view 99 --repo OWNER/PROJECT
glab mr diff 99 --repo OWNER/PROJECT
glab ci view --repo OWNER/PROJECT --branch <BRANCH>
```

### Approve / merge / leave a note on an MR

```sh
glab mr approve 99 --repo OWNER/PROJECT
glab mr note 99 --repo OWNER/PROJECT --message "Looks good — ready when CI is green."
glab mr merge 99 --repo OWNER/PROJECT --squash --remove-source-branch
```

### Read a file from the default branch (raw bytes)

```sh
# URL-encode the project path AND the file path because both contain '/'.
PROJECT=$(printf '%s' 'OWNER/PROJECT' | jq -sRr @uri)
FILE=$(printf '%s' 'src/main.go' | jq -sRr @uri)
glab api "projects/${PROJECT}/repository/files/${FILE}/raw?ref=main"
```

### List the latest pipelines on a branch

```sh
glab ci list --repo OWNER/PROJECT --status running,success,failed
glab ci view --repo OWNER/PROJECT --branch main
glab ci trace --repo OWNER/PROJECT <JOB_ID>     # stream a job log
```

### Search across a group's issues

```sh
glab api "groups/GROUP_PATH_OR_ID/issues?state=opened&search=keyword" \
  --paginate \
  | jq '.[] | {iid, title, project: .references.full, web_url}'
```

### GraphQL example: project metadata + open MR count

```sh
glab api graphql -f query='
  query($path: ID!) {
    project(fullPath: $path) {
      name webUrl
      mergeRequests(state: opened) { count }
    }
  }' -f path=OWNER/PROJECT
```

## Notes

- `--repo OWNER/PROJECT` accepts `OWNER/PROJECT`, `GROUP/SUBGROUP/PROJECT`,
  full HTTPS URL, or git URL. The project path goes verbatim (no URL
  encoding) for `--repo`, but does need `jq @uri` encoding when used
  inside a `glab api` path.
- For self-hosted GitLab the user must have authorized the connection
  with the right `host`. A 404 on a project you know exists usually
  means the connection is pointing at gitlab.com when the project lives
  elsewhere — surface that hint to the user.
- Many `glab` commands have an `--output` flag that takes `text` (default)
  or `json`. `glab issue list` and `glab mr list` additionally have
  `--output-format` (`details` / `ids` / `urls`) which is a separate,
  list-only formatter. Pass the long flag `--output json` to avoid the
  short-flag confusion (`-O` vs `-F`).
