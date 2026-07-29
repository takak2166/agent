"""Format allow/deny responses for Cursor, Claude Code, and Codex hooks."""

from __future__ import annotations

from typing import Any

ALLOWED_SCOPE = "ファイル編集、git commit/push、MCP 書き込み、読み取り専用操作"


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

    detail = reason or "ポリシーによりブロックされました"
    if rule_id:
        detail = f"[{rule_id}] {detail}"
    message = (
        f"{detail}\n"
        f"許可されている操作: {ALLOWED_SCOPE}\n"
        "このガードは本番影響のある変更系操作のみをブロックします。"
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
