#!/usr/bin/env python3
"""Targeted table-driven tests to improve mutmut mutation score."""

from __future__ import annotations

import shlex
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_guard.engine import Engine, _compile_rule
from agent_guard.normalize import (
  _command_has_kubectl_mutate,
  _detect_http_method,
  _detect_sql_operation,
  _extract_url,
  _first_subcommand,
  _gh_api_explicit_method,
  _gh_read_only,
  _git_commit_has_bypass,
  _git_commit_segment_has_bypass,
  _git_commit_short_cluster_has_bypass,
  _git_read_only,
  _http_tool,
  _is_read_only_segment,
  _is_read_only_shell,
  _kubectl_read_only,
  _kubectl_subcommand,
  _segment_has_kubectl_mutate,
  _segment_has_shell_mutation,
  _unwrap_wrapper,
  normalize,
)
from agent_guard.policy_loader import (
  PolicyLoader,
  Vocab,
  _alt_join,
  _as_lower_set,
  _as_upper_set,
  _resolve_rule,
  _resolve_value,
  get_compiled_vocab,
  get_policy,
  get_vocab,
)

_MIN_VOCAB = {
  "sql_mutate": ["insert", "delete"],
  "sql_read": ["select"],
  "http_mutate": ["POST", "PUT"],
  "http_read": ["GET"],
  "kubectl_mutate": ["apply", "delete"],
  "kubectl_read": ["get", "describe"],
  "kubectl_value_flags": ["-n", "--namespace"],
  "sql_clients": ["psql", "mysql"],
  "http_clients": ["curl", "wget"],
  "gh_read": ["status", "view", "repo"],
  "gh_write": ["create", "pr"],
}


def _yaml_vocab() -> str:
  lines = ["vocab:"]
  for key, values in _MIN_VOCAB.items():
    quoted = ", ".join(f'"{v}"' if " " in v else v for v in values)
    lines.append(f"  {key}: [{quoted}]")
  return "\n".join(lines)


@dataclass(frozen=True)
class ShellDecideCase:
  id: str
  command: str
  read_only: bool
  allowed: bool
  kubectl_mutate: bool | None = None
  git_commit_bypass: bool | None = None
  rule_id: str | None = None


SHELL_DECIDE_CASES: tuple[ShellDecideCase, ...] = (
  ShellDecideCase("ls", "ls -la", True, True),
  ShellDecideCase("cat", "cat README.md", True, True),
  ShellDecideCase("pwd", "pwd", True, True),
  ShellDecideCase("rg", "rg pattern", True, True),
  ShellDecideCase("true", "true", True, True),
  ShellDecideCase("sudo", "sudo apt update", False, False),
  ShellDecideCase("doas", "doas id", False, False),
  ShellDecideCase("pkexec", "pkexec true", False, False),
  ShellDecideCase("wrapper_command", "command git status", True, True),
  ShellDecideCase("wrapper_env", "env GIT_DIR=/tmp git status", True, True),
  ShellDecideCase("wrapper_env_dd", "env -- git status", True, True),
  ShellDecideCase("wrapper_time", "time git status", True, True),
  ShellDecideCase("wrapper_nice", "nice git status", True, True),
  ShellDecideCase(
    "wrapper_kubectl_mutate",
    "command kubectl apply -f x.yaml",
    False,
    False,
    kubectl_mutate=True,
  ),
  ShellDecideCase("env_assign", "FOO=bar git status", True, True),
  ShellDecideCase("yq_read", "yq . file.yaml", True, True),
  ShellDecideCase("yq_mutate", "yq -i '.x=1' file.yaml", False, False),
  ShellDecideCase("sed_mutate", "sed -i 's/a/b/' file.txt", False, False),
  ShellDecideCase("git_stash_list", "git stash list", False, False),
  ShellDecideCase("git_stash_show", "git stash show", False, False),
  ShellDecideCase("git_stash", "git stash", False, False),
  ShellDecideCase("git_config_get", "git config user.name", False, False),
  ShellDecideCase("git_config_unset", "git config --unset user.name", False, False),
  ShellDecideCase("git_add", "git add .", False, False),
  ShellDecideCase("git_merge", "git merge main", False, False),
  ShellDecideCase("git_rebase", "git rebase main", False, False),
  ShellDecideCase("gh_version", "gh --version", True, True),
  ShellDecideCase("gh_repo_view", "gh repo view owner/repo", True, True),
  ShellDecideCase("gh_unknown", "gh foobar", False, False),
  ShellDecideCase("gh_api_get", "gh api --method=GET repos/o/r", True, True),
  ShellDecideCase("python", "python3 -c 'print(1)'", False, False),
  ShellDecideCase("node", "node -e '1'", False, False),
  ShellDecideCase("rm", "rm -rf /tmp/x", False, False),
  ShellDecideCase("touch", "touch x", False, False),
  ShellDecideCase("find_read", "find . -name '*.txt'", True, True),
  ShellDecideCase("find_delete", "find . -name '*.txt' -delete", False, False),
  ShellDecideCase("multi_read", "git status && kubectl get pods", True, True),
  ShellDecideCase("multi_mutate", "git status && kubectl apply -f x.yaml", False, False),
  ShellDecideCase("kubectl_get", "kubectl -n prod get pods", True, True),
  ShellDecideCase(
    "kubectl_delete",
    "kubectl -n prod delete pod x",
    False,
    False,
    kubectl_mutate=True,
  ),
  ShellDecideCase("empty_command", "", False, False),
  ShellDecideCase(
    "git_commit_bypass",
    "git commit --no-gpg-sign -m x",
    False,
    False,
    git_commit_bypass=True,
    rule_id="deny-git-commit-bypass",
  ),
  ShellDecideCase(
    "git_commit_bypass_after_message",
    'git commit -m "x" --no-verify',
    False,
    False,
    git_commit_bypass=True,
    rule_id="deny-git-commit-bypass",
  ),
  ShellDecideCase("git_log", "git log --oneline -5", True, True),
  ShellDecideCase("git_diff", "git diff HEAD", True, True),
  ShellDecideCase("git_fetch", "git fetch origin", True, True),
  ShellDecideCase("git_push", "git push origin main", False, True),
  ShellDecideCase("git_commit_ok", 'git commit -m "ok"', False, True),
  ShellDecideCase("chmod", "chmod +x script.sh", False, False),
  ShellDecideCase("mkdir", "mkdir -p /tmp/x", False, False),
  ShellDecideCase("awk_deny", "awk '{print $1}' file", False, False),
  ShellDecideCase("echo_deny", "echo hello", False, False),
  ShellDecideCase("sed_read", "sed 's/a/b/' file.txt", False, False),
  ShellDecideCase("curl_post", "curl -X POST https://example.com", False, False),
  ShellDecideCase("psql_file", "psql -f schema.sql", False, False),
  ShellDecideCase("mysql_select", 'mysql -e "SELECT 1"', True, True),
  ShellDecideCase("pipe_read", "git status | head", True, True),
  ShellDecideCase("semicolon_mutate", "git status; kubectl apply -f x.yaml", False, False),
  ShellDecideCase("gh_status", "gh status", True, True),
  ShellDecideCase("gh_pr_create", "gh pr create", False, False),
  ShellDecideCase("kubectl_describe", "kubectl describe pod x", True, True),
  ShellDecideCase("kubectl_unknown", "kubectl unknown-verb", False, False),
  ShellDecideCase("cmd_subst", "echo $(git status)", False, False),
  ShellDecideCase("redirect_write", "echo x > /tmp/out.txt", False, False),
  ShellDecideCase("path_git", "/usr/bin/git status", True, True),
  ShellDecideCase("sqlite_select", 'sqlite3 db.sqlite "SELECT 1"', True, True),
  ShellDecideCase("httpie_get", "http GET https://example.com", True, True),
)


