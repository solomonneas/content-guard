# Report Contract

This page documents the current JSON report shape emitted by Content Guard.

Status: draft v0. The fields below describe the current behavior of `scan --json`, `git_scan --json`, `git_commits --json`, `pr_prepare --json`, and `publish_check --json`. Treat this as the compatibility target for early adopters, but expect the contract to be finalized before v1.

## Compatibility Rules

Draft v0 consumers should expect:

- field names and value types listed here to remain stable during the draft period unless a migration note is added
- new optional fields may be added
- object key ordering is not part of the contract
- count maps may omit actions or categories with zero findings
- paths are emitted as command-local string paths

Draft v0 consumers should not require:

- a schema version field, because the current payload does not emit one
- every possible action or category to appear in count maps
- every file scanned by `git_scan --json` to appear in `files`
- every commit scanned by `git_commits --json` to appear in `commits`
- every file scanned by directory `scan --json` to appear in `files`

## `publish_check --json`

Command shapes:

```bash
python -m content_guard.publish_check --json
python -m content_guard.publish_check --pr-body path/to/pr-body.md --json
python -m content_guard.publish_check --pr-body path/to/pr-body.md --all-tracked --json
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `ok` | boolean | `true` when the effective publish check exits successfully. `--advisory-only` can make this true even when `would_fail` is true. |
| `blocked` | boolean | `true` when any enabled check has blocked findings, including advisory PR body findings. |
| `would_fail` | boolean | `true` when staged files, commit messages, or all-tracked files would fail the default gate. |
| `advisory_only` | boolean | `true` when `--advisory-only` was set. |
| `publish_body_file` | string | Present when `--pr-body` is provided. Path to the sanitized PR body. |
| `checks` | object | Per-check payloads keyed by `pr_body`, `staged_files`, `commit_messages`, and `all_tracked_files`. |

`checks.pr_body` uses the same fields as `pr_prepare --json` plus `enabled`. It is advisory by default inside `publish_check`; blocked PR body findings do not set `would_fail` because the sanitized body is the publishing input.

`checks.staged_files` and `checks.all_tracked_files` use the same summary fields as `git_scan --json`, plus:

| Field | Type | Description |
| --- | --- | --- |
| `enabled` | boolean | Whether this check ran. |
| `mode` | string | `staged` or `all-tracked`. |
| `files_scanned` | integer | Number of Git paths returned for the check. |

`checks.commit_messages` uses the same fields as `git_commits --json` plus `enabled`.

Example:

```json
{
  "advisory_only": false,
  "blocked": true,
  "checks": {
    "all_tracked_files": {
      "enabled": false
    },
    "commit_messages": {
      "blocked": false,
      "commits": [],
      "commits_scanned": 1,
      "commits_with_findings": 0,
      "enabled": true,
      "ok": true
    },
    "pr_body": {
      "advisory": true,
      "blocked": true,
      "enabled": true,
      "publish_body_file": ".content-guard/pr-drafts/pr-body.public.md",
      "strict": false
    },
    "staged_files": {
      "blocked": false,
      "enabled": true,
      "files": [],
      "files_scanned": 0,
      "files_with_findings": 0,
      "mode": "staged",
      "ok": true
    }
  },
  "ok": true,
  "publish_body_file": ".content-guard/pr-drafts/pr-body.public.md",
  "would_fail": false
}
```

## `pr_prepare --json`

Command shapes:

```bash
python -m content_guard.pr_prepare path/to/pr-body.md --json
python -m content_guard.pr_prepare --json < path/to/pr-body.md
```

Top-level fields include the single-file scan fields from `scan --json`, plus PR handoff fields:

| Field | Type | Description |
| --- | --- | --- |
| `source` | string | Source body path, or `<stdin>` when read from standard input. |
| `draft` | string | Private copy of the original PR draft body. |
| `sanitized` | string | Sanitized PR body path. |
| `report` | string | Private JSON report path. |
| `publish_body_file` | string | Path a PR publishing command should use as its body file. Currently the same as `sanitized`. |
| `advisory` | boolean | `true` when blocked findings exist but the command is not in strict mode. |
| `strict` | boolean | `true` when the command was run with `--strict`. |

Treat `draft` and `report` as private artifacts because they can include raw findings. Publishing tools should use only `publish_body_file` or `sanitized`.

Example:

```json
{
  "advisory": true,
  "blocked": true,
  "changed": true,
  "counts_by_action": {
    "block": 1
  },
  "counts_by_category": {
    "infrastructure": 1
  },
  "draft": ".content-guard/pr-drafts/pr-body.draft.md",
  "findings": [
    {
      "action": "block",
      "allowed_by": null,
      "category": "infrastructure",
      "column": 14,
      "end": 27,
      "line": 1,
      "match": "local\\u0068ost:5204",
      "message": "Local service endpoint.",
      "replacement": "[redacted-service]",
      "rule_id": "localhost-port",
      "source": "regex",
      "start": 13
    }
  ],
  "ok": false,
  "publish_body_file": ".content-guard/pr-drafts/pr-body.public.md",
  "report": ".content-guard/pr-drafts/pr-body.content-guard.json",
  "sanitized": ".content-guard/pr-drafts/pr-body.public.md",
  "source": "pr-body.md",
  "strict": false
}
```

## `scan --json`

Command shape:

```bash
python -m content_guard scan path/to/file.md --json
```

Directory command shape:

```bash
python -m content_guard scan path/to/content-dir --json
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `ok` | boolean | `true` when the scan is not blocked. |
| `blocked` | boolean | `true` when at least one finding resolves to the `block` action. |
| `changed` | boolean | `true` when redaction would change the input text. |
| `counts_by_action` | object | Map of action name to finding count. |
| `counts_by_category` | object | Map of category name to finding count. |
| `findings` | array | Finding objects in scan order. |

