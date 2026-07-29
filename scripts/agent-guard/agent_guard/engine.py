"""Policy engine: match normalized actions against rules.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from e


@dataclass(frozen=True)
class Decision:
    allowed: bool
    rule_id: str | None
    reason: str | None
    default: bool = False


class Engine:
    def __init__(self, rules: dict[str, Any]):
        self.default = str(rules.get("default", "deny")).lower()
        self.rules = list(rules.get("rules") or [])

    @classmethod
    def from_path(cls, path: str | Path) -> "Engine":
        text = Path(path).read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        return cls(data)

    def evaluate(self, action: dict[str, Any]) -> Decision:
        for rule in self.rules:
            if self._matches(rule.get("match") or {}, action):
                action_name = str(rule.get("action", "deny")).lower()
                allowed = action_name == "allow"
                return Decision(
                    allowed=allowed,
                    rule_id=rule.get("id"),
                    reason=None if allowed else (rule.get("reason") or "blocked by policy"),
                )
        if self.default == "allow":
            return Decision(allowed=True, rule_id=None, reason=None, default=True)
        return Decision(
            allowed=False,
            rule_id=None,
            reason="どの許可ルールにも一致しないためブロックしました（fail-closed）",
            default=True,
        )

    def _matches(self, match: dict[str, Any], action: dict[str, Any]) -> bool:
        kind = match.get("kind")
        if kind is not None and action.get("kind") != kind:
            return False

        if "read_only" in match:
            if bool(action.get("read_only")) != bool(match["read_only"]):
                return False

        regex = match.get("command_regex")
        if regex is not None:
            command = str(action.get("command") or "")
            if not re.search(regex, command, re.IGNORECASE | re.DOTALL):
                return False

        ops = match.get("operation_in")
        if ops is not None:
            op = str(action.get("operation") or "").lower()
            if op not in {str(x).lower() for x in ops}:
                return False

        methods = match.get("method_in")
        if methods is not None:
            method = str(action.get("method") or "").upper()
            if method not in {str(x).upper() for x in methods}:
                return False

        # Unused legacy keys (git_tracked / file_exists) intentionally ignored.
        return True


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent.parent / "rules.yaml"
