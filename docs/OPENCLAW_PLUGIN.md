# OpenClaw Plugin

Content Guard can run as an OpenClaw outbound message plugin.

The plugin is intentionally thin. It does not duplicate rules. It shells out to the Python engine with the selected policy and returns redacted message content to OpenClaw.

## Package

Plugin package:

```text
openclaw-plugin/
```

Entrypoint:

```text
openclaw-plugin/index.mjs
```

Manifest:

```text
openclaw-plugin/openclaw.plugin.json
```

## OpenClaw Config

Example:

```json
{
  "plugins": {
    "allow": ["content-guard"],
    "load": {
      "paths": ["/path/to/content-guard/openclaw-plugin"]
    },
    "entries": {
      "content-guard": {
        "enabled": true,
        "config": {
          "rootDir": "/path/to/content-guard",
          "policyPath": "/path/to/content-guard/policies/openclaw-message.json",
          "pythonCommand": "python3",
          "timeoutMs": 5000,
          "failOpen": true,
          "opf": false
        }
      }
    }
  }
}
```

## Policy

Default policy:

```text
policies/openclaw-message.json
```

The OpenClaw message policy should redact high-confidence infrastructure and secret findings. PII should usually remain warn-only until local fixtures prove the model-backed path is reliable enough for automatic message mutation.

## Ownership Rule

Keep outbound-message guarding single-owner. Do not enable the Content Guard OpenClaw plugin while another overlapping scrubber is active.

Before enabling the plugin for a real channel:

- run local verification for the Python package and plugin syntax
- run the configured policy against representative message fixtures
- confirm PR bodies use `content_guard.pr_prepare`
- confirm public repo files use `content_guard.git_scan`
- confirm commit messages use `content_guard.git_commits`

## Failure Mode

`failOpen` defaults to `true`. If Content Guard fails or times out, the original message is sent and an error is logged.

For stricter channels, set:

```json
{
  "failOpen": false,
  "failureReplacement": "[content blocked by content-guard]"
}
```

## OPF

OPF is disabled by default. Enable it only after measuring latency and false positives:

```json
{
  "opf": true,
  "opfDevice": "cpu",
  "opfBin": "/home/user/.opf-venv/bin/opf"
}
```
