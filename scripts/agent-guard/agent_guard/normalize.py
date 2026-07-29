"""Normalize harness hook events into a common action shape.

No git file-tracking enrichment — file edits are out of scope for hooks
(tracked/untracked alike). Shell / SQL / HTTP / MCP only.
"""

from __future__ import annotations

import re
import shlex
from typing import Any

from agent_guard.policy_loader import get_compiled_vocab, get_vocab

# Simple read-only commands when the segment has no wrappers/substitution/redirects.
_READ_ONLY_PREFIXES = frozenset(
    {
        "ls",
        "ll",
        "dir",
        "pwd",
        "cd",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "bat",
        "rg",
        "grep",
        "fd",
        "which",
        "type",
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
        "git",
        "kubectl",
        "curl",
        "wget",
        "http",
        "https",
        "psql",
        "mysql",
        "sqlite3",
    }
)

_WRAPPER_CMDS = frozenset({"command", "env", "time", "nice"})

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

_FIND_MUTATE = re.compile(r"-(?:delete|exec|execdir|ok|fprint|fls)\b")
_CMD_SUBST = re.compile(r"\$\(|`")
# Writes except common null/stderr sinks used by read-only diagnostics.
_WRITE_REDIRECT = re.compile(
    r"(?<![0-9])>>?(?!\s*/dev/null\b)|(?<![0-9])>(?!\s*/dev/null\b)|<<<?"
)
_INPUT_REDIRECT = re.compile(r"(?<![0-9])<(?!<<)(?!\s*/dev/null\b)")
_SQL_FILE_INPUT = re.compile(r"(?:^|\s)(?:-[ef]|--file)(?:=|\s|\b)", re.I)


def _compiled():
    return get_compiled_vocab()


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

    if tool_l in ("edit", "write", "multiedit", "strreplace", "delete", "read", "searchreplace"):
        return {
            "kind": "file",
            "path": str(raw_input.get("path") or raw_input.get("file_path") or ""),
            "operation": tool_l,
        }

    if raw_input.get("command"):
        return _from_shell(str(raw_input["command"]), cwd=raw_input.get("cwd"))

    return {"kind": "unknown", "tool": tool or "unknown"}


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
    if _git_commit_has_bypass(command):
        action["git_commit_bypass"] = True
    if _command_has_kubectl_mutate(command):
        action["kubectl_mutate"] = True

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
    return bool(_compiled().sql_client_re.search(command))


def _looks_like_http_client(command: str) -> bool:
    return bool(_compiled().http_client_re.search(command))


def _detect_sql_operation(command: str) -> str | None:
    compiled = _compiled()
    m = compiled.sql_mutate_re.search(command)
    if m:
        return m.group(1).lower()
    if compiled.sql_read_re.search(command):
        return "select"
    return None


def _detect_http_method(command: str) -> str | None:
    compiled = _compiled()
    vocab = compiled.vocab

    if compiled.mutating_http_flags_re.search(command):
        m = compiled.http_method_re.search(command) or compiled.http_method_eq_re.search(command)
        if m:
            method = m.group(1).upper()
            if method in vocab.http_mutate:
                return method
        return "POST"

    m = compiled.http_method_re.search(command) or compiled.http_method_eq_re.search(command)
    if m:
        return m.group(1).upper()

    m = compiled.httpie_mutate_re.search(command)
    if m:
        return m.group(2).upper()

    if compiled.http_client_re.search(command):
        return "GET"
    return None


def _http_tool(command: str) -> str:
    m = _compiled().http_client_re.search(command)
    return (m.group(2) if m else "curl").lower()


def _extract_url(command: str) -> str:
    m = re.search(r"https?://\S+", command)
    return m.group(0) if m else ""


def _segment_has_shell_mutation(segment: str) -> bool:
    if _CMD_SUBST.search(segment):
        return True
    if _WRITE_REDIRECT.search(segment):
        return True
    if _INPUT_REDIRECT.search(segment):
        return True
    return False


def _is_read_only_shell(command: str) -> bool:
    if not command:
        return False
    parts = re.split(r"(?:&&|\|\||;|\n|\|(?!\|))", command)
    return all(_is_read_only_segment(p.strip()) for p in parts if p.strip())


def _unwrap_wrapper(tokens: list[str]) -> str | None:
    if not tokens:
        return None
    base = tokens[0].rsplit("/", 1)[-1].lower()
    if base == "command":
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 1
        if i >= len(tokens):
            return None
        return shlex.join(tokens[i:])
    if base == "env":
        i = 1
        while i < len(tokens):
            token = tokens[i]
            if token == "--":
                rest = tokens[i + 1 :]
                return shlex.join(rest) if rest else None
            if token.startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                i += 1
                continue
            return shlex.join(tokens[i:])
        return None
    if base in {"time", "nice"}:
        i = 1
        while i < len(tokens) and tokens[i].startswith("-"):
            i += 1
        if i >= len(tokens):
            return None
        return shlex.join(tokens[i:])
    return None


