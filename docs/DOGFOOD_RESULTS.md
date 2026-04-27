# Dogfood Results

## 2026-04-27 PR Boundary Test Repo

Test repo:

```text
~/scratch/content-guard-dogfood-test
```

Command:

```bash
scripts/dogfood-pr-boundary.sh ~/scratch/content-guard-dogfood-test
```

Result summary:

- Legacy `scrub-content` caught infrastructure in `pr-body.md`.
<!-- content-guard: allow all -->
- Content Guard caught infrastructure and PII in `pr-body.md`: `localhost:5204`, `alice@example.com`, and `192.168.1.50`.
- The advisory PR helper wrote `pr-body.public.md` and `pr-body.content-guard.json`, then exited zero with `advisory=true`.
<!-- content-guard: allow all -->
- Content Guard staged-file scan caught PR-body findings plus public staged file findings: `token = abcdefghijklmnopqrstuvwxyz123456` and `alice@example.com`.
- Content Guard found more true positives than the legacy scrubber because the PR/public-repo policies block PII and secrets, not just infrastructure patterns.

Decision:

- Keep live publish/OpenClaw paths unchanged.
- Use this dogfood check as the first migration comparison.
- The advisory PR helper is now the first migration wrapper. Next target should be running it against one real generated PR body before publishing, still without changing live OpenClaw or publish hooks.

## 2026-04-27 Watchtower PR Draft Scratch Test

Source:

```text
~/scratch/watchtower-pr-dogfood/pr-body.md
```

The draft used recent Watchtower speedtest auth/export work plus review context, then intentionally included boundary-risk validation notes.

Commands:

```bash
PYTHONPATH=src python3 -m content_guard.pr_draft ~/scratch/watchtower-pr-dogfood/pr-body.md \
  --policy policies/pr-draft.json
PYTHONPATH=src python3 -m content_guard.pr_draft ~/scratch/watchtower-pr-dogfood/pr-body.md \
  --policy policies/pr-draft.json --strict
```

Result summary:

- Advisory mode wrote `pr-body.public.md` and `pr-body.content-guard.json`, then exited zero with `advisory=true`.
- Strict mode exited nonzero with the same five blocking findings.
- Findings were two local host services, one private lab target, one email address, and one token assignment.
- Redaction preserved PR body readability and kept punctuation around the token assignment after tightening the secret rule.

Decision:

- This is a useful pre-PR dogfood boundary even when the source repo is not being modified.
- Keep generated PR bodies in scratch until the user chooses to publish.
- The next migration step was to add a small wrapper command that prepares a PR body, runs advisory guard, and makes the sanitized path explicit to the publishing tool.

## 2026-04-27 PR Prepare Wrapper

Command:

```bash
PYTHONPATH=src python3 -m content_guard.pr_prepare ~/scratch/watchtower-pr-dogfood/pr-body.md \
  --out-dir ~/scratch/watchtower-pr-dogfood/prepared \
  --policy policies/pr-draft.json --json
```

Result summary:

- The wrapper wrote `pr-body.draft.md`, `pr-body.public.md`, and `pr-body.content-guard.json` into the prepared scratch directory.
- The JSON payload included `publish_body_file`, pointing to the sanitized body that a later PR publisher should use.
- The wrapper kept advisory behavior by default and still exposed strict mode for hard gates.
- The sanitized body scanned clean with the PR draft policy.

Decision:

- Use `content_guard.pr_prepare` as the handoff layer between generated PR body text and any future publishing command.
- Do not publish the raw draft or JSON report. They can contain private findings for review.

## 2026-04-27 Commit Message Guard

Command:

```bash
PYTHONPATH=src python3 -m content_guard.git_commits --range HEAD \
  --policy policies/public-repo.json --json
```

Result summary:

- Temporary Git fixture with a co-author trailer blocked on `attribution/coauthored-by-trailer`.
- Temporary Git fixture with a normal commit message passed.
- Empty repositories return a clean zero-commit JSON report instead of failing on an unborn `HEAD`.
- The JSON commit report intentionally omits raw matched text because commit messages can contain names and email addresses.

Decision:

- Use `content_guard.git_commits` alongside `content_guard.git_scan` for public repo guarding.
- Staged-file scans cannot cover commit-message-only metadata, so commit scanning must be its own gate before push or PR publish.

## 2026-04-27 Publish Check Wrapper

Source:

```text
~/scratch/watchtower-pr-dogfood/pr-body.md
```

Command:

```bash
PYTHONPATH=src python3 -m content_guard.publish_check \
  --pr-body /home/clawdbot/scratch/watchtower-pr-dogfood/pr-body.md \
  --out-dir /home/clawdbot/scratch/watchtower-pr-dogfood/publish-check \
  --json
```

Result summary:

- The wrapper exited zero because only the PR body had blockers, and PR body preparation is advisory by default.
- The combined payload reported `blocked=true`, `ok=true`, and `would_fail=false`.
- `publish_body_file` pointed to `/home/clawdbot/scratch/watchtower-pr-dogfood/publish-check/pr-body.public.md`.
- The PR body check found the same five blockers as the prior prepare test.
- Staged-file scanning checked zero staged files and passed.
- Commit-message scanning checked zero commits in this scratch context and passed.

Decision:

- Use `content_guard.publish_check` as the practical local pre-publish wrapper for PR body plus repo guard checks.
- Keep `pr_prepare`, `git_scan`, and `git_commits` available as focused lower-level commands.
- Do not wire the wrapper into live OpenClaw or live publishing until the surrounding workflow is explicitly switched.
