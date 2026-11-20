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

# 5) Home always-on + workspace only paths-scoped rules → home rules still emit
WS_SCOPED="${TMP_BASE}/ws-scoped-only"
HOME_LAYER="${TMP_BASE}/home-layer"
mkdir -p "${WS_SCOPED}/.claude/rules" "${HOME_LAYER}/.claude/rules"
cp "${RULES_MIXED}/scoped-one.md" "${WS_SCOPED}/.claude/rules/"
cp "${RULES_ALWAYS}/always-one.md" "${HOME_LAYER}/.claude/rules/"
json_layer='{"cursor_version":"1","session_id":"sess-layer","workspace_roots":["'"${WS_SCOPED}"'"]}'
out4=$(run_hook "HOME=${HOME_LAYER} XDG_RUNTIME_DIR=${STAMP_BASE}/c" "$json_layer" 2>/dev/null || true)
assert_json_context "home rules when workspace is paths-only" "$out4" "RULE_BODY_ALWAYS"
if printf '%s' "$out4" | jq -r '.additional_context' | grep -q 'RULE_BODY_SCOPED'; then
  echo "FAIL: home rules when workspace is paths-only — scoped body leaked"
  FAIL=1
else
  echo "ok: home rules when workspace is paths-only — scoped excluded"
fi

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

# 10) Home + workspace both have always-on rules (both bodies present)
WS_BOTH="${TMP_BASE}/ws-both"
HOME_BOTH="${TMP_BASE}/home-both"
mkdir -p "${WS_BOTH}/.claude/rules" "${HOME_BOTH}/.claude/rules"
cp "${RULES_ALWAYS}/always-one.md" "${HOME_BOTH}/.claude/rules/"
cp "${RULES_MIXED}/always-ws.md" "${WS_BOTH}/.claude/rules/"
json_both='{"cursor_version":"1","session_id":"sess-both","workspace_roots":["'"${WS_BOTH}"'"]}'
out_both=$(run_hook "HOME=${HOME_BOTH} XDG_RUNTIME_DIR=${STAMP_BASE}/h" "$json_both" 2>/dev/null || true)
assert_json_context "home and workspace always-on" "$out_both" "RULE_BODY_ALWAYS"
assert_json_context "home and workspace always-on (ws)" "$out_both" "RULE_BODY_WORKSPACE_ALWAYS"

# 11) Basename dedupe: workspace file with same name as home is skipped
WS_DEDUP="${TMP_BASE}/ws-dedup"
HOME_DEDUP="${TMP_BASE}/home-dedup"
mkdir -p "${WS_DEDUP}/.claude/rules" "${HOME_DEDUP}/.claude/rules"
printf '%s\n' 'HOME_WINS' >"${HOME_DEDUP}/.claude/rules/shared.md"
printf '%s\n' 'WORKSPACE_LOSES' >"${WS_DEDUP}/.claude/rules/shared.md"
cat >"${HOME_DEDUP}/.claude/rules/shared.md" <<'MD'
---
description: shared name
---

HOME_WINS
MD
cat >"${WS_DEDUP}/.claude/rules/shared.md" <<'MD'
---
description: shared name ws
---

WORKSPACE_LOSES
MD
json_dedup='{"cursor_version":"1","session_id":"sess-dedup","workspace_roots":["'"${WS_DEDUP}"'"]}'
out_dedup=$(run_hook "HOME=${HOME_DEDUP} XDG_RUNTIME_DIR=${STAMP_BASE}/i" "$json_dedup" 2>/dev/null || true)
assert_json_context "basename dedupe home wins" "$out_dedup" "HOME_WINS"
if printf '%s' "$out_dedup" | jq -r '.additional_context' | grep -q 'WORKSPACE_LOSES'; then
  echo "FAIL: basename dedupe — workspace duplicate was not skipped"
  FAIL=1
else
  echo "ok: basename dedupe — workspace duplicate skipped"
fi

# 12) No-jq fallback: whitespace before [ in workspace_roots
NOJQF_HOME="${TMP_BASE}/nojqf-home"
mkdir -p "${NOJQF_HOME}/.claude/rules"
cp "${RULES_ALWAYS}/always-one.md" "${NOJQF_HOME}/.claude/rules/"
json_ws='{"cursor_version":"1","session_id":"sess-nojq","workspace_roots" : []}'
PATH_NOJQ="${TMP_BASE}/fakebin:${PATH}"
mkdir -p "${TMP_BASE}/fakebin"
# jq exists on CI; hide it for this test only
if command -v jq >/dev/null 2>&1; then
  ln -sf /bin/false "${TMP_BASE}/fakebin/jq"
fi
out_nojq=$(run_hook "PATH=${PATH_NOJQ} HOME=${NOJQF_HOME} XDG_RUNTIME_DIR=${STAMP_BASE}/j" "$json_ws" 2>/dev/null || true)
assert_json_context "no-jq sed fallback" "$out_nojq" "RULE_BODY_ALWAYS"

json_ws2='{"cursor_version":"1","session_id":"sess-nojq2","workspace_roots" : ["'"${WS_BOTH}"'"]}'
PATH_NOJQ2="${TMP_BASE}/fakebin2:${PATH}"
mkdir -p "${TMP_BASE}/fakebin2"
if command -v jq >/dev/null 2>&1; then
  ln -sf /bin/false "${TMP_BASE}/fakebin2/jq"
fi
HOME_NOJQ2="${TMP_BASE}/nojqf-home2"
mkdir -p "${HOME_NOJQ2}/.claude/rules"
cp "${RULES_ALWAYS}/always-one.md" "${HOME_NOJQ2}/.claude/rules/"
out_nojq2=$(run_hook "PATH=${PATH_NOJQ2} HOME=${HOME_NOJQ2} XDG_RUNTIME_DIR=${STAMP_BASE}/k" "$json_ws2" 2>/dev/null || true)
assert_json_context "no-jq workspace root parse" "$out_nojq2" "RULE_BODY_ALWAYS"

# 13) Stamp cleanup removes files older than 7 days
STAMP_CLEAN="${TMP_BASE}/stamp-clean"
mkdir -p "${STAMP_CLEAN}/apm-always-on-rules-stamps"
touch -t 202001010000 "${STAMP_CLEAN}/apm-always-on-rules-stamps/old-stamp"
json_stamp='{"cursor_version":"1","session_id":"sess-stamp-clean","workspace_roots":[]}'
run_hook "APM_ALWAYS_ON_RULES_DIR=${RULES_ALWAYS} XDG_RUNTIME_DIR=${STAMP_CLEAN}" "$json_stamp" >/dev/null 2>&1 || true
if [ -f "${STAMP_CLEAN}/apm-always-on-rules-stamps/old-stamp" ]; then
  echo "FAIL: stamp cleanup — old stamp file still present"
  FAIL=1
else
  echo "ok: stamp cleanup"
fi

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
echo "All tests passed."