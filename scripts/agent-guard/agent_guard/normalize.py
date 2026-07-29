"""Normalize harness hook events into a common action shape.

No git file-tracking enrichment — file edits are out of scope for hooks
(tracked/untracked alike). Shell / SQL / HTTP / MCP only.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

# Leading tokens that are treated as read-only when the whole command is simple.
_READ_ONLY_PREFIXES = (
    "ls",
    "ll",
    "dir",
    "pwd",
    "cd",
    "echo",
    "printf",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "bat",
    "rg",
    "grep",
    "find",
    "fd",
    "which",
    "type",
    "command",
    "true",
    "false",
    "test",
    "[",
    "stat",
    "file",
    "wc",
    "sort",
    "uniq",
    "diff",
    "tree",
    "env",
    "printenv",
    "date",
    "whoami",
    "id",
    "uname",
    "hostname",
    "df",
    "du",
    "free",
    "ps",
    "top",
    "htop",
    "jq",
    "yq",
    "python",
    "python3",
    "node",
    "ruby",
    "perl",
    "awk",
    "sed",  # sed without -i is often filter; -i handled as not read-only below
    "git",
    "gh",
    "kubectl",
    "curl",
    "wget",
    "http",
    "https",
    "psql",
    "mysql",
    "sqlite3",
)

_GIT_READ_ONLY = {
    "status",
    "log",
    "show",
    "diff",
    "branch",
    "tag",
    "remote",
    "fetch",
    "ls-files",
    "ls-tree",
    "rev-parse",
    "rev-list",
    "describe",
    "blame",
    "stash",  # stash list default; stash drop/pop denied elsewhere if needed
    "config",  # get; --unset mutating is rare in agents
    "help",
    "version",
}

_GIT_WRITE = {
    "add",
    "commit",
    "push",
    "pull",
    "merge",
    "rebase",
    "cherry-pick",
    "reset",
    "checkout",
    "switch",
    "restore",
    "clean",
    "rm",
    "mv",
    "init",
    "clone",
    "stash",
}

_KUBECTL_READ = {
    "get",
    "describe",
    "logs",
    "top",
    "api-resources",
    "api-versions",
    "explain",
    "cluster-info",
    "config",
    "version",
    "auth",
    "wait",
}

_SQL_MUTATE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|REPLACE|MERGE|COPY|CALL)\b",
    re.I,
)
_SQL_SELECT = re.compile(r"\b(SELECT|SHOW|DESCRIBE|EXPLAIN|WITH)\b", re.I)

_HTTP_METHOD = re.compile(
    r"(?:(?:-X|--request|--method)\s*)(GET|HEAD|OPTIONS|POST|PUT|PATCH|DELETE)\b",
    re.I,
)


def normalize(event: dict[str, Any], *, source: str = "cursor") -> dict[str, Any]:
    """Convert a raw hook event into a normalized action dict."""
    source = (source or "cursor").lower()
    if source in ("claude", "claude-code", "codex"):
        return _normalize_pre_tool_use(event)
    return _normalize_cursor(event)


def _normalize_cursor(event: dict[str, Any]) -> dict[str, Any]:
    hook = (event.get("hook_event_name") or event.get("event") or "").lower()
    if "mcp" in hook:
        return _mcp_action(event)
    command = event.get("command") or ""
    if isinstance(command, list):
        command = " ".join(str(x) for x in command)
    return _from_shell(str(command), cwd=event.get("cwd"))


def _normalize_pre_tool_use(event: dict[str, Any]) -> dict[str, Any]:
    tool = str(event.get("tool_name") or event.get("toolName") or "")
    raw_input = event.get("tool_input") or event.get("toolInput") or event.get("input") or {}
    if isinstance(raw_input, str):
        # Some harnesses pass JSON string
        import json

        try:
            raw_input = json.loads(raw_input)
        except Exception:
            raw_input = {"command": raw_input}

    if not isinstance(raw_input, dict):
        raw_input = {}

    tool_l = tool.lower()
    if tool_l in ("bash", "shell", "run_terminal_cmd", "terminal"):
        command = str(raw_input.get("command") or raw_input.get("cmd") or "")
        return _from_shell(command, cwd=raw_input.get("cwd") or event.get("cwd"))

    if "mcp" in tool_l or tool_l.startswith("mcp__") or event.get("mcp_server") or event.get("server"):
        return _mcp_action({**event, **raw_input, "tool_name": tool})

    # File tools are intentionally not guarded (tracked/untracked alike).
    if tool_l in ("edit", "write", "multiedit", "strreplace", "delete", "read", "searchreplace"):
        return {
            "kind": "file",
            "path": str(raw_input.get("path") or raw_input.get("file_path") or ""),
            "operation": tool_l,
        }

    # Fallback: treat unknown as shell-ish if command present, else opaque allow via mcp-like
    if raw_input.get("command"):
        return _from_shell(str(raw_input["command"]), cwd=raw_input.get("cwd"))

    return {"kind": "mcp", "server": "unknown", "tool": tool or "unknown", "is_write": False}


def _mcp_action(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "mcp",
        "server": str(event.get("server") or event.get("mcp_server") or event.get("url") or ""),
        "tool": str(event.get("tool_name") or event.get("tool") or event.get("name") or ""),
        "is_write": bool(event.get("is_write", True)),
    }


def _from_shell(command: str, cwd: Any = None) -> dict[str, Any]:
    command = command.strip()
    action: dict[str, Any] = {
        "kind": "shell",
        "command": command,
        "cwd": cwd,
        "read_only": _is_read_only_shell(command),
    }

    # Promote to sql/http when clearly detectable as a dedicated statement.
    # Keep read-only clients as shell (allow-read-only-shell).
    # Promote only when useful for typed deny/allow rules.
    sql_op = _detect_sql_operation(command)
    if sql_op is not None and _looks_like_sql_client(command):
        return {
            "kind": "sql",
            "statement": command,
            "operation": sql_op,
        }

    http_method = _detect_http_method(command)
    if http_method and _looks_like_http_client(command):
        return {
            "kind": "http",
            "method": http_method.upper(),
            "url": _extract_url(command),
            "tool": _http_tool(command),
        }

    return action


def _looks_like_sql_client(command: str) -> bool:
    return bool(
        re.search(
            r"(^|[;&|]\s*)(psql|mysql|mariadb|sqlite3|sqlcmd|clickhouse-client)\b",
            command,
            re.I,
        )
    )


def _looks_like_http_client(command: str) -> bool:
    return bool(re.search(r"(^|[;&|]\s*)(curl|wget|http|https?)\b", command, re.I))


def _detect_sql_operation(command: str) -> str | None:
    m = _SQL_MUTATE.search(command)
    if m:
        return m.group(1).lower()
    if _SQL_SELECT.search(command):
        return "select"
    return None


def _detect_http_method(command: str) -> str | None:
    m = _HTTP_METHOD.search(command)
    if m:
        return m.group(1).upper()
    # curl with body flags implies POST
    if re.search(r"(^|[;&|]\s*)curl\b", command, re.I) and re.search(
        r"(\s-d\s|--data([=\s]|-raw|--)|--json\s)", command
    ):
        return "POST"
    if re.search(r"(^|[;&|]\s*)(curl|wget)\b", command, re.I):
        return "GET"
    return None


def _http_tool(command: str) -> str:
    m = re.search(r"(^|[;&|]\s*)(curl|wget|http|https?)\b", command, re.I)
    return (m.group(2) if m else "curl").lower()


def _extract_url(command: str) -> str:
    m = re.search(r"https?://\S+", command)
    return m.group(0) if m else ""


def _is_read_only_shell(command: str) -> bool:
    if not command:
        return True
    # Split on shell operators; every segment must be read-only.
    parts = re.split(r"(?:&&|\|\||;|\n|\|(?!\|))", command)
    return all(_is_read_only_segment(p.strip()) for p in parts if p.strip())


def _is_read_only_segment(segment: str) -> bool:
    if not segment:
        return True
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if not tokens:
        return True

    # Strip env assignments: FOO=bar cmd
    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        return True

    prog = tokens[0]
    base = prog.rsplit("/", 1)[-1].lower()

    if base in ("sudo", "doas", "pkexec"):
        return False

    if base == "git":
        return _git_read_only(tokens[1:])

    if base == "kubectl":
        sub = _first_subcommand(tokens[1:])
        return sub in _KUBECTL_READ

    if base in ("curl", "wget", "http", "https"):
        method = _detect_http_method(segment) or "GET"
        return method.upper() in {"GET", "HEAD", "OPTIONS"}

    if base in ("psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "clickhouse-client"):
        op = _detect_sql_operation(segment)
        return op in (None, "select")

    if base == "sed" and any(t == "-i" or t.startswith("-i") for t in tokens[1:]):
        return False

    if base in ("rm", "mv", "cp", "chmod", "chown", "chgrp", "mkdir", "rmdir", "touch", "tee", "dd"):
        return False

    if base in ("python", "python3", "node", "ruby", "perl"):
        # Interpreters may mutate; only treat obvious one-liners printing as RO when -c and no write APIs — fail closed.
        return False

    if base in _READ_ONLY_PREFIXES:
        return True

    # Unknown binaries: not read-only (fail-closed via default deny unless another rule matches)
    return False


def _git_read_only(args: list[str]) -> bool:
    sub = _first_subcommand(args)
    if not sub:
        return True
    if sub in _GIT_READ_ONLY and sub not in _GIT_WRITE - {"stash", "config"}:
        # stash without args defaults to push (write). stash list is RO.
        if sub == "stash":
            rest = [a for a in args if not a.startswith("-")]
            if len(rest) >= 2 and rest[1] in {"list", "show"}:
                return True
            if len(rest) == 1:
                return False
            return rest[1] in {"list", "show"}
        return True
    if sub in {"diff", "log", "show", "status", "branch", "tag", "remote", "fetch"}:
        return True
    return False


def _first_subcommand(args: list[str]) -> str:
    for a in args:
        if a.startswith("-"):
            continue
        return a.lower()
    return ""
