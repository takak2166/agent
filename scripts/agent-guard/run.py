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

from agent_guard.engine import Engine, default_rules_path  # noqa: E402
from agent_guard.normalize import normalize  # noqa: E402
from agent_guard.output import format_decision  # noqa: E402


def _audit(path: Path | None, record: dict) -> None:
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
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

    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
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

    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    # Exit 0 always; harnesses honor JSON permission field.
    # Exit 2 is an alternate deny signal some harnesses accept — keep 0 + JSON.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