def _is_read_only_segment(segment: str) -> bool:
    if not segment:
        return False
    if _segment_has_shell_mutation(segment):
        return False

    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if not tokens:
        return False

    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        return False

    prog = tokens[0]
    base = prog.rsplit("/", 1)[-1].lower()

    if base in _WRAPPER_CMDS:
        inner = _unwrap_wrapper(tokens)
        if inner is None:
            return False
        return _is_read_only_segment(inner)

    if base in ("sudo", "doas", "pkexec"):
        return False

    if base == "git":
        return _git_read_only(tokens[1:])

    if base == "kubectl":
        return _kubectl_read_only(tokens[1:])

    if base in ("curl", "wget", "http", "https"):
        method = _detect_http_method(segment)
        if method is None:
            return False
        return method.upper() in get_vocab().http_read

    if base in ("psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "clickhouse-client"):
        if _SQL_FILE_INPUT.search(segment) or _INPUT_REDIRECT.search(segment):
            return False
        op = _detect_sql_operation(segment)
        return op in (None, "select")

    if base == "find":
        return _FIND_MUTATE.search(segment) is None

    if base == "awk":
        return False

    if base in ("echo", "printf"):
        return False

    if base == "gh":
        return _gh_read_only(tokens[1:])

    if base == "yq":
        return not any(t == "-i" or t.startswith("-i") for t in tokens[1:])

    if base == "sed" and any(t == "-i" or t.startswith("-i") for t in tokens[1:]):
        return False

    if base in ("rm", "mv", "cp", "chmod", "chown", "chgrp", "mkdir", "rmdir", "touch", "tee", "dd"):
        return False

    if base in ("python", "python3", "node", "ruby", "perl"):
        return False

    if base in _READ_ONLY_PREFIXES:
        return True

    return False


def _gh_read_only(args: list[str]) -> bool:
    vocab = get_vocab()
    positional = [a for a in args if not a.startswith("-")]
    if not positional:
        return True
    sub = positional[0]
    if sub == "api":
        return _gh_api_explicit_method(args) == "GET"
    if sub in vocab.gh_write:
        return False
    if len(positional) >= 2 and positional[1] in vocab.gh_write:
        return False
    if sub in vocab.gh_read:
        return True
    return False


def _gh_api_explicit_method(args: list[str]) -> str | None:
    """Return HTTP method only when explicitly set via -X / --method."""
    for i, token in enumerate(args):
        if token in ("-X", "--method") and i + 1 < len(args):
            return args[i + 1].upper()
        if token.startswith("--method="):
            return token.split("=", 1)[1].upper()
    return None


def _command_has_kubectl_mutate(command: str) -> bool:
    parts = re.split(r"(?:&&|\|\||;|\n|\|(?!\|))", command)
    return any(_segment_has_kubectl_mutate(p.strip()) for p in parts if p.strip())


def _segment_has_kubectl_mutate(segment: str) -> bool:
    if not segment:
        return False
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if not tokens:
        return False

    while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        tokens = tokens[1:]
    if not tokens:
        return False

    base = tokens[0].rsplit("/", 1)[-1].lower()
    if base in _WRAPPER_CMDS:
        inner = _unwrap_wrapper(tokens)
        if inner is None:
            return False
        return _segment_has_kubectl_mutate(inner)

    if base != "kubectl":
        return False
    verb = _kubectl_subcommand(tokens[1:])
    return verb in get_vocab().kubectl_mutate


def _kubectl_read_only(args: list[str]) -> bool:
    vocab = get_vocab()
    verb = _kubectl_subcommand(args)
    if not verb:
        return True
    if verb in vocab.kubectl_mutate:
        return False
    if verb in vocab.kubectl_read:
        return True
    return False


def _kubectl_subcommand(args: list[str]) -> str:
    value_flags = get_vocab().kubectl_value_flags
    i = 0
    while i < len(args):
        token = args[i]
        if token in value_flags:
            i += 2
            continue
        if token.startswith("-") and "=" not in token:
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        return token.lower()
    return ""


def _git_commit_has_bypass(command: str) -> bool:
    parts = re.split(r"(?:&&|\|\||;|\n|\|(?!\|))", command)
    return any(_git_commit_segment_has_bypass(p.strip()) for p in parts if p.strip())


def _git_commit_segment_has_bypass(segment: str) -> bool:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if len(tokens) < 2:
        return False
    if tokens[0].rsplit("/", 1)[-1].lower() != "git":
        return False

    i = 1
    while i < len(tokens) and tokens[i] != "commit":
        if not tokens[i].startswith("-"):
            return False
        i += 1
    if i >= len(tokens) or tokens[i] != "commit":
        return False

    i += 1
    while i < len(tokens):
        token = tokens[i]
        if token in ("-m", "--message"):
            return False
        if token in ("--no-verify", "--no-gpg-sign"):
            return True
        if token == "-n":
            return True
        if token.startswith("-") and len(token) > 1 and token not in ("-m",):
            if "n" in token[1:]:
                return True
        i += 1
    return False


def _git_read_only(args: list[str]) -> bool:
    sub = _first_subcommand(args)
    if not sub:
        return True
    if sub in _GIT_READ_ONLY and sub not in _GIT_WRITE - {"stash", "config"}:
        if sub == "stash":
            rest = [a for a in args if not a.startswith("-")]
            if len(rest) >= 2 and rest[1] in {"list", "show"}:
                return True
            if len(rest) == 1:
                return False
            return rest[1] in {"list", "show"}
        if sub == "config":
            return not any(a in {"--unset", "--unset-all", "--replace-all"} for a in args)
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
