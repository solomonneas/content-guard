# Migration Strategy

This page describes the staged migration from the old `scrub-content` and `content-scrubber` paths to Content Guard.

The migration goal is continuity first: keep the existing scrubber available while Content Guard proves equivalent or better behavior at each publishing boundary.

## Stage 1: Run Alongside

Keep the old scrubber in place and add Content Guard as a parallel check.

Recommended boundaries:

- PR draft text before publishing to GitHub
- public blog or social drafts before posting
- staged Git files before commit
- commit messages before push
- all tracked files before making a repository public
- generated release notes, changelogs, examples, and fixtures

Example commands:

```bash
python -m content_guard scan path/to/draft.md --policy policies/public-content.json --json
python -m content_guard.publish_check --pr-body path/to/pr-body.md --json
python -m content_guard.pr_prepare path/to/pr-body.md --policy policies/pr-draft.json --json
python -m content_guard.git_scan --policy policies/public-repo.json --json
python -m content_guard.git_commits --range origin/main..HEAD --policy policies/public-repo.json --json
```

During this stage, do not fail production publishing solely on Content Guard unless the same issue is also caught by the old scrubber or confirmed by review.

## Stage 2: Compare

Compare old scrubber output with Content Guard output for the same input corpus.

Track:

- findings caught by both tools
- findings caught only by the old scrubber
- findings caught only by Content Guard
- false positives that block or redact acceptable content
- missing private policy terms that should live outside the public repo
- differences between warning, redaction, and blocking behavior

Use the report contract in [REPORT_CONTRACT.md](REPORT_CONTRACT.md) for automated comparisons. For file-level Git checks, use `git_scan --json` to identify files with findings, then run `scan --json` on individual files when exact finding locations are needed.

Expected outcomes:

- Content Guard policies include all required old scrubber private terms through untracked or external private policy files
- deterministic categories have clear actions for each publishing boundary
- accepted differences are documented as policy decisions, not left as unexplained drift

## Stage 3: Switch

Switch one boundary at a time from the old scrubber to Content Guard.

Recommended order:

1. Manual draft review commands.
2. PR body and local repo checks through `content_guard.publish_check`.
3. Focused PR body and release note checks through `content_guard.pr_prepare` where a combined repo check is not needed.
4. Public content publish gates.
5. Git staged-file, commit-message, or all-tracked repository guards.
6. Agent outbound message checks.

For each boundary:

- keep the old scrubber command available for fallback
- record the Content Guard command, policy path, and expected exit behavior
- fail the boundary on `block`
- treat `warn` findings as review signals
- preserve private rules in untracked local policy files or external workspace policy paths
- use `publish_check --advisory-only` only for run-alongside comparison, not as the final hard gate

Switching is complete for a boundary when Content Guard is the default command, the old scrubber no longer runs automatically there, and rollback instructions are documented.

## Stage 4: Retire

Retire `scrub-content` and `content-scrubber` only after the switched boundaries have run successfully for a full review period.

Before removal:

- confirm no active scripts, hooks, CI jobs, aliases, or plugin configs still call the old paths
- archive any old scrubber rules that were intentionally not migrated
- move durable operational notes into Content Guard docs
- keep private policy material out of tracked public files
- update local runbooks to reference Content Guard commands

After removal:

- delete obsolete local wrappers or aliases
- remove old scrubber references from internal docs
- keep a short migration note with the retirement date and rollback context

## Rollback

If Content Guard blocks a required publishing path incorrectly, restore the old scrubber for that boundary while the policy is corrected.

Rollback should be narrow:

- revert only the affected boundary
- keep Content Guard running manually or in advisory mode for comparison
- add a policy fixture or documented example for the failure mode
- switch back after the policy behavior is verified
