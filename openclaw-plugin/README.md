# @solomonneas/content-guard

OpenClaw outbound message adapter for [Content Guard](https://github.com/solomonneas/content-guard).

Scans every outbound OpenClaw message against a Content Guard policy before delivery. Replaces the message with a redacted form (or blocks it entirely) when sensitive content is detected: secrets, infrastructure identifiers, PII, and any custom rules you add to the policy.

## Install

```bash
# 1. The Python core (does the actual scanning):
pip install content-guard

# 2. This OpenClaw adapter:
npm install @solomonneas/content-guard
```

## Wire into OpenClaw

Add to your `openclaw.json`:

```json
{
  "plugins": {
    "load": {
      "paths": ["@solomonneas/content-guard"]
    },
    "entries": {
      "content-guard": {
        "enabled": true,
        "dryRun": false
      }
    }
  }
}
```

## Config

| Key | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `true` | Disable without uninstalling |
| `dryRun` | bool | `false` | Log decisions, deliver original message |
| `allowedRecipients` | string[] | `[]` | Recipient IDs that bypass guarding |
| `policyPath` | string | bundled `openclaw-message.json` | Path to a custom policy file |
| `pythonCommand` | string | `python3` | Override Python binary |
| `timeoutMs` | number | `5000` | Per-message scan timeout |
| `failOpen` | bool | `true` | On scanner error: deliver original (`true`) or block (`false`) |
| `failureReplacement` | string | `[content blocked by content-guard]` | Replacement when blocked |
| `opf` | bool | `false` | Run OpenAI Privacy Filter as an extra backend |
| `opfDevice` | string | `cpu` | OPF device hint |
| `opfBin` | string | `~/.opf-venv/bin/opf` | Path to OPF binary |

## How it works

The plugin shells out to `python3 -m content_guard scan --json` for each outbound message, applies the policy decision (`allow` / `redact` / `block`), and either:

- delivers the original message (allow, dryRun, or failOpen on error),
- delivers a redacted form (any `redact` rule matches), or
- replaces with `failureReplacement` (any `block` rule matches).

## Single-owner rule

Do not enable Content Guard alongside another outbound scrubber. Pick one. They will fight over message shape and produce inconsistent redactions.

## License

Apache-2.0. See [LICENSE](./LICENSE).
