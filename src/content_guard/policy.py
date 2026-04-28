from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib import resources
from importlib.abc import Traversable
from os import PathLike
from pathlib import Path
from typing import Any

from .rules import DEFAULT_RULES
from .types import Action, Rule

VALID_ACTIONS: set[str] = {"allow", "warn", "redact", "block"}


@dataclass
class OpfBackendConfig:
    enabled: bool = False
    device: str = "cpu"
    bin: str | None = None


@dataclass
class Policy:
    name: str = "default"
    defaults: dict[str, Action] = field(
        default_factory=lambda: {
            "infrastructure": "block",
            "secret": "block",
            "pii": "warn",
            "personal": "block",
            "business": "warn",
            "attribution": "block",
        }
    )
    rules: dict[str, Action] = field(default_factory=dict)
    custom_rules: list[Rule] = field(default_factory=list)
    opf_backend: OpfBackendConfig = field(default_factory=OpfBackendConfig)

    def action_for(self, rule: Rule) -> Action:
        return self.rules.get(rule.id) or self.defaults.get(rule.category, "warn")

    def all_rules(self) -> list[Rule]:
        return [*DEFAULT_RULES, *self.custom_rules]


def _as_action(value: Any, where: str) -> Action:
    if not isinstance(value, str) or value not in VALID_ACTIONS:
        raise ValueError(f"{where} must be one of: {', '.join(sorted(VALID_ACTIONS))}")
    return value  # type: ignore[return-value]


def default_policy(name: str) -> Path | Traversable:
    repo_path = Path(__file__).resolve().parents[2] / "policies" / name
    if repo_path.is_file():
        return repo_path

    packaged_path = resources.files("content_guard").joinpath("policies", name)
    if packaged_path.is_file():
        return packaged_path

    return repo_path


def load_policy(path: str | PathLike[str] | Traversable | None) -> Policy:
    if path is None:
        return Policy()

    if isinstance(path, (str, PathLike)):
        policy_path = Path(path)
        raw_text = policy_path.read_text()
        fallback_name = policy_path.stem
    else:
        raw_text = path.read_text()
        fallback_name = Path(path.name).stem

    raw = json.loads(raw_text)
    if not isinstance(raw, dict):
        raise ValueError("policy root must be an object")

    defaults = Policy().defaults
    for category, action in raw.get("defaults", {}).items():
        defaults[str(category)] = _as_action(action, f"defaults.{category}")

    rules: dict[str, Action] = {}
    for rule_id, action in raw.get("rules", {}).items():
        rules[str(rule_id)] = _as_action(action, f"rules.{rule_id}")

    custom_rules = [_parse_custom_rule(item, i) for i, item in enumerate(raw.get("custom_rules", []))]
    opf_backend = _parse_opf_backend(raw.get("backends", {}).get("opf") if isinstance(raw.get("backends"), dict) else None)
    if opf_backend.action:
        rules["opf-pii"] = opf_backend.action

    return Policy(
        name=str(raw.get("name") or fallback_name),
        defaults=defaults,
        rules=rules,
        custom_rules=custom_rules,
        opf_backend=OpfBackendConfig(
            enabled=opf_backend.enabled,
            device=opf_backend.device,
            bin=opf_backend.bin,
        ),
    )


def _parse_custom_rule(item: Any, index: int) -> Rule:
    if not isinstance(item, dict):
        raise ValueError(f"custom_rules[{index}] must be an object")

    try:
        rule_id = str(item["id"])
        category = str(item["category"])
        pattern = str(item["pattern"])
    except KeyError as exc:
        raise ValueError(f"custom_rules[{index}] missing required field {exc.args[0]!r}") from exc

    replacement = str(item.get("replacement", f"[redacted-{category}]"))
    description = str(item.get("description", ""))
    flags = 0
    for flag in item.get("flags", []):
        if flag == "ignorecase":
            flags |= re.IGNORECASE
        elif flag == "multiline":
            flags |= re.MULTILINE
        elif flag == "dotall":
            flags |= re.DOTALL
        else:
            raise ValueError(f"custom_rules[{index}].flags has unsupported flag {flag!r}")

    re.compile(pattern, flags)
    return Rule(
        id=rule_id,
        category=category,
        pattern=pattern,
        replacement=replacement,
        description=description,
        flags=flags,
    )


@dataclass
class _ParsedOpfBackend:
    enabled: bool = False
    device: str = "cpu"
    bin: str | None = None
    action: Action | None = None


def _parse_opf_backend(raw: Any) -> _ParsedOpfBackend:
    if raw is None:
        return _ParsedOpfBackend()
    if not isinstance(raw, dict):
        raise ValueError("backends.opf must be an object")

    enabled = bool(raw.get("enabled", False))
    device = str(raw.get("device", "cpu"))
    opf_bin = raw.get("bin")
    action = raw.get("action")

    return _ParsedOpfBackend(
        enabled=enabled,
        device=device,
        bin=str(opf_bin) if opf_bin else None,
        action=_as_action(action, "backends.opf.action") if action is not None else None,
    )
