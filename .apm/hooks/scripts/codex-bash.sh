#!/usr/bin/env bash
# Codex PreToolUse (Bash) → agent-guard
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname "$0")/../../.." && pwd)"
PLUGIN="${PLUGIN_ROOT:-${CURSOR_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}}"
if [ -n "${AGENT_GUARD_ROOT:-}" ]; then
  GUARD="$AGENT_GUARD_ROOT"
elif [ -n "$PLUGIN" ]; then
  GUARD="${PLUGIN}/scripts/agent-guard"
else
  GUARD="${ROOT}/scripts/agent-guard"
fi
exec python3 "$GUARD/run.py" --target codex --source codex
