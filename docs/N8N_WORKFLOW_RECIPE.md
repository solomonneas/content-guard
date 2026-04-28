# n8n Workflow Recipe

This recipe adds Content Guard as an advisory step before a public publish
side effect. It does not mutate the content, block the workflow, or change live
OpenClaw behavior.

Use this first in a cloned workflow. Promote to strict blocking only after the
clone passes synthetic leak tests and normal draft traffic.

## Node Sequence

Place these nodes immediately before the public side effect:

1. `Build Content Guard Payload` Code node
2. `Content Guard Advisory` Execute Command node
3. `Attach Content Guard Report` Code node
4. Existing publish node

Public side effects include platform API posts, GitHub PR body creation or
updates, blog deploy commits, social posting nodes, and browser handoff packets
that another system will publish.

## Build Content Guard Payload

Add a Code node named `Build Content Guard Payload`:

```js
const text = [
  $json.title,
  $json.summary,
  $json.body,
  $json.markdown,
  $json.social_text,
]
  .filter((value) => typeof value === "string" && value.trim())
  .join("\n\n");

if (!text) {
  throw new Error("Content Guard requires at least one publish text field");
}

const payload = {
  text,
  name: $json.slug || $json.title || "publish-item",
  source: "n8n:publish-advisory",
  policy: "public-content",
};

return [
  {
    json: {
      ...$json,
      content_guard_input_b64: Buffer.from(JSON.stringify(payload), "utf8").toString("base64"),
    },
  },
];
```

Keep the payload narrow. Send the text that will become public, not the entire
workflow item.

## Content Guard Advisory

Add an Execute Command node named `Content Guard Advisory`:

```bash
printf '%s' '{{$json.content_guard_input_b64}}' | base64 --decode | content-guard-n8n-advisory
```

The base64 wrapper keeps draft text out of shell interpolation. The command
exits zero in advisory mode, even when findings are present. The report is
written to stdout as JSON.

If the command is not on the n8n host path, use the module form from the repo or
virtual environment that contains Content Guard:

```bash
printf '%s' '{{$json.content_guard_input_b64}}' | base64 --decode | PYTHONPATH=src python3 -m content_guard.n8n_advisory
```

## Attach Content Guard Report

Add a Code node named `Attach Content Guard Report`:

```js
const original = $("Build Content Guard Payload").first().json;
const report = JSON.parse($json.stdout);

const { content_guard_input_b64, ...publicItem } = original;

return [
  {
    json: {
      ...publicItem,
      content_guard: report,
    },
  },
];
```

Downstream nodes should continue using their existing content fields. During
advisory rollout, use `content_guard` for logging, review queues, or dashboard
annotations.

## Optional Review Branch

Add an IF node after `Attach Content Guard Report` when reviewers need an
explicit branch:

- condition: `{{$json.content_guard.blocked}}`
- true branch: send to review or mark the item for manual handling
- false branch: continue to the existing publish node

Keep the original publish path advisory until the cloned workflow has enough
clean run history.

## Strict Promotion

After the advisory clone is stable, change only the cloned workflow command to:

```bash
printf '%s' '{{$json.content_guard_input_b64}}' | base64 --decode | content-guard-n8n-advisory --strict
```

With `--strict`, blocked findings return a nonzero exit code. Confirm the n8n
error path routes the item to review instead of dropping it silently.

## Validation Checklist

- The workflow is a clone, not the live publisher.
- The Content Guard node is immediately before the public side effect.
- The payload includes only explicit public-draft text fields.
- The raw report is stored internally because findings can include matched text.
- Clean sample drafts continue through the publish branch.
- Synthetic leak samples produce `content_guard.blocked=true`.
- Strict mode is tested in the clone before any live workflow uses it.
- OpenClaw outbound-message guarding remains single-owner.
