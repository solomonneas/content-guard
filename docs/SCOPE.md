# Scope

## What Content Guard Is

Content Guard is a scanner, redactor, and policy gate for text leaving a private workspace.

Primary use cases:
- public blog publishing
- social post drafting
- PR draft scanning before GitHub publishing
- public Git repository content guarding
- cross-posting to platforms
- agent outbound messages
- CI checks for accidental leaks
- manual review before sharing generated content

## What It Detects

Built-in deterministic categories:
- infrastructure: private IPs, local host references, internal service ports
- secrets: bearer tokens, API key assignments, private key blocks
- PII basics: email and US-style phone numbers

Policy-defined categories:
- personal names
- private organizations or roles
- unreleased projects
- business strategy
- sensitive financial context
- internal hostnames, domains, service accounts, and path patterns

Optional model-backed categories:
- OPF-detected PII, surfaced as the `opf-pii` rule id in the `pii` category

## Action Model

Each finding resolves to one action:

- `allow`: record or ignore as intentional depending on caller
- `warn`: report, do not fail
- `redact`: replace in redacted output, do not fail
- `block`: fail scan and replace in redacted output

This lets the same detector support multiple boundaries. A blog publish gate can block private IPs, while an owner-only review command can warn.

## Boundaries

Content Guard should run at boundaries, not constantly mutate drafts.

Good boundaries:
- before `git commit` or `git push` of public content
- before creating or updating a PR body
- before making a private repo public
- before browser automation posts to a platform
- before an agent response is sent to an external channel
- before publishing generated longform content

Bad boundaries:
- every keystroke
- automatic in-place mutation without review
- private notes where false positives would create noise

## Public vs Private Configuration

The public repo should contain generic rules and example policies only.

Private policy should live outside tracked public files, for example:

```text
~/.openclaw/workspace/config/content-guard/private-policy.json
```

or an untracked local file:

```text
policies/private.local.json
```

Private policy can include names, employers, hostnames, internal project labels, and personal context.
