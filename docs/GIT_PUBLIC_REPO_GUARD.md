# Git Public Repo Guard

Public repositories need guarding around more than PR bodies.

Content Guard should protect:

- staged files before commit
- commit messages before push
- tracked files before first public push
- generated PR bodies
- release notes and changelogs
- examples, fixtures, docs, and test data
- optional Git config review for tokenized remotes

Do not scan raw `.git/objects` as normal content. It is a compressed object database, can contain historical content, and will create noise. Guard the public surfaces that leave the machine: tracked files, staged diffs, PR text, and release artifacts.

## Publish Check Wrapper

For the normal PR or repo publish path, run the combined wrapper first:

```bash
PYTHONPATH=src python3 -m content_guard.publish_check \
  --pr-body pr-body.md \
  --json
```

This prepares a sanitized PR body, scans staged files, and scans commit messages. Add `--all-tracked` before the first public push or when checking a cleanup branch:

```bash
PYTHONPATH=src python3 -m content_guard.publish_check \
  --pr-body pr-body.md \
  --all-tracked
```

The command fails on blocked staged files, blocked commit messages, or blocked all-tracked findings. PR body blockers remain advisory by default because the wrapper writes a sanitized body and prints `publish_body_file`. Use `--advisory-only` to collect the same report without a nonzero exit.

## Staged Files

Before commit:

```bash
PYTHONPATH=src python3 -m content_guard.git_scan \
  --policy policies/public-repo.json
```

This scans staged added, copied, modified, and renamed files.

## Commit Messages

Before pushing or opening a PR:

```bash
PYTHONPATH=src python3 -m content_guard.git_commits \
  --policy policies/public-repo.json
```

By default, this scans `@{upstream}..HEAD` when the current branch has an upstream, or `HEAD` when no upstream is configured. To scan a specific PR range:

```bash
PYTHONPATH=src python3 -m content_guard.git_commits \
  --range origin/main..HEAD \
  --policy policies/public-repo.json
```

This catches commit-message-only publishing risks such as co-author trailers. Staged-file scanning cannot see those because they live in Git metadata, not tracked file content.

## Entire Tracked Repo

Before making a repo public or pushing a cleanup branch:

```bash
PYTHONPATH=src python3 -m content_guard.git_scan \
  --all-tracked \
  --policy policies/public-repo.json
```

Use `git_commits --all` separately if the full public history also needs commit-message review:

```bash
PYTHONPATH=src python3 -m content_guard.git_commits \
  --all \
  --policy policies/public-repo.json
```

## Include Git Config

To check `.git/config` for accidentally tokenized remotes:

```bash
PYTHONPATH=src python3 -m content_guard.git_scan \
  --all-tracked \
  --include-git-config \
  --policy policies/public-repo.json
```

## Pre-Commit Hook

Local hook example:

```bash
#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python3 -m content_guard.git_scan \
  --policy policies/public-repo.json
PYTHONPATH=src python3 -m content_guard.git_commits \
  --policy policies/public-repo.json
```

Keep hooks local by default. The tool should protect the workflow without forcing every public contributor to install local private policies.

## Private Repo Policy

The public `public-repo.json` policy blocks generic leak classes. Use an untracked local policy for private names, internal project labels, hostnames, and business context:

```bash
PYTHONPATH=src python3 -m content_guard.git_scan \
  --policy policies/private-repo.local.json
```

Do not commit private policy files.
