# Content Guard Roadmap

## Name

Working name: **Content Guard**

Why this name:
- Broad enough for blog posts, social drafts, agent messages, and CI gates.
- Does not imply perfect anonymization or legal compliance.
- Avoids copying Privacy Filter branding while still making the purpose obvious.
- Works naturally as a CLI: `content-guard scan`, `content-guard redact`, `content-guard diff`.

Alternatives considered:
- **ScrubKit**: good developer feel, but less clear for non-code publishing workflows.
- **Publish Guard**: strong for blog/social gates, too narrow for agent message hooks.
- **Redaction Guard**: accurate, but sounds narrower than policy scanning and blocking.
- **Signal Scrubber**: memorable, but ambiguous and more brand-heavy.

Decision: keep `content-guard` for now.

## Vision

Content Guard is a maintainable, policy-driven sanitization layer for public writing and agent output.

It combines:
- deterministic, explainable rules for high-confidence leaks
- optional model-backed PII detection through OPF
- private policy files for user-specific, organization-specific, and environment-specific concerns
- one report format that can power CLI checks, publish gates, OpenClaw hooks, and CI

The tool should fail loudly on known-dangerous leaks and avoid pretending that model-based PII detection is a guarantee.

The primary goal is to build what we will actually use. Every improvement should be able to make the local publishing and OpenClaw system safer, cleaner, or easier to operate. Open-source usefulness matters, but the first feedback loop is our own workflow.

## Core Principles

- **Explainable first:** every deterministic finding has a rule id, category, line, column, action, and replacement.
- **Policy over code edits:** personal names, private hostnames, business strategy, and organization-specific rules belong in policy files.
- **Optional heavy backends:** OPF and future model backends should be useful when installed, but never required for the core CLI.
- **No silent publish risk:** public publishing gates should block infrastructure and secret leaks by default.
- **Reviewable redaction:** preview/diff should be first-class. In-place mutation is explicit.
- **Honest scope:** this is a sanitization aid, not anonymization, compliance, or a privacy guarantee.

## Non-Goals

- No promise of complete anonymization.
- No bundled model weights.
- No copied Privacy Filter implementation.
- No required network calls in the core scanner.
- No default public policy that embeds private names, hosts, employers, or personal context.

## MVP Status

Implemented:
- Python package under `src/content_guard`
- CLI commands: `scan`, `redact`, `diff`
- Advisory PR draft helper: `python3 -m content_guard.pr_draft`
- OpenClaw plugin adapter under `openclaw-plugin/`
- Directory scans for markdown trees
- Built-in deterministic rules for infrastructure, secrets, email, and phone numbers
- Policy JSON loader
- Policy-controlled OPF backend configuration
- Actions: `allow`, `warn`, `redact`, `block`
- Markdown frontmatter skipping
- Fenced code block skipping option
- Allow comments: `<!-- content-guard: allow rule-id -->`
- Optional OPF subprocess adapter behind `--opf`
- Example policies for public content and OpenClaw messages
- Unit tests for core engine behavior

## Strategic Direction

The project should absorb the best parts of the existing local scrubber and the OPF-style model-backed approach, then improve them through daily use.

Near-term priority:
- make our publish gates better
- make our OpenClaw outbound message boundary better
- reduce false positives in real content
- evaluate where OPF helps and where deterministic rules are enough

Secondary priority:
- keep the repo clean enough to publish
- document design choices clearly
- leave a contribution-quality trail if Privacy Filter or similar projects become worth contributing to later

This is not a fork strategy. It is a use-first, learn-fast repo with optional OPF integration.

## Phase 1: Use-It-Here CLI

Goal: replace ad hoc local scripts for manual scans and publish gates.

Tasks:
- Add Git-aware scans for staged files and all tracked public repo content.
- Add `--format text|json|sarif` once the JSON schema settles.
- Add `--fail-on warn|block` for CI and scripts.
- Add `--summary-only` for low-noise automation.
- Add `--include` and `--exclude` glob handling.
- Add better markdown handling for inline code and HTML comments.
- Add fixture tests for existing false positives from scrubber-related blog posts.

