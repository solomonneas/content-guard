# n8n Advisory Integration

Content Guard can run as a read-only advisory step inside n8n before a public
publish node. The first integration should annotate items with findings and
sanitized text, not block or mutate live publishes.

## Command

Install the package in the environment that the n8n command can reach, then run:

```bash
content-guard-n8n-advisory
```

The command reads one JSON object from stdin and writes one JSON object to
stdout.

## Input

```json
{
  "text": "Draft text to scan",
  "name": "optional-report-name",
  "source": "optional workflow/node/item label",
  "policy": "public-content"
}
```

`policy` may be one of:

- `public-content`
- `pr-draft`
- `public-repo`
- `openclaw-message`

It may also be a path to a JSON policy file.

## Output

```json
{
  "ok": true,
  "blocked": false,
  "changed": false,
  "advisory": false,
  "sanitized_text": "Draft text to scan",
  "counts_by_action": {},
  "counts_by_category": {},
  "findings": []
}
```

When findings are present, keep the raw report internal. Some reports include
matched text so reviewers can understand the finding.

## Suggested Placement

Add the advisory step immediately before public side effects:

- after content generation or approval
- before platform API posts
- before GitHub PR body creation or update
- before blog deploy commits
- before social posting nodes

Initial behavior should pass through the original item and attach the advisory
payload under a field such as `content_guard`. Switch to blocking only after a
cloned workflow passes synthetic leak tests.

## Example Execute Command Shape

```bash
printf '%s' "$CONTENT_GUARD_INPUT_JSON" | content-guard-n8n-advisory
```

For n8n Code nodes, prefer constructing the JSON payload from explicit fields
such as title, body, markdown, or social post content. Avoid sending the entire
item if it contains credentials, cookies, or private execution metadata.

## Promotion Rules

- PR body checks can stay advisory if publishing uses sanitized output.
- Staged file and commit-message checks should block before push or public PR
  creation.
- Live OpenClaw outbound-message guarding must remain single-owner. Do not run
  Content Guard and another outbound scrubber as competing mutators.
