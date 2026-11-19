#!/bin/bash
# Cursor sessionStart hook: inject always-on rules as additional_context.
#
# Claude Code loads ~/.claude/rules/*.md without `paths:` at launch, but Cursor
# turns instructions without applyTo into description-only rules. This hook
# reads the always-on rules APM deployed to ~/.claude/rules/ and returns them to
# Cursor as {"additional_context": "..."}.
#
# APM deploys every hook file to every hook target, so the script only answers
# Cursor (its input carries "cursor_version") and prints nothing elsewhere;
# Claude Code already has these rules natively. It never fails the session:
# any missing dependency or error exits 0 with no output.

set -u

rules_dir="${APM_ALWAYS_ON_RULES_DIR:-${CLAUDE_CONFIG_DIR:-$HOME/.claude}/rules}"

input=$(cat 2>/dev/null || true)

case "$input" in
  *'"cursor_version"'*) ;;
  *) exit 0 ;;
esac

[ -d "$rules_dir" ] || exit 0

# Cursor can also import Claude Code hooks, so the same session may run this
# script twice. Answer each session once.
session_id=$(printf '%s' "$input" | sed -n 's/.*"session_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)
if [ -n "$session_id" ]; then
  stamp_dir="${TMPDIR:-/tmp}/apm-always-on-rules"
  mkdir -p "$stamp_dir" 2>/dev/null || true
  stamp="$stamp_dir/$(printf '%s' "$session_id" | tr -c 'A-Za-z0-9._-' '_')"
  if [ -e "$stamp" ]; then
    exit 0
  fi
  : > "$stamp" 2>/dev/null || true
fi

context=""
for f in "$rules_dir"/*.md; do
  [ -f "$f" ] || continue
  # Skip path-scoped rules: a leading frontmatter block that declares paths:.
  if awk 'NR==1 { if ($0 != "---") exit 1; next } /^---$/ { exit 1 } /^paths:/ { found=1; exit } END { exit found ? 0 : 1 }' "$f"; then
    continue
  fi
  body=$(awk 'NR==1 && $0=="---" { fm=1; next } fm && $0=="---" { fm=0; next } !fm' "$f")
  [ -n "$body" ] || continue
  context="${context}

<!-- source: ~/.claude/rules/$(basename "$f") -->
${body}"
done

[ -n "$context" ] || exit 0

context="Always-on rules (injected by the takak2166/agent cursor-always-on-rules sessionStart hook):${context}"

if command -v jq >/dev/null 2>&1; then
  jq -n --arg c "$context" '{additional_context: $c}' 2>/dev/null || exit 0
elif command -v python3 >/dev/null 2>&1; then
  printf '%s' "$context" | python3 -c 'import json, sys; print(json.dumps({"additional_context": sys.stdin.read()}, ensure_ascii=False))' 2>/dev/null || exit 0
fi
exit 0
