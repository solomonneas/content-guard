# Dogfood Test Repo

Use a throwaway local Git repository to compare Content Guard against the legacy scrubber before changing live publishing paths.

Recommended location:

```text
~/scratch/content-guard-dogfood-test
```

Run:

```bash
scripts/dogfood-pr-boundary.sh ~/scratch/content-guard-dogfood-test
```

The script checks:

- `pr-body.md` with legacy `scrub-content`
- `pr-body.md` with `content_guard scan --policy policies/pr-draft.json`
- `pr-body.md` with advisory `content_guard.pr_draft`
- staged Git files with `content_guard.git_scan --policy policies/public-repo.json`
- commit messages with `content_guard.git_commits --policy policies/public-repo.json`

## Expected Comparison

The legacy scrubber only knows deterministic infrastructure patterns. It should catch local service and private IP references.

Content Guard should catch those plus stricter PR and public repo findings such as:

- email addresses
- phone numbers
- bearer tokens
- API key assignments
- private key blocks
- co-author trailers in commit messages or copied commit text
- custom private policy matches, when configured

Do not switch a live boundary just because Content Guard catches more. First decide whether the extra findings are true positives or policy noise.
