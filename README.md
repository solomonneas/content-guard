<p align="center">
  <img src="docs/assets/content-guard-banner.jpg" alt="Content Guard banner">
</p>

<h1 align="center">Content Guard</h1>

<p align="center">
  <strong>Policy-driven scanning and redaction for public content, publishing pipelines, and agent output.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue?style=for-the-badge" alt="Apache-2.0 license">
  <img src="https://img.shields.io/badge/dependencies-zero_required-2ea44f?style=for-the-badge" alt="Zero required third-party dependencies">
  <img src="https://img.shields.io/badge/OPF-optional-8A2BE2?style=for-the-badge" alt="Optional OPF backend">
  <img src="https://img.shields.io/badge/markdown-aware-083344?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown aware">
</p>

Content Guard keeps private infrastructure, secrets, and personal context out of public surfaces before they ship. It is built for Markdown docs, PR bodies, social drafts, generated agent output, and automation pipelines where one sloppy paste can leak more than intended.

It takes the practical parts of the local content scrubber and the useful model-backed idea behind Privacy Filter, then turns them into one maintainable system.

## What It Checks

- Deterministic rules for infrastructure, secrets, and high-confidence patterns
- Optional OPF backend for model-based PII review and redaction
- Custom policy files for private names, internal projects, unreleased plans, and environment-specific rules
- Blocking, warning, redaction, and allow decisions from one report format
- Markdown-aware scanning with frontmatter and allow-comment support

The core package has no required third-party dependencies. OPF is optional and runs through its CLI when available.

## Quick Start

Install from a local clone:

```bash
python -m pip install -e .
```

Scan or redact a file:

```bash
content-guard scan examples/sample.md --policy policies/public-content.json
content-guard redact examples/sample.md --policy policies/public-content.json
content-guard scan examples/sample.md --json
content-guard scan examples/ --policy policies/public-content.json
```

Use OPF if it is installed locally:

```bash
content-guard redact examples/sample.md --opf
```

By default, `--opf` looks for `~/.opf-venv/bin/opf`. Override it with:

```bash
CONTENT_GUARD_OPF_BIN=/path/to/opf content-guard scan file.md --opf
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

## Policies

Policies are JSON so the project stays dependency-free. A policy can set default actions by category, override individual rules, and add private custom regex rules.

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
- `redact`: rewrite matching content
- `warn`: report without failing
- `allow`: ignore matching findings

### Bundled Policies

Two bundled policies share the `infrastructure` category but treat it differently on purpose:

- `policies/public-repo.json`: for technical docs repos. It keeps `private-ipv4` (RFC 1918), secrets, PII, and `Co-authored-by` trailers as hard blocks, but downgrades `loopback-ipv4` (127.x), `localhost-port`, `localhost-bare`, and `port-reference` to warnings. README and CONTRIBUTING files often need to discuss `localhost`, named ports, and `127.0.0.1` for setup instructions. See [policies/public-repo.md](policies/public-repo.md) for the long-form rationale.
- `policies/public-content.json`: for blog posts and social drafts. It keeps the full infrastructure category at block because marketing surfaces have a higher leak risk and should not expose internal addresses or named ports.

## Allow Comments

Use a local allow comment on the same line or directly above a line:

```md
<!-- content-guard: allow localhost-bare -->
This tutorial uses localhost as an example.
```

Use `content-guard: allow all` sparingly for examples where every finding is intentional.

## PR and Git Guards

PR bodies and public repository content are publishing boundaries too. Use stricter policies before copying generated summaries, dogfood notes, local test output, fixtures, or docs into public GitHub surfaces:

```bash
content-guard scan examples/pr-body.md --policy policies/pr-draft.json
content-guard diff examples/pr-body.md --policy policies/pr-draft.json
content-guard-pr examples/pr-body.md
content-guard-pr-prepare examples/pr-body.md --json
content-guard-publish-check --pr-body examples/pr-body.md --json
content-guard-n8n-advisory < payload.json
content-guard-n8n-validate --json
content-guard-git --policy policies/public-repo.json
content-guard-git --all-tracked --policy policies/public-repo.json
content-guard-commits --range origin/main..HEAD --policy policies/public-repo.json
```

See [docs/PR_DRAFTS.md](docs/PR_DRAFTS.md) and [docs/GIT_PUBLIC_REPO_GUARD.md](docs/GIT_PUBLIC_REPO_GUARD.md).

Use `content-guard-publish-check` as the practical local pre-publish wrapper. It prepares a sanitized PR body when `--pr-body` is provided, scans staged files, scans commit messages, and can optionally scan all tracked files:

```bash
content-guard-publish-check --pr-body pr-body.md --json
content-guard-publish-check --pr-body pr-body.md --all-tracked
```

PR body findings are advisory by default because the wrapper writes a sanitized body and prints `publish_body_file`. Staged file, commit message, and optional all-tracked blockers fail the command unless `--advisory-only` is set.

Use `content-guard-pr-prepare` when a later PR publishing step needs a stable sanitized body path:

```bash
content-guard-pr-prepare pr-body.md
gh pr create --body-file .content-guard/pr-drafts/pr-body.public.md
```

For local run-alongside testing against the legacy scrubber, see [docs/DOGFOOD_TEST_REPO.md](docs/DOGFOOD_TEST_REPO.md).

For n8n publish workflows, start with an advisory step that reports findings without mutating live publishes. See [docs/N8N_ADVISORY.md](docs/N8N_ADVISORY.md) and [docs/N8N_WORKFLOW_RECIPE.md](docs/N8N_WORKFLOW_RECIPE.md). Validate cloned workflow wiring with [docs/N8N_VALIDATION_PACK.md](docs/N8N_VALIDATION_PACK.md).

## OpenClaw Plugin

Content Guard can also run as an OpenClaw outbound message plugin. The plugin lives in `openclaw-plugin/` and shells out to the same Python engine, so OpenClaw messages use the same policy model as publish gates.

See [docs/OPENCLAW_PLUGIN.md](docs/OPENCLAW_PLUGIN.md).

## Design Notes

Privacy Filter influenced the optional model-backed PII layer, especially the idea that some personal data detection benefits from context. Content Guard does not copy Privacy Filter code. OPF integration is a subprocess adapter so the deterministic engine remains portable and maintainable.

The deterministic rules are intentionally conservative. Public publishing should fail loudly on infrastructure and secret leakage, while model findings are better treated as review signals until a local policy proves they are reliable enough to block.
