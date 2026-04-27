from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .engine import scan_text
from .policy import Policy, load_policy
from .report import to_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="content-guard-git",
        description="Scan public Git repository content before commit or push.",
    )
    parser.add_argument("--policy", help="JSON policy file")
    parser.add_argument("--all-tracked", action="store_true", help="scan all tracked files")
    parser.add_argument("--staged", action="store_true", help="scan staged files, default mode")
    parser.add_argument("--include-git-config", action="store_true", help="also scan .git/config when present")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    policy = load_policy(args.policy) if args.policy else _default_repo_policy()
    paths = _tracked_paths(all_tracked=args.all_tracked)
    if args.include_git_config and Path(".git/config").is_file():
        paths.append(Path(".git/config"))

    results = []
    blocked = False
    for path in paths:
        text = _read_text(path)
        if text is None:
            continue
        result = scan_text(text, policy=policy)
        if result.findings:
            blocked = blocked or result.blocked
            results.append((path, result))

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not blocked,
                    "blocked": blocked,
                    "files_with_findings": len(results),
                    "files": [
                        {
                            "path": str(path),
                            "blocked": result.blocked,
                            "changed": result.changed,
                            "counts_by_action": result.counts_by_action(),
                            "counts_by_category": result.counts_by_category(),
                        }
                        for path, result in results
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif not results:
        print(f"Clean. {len(paths)} Git file(s) checked.")
    else:
        for path, result in results:
            print(to_text(result, path=str(path)))

    return 1 if blocked else 0


def _default_repo_policy() -> Policy:
    return Policy(
        name="public-repo-default",
        defaults={
            "infrastructure": "block",
            "secret": "block",
            "pii": "block",
            "personal": "block",
            "business": "block",
            "tooling": "warn",
        },
        rules={"opf-pii": "warn"},
    )


def _tracked_paths(*, all_tracked: bool) -> list[Path]:
    if all_tracked:
        cmd = ["git", "ls-files"]
    else:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print((proc.stderr or proc.stdout or "git command failed").strip(), file=sys.stderr)
        raise SystemExit(2)

    return [Path(line) for line in proc.stdout.splitlines() if line.strip()]


def _read_text(path: Path) -> str | None:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
