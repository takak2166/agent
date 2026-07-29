#!/usr/bin/env python3
"""Fail CI when mutation score drops below the configured baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATS_PATH = ROOT / "mutants" / "mutmut-cicd-stats.json"
BASELINE_PATH = ROOT / "mutmut-baseline.json"


def main() -> int:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    min_score = float(baseline["min_score"])

    if not STATS_PATH.exists():
        print(
            "Missing mutmut stats. Run: mutmut run && mutmut export-cicd-stats",
            file=sys.stderr,
        )
        return 1

    stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
    killed = int(stats["killed"])
    survived = int(stats["survived"])
    timeout = int(stats.get("timeout", 0))
    denominator = killed + survived + timeout
    if denominator == 0:
        print("No mutants evaluated", file=sys.stderr)
        return 1

    score = killed / denominator
    print(
        f"Mutation score: {score:.1%} "
        f"({killed} killed, {survived} survived, {timeout} timeout)"
    )
    print(f"Minimum required: {min_score:.1%}")

    if score < min_score:
        print(f"FAIL: mutation score {score:.1%} < {min_score:.1%}", file=sys.stderr)
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