Exit criteria:
- Can run `content-guard scan content/ --policy policies/public-content.json`.
- Output is stable enough to use in publish scripts.
- One real local publishing path runs Content Guard alongside the old scrubber before we remove anything.

## Phase 2: Policy Model

Goal: make policies expressive enough to replace `content-scrubber.py` without hardcoding private details in public files.

Tasks:
- Add backend config to policy files, especially OPF enablement.
- Add rule severity independent from action.
- Add per-path overrides.
- Add frontmatter-specific controls.
- Add custom replacement templates.
- Add named allowlists with expiration comments.
- Add policy validation command: `content-guard policy check`.

Example target:

```json
{
  "name": "public-content",
  "backends": {
    "opf": {
      "enabled": true,
      "action": "warn",
      "device": "cpu"
    }
  },
  "defaults": {
    "infrastructure": "block",
    "secret": "block",
    "pii": "warn"
  }
}
```

Exit criteria:
- OPF can be enabled by policy without requiring `--opf`.
- Private policy files can model the existing personal/business scrubber rules.
- OPF impact is measurable on local content fixtures before it becomes a blocker.

## Phase 3: Publishing Integration

Goal: wire Content Guard into real publish boundaries.

Tasks:
- Replace `scrub-content` calls in blog/social scripts with `content-guard scan`.
- Add PR draft scanning before generated PR bodies are published.
- Add staged-file scanning before commits to public repos.
- Keep old scripts as compatibility wrappers during transition.
- Add a `content-guard redact --in-place` workflow for manual cleanup.
- Add structured JSON reports to publishing logs.
- Define separate policies for blog, social, longform, and agent-message output.

Exit criteria:
- Publishing scripts use Content Guard as the hard gate.
- PR body publishing uses `policies/pr-draft.json`.
- Public repo commits can run `content-guard-git`.
- OPF runs only where the selected policy enables it.
- Existing skip environment variables are migrated or intentionally retired.

## Phase 4: OpenClaw Plugin

Goal: replace the current local OpenClaw content-scrubber plugin with a thin adapter around the shared engine.

Tasks:
- Use CLI shell-out first for single-source behavior.
- Add timeout and failure policy for message hooks.
- Support per-channel or per-recipient policies.
- Preserve owner-DM behavior intentionally, not by accident.
- Add plugin smoke tests.

Exit criteria:
- OpenClaw outbound message scrubbing uses the same policies and rule ids as publish gates.

## Phase 5: Evaluation and Quality

Goal: make the scrubber measurable and maintainable.

Tasks:
- Add a labeled fixture corpus with expected findings.
- Seed fixtures from real local false positives and leaks after redaction.
- Track false positives and false negatives by rule id.
- Add regression tests for all fixed leaks and false positives.
- Add benchmark mode for OPF latency and deterministic scanner latency.
- Add changelog and versioning policy.
- Compare deterministic-only, OPF-only, and combined modes on the same fixture set.

Exit criteria:
- Changes to rules or policies can be reviewed with objective fixture diffs.
- We can say when OPF improves recall enough to justify latency and review noise.

## First Integration Target

Use Content Guard alongside the old scripts first:

```bash
PYTHONPATH=src python3 -m content_guard scan file.md \
  --policy policies/public-content.json
```

Then migrate wrappers one at a time.

Recommended order:
1. `publish-blog.sh`
2. `blog-to-social.py`
3. `blog-to-substack.py`
4. `blog-to-x-article.py`
5. `blog-to-coderlegion.py`
6. PR draft generation/update workflow
7. public Git repo pre-commit/pre-push workflow
8. OpenClaw message hook

## Open Questions

- Should OPF be warn-only forever for public content, or block on specific categories after evaluation?
- Should private policy live in this repo untracked, or in the OpenClaw workspace?
- Should OpenClaw use the CLI directly, or should we eventually ship a TypeScript plugin package?
- Should the public repo include only generic policies, with private policy examples generated from templates?
- Should Git history scanning be a separate command, since scanning `.git/objects` directly is noisy and expensive?
