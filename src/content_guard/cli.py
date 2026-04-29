from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

from .engine import scan_text
from .policy import load_policy
from .report import to_json, to_payload, to_text
from .types import ScanOptions


DEFAULT_EXCLUDE_DIR_NAMES = frozenset(
    {
        "node_modules",
        ".git",
        "dist",
        "build",
        "coverage",
        ".next",
        ".cache",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "out",
        ".turbo",
        ".parcel-cache",
        "vendor",
        ".claude",
    }
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "scan":
        return _scan(args)
    if args.command == "redact":
        return _redact(args)
    if args.command == "diff":
        return _diff(args)

    parser.error(f"unknown command: {args.command}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="content-guard",
        description="Policy-driven content scanning and redaction.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("scan", "redact", "diff"):
        cmd = sub.add_parser(name)
        cmd.add_argument("target", nargs="?", help="file to read, or stdin when omitted")
        cmd.add_argument("--policy", help="JSON policy file")
        cmd.add_argument("--opf", action="store_true", help="run optional OPF backend")
        cmd.add_argument("--opf-bin", help="path to opf binary")
        cmd.add_argument("--opf-device", help="OPF device, default comes from policy or cpu")
        cmd.add_argument("--scan-frontmatter", action="store_true", help="scan YAML frontmatter")
        cmd.add_argument("--skip-code-blocks", action="store_true", help="ignore fenced code blocks")
        cmd.add_argument("--no-allow-comments", action="store_true", help="ignore content-guard allow comments")

    sub.choices["scan"].add_argument("--json", action="store_true", help="emit JSON report")
    sub.choices["redact"].add_argument("--in-place", action="store_true", help="rewrite the target file")
    return parser


def _options(args: argparse.Namespace) -> ScanOptions:
    return ScanOptions(
        scan_frontmatter=args.scan_frontmatter,
        scan_code_blocks=not args.skip_code_blocks,
        honor_allow_comments=not args.no_allow_comments,
        include_opf=args.opf,
        opf_device=args.opf_device,
        opf_bin=args.opf_bin,
    )


def _read_target(target: str | None) -> tuple[str, str | None]:
    if not target or target == "-":
        return sys.stdin.read(), None
    path = Path(target)
    return path.read_text(), str(path)


def _scan(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    options = _options(args)
    target_path = Path(args.target) if args.target and args.target != "-" else None

    if target_path and target_path.is_dir():
        results = _scan_directory(target_path, policy, options)
        blocked = any(result.blocked for _, result in results)
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": not blocked,
                        "blocked": blocked,
                        "files_scanned": len(results),
                        "files": [
                            {"path": str(path), **to_payload(result)}
                            for path, result in results
                            if result.findings
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        elif not any(result.findings for _, result in results):
            print(f"Clean. {len(results)} file(s) checked.")
        else:
            for path, result in results:
                if result.findings:
                    print(to_text(result, path=str(path)))
        return 1 if blocked else 0

    text, path = _read_target(args.target)
    result = scan_text(text, policy=policy, options=options)
    if args.json:
        print(to_json(result))
    else:
        print(to_text(result, path=path or "<stdin>"))
    return 1 if result.blocked else 0


def _redact(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    options = _options(args)
    target_path = Path(args.target) if args.target and args.target != "-" else None

    if target_path and target_path.is_dir():
        if not args.in_place:
            print("directory redact requires --in-place", file=sys.stderr)
            return 2
        results = _scan_directory(target_path, policy, options)
        for path, result in results:
            if result.changed:
                path.write_text(result.redacted_text)
        return 1 if any(result.blocked for _, result in results) else 0

    text, path = _read_target(args.target)
    result = scan_text(text, policy=policy, options=options)

    if args.in_place:
        if not path:
            print("--in-place requires a file target", file=sys.stderr)
            return 2
        Path(path).write_text(result.redacted_text)
    else:
        sys.stdout.write(result.redacted_text)
    return 1 if result.blocked else 0


def _diff(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    options = _options(args)
    target_path = Path(args.target) if args.target and args.target != "-" else None

    if target_path and target_path.is_dir():
        results = _scan_directory(target_path, policy, options)
        for path, result in results:
            if not result.changed:
                continue
            _write_diff(result.text, result.redacted_text, str(path))
        return 1 if any(result.blocked for _, result in results) else 0

    text, path = _read_target(args.target)
    result = scan_text(text, policy=policy, options=options)
    source_name = path or "<stdin>"
    _write_diff(text, result.redacted_text, source_name)
    return 1 if result.blocked else 0


def _scan_directory(
    path: Path,
    policy,
    options: ScanOptions,
    exclude_dirs: frozenset[str] = DEFAULT_EXCLUDE_DIR_NAMES,
):
    results = []
    for file_path in sorted(path.rglob("*.md")):
        if exclude_dirs.intersection(file_path.parts):
            continue
        text = file_path.read_text()
        results.append((file_path, scan_text(text, policy=policy, options=options)))
    return results


def _write_diff(text: str, redacted_text: str, source_name: str) -> None:
    diff = difflib.unified_diff(
        text.splitlines(keepends=True),
        redacted_text.splitlines(keepends=True),
        fromfile=source_name,
        tofile=f"{source_name} (redacted)",
    )
    sys.stdout.writelines(diff)