When scanning a directory, the payload uses file aggregation:

| Field | Type | Description |
| --- | --- | --- |
| `ok` | boolean | `true` when no scanned file has a blocking finding. |
| `blocked` | boolean | `true` when at least one scanned file has a blocking finding. |
| `files_scanned` | integer | Number of markdown files scanned. |
| `files` | array | Per-file scan payloads for files with findings only. Each object includes `path` plus the single-file fields listed above. |

Finding fields:

| Field | Type | Description |
| --- | --- | --- |
| `rule_id` | string | Rule identifier that produced the finding. |
| `category` | string | Finding category, such as `infrastructure`, `secret`, `pii`, `personal`, `business`, `tooling`, or `opf-pii`. |
| `action` | string | Resolved action: `allow`, `warn`, `redact`, or `block`. |
| `match` | string | Matched input text. |
| `replacement` | string | Replacement text used when the finding redacts. |
| `line` | integer | One-based line number for the finding. |
| `column` | integer | One-based column number for the finding. |
| `start` | integer | Zero-based character offset where the match starts. |
| `end` | integer | Zero-based character offset where the match ends. |
| `source` | string | Detector source, currently usually `regex` or an optional backend source. |
| `message` | string | Human-readable rule message. Empty string when no message is set. |
| `allowed_by` | string or null | Allow rule identifier or allow-comment source when the finding is allowed. `null` when not allowed. |

Example:

```json
{
  "blocked": true,
  "changed": true,
  "counts_by_action": {
    "block": 1,
    "warn": 1
  },
  "counts_by_category": {
    "infrastructure": 1,
    "pii": 1
  },
  "findings": [
    {
      "action": "block",
      "allowed_by": null,
      "category": "infrastructure",
      "column": 12,
      "end": 30,
      "line": 1,
      "match": "local\\u0068ost:5204",
      "message": "",
      "replacement": "[redacted-service]",
      "rule_id": "localhost-port",
      "source": "regex",
      "start": 16
    }
  ],
  "ok": false
}
```

## `git_scan --json`

Command shapes:

