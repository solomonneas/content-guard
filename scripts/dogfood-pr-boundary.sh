#!/usr/bin/env bash
# Run Content Guard alongside the legacy scrub-content script for PR draft and
# staged-file boundaries.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: scripts/dogfood-pr-boundary.sh <git-repo>" >&2
  exit 2
fi

TARGET="$(cd "$TARGET" && pwd)"
LEGACY_SCRUB="${LEGACY_SCRUB:-$HOME/.openclaw/workspace/scripts/scrub-content}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -x "$LEGACY_SCRUB" ]]; then
  echo "ERROR: legacy scrub-content not executable at $LEGACY_SCRUB" >&2
  exit 2
fi

run_step() {
  local name="$1"
  shift
  echo "==> $name"
  set +e
  "$@"
  local status=$?
  set -e
  echo "status=$status"
  echo
  return 0
}

PR_BODY="$TARGET/pr-body.md"
if [[ -f "$PR_BODY" ]]; then
  run_step "legacy scrub-content PR body" "$LEGACY_SCRUB" "$PR_BODY"
  run_step "content-guard PR body" env PYTHONPATH="$ROOT/src" "$PYTHON_BIN" -m content_guard scan "$PR_BODY" --policy "$ROOT/policies/pr-draft.json"
  run_step "content-guard advisory PR helper" env PYTHONPATH="$ROOT/src" "$PYTHON_BIN" -m content_guard.pr_draft "$PR_BODY" --policy "$ROOT/policies/pr-draft.json"
else
  echo "==> PR body"
  echo "missing: $PR_BODY"
  echo
fi

run_step "content-guard staged Git files" bash -c 'cd "$1" && shift && "$@"' _ "$TARGET" env PYTHONPATH="$ROOT/src" "$PYTHON_BIN" -m content_guard.git_scan --policy "$ROOT/policies/public-repo.json"
run_step "content-guard commit messages" bash -c 'cd "$1" && shift && "$@"' _ "$TARGET" env PYTHONPATH="$ROOT/src" "$PYTHON_BIN" -m content_guard.git_commits --policy "$ROOT/policies/public-repo.json"

echo "Dogfood comparison complete. Review differences above before switching any live boundary."