@dataclass(frozen=True)
class ShellKindCase:
  id: str
  command: str
  kind: str
  operation: str | None = None
  method: str | None = None
  tool: str | None = None
  url_contains: str | None = None
  allowed: bool | None = None


SHELL_KIND_CASES: tuple[ShellKindCase, ...] = (
  ShellKindCase("psql_select", 'psql -c "SELECT 1"', "sql", operation="select", allowed=True),
  ShellKindCase(
    "mysql_delete",
    'mysql -e "DELETE FROM t"',
    "sql",
    operation="delete",
    allowed=False,
  ),
  ShellKindCase(
    "curl_get",
    "curl -s https://example.com",
    "http",
    method="GET",
    tool="curl",
    url_contains="https://example.com",
  ),
  ShellKindCase("wget", "wget -q https://example.com/data", "http", tool="wget"),
  ShellKindCase(
    "curl_post",
    "curl -X POST -d '{}' https://example.com/api",
    "http",
    method="POST",
    tool="curl",
    allowed=False,
  ),
  ShellKindCase(
    "psql_insert",
    'psql -c "INSERT INTO t VALUES (1)"',
    "sql",
    operation="insert",
    allowed=False,
  ),
)


@dataclass(frozen=True)
class NormalizeEventCase:
  id: str
  event: dict[str, Any]
  source: str
  expected: dict[str, Any]


