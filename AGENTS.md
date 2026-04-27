# Project Rules

- Keep the core package dependency-free unless a dependency is explicitly approved.
- Treat OpenAI Privacy Filter as inspiration and an optional runtime backend. Do not copy its implementation into this repo.
- Prefer deterministic, explainable rules for hard publish gates.
- Keep personal or environment-specific patterns in policy files, not in public default code.
- Run the smallest meaningful verification before reporting success.

## Review Gates

- For substantive code changes, run the smallest meaningful local verification first.
- After local verification passes, run `codex review --uncommitted` when the Codex CLI is available.
- Also run the Claude Code `code-review` workflow with Opus when available. If the slash command is unavailable in non-interactive mode, use the installed code-reviewer agent with `--model opus`.
- Treat external review output as read-only input. Apply fixes intentionally in the main workspace and re-run local verification.
- If a review tool cannot run because of sandboxing, auth, missing commands, or unavailable skills, report the exact blocker. Do not bypass sandboxing or permissions without explicit approval.

## Publishing Boundaries

- PR bodies must go through `content_guard.pr_prepare` before a public PR create or update command uses them.
- Public repo file checks must run through `content_guard.git_scan`.
- Commit-message checks must run through `content_guard.git_commits`, because staged-file scans cannot see Git metadata such as co-author trailers.
- OpenClaw outbound-message guarding must remain single-owner. Do not enable the Content Guard OpenClaw plugin while another overlapping scrubber is active.
