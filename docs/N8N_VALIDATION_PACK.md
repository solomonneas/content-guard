# n8n Validation Pack

The n8n validation pack proves that the advisory wrapper still detects
synthetic publish leaks before a cloned workflow touches live publishing. It is
intended for local and clone-workflow validation, not live OpenClaw wiring.

## Fixtures

Fixtures live in `examples/n8n-validation/`. Each fixture is a JSON object with:

- `description`: short human context
- `request`: the exact advisory payload shape to test
- `expected`: expected `blocked`, `changed`, and `finding_rule_ids` values

The runner strips request fields whose names start with `_` before scanning.
That lets public repo fixtures carry Content Guard allow metadata while still
feeding a clean payload to `content-guard-n8n-advisory`.

Current fixture coverage:

- clean blog post
- clean social post
- local service leak
- synthetic token assignment
- synthetic reviewer email warning

## Local Runner

Run the default fixture pack from the repository root:

```bash
PYTHONPATH=src python3 -m content_guard.n8n_validate
```

Machine-readable output:

```bash
PYTHONPATH=src python3 -m content_guard.n8n_validate --json
```

Installed console script:

```bash
content-guard-n8n-validate examples/n8n-validation
```

The command exits zero only when every fixture matches its expected result.

## Cloned Workflow Use

Use the fixture pack against a cloned n8n workflow before enabling strict mode:

1. Keep the workflow clone disconnected from live publish credentials or route
   its publish branch to a review sink.
2. Feed each fixture `request` object into the same fields used by the
   `Build Content Guard Payload` node.
3. Confirm clean fixtures produce `content_guard.blocked=false`.
4. Confirm blocking leak fixtures produce `content_guard.blocked=true` and the
   expected rule IDs.
5. Confirm warning fixtures surface findings without blocking.
6. Confirm blocked fixture items do not reach a real publish side effect.

For the node sequence, see [N8N_WORKFLOW_RECIPE.md](N8N_WORKFLOW_RECIPE.md).

## Promotion Gate

Do not switch a workflow to `content-guard-n8n-advisory --strict` until:

- the local validation pack passes
- the cloned workflow passes the same fixture cases
- normal draft traffic has been observed in advisory mode
- the n8n error path routes blocked items to review instead of dropping them
- OpenClaw outbound-message guarding remains single-owner