NORMALIZE_EVENT_CASES: tuple[NormalizeEventCase, ...] = (
  NormalizeEventCase(
    "claude_bash",
    {"tool_name": "bash", "tool_input": {"command": "git log --oneline"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_tool_name_camel",
    {"toolName": "bash", "toolInput": {"command": "git status"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_mcp",
    {"tool_name": "mcp__linear", "tool_input": {"server": "linear", "tool": "list_issues"}},
    "claude",
    {"kind": "mcp", "is_write": True},
  ),
  NormalizeEventCase(
    "claude_file_read",
    {"tool_name": "read", "tool_input": {"path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "read"},
  ),
  NormalizeEventCase(
    "claude_unknown",
    {"tool_name": "custom_tool", "tool_input": {}},
    "claude",
    {"kind": "unknown"},
  ),
  NormalizeEventCase(
    "claude_json_string_input",
    {"tool_name": "bash", "tool_input": '{"command": "git status"}'},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "cursor_mcp_hook",
    {"hook_event_name": "mcp", "server": "context7", "tool_name": "query-docs"},
    "cursor",
    {"kind": "mcp"},
  ),
  NormalizeEventCase(
    "codex_bash",
    {"tool_name": "bash", "tool_input": {"command": "git status"}},
    "codex",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_code_shell",
    {"tool_name": "shell", "tool_input": {"cmd": "ls -la"}},
    "claude-code",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_run_terminal_cmd",
    {"tool_name": "run_terminal_cmd", "tool_input": {"command": "pwd"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_terminal",
    {"tool_name": "terminal", "tool_input": {"command": "true"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_input_key",
    {"tool_name": "bash", "input": {"command": "git status"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_write_file",
    {"tool_name": "write", "tool_input": {"path": "/tmp/out.txt"}},
    "claude",
    {"kind": "file", "operation": "write"},
  ),
  NormalizeEventCase(
    "claude_edit_file",
    {"tool_name": "edit", "tool_input": {"file_path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "edit"},
  ),
  NormalizeEventCase(
    "claude_delete_file",
    {"tool_name": "delete", "tool_input": {"path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "delete"},
  ),
  NormalizeEventCase(
    "claude_multiedit",
    {"tool_name": "multiedit", "tool_input": {"path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "multiedit"},
  ),
  NormalizeEventCase(
    "claude_strreplace",
    {"tool_name": "strreplace", "tool_input": {"path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "strreplace"},
  ),
  NormalizeEventCase(
    "claude_searchreplace",
    {"tool_name": "searchreplace", "tool_input": {"path": "/tmp/x"}},
    "claude",
    {"kind": "file", "operation": "searchreplace"},
  ),
  NormalizeEventCase(
    "claude_mcp_server_field",
    {"tool_name": "query", "mcp_server": "linear", "tool_input": {}},
    "claude",
    {"kind": "mcp"},
  ),
  NormalizeEventCase(
    "claude_server_field",
    {"tool_name": "query", "server": "linear", "tool_input": {}},
    "claude",
    {"kind": "mcp", "server": "linear"},
  ),
  NormalizeEventCase(
    "claude_mcp_via_server_in_input",
    {"tool_name": "tool", "tool_input": {"server": "notion", "tool": "search"}},
    "claude",
    {"kind": "unknown", "tool": "tool"},
  ),
  NormalizeEventCase(
    "claude_json_invalid_string",
    {"tool_name": "bash", "tool_input": "git status"},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_raw_input_not_dict",
    {"tool_name": "custom", "tool_input": 42},
    "claude",
    {"kind": "unknown", "tool": "custom"},
  ),
  NormalizeEventCase(
    "claude_unknown_with_command_fallback",
    {"tool_name": "custom", "tool_input": {"command": "git status"}},
    "claude",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "claude_empty_tool",
    {"tool_name": "", "tool_input": {}},
    "claude",
    {"kind": "unknown", "tool": "unknown"},
  ),
  NormalizeEventCase(
    "cursor_command_list",
    {"command": ["git", "status"]},
    "cursor",
    {"kind": "shell", "read_only": True},
  ),
  NormalizeEventCase(
    "cursor_event_mcp",
    {"event": "beforeMCP", "server": "x", "tool_name": "y"},
    "cursor",
    {"kind": "mcp"},
  ),
  NormalizeEventCase(
    "mcp_is_write_false",
    {"hook_event_name": "mcp", "server": "s", "tool_name": "t", "is_write": False},
    "cursor",
    {"kind": "mcp", "is_write": False},
  ),
  NormalizeEventCase(
    "mcp_url_server",
    {"hook_event_name": "mcp", "url": "https://mcp.example", "name": "fetch"},
    "cursor",
    {"kind": "mcp", "server": "https://mcp.example", "tool": "fetch"},
  ),
  NormalizeEventCase(
    "mcp_tool_field",
    {"hook_event_name": "mcp", "server": "s", "tool": "list"},
    "cursor",
    {"kind": "mcp", "tool": "list"},
  ),
  NormalizeEventCase(
    "normalize_default_source",
    {"command": "git status"},
    "",
    {"kind": "shell", "read_only": True},
  ),
)


@dataclass(frozen=True)
class EngineActionCase:
  id: str
  action: dict[str, Any] | None
  allowed: bool
  rule_id: str | None = None
  default: bool | None = None
  reason: str | None = None


ENGINE_ACTION_CASES: tuple[EngineActionCase, ...] = (
  EngineActionCase(
    "none",
    None,
    False,
    default=True,
    reason="No actions to evaluate",
  ),
  EngineActionCase(
    "read_only_false",
    {"kind": "shell", "command": "x", "read_only": False},
    False,
  ),
  EngineActionCase(
    "git_commit_bypass",
    {"kind": "shell", "command": "x", "git_commit_bypass": True},
    False,
  ),
  EngineActionCase(
    "kubectl_mutate",
    {"kind": "shell", "command": "x", "kubectl_mutate": True},
    False,
  ),
  EngineActionCase(
    "operation_insert",
    {"kind": "sql", "operation": "insert"},
    False,
  ),
  EngineActionCase(
    "method_post",
    {"kind": "http", "method": "POST"},
    False,
  ),
  EngineActionCase(
    "allow_read_only_shell",
    {"kind": "shell", "command": "git status", "read_only": True},
    True,
    rule_id="allow-read-only-shell",
  ),
  EngineActionCase(
    "default_deny_unknown",
    {"kind": "unknown", "tool": "custom"},
    False,
    default=True,
  ),
  EngineActionCase(
    "allow_mcp",
    {"kind": "mcp", "server": "x", "tool": "y"},
    True,
    rule_id="allow-mcp",
  ),
)


@dataclass(frozen=True)
class InvalidCompileRuleCase:
  id: str
  rule: Any
  pattern: str


INVALID_COMPILE_RULE_CASES: tuple[InvalidCompileRuleCase, ...] = (
  InvalidCompileRuleCase("not_dict", "not-a-dict", r"each rule must be a mapping"),
  InvalidCompileRuleCase("missing_id", {"action": "allow"}, r"rule missing id"),
  InvalidCompileRuleCase("bad_action", {"id": "x", "action": "maybe"}, r"action must be allow or deny"),
  InvalidCompileRuleCase("bad_match_type", {"id": "x", "action": "deny", "match": "bad"}, r"match must be a mapping"),
  InvalidCompileRuleCase(
    "bad_operation_in",
    {"id": "x", "action": "deny", "match": {"operation_in": "bad"}},
    r"operation_in must be a list",
  ),
  InvalidCompileRuleCase(
    "bad_method_in",
    {"id": "x", "action": "deny", "match": {"method_in": "bad"}},
    r"method_in must be a list",
  ),
)


@dataclass(frozen=True)
class EngineYamlCase:
  id: str
  yaml: str
  action: dict[str, Any]
  allowed: bool
  rule_id: str | None = None
  reason: str | None = None
  default: bool | None = None


ENGINE_YAML_CASES: tuple[EngineYamlCase, ...] = (
  EngineYamlCase(
    "deny_no_reason",
    f"""default: deny
{_yaml_vocab()}
rules:
  - id: deny-shell
    action: deny
    match:
      kind: shell
""",
    {"kind": "shell", "command": "ls"},
    False,
    rule_id="deny-shell",
    reason="blocked by policy",
  ),
  EngineYamlCase(
    "allow_no_reason",
    f"""default: deny
{_yaml_vocab()}
rules:
  - id: allow-file
    action: allow
    match:
      kind: file
""",
    {"kind": "file", "operation": "read"},
    True,
    rule_id="allow-file",
    reason="All actions allowed",
  ),
  EngineYamlCase(
    "deny_explicit_reason",
    f"""default: allow
{_yaml_vocab()}
rules:
  - id: deny-sql
    action: deny
    reason: "SQL blocked"
    match:
      kind: sql
""",
    {"kind": "sql", "operation": "select"},
    False,
    reason="SQL blocked",
  ),
  EngineYamlCase(
    "default_allow",
    f"""default: allow
{_yaml_vocab()}
rules: []
""",
    {"kind": "other"},
    True,
    default=True,
    reason="All actions allowed",
  ),
  EngineYamlCase(
    "default_deny",
    f"""default: deny
{_yaml_vocab()}
rules: []
""",
    {"kind": "other"},
    False,
    reason="No matching policy rule (default)",
  ),
  EngineYamlCase(
    "command_regex",
    f"""default: deny
{_yaml_vocab()}
rules:
  - id: deny-sudo
    action: deny
    reason: "sudo blocked"
    match:
      kind: shell
      command_regex: 'sudo'
""",
    {"kind": "shell", "command": "sudo apt"},
    False,
    rule_id="deny-sudo",
    reason="sudo blocked",
  ),
  EngineYamlCase(
    "match_read_only",
    f"""default: deny
{_yaml_vocab()}
rules:
  - id: allow-read-shell
    action: allow
    match:
      kind: shell
      read_only: true
""",
    {"kind": "shell", "command": "git status", "read_only": True},
    True,
    rule_id="allow-read-shell",
  ),
  EngineYamlCase(
    "match_kubectl_mutate",
    f"""default: allow
{_yaml_vocab()}
rules:
  - id: deny-kubectl-mutate
    action: deny
    match:
      kind: shell
      kubectl_mutate: true
""",
    {"kind": "shell", "command": "kubectl apply -f x.yaml", "kubectl_mutate": True},
    False,
    rule_id="deny-kubectl-mutate",
  ),
  EngineYamlCase(
    "match_git_commit_bypass",
    f"""default: allow
{_yaml_vocab()}
rules:
  - id: deny-commit-bypass
    action: deny
    match:
      kind: shell
      git_commit_bypass: true
""",
    {"kind": "shell", "command": "git commit --no-verify -m x", "git_commit_bypass": True},
    False,
    rule_id="deny-commit-bypass",
  ),
)


@dataclass(frozen=True)
class ParseErrorCase:
  id: str
  fn: Callable[[], Any]
  pattern: str


def _parse_cases() -> tuple[ParseErrorCase, ...]:
  vocab = _MIN_VOCAB
  missing_key_vocab = dict(vocab)
  del missing_key_vocab["sql_mutate"]
  empty_list_vocab = dict(vocab)
  empty_list_vocab["sql_mutate"] = []
  non_list_vocab = dict(vocab)
  non_list_vocab["http_read"] = "GET"
  v = Vocab.from_mapping(vocab)
  return (
    ParseErrorCase("non_dict", lambda: PolicyLoader._parse([]), r"^policy document must be a mapping$"),
    ParseErrorCase(
      "missing_vocab",
      lambda: PolicyLoader._parse({"rules": []}),
      r"^vocab section is required$",
    ),
    ParseErrorCase(
      "vocab_not_dict",
      lambda: PolicyLoader._parse({"vocab": "bad", "rules": []}),
      r"^vocab section is required$",
    ),
    ParseErrorCase(
      "rules_not_list",
      lambda: PolicyLoader._parse({"vocab": vocab, "rules": "bad"}),
      r"^rules must be a list$",
    ),
    ParseErrorCase(
      "invalid_default",
      lambda: PolicyLoader._parse({"vocab": vocab, "rules": [], "default": "maybe"}),
      r"^default must be allow or deny$",
    ),
    ParseErrorCase(
      "vocab_missing_keys",
      lambda: Vocab.from_mapping(missing_key_vocab),
      "vocab missing keys",
    ),
    ParseErrorCase(
      "vocab_empty_list",
      lambda: Vocab.from_mapping(empty_list_vocab),
      r"^vocab list must be a non-empty list$",
    ),
    ParseErrorCase(
      "vocab_non_list",
      lambda: Vocab.from_mapping(non_list_vocab),
      r"^vocab list must be a non-empty list$",
    ),
    ParseErrorCase(
      "rule_missing_id",
      lambda: _resolve_rule({"match": {}}, v, {}),
      r"^rule missing id$",
    ),
    ParseErrorCase(
      "rule_not_dict",
      lambda: _resolve_rule("bad", v, {}),
      r"^each rule must be a mapping",
    ),
    ParseErrorCase(
      "rule_bad_match",
      lambda: _resolve_rule({"id": "x", "match": "bad"}, v, {}),
      "match must be a mapping",
    ),
    ParseErrorCase(
      "unknown_vocab_ref",
      lambda: _resolve_value("$vocab.missing_key", v, {}),
      r"^unknown vocab key: missing_key$",
    ),
    ParseErrorCase(
      "unknown_pattern_ref",
      lambda: _resolve_value("$pattern.missing", v, {}),
      r"^unknown pattern key: missing$",
    ),
  )


PARSE_ERROR_CASES = _parse_cases()


@dataclass(frozen=True)
class UnwrapWrapperCase:
  id: str
  command: str
  expected: str | None


UNWRAP_WRAPPER_CASES: tuple[UnwrapWrapperCase, ...] = (
  UnwrapWrapperCase("path_command", "/usr/bin/command git status", "git status"),
  UnwrapWrapperCase("path_env", "/bin/env git status", "git status"),
  UnwrapWrapperCase("env_double_dash", "env -- git status", "git status"),
  UnwrapWrapperCase("env_assignment", "env FOO=bar git status", "git status"),
  UnwrapWrapperCase("nice_plain", "nice git status", "git status"),
  UnwrapWrapperCase("nice_flags", "nice -n 10 git status", "10 git status"),
)


@dataclass(frozen=True)
class IdTokensCase:
  id: str
  tokens: list[str]


@dataclass(frozen=True)
class IdStrBoolCase:
  id: str
  value: str
  expected: bool


@dataclass(frozen=True)
class IdArgsBoolCase:
  id: str
  args: list[str]
  expected: bool


@dataclass(frozen=True)
class IdArgsStrCase:
  id: str
  args: list[str]
  expected: str


@dataclass(frozen=True)
class IdArgsOptionalStrCase:
  id: str
  args: list[str]
  expected: str | None


@dataclass(frozen=True)
class IdCommandStrCase:
  id: str
  command: str
  expected: str


@dataclass(frozen=True)
class IdAttrTextCase:
  id: str
  attr: str
  text: str


UNWRAP_WRAPPER_NONE_CASES: tuple[IdTokensCase, ...] = (
  IdTokensCase("empty", []),
  IdTokensCase("command_only", ["command"]),
  IdTokensCase("non_wrapper", ["git", "status"]),
)


READ_ONLY_SEGMENT_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("empty", "", False),
  IdStrBoolCase("whitespace", "   ", False),
  IdStrBoolCase("head", "head -20 README.md", True),
  IdStrBoolCase("grep", "grep pattern file.txt", True),
  IdStrBoolCase("jq", "jq . data.json", True),
  IdStrBoolCase("stat", "stat file.txt", True),
  IdStrBoolCase("awk", "awk '{print $1}' file", False),
  IdStrBoolCase("echo", "echo hello", False),
  IdStrBoolCase("printf", "printf '%s' x", False),
  IdStrBoolCase("python", "python3 -c 'print(1)'", False),
  IdStrBoolCase("node", "node -e '1'", False),
  IdStrBoolCase("ruby", "ruby -e '1'", False),
  IdStrBoolCase("perl", "perl -e '1'", False),
  IdStrBoolCase("rm", "rm -rf /tmp/x", False),
  IdStrBoolCase("mv", "mv a b", False),
  IdStrBoolCase("cp", "cp a b", False),
  IdStrBoolCase("chmod", "chmod +x script.sh", False),
  IdStrBoolCase("mkdir", "mkdir -p /tmp/x", False),
  IdStrBoolCase("touch", "touch x", False),
  IdStrBoolCase("tee", "tee /tmp/x", False),
  IdStrBoolCase("dd", "dd if=/dev/zero of=/tmp/x", False),
  IdStrBoolCase("git_status", "git status", True),
  IdStrBoolCase("git_log", "git log --oneline", True),
  IdStrBoolCase("git_add", "git add .", False),
  IdStrBoolCase("git_push", "git push", False),
  IdStrBoolCase("git_config_unset", "git config --unset user.name", False),
  IdStrBoolCase("kubectl_get", "kubectl get pods", True),
  IdStrBoolCase("kubectl_apply", "kubectl apply -f x.yaml", False),
  IdStrBoolCase("kubectl_no_verb", "kubectl -n prod", True),
  IdStrBoolCase("curl_get_implicit", "curl -s https://example.com", True),
  IdStrBoolCase("curl_post", "curl -X POST https://example.com", False),
  IdStrBoolCase("wget_get", "wget -q https://example.com", True),
  IdStrBoolCase("http_get", "http GET https://example.com", True),
  IdStrBoolCase("psql_select", 'psql -c "SELECT 1"', True),
  IdStrBoolCase("psql_insert", 'psql -c "INSERT INTO t VALUES (1)"', False),
  IdStrBoolCase("psql_file", "psql -f schema.sql", False),
  IdStrBoolCase("mysql_select", 'mysql -e "SELECT 1"', False),
  IdStrBoolCase("sqlite_select", 'sqlite3 db.sqlite "SELECT 1"', True),
  IdStrBoolCase("find_read", "find . -name '*.txt'", True),
  IdStrBoolCase("find_delete", "find . -delete", False),
  IdStrBoolCase("gh_status", "gh status", True),
  IdStrBoolCase("gh_view", "gh view 123", True),
  IdStrBoolCase("gh_pr_create", "gh pr create", False),
  IdStrBoolCase("gh_api_no_method", "gh api repos/o/r", False),
  IdStrBoolCase("gh_api_get", "gh api --method=GET repos/o/r", True),
  IdStrBoolCase("yq_read", "yq . file.yaml", True),
  IdStrBoolCase("yq_inplace", "yq -i '.x=1' file.yaml", False),
  IdStrBoolCase("sed_read", "sed 's/a/b/' file.txt", False),
  IdStrBoolCase("sed_inplace", "sed -i 's/a/b/' file.txt", False),
  IdStrBoolCase("sudo", "sudo apt update", False),
  IdStrBoolCase("doas", "doas id", False),
  IdStrBoolCase("pkexec", "pkexec true", False),
  IdStrBoolCase("env_assign_ls", "FOO=bar ls", True),
  IdStrBoolCase("wrapper_command", "command git status", True),
  IdStrBoolCase("wrapper_env", "env FOO=bar git status", True),
  IdStrBoolCase("wrapper_time", "time git status", True),
  IdStrBoolCase("wrapper_empty", "command", False),
  IdStrBoolCase("path_git", "/usr/bin/git status", True),
  IdStrBoolCase("cmd_subst", "echo $(git status)", False),
  IdStrBoolCase("redirect_out", "echo x > /tmp/out.txt", False),
  IdStrBoolCase("redirect_append", "echo x >> /tmp/out.txt", False),
  IdStrBoolCase("input_redirect", "cat < /tmp/in.txt", False),
  IdStrBoolCase("unknown_cmd", "foobar --help", False),
)


READ_ONLY_SHELL_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("empty", "", False),
  IdStrBoolCase("single_read", "git status", True),
  IdStrBoolCase("multi_read", "git status && kubectl get pods", True),
  IdStrBoolCase("multi_mutate", "git status && kubectl apply -f x.yaml", False),
  IdStrBoolCase("semicolon", "git status; git log", True),
  IdStrBoolCase("pipe", "git status | head", True),
  IdStrBoolCase("newline", "git status\ngit log", True),
)


GIT_READ_ONLY_CASES: tuple[IdArgsBoolCase, ...] = (
  IdArgsBoolCase("empty", [], True),
  IdArgsBoolCase("status", ["status"], True),
  IdArgsBoolCase("log", ["log", "--oneline"], True),
  IdArgsBoolCase("diff", ["diff", "HEAD"], True),
  IdArgsBoolCase("show", ["show", "HEAD"], True),
  IdArgsBoolCase("branch", ["branch", "-a"], True),
  IdArgsBoolCase("tag", ["tag", "-l"], True),
  IdArgsBoolCase("remote", ["remote", "-v"], True),
  IdArgsBoolCase("fetch", ["fetch", "origin"], True),
  IdArgsBoolCase("ls_files", ["ls-files"], True),
  IdArgsBoolCase("rev_parse", ["rev-parse", "HEAD"], True),
  IdArgsBoolCase("add", ["add", "."], False),
  IdArgsBoolCase("commit", ["commit", "-m", "x"], False),
  IdArgsBoolCase("push", ["push"], False),
  IdArgsBoolCase("config_unset", ["config", "--unset", "user.name"], False),
  IdArgsBoolCase("config_replace", ["config", "--replace-all", "a", "b"], False),
  IdArgsBoolCase("config_get", ["config", "user.name"], False),
  IdArgsBoolCase("stash_list", ["stash", "list"], False),
  IdArgsBoolCase("stash_show", ["stash", "show"], False),
  IdArgsBoolCase("stash_alone", ["stash"], False),
  IdArgsBoolCase("flags_only", ["-v"], True),
)


KUBECTL_SUBCOMMAND_CASES: tuple[IdArgsStrCase, ...] = (
  IdArgsStrCase("namespace_flag", ["-n", "prod", "get", "pods"], "get"),
  IdArgsStrCase("long_namespace", ["--namespace=prod", "describe", "pod", "x"], "describe"),
)


GH_READ_ONLY_CASES: tuple[IdArgsBoolCase, ...] = (
  IdArgsBoolCase("no_args", [], True),
  IdArgsBoolCase("status", ["status"], True),
  IdArgsBoolCase("view", ["view", "123"], True),
  IdArgsBoolCase("repo_view", ["repo", "view", "o/r"], True),
  IdArgsBoolCase("pr_create", ["pr", "create"], False),
  IdArgsBoolCase("create", ["create", "issue"], False),
  IdArgsBoolCase("repo_create", ["repo", "create"], False),
  IdArgsBoolCase("unknown", ["foobar"], False),
)


GH_API_METHOD_CASES: tuple[IdArgsOptionalStrCase, ...] = (
  IdArgsOptionalStrCase("explicit_get", ["api", "--method=GET", "repos/o/r"], "GET"),
  IdArgsOptionalStrCase("explicit_get_flag", ["api", "-X", "GET", "repos/o/r"], "GET"),
  IdArgsOptionalStrCase("explicit_post", ["api", "--method=POST", "repos/o/r"], "POST"),
  IdArgsOptionalStrCase("no_method", ["api", "repos/o/r"], None),
)


SQL_DETECT_CASES: tuple[IdCommandStrCase, ...] = (
  IdCommandStrCase("select", 'psql -c "SELECT 1"', "select"),
  IdCommandStrCase("insert", 'psql -c "INSERT INTO t VALUES (1)"', "insert"),
)


HTTP_DETECT_CASES: tuple[IdCommandStrCase, ...] = (
  IdCommandStrCase("get", "curl -X GET https://example.com", "GET"),
  IdCommandStrCase("post_data", "curl -d '{}' https://example.com", "POST"),
)


GIT_COMMIT_BYPASS_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("short_n", "git commit -nm x", True),
  IdStrBoolCase("no_verify", "git commit --no-verify -m x", True),
  IdStrBoolCase("no_verify_after_message", 'git commit -m "msg" --no-verify', True),
  IdStrBoolCase("message_eq_flag", "git commit --message=msg --no-verify", True),
  IdStrBoolCase("mnote_not_bypass", "git commit -mnote", False),
  IdStrBoolCase("message_contains_bypass_text", 'git commit -m "document --no-verify handling"', False),
  IdStrBoolCase("no_gpg_sign", "git commit --no-gpg-sign -m x", True),
  IdStrBoolCase("short_m_cluster", "git commit -am msg", False),
  IdStrBoolCase("normal", 'git commit -m "ok"', False),
  IdStrBoolCase("not_git", "echo commit --no-verify", False),
  IdStrBoolCase("git_status", "git status", False),
  IdStrBoolCase("multi_ok_then_bypass", "git status && git commit --no-verify -m x", True),
  IdStrBoolCase("path_git", "/usr/bin/git commit --no-verify -m x", True),
)


KUBECTL_MUTATE_SEGMENT_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("wrapper_apply", "command kubectl apply -f x.yaml", True),
  IdStrBoolCase("direct_apply", "kubectl apply -f x.yaml", True),
  IdStrBoolCase("direct_delete", "kubectl delete pod x", True),
  IdStrBoolCase("direct_get", "kubectl get pods", False),
  IdStrBoolCase("env_assign", "FOO=bar kubectl apply -f x.yaml", True),
  IdStrBoolCase("wrapper_get", "env kubectl get pods", False),
  IdStrBoolCase("empty", "", False),
)


KUBECTL_READ_ONLY_CASES: tuple[IdArgsBoolCase, ...] = (
  IdArgsBoolCase("empty", [], True),
  IdArgsBoolCase("get", ["get", "pods"], True),
  IdArgsBoolCase("describe", ["describe", "pod", "x"], True),
  IdArgsBoolCase("apply", ["apply", "-f", "x.yaml"], False),
  IdArgsBoolCase("delete", ["delete", "pod", "x"], False),
  IdArgsBoolCase("unknown", ["unknown-verb"], False),
)


SHELL_MUTATION_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("cmd_subst", "echo $(id)", True),
  IdStrBoolCase("backtick", "echo `id`", True),
  IdStrBoolCase("redirect_out", "echo x > /tmp/a", True),
  IdStrBoolCase("redirect_devnull", "echo x > /dev/null", False),
  IdStrBoolCase("input_redirect", "cat < /tmp/in", True),
  IdStrBoolCase("input_devnull", "cat < /dev/null", False),
  IdStrBoolCase("clean", "git status", False),
)


GIT_COMMIT_SEGMENT_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("no_verify", "git commit --no-verify -m x", True),
  IdStrBoolCase("no_verify_after_message", 'git commit -m "msg" --no-verify', True),
  IdStrBoolCase("message_eq_flag", "git commit --message=msg --no-verify", True),
  IdStrBoolCase("mnote_not_bypass", "git commit -mnote", False),
  IdStrBoolCase("n_flag", "git commit -n -m x", True),
  IdStrBoolCase("short_cluster_n", "git commit -nm x", True),
  IdStrBoolCase("normal", 'git commit -m "ok"', False),
  IdStrBoolCase("too_short", "git", False),
)


GIT_COMMIT_SHORT_CLUSTER_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("has_n", "-nm", True),
  IdStrBoolCase("no_n", "-am", False),
  IdStrBoolCase("too_short", "-", False),
  IdStrBoolCase("long_opt", "--no-verify", False),
)


FIRST_SUBCOMMAND_CASES: tuple[IdArgsStrCase, ...] = (
  IdArgsStrCase("plain", ["status"], "status"),
  IdArgsStrCase("skip_flags", ["-v", "log"], "log"),
  IdArgsStrCase("flags_only", ["-v"], ""),
)


COMMAND_KUBECTL_MUTATE_CASES: tuple[IdStrBoolCase, ...] = (
  IdStrBoolCase("single", "kubectl apply -f x.yaml", True),
  IdStrBoolCase("multi_read", "kubectl get pods && git status", False),
  IdStrBoolCase("multi_mutate", "git status && kubectl delete pod x", True),
)


COMPILED_VOCAB_PATTERN_CASES: tuple[IdAttrTextCase, ...] = (
  IdAttrTextCase("sql_mutate_re", "sql_mutate_re", "INSERT INTO t"),
  IdAttrTextCase("sql_read_re", "sql_read_re", "SELECT 1"),
  IdAttrTextCase("http_client_re", "http_client_re", "curl https://x"),
  IdAttrTextCase("mutating_http_flags_re", "mutating_http_flags_re", "curl -d '{}'"),
  IdAttrTextCase("http_method_re", "http_method_re", "curl -X GET x"),
  IdAttrTextCase("http_method_eq_re", "http_method_eq_re", "curl --method=POST x"),
  IdAttrTextCase("httpie_mutate_re", "httpie_mutate_re", "http POST example.com"),
)


@dataclass(frozen=True)
class AsSetCase:
  id: str
  values: list[str]
  expected: frozenset[str]
  fn: str


AS_SET_CASES: tuple[AsSetCase, ...] = (
  AsSetCase("lower", ["A", "B"], frozenset({"a", "b"}), "lower"),
  AsSetCase("upper", ["get", "post"], frozenset({"GET", "POST"}), "upper"),
)


@dataclass(frozen=True)
class AltJoinCase:
  id: str
  words: frozenset[str]
  upper: bool
  expected: str


ALT_JOIN_CASES: tuple[AltJoinCase, ...] = (
  AltJoinCase("lower_default", frozenset({"apply", "get"}), False, "apply|get"),
  AltJoinCase("upper_flag", frozenset({"insert", "id"}), True, "INSERT|ID"),
)


HTTP_TOOL_CASES: tuple[IdCommandStrCase, ...] = (
  IdCommandStrCase("curl", "curl -s https://example.com", "curl"),
  IdCommandStrCase("wget", "wget -q https://example.com", "wget"),
)


EXTRACT_URL_CASES: tuple[IdCommandStrCase, ...] = (
  IdCommandStrCase("https", "curl https://example.com/path", "https://example.com/path"),
  IdCommandStrCase("none", "echo hello", ""),
)


@pytest.fixture(scope="module")
def engine() -> Engine:
  PolicyLoader.clear_cache()
  eng = Engine.from_path(ROOT / "rules.yaml")
  yield eng
  Engine.clear_cache()
  PolicyLoader.clear_cache()


def _shell(command: str, source: str = "cursor") -> dict[str, Any]:
  return normalize({"command": command}, source=source)


def _decide(engine: Engine, command: str) -> tuple[Any, dict[str, Any]]:
  action = _shell(command)
  return engine.evaluate(action), action


def _engine_from_yaml(yaml_text: str) -> Engine:
  PolicyLoader.clear_cache()
  with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
    f.write(yaml_text)
    path = Path(f.name)
  try:
    return Engine(PolicyLoader.load(path))
  finally:
    path.unlink(missing_ok=True)
    PolicyLoader.clear_cache()


@pytest.mark.parametrize("case", SHELL_DECIDE_CASES, ids=lambda c: c.id)
def test_shell_decide(engine: Engine, case: ShellDecideCase) -> None:
  d, action = _decide(engine, case.command)
  if action.get("kind") == "shell":
    assert action["read_only"] is case.read_only, case.id
  assert d.allowed is case.allowed, case.id
  if case.kubectl_mutate is not None:
    assert action.get("kubectl_mutate") is case.kubectl_mutate, case.id
  if case.git_commit_bypass is not None:
    assert action.get("git_commit_bypass") is case.git_commit_bypass, case.id
  if case.rule_id is not None:
    assert d.rule_id == case.rule_id, case.id


@pytest.mark.parametrize("case", SHELL_KIND_CASES, ids=lambda c: c.id)
def test_shell_kind(engine: Engine, case: ShellKindCase) -> None:
  action = _shell(case.command)
  assert action["kind"] == case.kind, case.id
  if case.operation is not None:
    assert action["operation"] == case.operation, case.id
  if case.method is not None:
    assert action["method"] == case.method, case.id
  if case.tool is not None:
    assert action["tool"] == case.tool, case.id
  if case.url_contains is not None:
    assert case.url_contains in action["url"], case.id
  if case.allowed is not None:
    d = engine.evaluate(action)
    assert d.allowed is case.allowed, case.id


@pytest.mark.parametrize("case", NORMALIZE_EVENT_CASES, ids=lambda c: c.id)
def test_normalize_event(case: NormalizeEventCase) -> None:
  action = normalize(case.event, source=case.source)
  for key, value in case.expected.items():
    assert action.get(key) == value, f"{case.id}.{key}"


@pytest.mark.parametrize("case", ENGINE_ACTION_CASES, ids=lambda c: c.id)
def test_engine_action(engine: Engine, case: EngineActionCase) -> None:
  d = engine.evaluate(case.action)
  assert d.allowed is case.allowed, case.id
  if case.rule_id is not None:
    assert d.rule_id == case.rule_id, case.id
  if case.default is not None:
    assert d.default is case.default, case.id
  if case.reason is not None:
    assert d.reason == case.reason, case.id


def test_compile_rule_valid() -> None:
  rule = _compile_rule(
    {
      "id": "test-rule",
      "action": "allow",
      "reason": "ok",
      "match": {
        "kind": "shell",
        "read_only": True,
        "operation_in": ["select"],
        "method_in": ["GET"],
        "kubectl_mutate": False,
        "git_commit_bypass": False,
        "command_regex": "git",
      },
    }
  )
  assert rule.id == "test-rule"
  assert rule.action == "allow"
  assert rule.match.command_regex is not None
  assert "select" in (rule.match.operation_in or ())
  assert "GET" in (rule.match.method_in or ())
  assert rule.match.read_only is True
  assert rule.match.kubectl_mutate is False
  assert rule.match.git_commit_bypass is False


@pytest.mark.parametrize("case", INVALID_COMPILE_RULE_CASES, ids=lambda c: c.id)
def test_compile_rule_invalid(case: InvalidCompileRuleCase) -> None:
  with pytest.raises(ValueError, match=case.pattern):
    _compile_rule(case.rule)


def test_engine_from_path_caches() -> None:
  Engine.clear_cache()
  path = ROOT / "rules.yaml"
  a = Engine.from_path(path)
  b = Engine.from_path(path)
  assert a is b
  Engine.clear_cache()


def test_vocab_singletons() -> None:
  PolicyLoader.clear_cache()
  v1 = get_vocab()
  v2 = get_vocab()
  assert v1 is v2
  c1 = get_compiled_vocab()
  c2 = get_compiled_vocab()
  assert c1 is c2


def test_load_custom_rules() -> None:
  PolicyLoader.clear_cache()
  yaml_text = f"""
version: 1
default: allow
{_yaml_vocab()}
rules:
  - id: deny-all-shell
    action: deny
    match:
      kind: shell
"""
  with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
    f.write(yaml_text)
    path = Path(f.name)
  try:
    policy = PolicyLoader.load(path)
    assert policy.default == "allow"
    eng = Engine(policy)
    d_shell = eng.evaluate({"kind": "shell", "command": "ls"})
    assert d_shell.allowed is False
    d_unknown = eng.evaluate({"kind": "other"})
    assert d_unknown.allowed is True
    assert d_unknown.default is True
  finally:
    path.unlink()
    PolicyLoader.clear_cache()


@pytest.mark.parametrize("case", COMPILED_VOCAB_PATTERN_CASES, ids=lambda c: c.id)
def test_compiled_vocab_patterns(case: IdAttrTextCase) -> None:
  PolicyLoader.clear_cache()
  compiled = get_compiled_vocab()
  pattern = getattr(compiled, case.attr)
  assert pattern.search(case.text) is not None


@pytest.mark.parametrize("case", ENGINE_YAML_CASES, ids=lambda c: c.id)
def test_engine_yaml_cases(case: EngineYamlCase) -> None:
  eng = _engine_from_yaml(case.yaml)
  d = eng.evaluate(case.action)
  assert d.allowed is case.allowed, case.id
  if case.rule_id is not None:
    assert d.rule_id == case.rule_id, case.id
  if case.reason is not None:
    assert d.reason == case.reason, case.id
  if case.default is not None:
    assert d.default is case.default, case.id


@pytest.mark.parametrize("case", PARSE_ERROR_CASES, ids=lambda c: c.id)
def test_parse_errors(case: ParseErrorCase) -> None:
  with pytest.raises(ValueError, match=case.pattern):
    case.fn()


def test_resolve_vocab_ref_returns_sorted_list() -> None:
  vocab = Vocab.from_mapping(_MIN_VOCAB)
  resolved = _resolve_value("$vocab.sql_mutate", vocab, {})
  assert resolved == sorted(_MIN_VOCAB["sql_mutate"])


@pytest.mark.parametrize("case", AS_SET_CASES, ids=lambda c: c.id)
def test_as_sets(case: AsSetCase) -> None:
  if case.fn == "lower":
    assert _as_lower_set(case.values) == case.expected
  else:
    assert _as_upper_set(case.values) == case.expected


@pytest.mark.parametrize("case", ALT_JOIN_CASES, ids=lambda c: c.id)
def test_alt_join(case: AltJoinCase) -> None:
  assert _alt_join(case.words, upper=case.upper) == case.expected


def test_alt_join_default_upper_false() -> None:
  assert _alt_join(frozenset({"delete"})) == "delete"


@pytest.mark.parametrize("case", HTTP_TOOL_CASES, ids=lambda c: c.id)
def test_http_tool(case: IdCommandStrCase) -> None:
  assert _http_tool(case.command) == case.expected


@pytest.mark.parametrize("case", EXTRACT_URL_CASES, ids=lambda c: c.id)
def test_extract_url(case: IdCommandStrCase) -> None:
  assert _extract_url(case.command) == case.expected


def test_reload_after_file_change() -> None:
  PolicyLoader.clear_cache()
  yaml_v1 = f"default: deny\n{_yaml_vocab()}\nrules: []\n"
  yaml_v2 = f"default: allow\n{_yaml_vocab()}\nrules: []\n"
  with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
    f.write(yaml_v1)
    path = Path(f.name)
  try:
    doc1 = PolicyLoader.load(path)
    assert doc1.default == "deny"
    path.write_text(yaml_v2, encoding="utf-8")
    time.sleep(0.05)
    doc2 = PolicyLoader.load(path)
    assert doc2.default == "allow"
    assert doc1 is not doc2
  finally:
    path.unlink()
    PolicyLoader.clear_cache()


def test_load_same_mtime_returns_cached() -> None:
  PolicyLoader.clear_cache()
  path = ROOT / "rules.yaml"
  doc1 = PolicyLoader.load(path)
  doc2 = PolicyLoader.load(path)
  assert doc1 is doc2


@pytest.mark.parametrize("case", UNWRAP_WRAPPER_CASES, ids=lambda c: c.id)
def test_unwrap_wrapper(case: UnwrapWrapperCase) -> None:
  tokens = shlex.split(case.command)
  assert _unwrap_wrapper(tokens) == case.expected


@pytest.mark.parametrize("case", UNWRAP_WRAPPER_NONE_CASES, ids=lambda c: c.id)
def test_unwrap_wrapper_none(case: IdTokensCase) -> None:
  assert _unwrap_wrapper(case.tokens) is None


@pytest.mark.parametrize("case", READ_ONLY_SEGMENT_CASES, ids=lambda c: c.id)
def test_read_only_segment(case: IdStrBoolCase) -> None:
  assert _is_read_only_segment(case.value) is case.expected


@pytest.mark.parametrize("case", READ_ONLY_SHELL_CASES, ids=lambda c: c.id)
def test_read_only_shell(case: IdStrBoolCase) -> None:
  assert _is_read_only_shell(case.value) is case.expected


@pytest.mark.parametrize("case", GIT_READ_ONLY_CASES, ids=lambda c: c.id)
def test_git_read_only(case: IdArgsBoolCase) -> None:
  assert _git_read_only(case.args) is case.expected


@pytest.mark.parametrize("case", KUBECTL_SUBCOMMAND_CASES, ids=lambda c: c.id)
def test_kubectl_subcommand(case: IdArgsStrCase) -> None:
  assert _kubectl_subcommand(case.args) == case.expected


@pytest.mark.parametrize("case", GH_READ_ONLY_CASES, ids=lambda c: c.id)
def test_gh_read_only(case: IdArgsBoolCase) -> None:
  assert _gh_read_only(case.args) is case.expected


@pytest.mark.parametrize("case", GH_API_METHOD_CASES, ids=lambda c: c.id)
def test_gh_api_explicit_method(case: IdArgsOptionalStrCase) -> None:
  assert _gh_api_explicit_method(case.args) == case.expected


@pytest.mark.parametrize("case", SQL_DETECT_CASES, ids=lambda c: c.id)
def test_detect_sql_operation(case: IdCommandStrCase) -> None:
  assert _detect_sql_operation(case.command) == case.expected


@pytest.mark.parametrize("case", HTTP_DETECT_CASES, ids=lambda c: c.id)
def test_detect_http_method(case: IdCommandStrCase) -> None:
  assert _detect_http_method(case.command) == case.expected


@pytest.mark.parametrize("case", GIT_COMMIT_BYPASS_CASES, ids=lambda c: c.id)
def test_git_commit_bypass(case: IdStrBoolCase) -> None:
  assert _git_commit_has_bypass(case.value) is case.expected


@pytest.mark.parametrize("case", KUBECTL_MUTATE_SEGMENT_CASES, ids=lambda c: c.id)
def test_segment_has_kubectl_mutate(case: IdStrBoolCase) -> None:
  assert _segment_has_kubectl_mutate(case.value) is case.expected


def test_get_policy_loads_document() -> None:
  PolicyLoader.clear_cache()
  doc = get_policy(ROOT / "rules.yaml")
  assert doc.default in ("allow", "deny")
  assert len(doc.rules) > 0


@pytest.mark.parametrize("case", KUBECTL_READ_ONLY_CASES, ids=lambda c: c.id)
def test_kubectl_read_only(case: IdArgsBoolCase) -> None:
  assert _kubectl_read_only(case.args) is case.expected


@pytest.mark.parametrize("case", SHELL_MUTATION_CASES, ids=lambda c: c.id)
def test_segment_has_shell_mutation(case: IdStrBoolCase) -> None:
  assert _segment_has_shell_mutation(case.value) is case.expected


@pytest.mark.parametrize("case", GIT_COMMIT_SEGMENT_CASES, ids=lambda c: c.id)
def test_git_commit_segment_has_bypass(case: IdStrBoolCase) -> None:
  assert _git_commit_segment_has_bypass(case.value) is case.expected


@pytest.mark.parametrize("case", GIT_COMMIT_SHORT_CLUSTER_CASES, ids=lambda c: c.id)
def test_git_commit_short_cluster_has_bypass(case: IdStrBoolCase) -> None:
  assert _git_commit_short_cluster_has_bypass(case.value) is case.expected


@pytest.mark.parametrize("case", FIRST_SUBCOMMAND_CASES, ids=lambda c: c.id)
def test_first_subcommand(case: IdArgsStrCase) -> None:
  assert _first_subcommand(case.args) == case.expected


@pytest.mark.parametrize("case", COMMAND_KUBECTL_MUTATE_CASES, ids=lambda c: c.id)
def test_command_has_kubectl_mutate(case: IdStrBoolCase) -> None:
  assert _command_has_kubectl_mutate(case.value) is case.expected


def test_resolve_pattern_ref() -> None:
  vocab = Vocab.from_mapping(_MIN_VOCAB)
  from agent_guard.policy_loader import _build_patterns

  patterns = _build_patterns(vocab)
  resolved = _resolve_value("$pattern.sql_mutate_shell", vocab, patterns)
  assert isinstance(resolved, str)
  assert "psql" in resolved.lower()


def test_engine_matches_operation_in(engine: Engine) -> None:
  d = engine.evaluate({"kind": "sql", "operation": "select"})
  assert d.allowed is True


def test_engine_matches_method_in(engine: Engine) -> None:
  d = engine.evaluate({"kind": "http", "method": "GET", "url": "https://x"})
  assert d.allowed is True


def test_normalize_shell_includes_cwd() -> None:
  action = normalize(
    {"command": "git status", "cwd": "/tmp/repo"},
    source="cursor",
  )
  assert action["cwd"] == "/tmp/repo"
