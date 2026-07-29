#!/usr/bin/env python3
"""CLI entry for agent-guard hooks.

Reads a JSON event from stdin, evaluates the shared policy, prints a
harness-specific JSON decision to stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")


def _fail_closed_payload(target: str, reason: str) -> dict:
    from agent_guard.output import format_decision

    return format_decision(allowed=False, reason=reason, target=target)


def _parse_target(argv: list[str]) -> str:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target", default="cursor")
    args, _ = parser.parse_known_args(argv)
    return args.target


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description="Agent Guard policy hook")
    parser.add_argument(
        "--target",
        default="cursor",
        choices=("cursor", "claude", "claude-code", "codex"),
        help="Hook harness response format",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Event source for normalization (defaults to --target)",
    )
    parser.add_argument(
        "--rules",
        default=None,
        help="Path to rules.yaml (default: alongside this script)",
    )
    parser.add_argument(
        "--audit-log",
        default=os.environ.get("AGENT_GUARD_AUDIT_LOG"),
        help="Append JSONL audit records to this path",
    )
    args = parser.parse_args(argv)

    try:
        from agent_guard.engine import Engine, default_rules_path
        from agent_guard.normalize import normalize
        from agent_guard.output import format_decision
    except ImportError as exc:
        _emit(_fail_closed_payload(args.target, f"Agent Guard error (fail-closed): {exc}"))
        return 0

    def _audit(path: Path | None, record: dict) -> None:
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass

    try:
        raw = sys.stdin.read()
        if not raw.strip():
            payload = format_decision(
                allowed=False,
                reason="Empty hook input (fail-closed)",
                target=args.target,
            )
            _emit(payload)
            return 0

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            event = {"command": raw}

        source = args.source or args.target
        rules_path = Path(args.rules) if args.rules else default_rules_path()
        engine = Engine.from_path(rules_path)
        action = normalize(event, source=source)
        decision = engine.evaluate(action)
        payload = format_decision(
            allowed=decision.allowed,
            reason=decision.reason,
            rule_id=decision.rule_id,
            target=args.target,
        )

        audit_path = Path(args.audit_log) if args.audit_log else None
        _audit(
            audit_path,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "target": args.target,
                "source": source,
                "action": action,
                "allowed": decision.allowed,
                "rule_id": decision.rule_id,
                "reason": decision.reason,
            },
        )
    except Exception as exc:
        payload = format_decision(
            allowed=False,
            reason=f"Agent Guard error (fail-closed): {exc}",
            target=args.target,
        )

    _emit(payload)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException as exc:
        target = _parse_target(sys.argv[1:])
        _emit(_fail_closed_payload(target, f"Agent Guard error (fail-closed): {exc}"))
        raise SystemExit(0) from exc
