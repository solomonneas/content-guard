# Project Brief

## Why This Exists

Content Guard exists because the current scrubber setup works but is split across too many surfaces:

- an OpenClaw message hook
- a shell-based infrastructure scrubber
- a Python personal/content policy checker
- an optional OPF wrapper
- one-off publish script gates

That makes it hard to improve one part without leaving the others behind.

The new repo should become the shared engine for the system we actually use. As Content Guard improves, the local publishing and OpenClaw workflows should improve with it.

## Relationship To Privacy Filter

Privacy Filter is inspiration, not a base.

Useful ideas:
- model-backed PII detection can catch context-sensitive spans that regex rules miss
- span-oriented outputs are more useful than opaque pass/fail checks
- evaluation matters if the tool is going to be trusted

What Content Guard does differently:
- deterministic rules stay first-class
- policy decides action at the boundary
- OPF is optional and measured, not assumed to be right
- private rules live outside public source
- the first customer is our own workflow

## Success Criteria

Content Guard is working when:

- it replaces the hard `scrub-content` gate in at least one publishing path
- it scans PR drafts before they become public dogfood data
- it can scan staged or tracked Git files before public repo publication
- it can run OPF from policy without a manual CLI flag
- it has a private policy that covers the important local scrubber rules
- it produces useful reports for fixing content, not just blocking it
- OpenClaw outbound scrubbing can become a thin adapter over the same engine
- regressions are caught with fixtures from real false positives and real leaks

## Contribution Strategy

The goal is not to chase attention on an early external repo. The better strategy is to build a maintained tool with clear tests, real workflow pressure, and useful design notes.

If Privacy Filter or another project becomes active enough to contribute to later, Content Guard can provide:
- bug reports grounded in real pipeline use
- evaluation ideas
- adapter patterns
- policy and boundary-design feedback

But the source of truth should remain the tool we use every day.
