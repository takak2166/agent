#!/bin/bash
# Fixture tests for always-on-rules.sh (bash only; no extra deps beyond jq/python3).
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HOOK="${ROOT}/.apm/hooks/scripts/always-on-rules.sh"
FIXTURES="${ROOT}/tests/fixtures"
FAIL=0

assert_empty() {
  local label="$1"
  local out="$2"
  if [ -n "$out" ]; then
    echo "FAIL: $label — expected empty stdout, got: ${out:0:80}"
    FAIL=1
  else
    echo "ok: $label"
  fi
}

assert_json_context() {
  local label="$1"
  local out="$2"
  local needle="$3"
  if ! printf '%s' "$out" | jq -e --arg n "$needle" '.additional_context | contains($n)' >/dev/null 2>&1; then
    echo "FAIL: $label — missing needle in JSON"
    FAIL=1
  else
    echo "ok: $label"
  fi
}

run_hook() {
  local env_prefix="$1"
  local json="$2"
  # shellcheck disable=SC2086
  env $env_prefix bash "$HOOK" <<<"$json"
}

TMP_BASE=$(mktemp -d)
trap 'rm -rf "$TMP_BASE"' EXIT

RULES_ALWAYS="${FIXTURES}/rules-always"
RULES_MIXED="${FIXTURES}/rules-mixed"
STAMP_BASE="${TMP_BASE}/stamps"
WS="${TMP_BASE}/workspace"
mkdir -p "${WS}/.claude/rules"
cp "${RULES_ALWAYS}/always-one.md" "${WS}/.claude/rules/"

# 1) Non-Cursor input → no output
out=$(run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_ALWAYS} XDG_RUNTIME_DIR=${STAMP_BASE}" '{}' 2>/dev/null || true)
assert_empty "non-cursor input" "$out"

# 2) Cursor input with always-on rule → JSON
json='{"cursor_version":"0.45.0","session_id":"sess-ok-1","workspace_roots":["'"${WS}"'"]}'
out=$(run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_ALWAYS} XDG_RUNTIME_DIR=${STAMP_BASE}/a" "$json" 2>/dev/null || true)
assert_json_context "cursor emits always-one" "$out" "RULE_BODY_ALWAYS"

# 3) Dedup: same session_id → second call empty
out2=$(run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_ALWAYS} XDG_RUNTIME_DIR=${STAMP_BASE}/a" "$json" 2>/dev/null || true)
assert_empty "session dedup" "$out2"

# 4) paths: scoped file excluded
json2='{"cursor_version":"1","session_id":"sess-mixed","workspace_roots":[]}'
out3=$(run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_MIXED} XDG_RUNTIME_DIR=${STAMP_BASE}/b" "$json2" 2>/dev/null || true)
assert_json_context "paths scoped excluded" "$out3" "RULE_BODY_ALWAYS"
if printf '%s' "$out3" | jq -r '.additional_context' | grep -q 'RULE_BODY_SCOPED'; then
  echo "FAIL: paths scoped excluded — scoped body leaked"
  FAIL=1
else
  echo "ok: paths scoped excluded — no scoped body"
fi

# 5) Workspace fallback without APM_ALWAYS_ON_RULES_DIR
json3='{"cursor_version":"1","session_id":"sess-ws","workspace_roots":["'"${WS}"'"]}'
out4=$(run_hook "XDG_RUNTIME_DIR=${STAMP_BASE}/c" "$json3" 2>/dev/null || true)
assert_json_context "workspace .claude/rules fallback" "$out4" "RULE_BODY_ALWAYS"

# 6) Debug mode writes to stderr (smoke)
EMPTY_HOME="${TMP_BASE}/emptyhome"
mkdir -p "$EMPTY_HOME"
err=$(run_hook "APM_ALWAYS_ON_RULES_DEBUG=1 HOME=${EMPTY_HOME} XDG_RUNTIME_DIR=${STAMP_BASE}/d" '{"cursor_version":"1","session_id":"dbg1","workspace_roots":[]}' 2>&1 >/dev/null || true)
if printf '%s' "$err" | grep -q 'skip:'; then
  echo "ok: debug stderr"
else
  echo "FAIL: debug stderr — expected skip message"
  FAIL=1
fi

# 7) Unsafe session_id rejected
json_bad='{"cursor_version":"1","session_id":"../evil"}'
out5=$(run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_ALWAYS} XDG_RUNTIME_DIR=${STAMP_BASE}/e" "$json_bad" 2>/dev/null || true)
assert_empty "unsafe session_id" "$out5"

# 8) CLAUDE_CONFIG_DIR/rules (config dir is ~/.claude equivalent, not parent of .claude)
CFG="${TMP_BASE}/claude-config"
mkdir -p "${CFG}/rules"
cp "${RULES_ALWAYS}/always-one.md" "${CFG}/rules/"
json_cfg='{"cursor_version":"1","session_id":"sess-cfg","workspace_roots":[]}'
EMPTY_HOME_CFG="${TMP_BASE}/home-no-claude"
mkdir -p "$EMPTY_HOME_CFG"
out_cfg=$(run_hook "CLAUDE_CONFIG_DIR=${CFG} HOME=${EMPTY_HOME_CFG} XDG_RUNTIME_DIR=${STAMP_BASE}/f" "$json_cfg" 2>/dev/null || true)
assert_json_context "CLAUDE_CONFIG_DIR rules" "$out_cfg" "RULE_BODY_ALWAYS"

# 9) Default HOME/.claude/rules when no workspace and no CLAUDE_CONFIG_DIR override
HOME_DEFAULT="${TMP_BASE}/home-default"
mkdir -p "${HOME_DEFAULT}/.claude/rules"
cp "${RULES_ALWAYS}/always-one.md" "${HOME_DEFAULT}/.claude/rules/"
json_home='{"cursor_version":"1","session_id":"sess-home","workspace_roots":[]}'
out_home=$(run_hook "HOME=${HOME_DEFAULT} XDG_RUNTIME_DIR=${STAMP_BASE}/g" "$json_home" 2>/dev/null || true)
assert_json_context "HOME .claude/rules default" "$out_home" "RULE_BODY_ALWAYS"

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
echo "All tests passed."