```bash
python -m content_guard.git_scan --json
python -m content_guard.git_scan --all-tracked --json
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `ok` | boolean | `true` when no scanned file has a blocking finding. |
| `blocked` | boolean | `true` when at least one scanned file has a blocking finding. |
| `files_with_findings` | integer | Number of scanned files with at least one finding. |
| `files` | array | File summary objects for files with findings only. |

File summary fields:

| Field | Type | Description |
| --- | --- | --- |
| `path` | string | Path of the file with findings, relative to the Git command context when Git returns a relative path. |
| `blocked` | boolean | `true` when the file has at least one blocking finding. |
| `changed` | boolean | `true` when redaction would change the file text. |
| `counts_by_action` | object | Map of action name to finding count for the file. |
| `counts_by_category` | object | Map of category name to finding count for the file. |

`git_scan --json` currently emits file-level summaries, not per-finding details. Consumers that need line, column, match, or replacement details should run `scan --json` on the specific file.

Example:

```json
{
  "blocked": true,
  "files": [
    {
      "blocked": true,
      "changed": true,
      "counts_by_action": {
        "block": 1
      },
      "counts_by_category": {
        "secret": 1
      },
      "path": "examples/sample.md"
    }
  ],
  "files_with_findings": 1,
  "ok": false
}
```

## `git_commits --json`

Command shapes:

```bash
python -m content_guard.git_commits --json
python -m content_guard.git_commits --range origin/main..HEAD --json
python -m content_guard.git_commits --all --json
```

Top-level fields:

| Field | Type | Description |
| --- | --- | --- |
| `ok` | boolean | `true` when no scanned commit message has a blocking finding. |
| `blocked` | boolean | `true` when at least one scanned commit message has a blocking finding. |
| `commits_scanned` | integer | Number of commit messages scanned. |
| `commits_with_findings` | integer | Number of commit messages with at least one finding. |
| `commits` | array | Commit summary objects for commits with findings only. |

Commit summary fields:

| Field | Type | Description |
| --- | --- | --- |
| `commit` | string | Full commit SHA. |
| `subject` | string | Redacted first nonblank line from the commit message. |
| `blocked` | boolean | `true` when the commit message has at least one blocking finding. |
| `changed` | boolean | `true` when redaction would change the commit message. |
| `counts_by_action` | object | Map of action name to finding count for the commit message. |
| `counts_by_category` | object | Map of category name to finding count for the commit message. |
| `findings` | array | Finding summaries without raw matched text. |

`git_commits --json` intentionally omits raw matched text from finding summaries because commit messages can contain names and email addresses. The `subject` field is emitted from the redacted commit message, not the raw commit message.

Example:

```json
{
  "blocked": true,
  "commits": [
    {
      "blocked": true,
      "changed": true,
      "commit": "0123456789abcdef0123456789abcdef01234567",
      "counts_by_action": {
        "block": 1
      },
      "counts_by_category": {
        "attribution": 1
      },
      "findings": [
        {
          "action": "block",
          "category": "attribution",
          "column": 1,
          "line": 3,
          "message": "Git co-author trailer.",
          "rule_id": "coauthored-by-trailer",
          "source": "regex"
        }
      ],
      "subject": "feat: example"
    }
  ],
  "commits_scanned": 1,
  "commits_with_findings": 1,
  "ok": false
}
```

## Exit Status

The JSON report is written to standard output. Gate commands return a nonzero exit status when blocked findings are present. Automation should use both the exit status and the JSON report:

- use exit status for gate pass or fail behavior
- use `blocked` and count fields for reporting
- use `findings` from `scan --json` when a caller needs exact locations
- use `pr_prepare --strict` when PR preparation should fail on blocked findings
- expect advisory `pr_prepare --json` to exit zero even when `blocked` is true
- use `git_commits --json` for commit-message-only data that staged-file scanning cannot inspect
- use `publish_check --json` for the combined local PR and repo publish gate
- expect `publish_check --advisory-only --json` to exit zero while preserving `would_fail`
