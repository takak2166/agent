#!/bin/bash
# Cursor sessionStart hook: inject always-on rules as additional_context.
#
# Assumes rule files under rules_dir are APM-generated `.claude/rules/*.md`
# (standard `---` / `paths:` frontmatter). Hand-edited or non-APM layouts are
# out of scope for path-scoped detection.
#
# Claude Code loads ~/.claude/rules/*.md without `paths:` at launch, but Cursor
# turns instructions without applyTo into description-only rules. This hook
# reads always-on rules and returns them to Cursor as {"additional_context": "..."}.
#
# Fail-open: missing deps or errors exit 0 with no stdout (optional stderr when
# APM_ALWAYS_ON_RULES_DEBUG=1).

set -u

_debug() {
  if [ "${APM_ALWAYS_ON_RULES_DEBUG:-}" = "1" ]; then
    printf '%s\n' "$*" >&2
  fi
}

_safe_stamp_dir() {
  local base="${XDG_RUNTIME_DIR:-${HOME}/.cache}"
  local dir="${base}/apm-always-on-rules-stamps"
  mkdir -p "$dir" 2>/dev/null || return 1
  chmod 700 "$dir" 2>/dev/null || true
  printf '%s' "$dir"
}

_session_id_safe() {
  local sid="$1"
  case "$sid" in
    '' | '.' | '..') return 1 ;;
  esac
  case "$sid" in
    *'/'* | *'..'* | *$'\n'* | *$'\r'*) return 1 ;;
  esac
  return 0
}

_stamp_path_for_session() {
  local sid="$1"
  local dir
  dir=$(_safe_stamp_dir) || return 1
  local safe
  safe=$(printf '%s' "$sid" | tr -c 'A-Za-z0-9._-' '_')
  printf '%s/%s' "$dir" "$safe"
}

_is_cursor_input() {
  local json="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$json" | jq -e 'type == "object" and .cursor_version != null' >/dev/null 2>&1
    return $?
  fi
  case "$json" in
    *'"cursor_version"'*) return 0 ;;
    *) return 1 ;;
  esac
}

_parse_hook_fields() {
  local json="$1"
  PARSED_SESSION_ID=""
  PARSED_WORKSPACE_ROOT=""
  if command -v jq >/dev/null 2>&1; then
    PARSED_SESSION_ID=$(printf '%s' "$json" | jq -r '.session_id // empty' 2>/dev/null || true)
    PARSED_WORKSPACE_ROOT=$(printf '%s' "$json" | jq -r '.workspace_roots[0] // .workspace_root // empty' 2>/dev/null || true)
    return 0
  fi
  PARSED_SESSION_ID=$(printf '%s' "$json" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
  PARSED_WORKSPACE_ROOT=$(printf '%s' "$json" | sed -n 's/.*"workspace_roots"[[:space:]]*:\[[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
}

_resolve_rules_dir() {
  local workspace_root="$1"
  if [ -n "${APM_ALWAYS_ON_RULES_DIR:-}" ] && [ -d "${APM_ALWAYS_ON_RULES_DIR}" ]; then
    printf '%s' "${APM_ALWAYS_ON_RULES_DIR}"
    return 0
  fi
  if [ -n "$workspace_root" ] && [ -d "${workspace_root}/.claude/rules" ]; then
    printf '%s' "${workspace_root}/.claude/rules"
    return 0
  fi
  local home_rules="${CLAUDE_CONFIG_DIR:-$HOME}/.claude/rules"
  if [ -d "$home_rules" ]; then
    printf '%s' "$home_rules"
    return 0
  fi
  return 1
}

_emit_json() {
  local context="$1"
  local out=""
  if command -v jq >/dev/null 2>&1; then
    out=$(jq -n --arg c "$context" '{additional_context: $c}' 2>/dev/null) || out=""
    if [ -n "$out" ]; then
      printf '%s' "$out"
      return 0
    fi
  fi
  if command -v python3 >/dev/null 2>&1; then
    out=$(printf '%s' "$context" | python3 -c 'import json, sys; print(json.dumps({"additional_context": sys.stdin.read()}, ensure_ascii=False))' 2>/dev/null) || out=""
    if [ -n "$out" ]; then
      printf '%s' "$out"
      return 0
    fi
  fi
  return 1
}

input=$(cat 2>/dev/null || true)

if ! _is_cursor_input "$input"; then
  _debug "skip: not Cursor hook input (no cursor_version)"
  exit 0
fi

_parse_hook_fields "$input"

rules_dir=$(_resolve_rules_dir "${PARSED_WORKSPACE_ROOT:-}") || {
  _debug "skip: no rules directory (set APM_ALWAYS_ON_RULES_DIR, install claude target, or use apm install -g)"
  exit 0
}

stamp=""
if [ -n "${PARSED_SESSION_ID:-}" ]; then
  if ! _session_id_safe "${PARSED_SESSION_ID}"; then
    _debug "skip: unsafe session_id"
    exit 0
  fi
  stamp=$(_stamp_path_for_session "${PARSED_SESSION_ID}") || true
  if [ -n "$stamp" ] && [ -e "$stamp" ]; then
    _debug "skip: session already answered (${PARSED_SESSION_ID})"
    exit 0
  fi
fi

context=""
for f in "$rules_dir"/*.md; do
  [ -f "$f" ] || continue
  # Skip path-scoped rules: APM emits `paths:` in the leading frontmatter block.
  if awk 'NR==1 { if ($0 != "---") exit 1; next } /^---$/ { exit 1 } /^paths:/ { found=1; exit } END { exit found ? 0 : 1 }' "$f"; then
    continue
  fi
  body=$(awk 'NR==1 && $0=="---" { fm=1; next } fm && $0=="---" { fm=0; next } !fm' "$f")
  [ -n "$body" ] || continue
  context="${context}

<!-- source: ${rules_dir}/$(basename "$f") -->
${body}"
done

if [ -z "$context" ]; then
  _debug "skip: no always-on rule bodies under ${rules_dir}"
  exit 0
fi

context="Always-on rules (injected from ${rules_dir} via cursor-always-on-rules sessionStart hook):${context}"

json_out=$(_emit_json "$context") || {
  _debug "skip: could not build JSON (jq/python3 missing or failed)"
  exit 0
}

printf '%s\n' "$json_out"

if [ -n "$stamp" ]; then
  : >"$stamp" 2>/dev/null || _debug "warn: could not write session stamp"
fi

exit 0