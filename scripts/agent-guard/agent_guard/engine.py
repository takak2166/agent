"""Policy engine: match normalized actions against rules.yaml."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

try:
    import yaml
except ImportError as e:  # pragma: no cover
    raise ImportError("PyYAML is required: python3 -m pip install pyyaml") from e


@dataclass(frozen=True)
class Decision:
    allowed: bool
    rule_id: str | None
    reason: str | None
    default: bool = False


@dataclass(frozen=True)
class _CompiledMatch:
    kind: str | None
    read_only: bool | None
    git_commit_bypass: bool | None
    command_regex: re.Pattern[str] | None
    operation_in: frozenset[str] | None
    method_in: frozenset[str] | None


@dataclass(frozen=True)
class _CompiledRule:
    id: str
    action: str
    reason: str | None
    match: _CompiledMatch


class Engine:
    _cache: ClassVar[dict[tuple[str, int], "Engine"]] = {}

    def __init__(self, rules: dict[str, Any]):
        _validate_rules(rules)
        self.default = str(rules.get("default", "deny")).lower()
        raw_rules = rules.get("rules")
        if not isinstance(raw_rules, list):
            raise ValueError("rules must be a list")
        self._compiled: list[_CompiledRule] = [_compile_rule(r) for r in raw_rules]

    @classmethod
    def from_path(cls, path: str | Path) -> "Engine":
        path = Path(path)
        mtime = path.stat().st_mtime_ns
        key = (str(path.resolve()), mtime)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
        engine = cls(data)
        cls._cache[key] = engine
        return engine

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()

    def evaluate(self, action: dict[str, Any] | None) -> Decision:
        if not action:
            return Decision(
                allowed=False,
                rule_id=None,
                reason="No actions to evaluate",
                default=True,
            )
        for rule in self._compiled:
            if self._matches(rule.match, action):
                allowed = rule.action == "allow"
                return Decision(
                    allowed=allowed,
                    rule_id=rule.id,
                    reason=rule.reason
                    or ("All actions allowed" if allowed else "blocked by policy"),
                )
        if self.default == "allow":
            return Decision(
                allowed=True,
                rule_id=None,
                reason="All actions allowed",
                default=True,
            )
        return Decision(
            allowed=False,
            rule_id=None,
            reason="No matching policy rule (default)",
            default=True,
        )

    def _matches(self, match: _CompiledMatch, action: dict[str, Any]) -> bool:
        if match.kind is not None and action.get("kind") != match.kind:
            return False

        if match.read_only is not None:
            if bool(action.get("read_only")) != match.read_only:
                return False

        if match.git_commit_bypass is not None:
            if bool(action.get("git_commit_bypass")) != match.git_commit_bypass:
                return False

        if match.command_regex is not None:
            command = str(action.get("command") or "")
            if not match.command_regex.search(command):
                return False

        if match.operation_in is not None:
            op = str(action.get("operation") or "").lower()
            if op not in match.operation_in:
                return False

        if match.method_in is not None:
            method = str(action.get("method") or "").upper()
            if method not in match.method_in:
                return False

        return True


def _compile_rule(rule: Any) -> _CompiledRule:
    if not isinstance(rule, dict):
        raise ValueError(f"each rule must be a mapping, got {type(rule).__name__}")
    rule_id = rule.get("id")
    if not rule_id:
        raise ValueError("rule missing id")
    action = str(rule.get("action", "deny")).lower()
    if action not in ("allow", "deny"):
        raise ValueError(f"rule {rule_id!r}: action must be allow or deny")

    raw_match = rule.get("match") or {}
    if not isinstance(raw_match, dict):
        raise ValueError(f"rule {rule_id!r}: match must be a mapping")

    regex_raw = raw_match.get("command_regex")
    compiled_regex = None
    if regex_raw is not None:
        compiled_regex = re.compile(str(regex_raw), re.IGNORECASE | re.DOTALL)

    ops_raw = raw_match.get("operation_in")
    operation_in = None
    if ops_raw is not None:
        if not isinstance(ops_raw, list):
            raise ValueError(f"rule {rule_id!r}: operation_in must be a list")
        operation_in = frozenset(str(x).lower() for x in ops_raw)

    methods_raw = raw_match.get("method_in")
    method_in = None
    if methods_raw is not None:
        if not isinstance(methods_raw, list):
            raise ValueError(f"rule {rule_id!r}: method_in must be a list")
        method_in = frozenset(str(x).upper() for x in methods_raw)

    read_only = raw_match.get("read_only") if "read_only" in raw_match else None
    git_commit_bypass = (
        raw_match.get("git_commit_bypass") if "git_commit_bypass" in raw_match else None
    )

    return _CompiledRule(
        id=str(rule_id),
        action=action,
        reason=rule.get("reason"),
        match=_CompiledMatch(
            kind=raw_match.get("kind"),
            read_only=read_only,
            git_commit_bypass=git_commit_bypass,
            command_regex=compiled_regex,
            operation_in=operation_in,
            method_in=method_in,
        ),
    )


def _validate_rules(rules: dict[str, Any]) -> None:
    if not isinstance(rules, dict):
        raise ValueError("rules document must be a mapping")
    default = str(rules.get("default", "deny")).lower()
    if default not in ("allow", "deny"):
        raise ValueError("default must be allow or deny")
    raw_rules = rules.get("rules")
    if raw_rules is None:
        raise ValueError("rules list is required")
    if not isinstance(raw_rules, list):
        raise ValueError("rules must be a list")


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent.parent / "rules.yaml"
