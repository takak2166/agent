#!/usr/bin/env python3
"""Emit a fail-closed deny payload when run.py cannot execute."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agent_guard.output import format_decision  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Guard fail-closed fallback")
    parser.add_argument(
        "--target",
        default="cursor",
        choices=("cursor", "claude", "claude-code", "codex"),
    )
    parser.add_argument("--reason", default="Agent Guard hook failed (fail-closed)")
    args = parser.parse_args(argv)

    payload = format_decision(allowed=False, reason=args.reason, target=args.target)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
