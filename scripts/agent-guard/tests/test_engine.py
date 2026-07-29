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
        self.assertIn(d.rule_id, {"deny-http-shell", "deny-http-mutate"})

    def test_allow_curl_get(self):
        d, action = self._eval_shell("curl -s https://example.com")
        self.assertTrue(d.allowed, msg=f"action={action} decision={d}")

    def test_deny_psql_insert(self):
        d, _ = self._eval_shell('psql -c "INSERT INTO t VALUES (1)"')
        self.assertFalse(d.allowed)
        self.assertIn(d.rule_id, {"deny-sql-shell", "deny-sql-mutate"})

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


class WrapperFallbackTests(unittest.TestCase):
    def test_wrapper_without_plugin_root(self):
        script = ROOT.parents[1] / ".apm" / "hooks" / "scripts" / "cursor-before-shell.sh"
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(Path.home()),
        }
        # Explicitly unset plugin roots
        for key in ("PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "AGENT_GUARD_ROOT"):
            env[key] = ""
        proc = subprocess.run(
            ["bash", str(script)],
            input=json.dumps({"command": "git status"}),
            text=True,
            capture_output=True,
            check=False,
            env={k: v for k, v in env.items() if v != "" or k.startswith("X")},
        )
        # Re-run with cleaned env (omit empty plugin vars entirely)
        clean = {"PATH": env["PATH"], "HOME": env["HOME"]}
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
