# Fixtures

Fixtures under `tests/fixtures/` are sanitized dogfood examples. They should
model real mistakes found during local use without preserving private material.

## Layout

- `tests/fixtures/real_world/clean_content.md` - publishable content with no expected findings.
- `tests/fixtures/real_world/infrastructure_leak.md` - internal infrastructure-shaped values.
- `tests/fixtures/real_world/pr_draft_leak.md` - draft pull request notes that include local-only context.
- `tests/fixtures/real_world/allowed_localhost_example.md` - intentional local host usage with an allow comment.
- `tests/fixtures/real_world/secret_leak.md` - fake secret-shaped values.

## Collection Workflow

Use fixtures to capture patterns from real local false positives and real leaks
after redaction.

1. Save the original finding outside the repository.
2. Replace private values with synthetic equivalents that preserve detector
   shape, such as RFC 1918-style addresses, `.example.test` hostnames, fake
   usernames, fake ticket IDs, and fake token strings.
3. Remove names, real repo paths, real service names, real domains, real IPs,
   credentials, account IDs, customer details, and personal context.
4. Keep enough surrounding text to explain why the example appeared in normal
   work.
5. Add a short expected-handling note when the fixture represents a leak.
6. Re-scan the fixture before committing it.

Fixtures should be small and readable. Prefer one concept per file so future
tests can opt into only the scenario they need.

## Redaction Rules

Never commit raw dogfood captures. Redaction should happen before a fixture file
is created in this repository.

Keep detector-relevant shape where possible:

- Use `redacted-internal.example.test` or another reserved example domain for
  hostnames.
- Use private-range but synthetic IPs for infrastructure examples.
- Use fake local paths like `/home/example-user/work/private-repo`.
- Use fake tokens that are clearly synthetic but still match generic secret
  patterns.
- Use fake issue keys such as `REDACTED-TRACKER-123`.

When a false positive needs a regression fixture, include only the minimum text
needed to reproduce it. If preserving the shape would expose private meaning,
prefer a less exact synthetic example and describe the tradeoff in this document
or the future test case.
