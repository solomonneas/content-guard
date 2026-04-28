# Content Guard

Content Guard is a policy-driven scanner and redactor for public content, publishing pipelines, and agent output.

It takes the practical parts of the existing local content scrubber and the useful model-backed idea behind Privacy Filter, then makes them one maintainable system:

- deterministic rules for infrastructure, secrets, and high-confidence patterns
- optional OPF backend for model-based PII redaction
- custom policy files for private names, internal projects, unreleased plans, and environment-specific rules
- blocking, warning, and redaction decisions from one report format
- markdown-aware scanning with frontmatter and allow-comment support

The core package has no required third-party dependencies. OPF is optional and runs through its CLI when available.

## Quick Start

```bash
python -m content_guard scan examples/sample.md --policy policies/public-content.json
python -m content_guard redact examples/sample.md --policy policies/public-content.json
python -m content_guard scan examples/sample.md --json
python -m content_guard scan examples/ --policy policies/public-content.json
```

Use OPF if it is installed locally:

```bash
python -m content_guard redact examples/sample.md --opf
```

By default, `--opf` looks for `~/.opf-venv/bin/opf`. Override with:

```bash
CONTENT_GUARD_OPF_BIN=/path/to/opf python -m content_guard scan file.md --opf
```

OPF can also be enabled from a policy file:

```json
{
  "backends": {
    "opf": {
      "enabled": true,
      "action": "warn",
      "device": "cpu"
    }
  }
}
```

## Allow Comments

Use a local allow comment on the same line or directly above a line:

```md
<!-- content-guard: allow localhost-bare -->
This tutorial uses localhost as an example.
```

Use `content-guard: allow all` sparingly for examples where every finding is intentional.

## Policy Files

Policies are JSON to keep the project dependency-free. A policy can set default actions by category, override individual rules, and add private custom regex rules.

```json
{
  "name": "public-content",
  "defaults": {
    "infrastructure": "block",
    "secret": "block",
    "pii": "warn"
  },
  "rules": {
    "email": "warn"
  },
  "custom_rules": [
    {
      "id": "internal-hostname-example",
      "category": "infrastructure",
      "pattern": "\\\\binternal-host\\\\b",
      "replacement": "[redacted-host]"
    }
  ]
}
```

Actions:

- `block`: fail the scan, usually for publish gates
- `redact`: rewrite the content
- `warn`: report without failing
- `allow`: ignore matching findings

### Bundled policies

Two of the bundled policies share the `infrastructure` category but treat it differently on purpose:

- `policies/public-repo.json` — for technical docs repos. Keeps `private-ipv4` (RFC 1918), secrets, PII, and `Co-authored-by` trailers as hard blocks, but downgrades `loopback-ipv4` (127.x), `localhost-port`, `localhost-bare`, and `port-reference` to warnings. README and CONTRIBUTING legitimately have to discuss `localhost`, named ports, and `127.0.0.1` for setup instructions. See [policies/public-repo.md](policies/public-repo.md) for the long-form rationale.
- `policies/public-content.json` — for blog posts and social drafts. Keeps the full infrastructure category at block, since marketing surfaces have a higher leak risk and shouldn't discuss internal addresses or named ports at all.

## PR And Git Guards

PR bodies and public repository content are publishing boundaries too. Use stricter policies before copying generated summaries, dogfood notes, local test output, fixtures, or docs into public GitHub surfaces:

```bash
python -m content_guard scan examples/pr-body.md --policy policies/pr-draft.json
python -m content_guard diff examples/pr-body.md --policy policies/pr-draft.json
python -m content_guard.pr_draft examples/pr-body.md
python -m content_guard.pr_prepare examples/pr-body.md --json
python -m content_guard.publish_check --pr-body examples/pr-body.md --json
python -m content_guard.n8n_advisory < payload.json
python -m content_guard.n8n_validate --json
python -m content_guard.git_scan --policy policies/public-repo.json
python -m content_guard.git_scan --all-tracked --policy policies/public-repo.json
python -m content_guard.git_commits --range origin/main..HEAD --policy policies/public-repo.json
```

See [docs/PR_DRAFTS.md](docs/PR_DRAFTS.md) and [docs/GIT_PUBLIC_REPO_GUARD.md](docs/GIT_PUBLIC_REPO_GUARD.md).

Use `content_guard.publish_check` as the practical local pre-publish wrapper. It prepares a sanitized PR body when `--pr-body` is provided, scans staged files, scans commit messages, and can optionally scan all tracked files:

```bash
PYTHONPATH=src python -m content_guard.publish_check --pr-body pr-body.md --json
PYTHONPATH=src python -m content_guard.publish_check --pr-body pr-body.md --all-tracked
```

PR body findings are advisory by default because the wrapper writes a sanitized body and prints `publish_body_file`. Staged file, commit message, and optional all-tracked blockers fail the command unless `--advisory-only` is set.

Use `content_guard.pr_prepare` when a later PR publishing step needs a stable sanitized body path:

```bash
PYTHONPATH=src python -m content_guard.pr_prepare pr-body.md
gh pr create --body-file .content-guard/pr-drafts/pr-body.public.md
```

For local run-alongside testing against the legacy scrubber, see [docs/DOGFOOD_TEST_REPO.md](docs/DOGFOOD_TEST_REPO.md).

For n8n publish workflows, start with an advisory step that reports findings
without mutating live publishes. See [docs/N8N_ADVISORY.md](docs/N8N_ADVISORY.md)
and [docs/N8N_WORKFLOW_RECIPE.md](docs/N8N_WORKFLOW_RECIPE.md). Validate cloned
workflow wiring with [docs/N8N_VALIDATION_PACK.md](docs/N8N_VALIDATION_PACK.md).

## OpenClaw Plugin

Content Guard can also run as an OpenClaw outbound message plugin. The plugin lives in `openclaw-plugin/` and shells out to the same Python engine, so OpenClaw messages use the same policy model as publish gates.

See [docs/OPENCLAW_PLUGIN.md](docs/OPENCLAW_PLUGIN.md).

## Design Notes

Privacy Filter influenced the optional model-backed PII layer, especially the idea that some personal data detection benefits from context. Content Guard does not copy Privacy Filter code. OPF integration is a subprocess adapter so the deterministic engine remains portable and maintainable.

The deterministic rules are intentionally conservative. Public publishing should fail loudly on infrastructure and secret leakage, while model findings are better treated as review signals until a local policy proves they are reliable enough to block.
