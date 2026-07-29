"""Format allow/deny responses for Cursor, Claude Code, and Codex hooks."""

from __future__ import annotations

from typing import Any

ALLOWED_SCOPE = "Allowed: file edits, git commit/push, MCP writes, read-only operations"


def format_decision(
    *,
    allowed: bool,
    reason: str | None = None,
    rule_id: str | None = None,
    target: str = "cursor",
) -> dict[str, Any]:
    """Build a harness-specific hook response payload."""
    if allowed:
        return _allow(target)

    detail = reason or "blocked by policy"
    if rule_id:
        detail = f"[{rule_id}] {detail}"
    message = (
        f"Blocked by Agent Guard: {detail}\n"
        f"{ALLOWED_SCOPE}\n"
        "This guard only blocks production-impacting mutating operations."
    )
    return _deny(target, message)


def _allow(target: str) -> dict[str, Any]:
    t = (target or "cursor").lower()
    if t in ("claude", "claude-code", "codex"):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }
    # Cursor beforeShellExecution (and flat preToolUse compatibility)
    return {"permission": "allow"}


def _deny(target: str, message: str) -> dict[str, Any]:
    t = (target or "cursor").lower()
    if t in ("claude", "claude-code", "codex"):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }
    return {
        "permission": "deny",
        "user_message": message,
        "agent_message": message,
    }
