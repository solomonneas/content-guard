# PR Draft Guard

PR drafts are a publishing boundary.

They often include implementation notes, test commands, copied logs, generated summaries, and dogfood observations. That makes them high-risk for private hostnames, local paths, personal context, internal project names, API endpoints, credentials, and accidental PII.

## Policy

Use:

```bash
PYTHONPATH=src python3 -m content_guard scan pr-body.md \
  --policy policies/pr-draft.json
```

The PR draft policy blocks:

- infrastructure
- secrets
- PII
- personal policy matches
- business policy matches

OPF is currently warn-only until fixture evaluation proves it is reliable enough to block.

## Workflow

Generate the PR body into a file first:

```bash
cat > pr-body.md <<'EOF'
Summary...
Tests...
EOF
```

Scan it before creating or updating the PR:

```bash
PYTHONPATH=src python3 -m content_guard scan pr-body.md \
  --policy policies/pr-draft.json
```

Preview redactions:

```bash
PYTHONPATH=src python3 -m content_guard diff pr-body.md \
  --policy policies/pr-draft.json
```

Create a sanitized copy only when the diff looks right:

```bash
PYTHONPATH=src python3 -m content_guard redact pr-body.md \
  --policy policies/pr-draft.json > pr-body.public.md
```

Then use the sanitized body with your PR tool.

## Publish Check Wrapper

Use the publish check wrapper when preparing a PR body and checking the local repo should happen together:

```bash
PYTHONPATH=src python3 -m content_guard.publish_check \
  --pr-body pr-body.md \
  --json
```

The wrapper:

- prepares the PR body through `content_guard.pr_prepare`
- prints `publish_body_file` for the sanitized body path
- scans staged files with the public repo policy
- scans commit messages with the public repo policy
- optionally scans all tracked files with `--all-tracked`

PR body findings are advisory by default because the sanitized body is the publishing input. Staged file, commit message, and optional all-tracked blockers fail the command unless `--advisory-only` is set.

## Prepare For Publishing

Use the prepare wrapper when PR creation or update tooling needs a clean handoff path:

```bash
PYTHONPATH=src python3 -m content_guard.pr_prepare pr-body.md
```

By default this writes a bundle under:

```text
.content-guard/pr-drafts/
```

The bundle contains:

- `<name>.draft.md` - the original draft body
- `<name>.public.md` - the sanitized body to pass to PR tooling
- `<name>.content-guard.json` - the private scan report

The human output includes:

```text
publish_body_file=.content-guard/pr-drafts/pr-body.public.md
gh_body_arg=--body-file .content-guard/pr-drafts/pr-body.public.md
```

Machine callers can use JSON:

```bash
PYTHONPATH=src python3 -m content_guard.pr_prepare pr-body.md --json
```

Use only `publish_body_file` or `sanitized` as the public PR body input. Treat the draft and JSON report as private artifacts because they can contain raw findings for review.

Strict mode turns the same wrapper into a gate:

```bash
PYTHONPATH=src python3 -m content_guard.pr_prepare pr-body.md --strict
```

## Advisory Helper

Use the advisory helper when you want sanitized output and a report without blocking the workflow:

```bash
PYTHONPATH=src python3 -m content_guard.pr_draft pr-body.md
```

By default this writes:

```text
pr-body.public.md
pr-body.content-guard.json
```

It exits zero even when blocked findings are present, then prints `advisory=true`. Use `--strict` when you want a nonzero exit on blocked findings:

```bash
PYTHONPATH=src python3 -m content_guard.pr_draft pr-body.md --strict
```

After reviewing the diff and report, use the `.public.md` file as the PR body.

## Private Dogfood Policy

The public `pr-draft.json` intentionally contains no private names or local environment details. Add those in an untracked private policy or an external workspace policy.

Keep real private policy files out of the public repo.
