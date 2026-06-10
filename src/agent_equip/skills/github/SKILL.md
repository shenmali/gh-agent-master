---
name: github
description: Work with GitHub repos, issues, pull requests, releases, and search using the gh CLI. Use whenever the user asks about a GitHub repository, issues, PRs, releases, CI runs, or wants to search GitHub.
---

# GitHub via the gh CLI

Use the official `gh` CLI for all GitHub work. It is installed and authenticated on this machine (if a command fails with an auth error, see Troubleshooting below).

## Ground rules

- Prefer `gh` subcommands; for anything without a subcommand, use `gh api <endpoint>`.
- Need machine-readable output? Add `--json <fields>` and filter with `--jq <expr>`.
- Destructive actions (deleting repos, force-pushing, closing others' issues) require explicit user confirmation first.
- For public repos, `gh` works even without auth for many read operations — try before declaring failure.

## Recipes

### Inspect a repo

```bash
gh repo view owner/repo                        # README + metadata
gh repo view owner/repo --json description,stargazerCount,primaryLanguage,licenseInfo
gh repo clone owner/repo                       # clone (uses your auth)
gh api repos/owner/repo/languages              # language breakdown
gh api repos/owner/repo/commits --jq '.[0:5] | .[] | .commit.message'   # last 5 commit messages
```

### Search GitHub

```bash
gh search repos "vector database" --language=rust --sort=stars --limit 10
gh search code "def parse_config" --repo owner/repo
gh search issues "memory leak" --repo owner/repo --state open
gh search prs "fix auth" --repo owner/repo --merged
```

### Issues

```bash
gh issue list --repo owner/repo --state open --limit 20
gh issue view 123 --repo owner/repo --comments
gh issue create --repo owner/repo --title "Bug: ..." --body "..."
gh issue comment 123 --repo owner/repo --body "..."
```

### Pull requests

```bash
gh pr list --repo owner/repo --state open
gh pr view 42 --repo owner/repo --comments
gh pr diff 42 --repo owner/repo
gh pr checkout 42                              # inside a clone
gh pr create --title "..." --body "..."        # from current branch
gh pr review 42 --approve --body "LGTM"
```

### Releases and CI

```bash
gh release list --repo owner/repo
gh release view v1.2.0 --repo owner/repo
gh run list --repo owner/repo --limit 10       # recent CI runs
gh run view <run-id> --repo owner/repo --log-failed
```

### Anything else: gh api

```bash
gh api repos/owner/repo/stats/participation    # weekly commit activity
gh api user                                    # who am I
gh api -X POST repos/owner/repo/forks          # fork a repo
```

## Troubleshooting

- **Auth errors / 401:** run `gh auth status`; if logged out, ask the user to run `gh auth login` (interactive).
- **404 on a repo that should exist:** likely a private repo and the current auth lacks access — check `gh auth status` output for the active account.
- **403 rate limit:** check `gh api rate_limit`; authenticated requests get much higher limits, so make sure auth is active.
- **`gh: command not found`:** ask the user to run `agent-equip doctor` for install guidance.
