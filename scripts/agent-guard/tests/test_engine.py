#!/usr/bin/env python3
"""Unit tests for agent-guard policy engine."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_guard.engine import Engine
from agent_guard.normalize import normalize
from agent_guard.output import ALLOWED_SCOPE, format_decision


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Engine.from_path(ROOT / "rules.yaml")

    def _eval_shell(self, command: str):
        action = normalize({"command": command}, source="cursor")
        return self.engine.evaluate(action), action

    def test_allow_git_status(self):
        d, _ = self._eval_shell("git status")
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-read-only-shell")

    def test_allow_git_commit(self):
        d, _ = self._eval_shell('git commit -m "hello"')
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-git-commit-push")

    def test_allow_git_push(self):
        d, _ = self._eval_shell("git push -u origin HEAD")
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-git-commit-push")

    def test_deny_git_commit_no_verify(self):
        d, _ = self._eval_shell('git commit --no-verify -m "x"')
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-git-commit-bypass")

    def test_deny_git_push_force(self):
        d, _ = self._eval_shell("git push --force origin main")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-git-destructive")

    def test_deny_git_reset_hard(self):
        d, _ = self._eval_shell("git reset --hard HEAD~1")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-git-destructive")

    def test_deny_sudo(self):
        d, _ = self._eval_shell("sudo apt update")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-sudo")

    def test_deny_kubectl_apply(self):
        d, _ = self._eval_shell("kubectl apply -f deploy.yaml")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-kubectl-mutate")

    def test_allow_kubectl_get(self):
        d, _ = self._eval_shell("kubectl get pods -A")
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-read-only-shell")

    def test_deny_curl_post(self):
        d, _ = self._eval_shell("curl -X POST https://example.com/api -d '{}'")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-http-mutate")

    def test_allow_curl_get(self):
        d, action = self._eval_shell("curl -s https://example.com")
        self.assertTrue(d.allowed, msg=f"action={action} decision={d}")

    def test_deny_psql_insert(self):
        d, _ = self._eval_shell('psql -c "INSERT INTO t VALUES (1)"')
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-sql-mutate")

    def test_allow_psql_select(self):
        d, action = self._eval_shell('psql -c "SELECT 1"')
        self.assertTrue(d.allowed, msg=f"action={action} decision={d}")

    def test_allow_mcp(self):
        action = normalize(
            {"hook_event_name": "beforeMCPExecution", "tool_name": "save_issue", "server": "Linear"},
            source="cursor",
        )
        d = self.engine.evaluate(action)
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-mcp")

    def test_fail_closed_unknown_write(self):
        d, _ = self._eval_shell("rm -rf /tmp/foo")
        self.assertFalse(d.allowed)
        self.assertTrue(d.default)

    def test_claude_bash_event(self):
        action = normalize(
            {"tool_name": "Bash", "tool_input": {"command": "sudo true"}},
            source="claude",
        )
        d = self.engine.evaluate(action)
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-sudo")

    def test_deny_command_wrapper_kubectl(self):
        d, _ = self._eval_shell("command kubectl apply -f deploy.yaml")
        self.assertFalse(d.allowed)

    def test_deny_command_wrapper_rm(self):
        d, _ = self._eval_shell("command rm -rf /tmp/foo")
        self.assertFalse(d.allowed)

    def test_deny_env_wrapper(self):
        d, _ = self._eval_shell("env kubectl apply -f deploy.yaml")
        self.assertFalse(d.allowed)

    def test_deny_find_exec(self):
        d, _ = self._eval_shell("find . -exec rm -rf {} +")
        self.assertFalse(d.allowed)

    def test_deny_find_delete(self):
        d, _ = self._eval_shell("find . -delete")
        self.assertFalse(d.allowed)

    def test_deny_awk_system(self):
        d, _ = self._eval_shell('awk \'BEGIN{system("rm -rf /tmp/foo")}\'')
        self.assertFalse(d.allowed)

    def test_deny_echo_command_substitution(self):
        d, _ = self._eval_shell("echo $(kubectl apply -f deploy.yaml)")
        self.assertFalse(d.allowed)

    def test_deny_shell_redirect(self):
        d, _ = self._eval_shell("echo evil > /tmp/agent-guard-pwn")
        self.assertFalse(d.allowed)

    def test_deny_psql_file_input(self):
        d, _ = self._eval_shell("psql -f /tmp/mutate.sql")
        self.assertFalse(d.allowed)

    def test_deny_psql_stdin_redirect(self):
        d, _ = self._eval_shell("psql < /tmp/mutate.sql")
        self.assertFalse(d.allowed)

    def test_deny_wget_post_data(self):
        d, _ = self._eval_shell("wget --post-data='{}' https://example.com/api")
        self.assertFalse(d.allowed)

    def test_deny_curl_data_binary(self):
        d, _ = self._eval_shell("curl --data-binary @payload.json https://example.com/api")
        self.assertFalse(d.allowed)

    def test_deny_httpie_post(self):
        d, _ = self._eval_shell("http POST https://example.com/api name=value")
        self.assertFalse(d.allowed)

    def test_deny_git_push_plus_ref(self):
        d, _ = self._eval_shell("git push origin +main")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-git-destructive")

    def test_deny_git_commit_nm(self):
        d, _ = self._eval_shell('git commit -nm "skip hooks"')
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-git-commit-bypass")

    def test_deny_unknown_tool_not_mcp(self):
        action = normalize({"tool_name": "CustomTool", "tool_input": {}}, source="claude")
        d = self.engine.evaluate(action)
        self.assertFalse(d.allowed)
        self.assertTrue(d.default)
        self.assertEqual(action["kind"], "unknown")

    def test_allow_file_tool(self):
        action = normalize(
            {"tool_name": "Write", "tool_input": {"path": "foo.txt"}},
            source="claude",
        )
        d = self.engine.evaluate(action)
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-file")

    def test_deny_kubectl_apply_with_namespace_flag(self):
        d, _ = self._eval_shell("kubectl -n default apply -f deploy.yaml")
        self.assertFalse(d.allowed)
        self.assertEqual(d.rule_id, "deny-kubectl-mutate")

    def test_allow_git_commit_message_mentions_no_verify(self):
        d, _ = self._eval_shell('git commit -m "document --no-verify handling"')
        self.assertTrue(d.allowed)
        self.assertEqual(d.rule_id, "allow-git-commit-push")

    def test_deny_gh_pr_create(self):
        d, _ = self._eval_shell("gh pr create --title test")
        self.assertFalse(d.allowed)
        self.assertTrue(d.default)

    def test_engine_cache_reuses_instance(self):
        from agent_guard.engine import Engine

        Engine.clear_cache()
        path = ROOT / "rules.yaml"
        first = Engine.from_path(path)
        second = Engine.from_path(path)
        self.assertIs(first, second)
        Engine.clear_cache()


class AuditTests(unittest.TestCase):
    def test_sanitize_redacts_secrets(self):
        from agent_guard.audit import sanitize_action

        action = {
            "kind": "shell",
            "command": "curl -H 'Authorization: Bearer secret-token' https://x.com",
        }
        sanitized = sanitize_action(action)
        self.assertIsNotNone(sanitized)
        assert sanitized is not None
        self.assertIn("***", sanitized["command"])
        self.assertNotIn("secret-token", sanitized["command"])

    def test_resolve_audit_path_rejects_escape(self):
        from agent_guard.audit import resolve_audit_path

        with self.assertRaises(ValueError):
            resolve_audit_path(Path("/etc/passwd"), base=ROOT)


class BypassMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Engine.from_path(ROOT / "rules.yaml")

    def _deny(self, command: str) -> None:
        action = normalize({"command": command}, source="cursor")
        decision = self.engine.evaluate(action)
        self.assertFalse(decision.allowed, msg=f"expected deny: {command!r} action={action}")

    def test_bypass_matrix(self):
        cases = [
            "command kubectl apply -f x.yaml",
            "kubectl -n prod apply -f x.yaml",
            "wget --post-data='{}' https://example.com/api",
            "gh issue create --title x",
        ]
        for cmd in cases:
            with self.subTest(cmd=cmd):
                self._deny(cmd)


class OutputTests(unittest.TestCase):
    def test_allowed_scope_text(self):
        self.assertEqual(
            ALLOWED_SCOPE,
            "Allowed: file edits, git commit/push, MCP writes, read-only operations",
        )

    def test_cursor_deny_payload(self):
        payload = format_decision(allowed=False, reason="blocked", rule_id="deny-sudo", target="cursor")
        self.assertEqual(payload["permission"], "deny")
        self.assertIn(ALLOWED_SCOPE, payload["agent_message"])

    def test_claude_allow_payload(self):
        payload = format_decision(allowed=True, target="claude")
        self.assertEqual(
            payload["hookSpecificOutput"]["permissionDecision"],
            "allow",
        )


class RunPyTests(unittest.TestCase):
    def test_run_py_cursor_allow(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "run.py"), "--target", "cursor"],
            input=json.dumps({"command": "git status"}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload.get("permission"), "allow")

    def test_run_py_cursor_deny(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "run.py"), "--target", "cursor"],
            input=json.dumps({"command": "sudo true"}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload.get("permission"), "deny")

    def test_run_py_empty_stdin_denies(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "run.py"), "--target", "cursor"],
            input="",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload.get("permission"), "deny")

    def test_fail_closed_py_emits_deny(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "fail_closed.py"), "--target", "claude"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")


class WrapperFallbackTests(unittest.TestCase):
    def test_wrapper_without_plugin_root(self):
        script = ROOT.parents[1] / ".apm" / "hooks" / "scripts" / "cursor-before-shell.sh"
        clean = {"PATH": "/usr/bin:/bin", "HOME": str(Path.home())}
        proc = subprocess.run(
            ["bash", str(script)],
            input=json.dumps({"command": "git status"}),
            text=True,
            capture_output=True,
            check=False,
            env=clean,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload.get("permission"), "allow")


if __name__ == "__main__":
    unittest.main()
