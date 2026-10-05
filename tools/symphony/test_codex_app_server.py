"""Check permission boundaries and the launcher transport without model calls."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

LAUNCHER = Path(__file__).with_name("codex-app-server.py")
spec = importlib.util.spec_from_file_location("codex_launcher", LAUNCHER)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "GH-2"
        (self.workspace / ".git").mkdir(parents=True)
        self.request = {
            "id": 3,
            "method": "turn/start",
            "params": {
                "cwd": str(self.workspace),
                "threadId": "test-thread",
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "workspaceWrite", "networkAccess": True},
            },
        }

    def test_future_issue_numbers_get_only_their_own_git_grant(self):
        original = copy.deepcopy(self.request)
        for issue in (2, 3, 6, 12345):
            workspace = self.root / f"GH-{issue}"
            (workspace / ".git").mkdir(parents=True, exist_ok=True)
            workspace = launcher.validate_workspace(workspace, self.root)
            request = copy.deepcopy(original)
            request["params"]["cwd"] = str(workspace)
            result = launcher.grant_git_access(request, workspace)
            self.assertEqual(result["params"]["sandboxPolicy"], {
                "type": "workspaceWrite", "networkAccess": True,
                "writableRoots": [str(workspace), str(workspace / ".git")],
            })
            self.assertEqual(request["params"]["sandboxPolicy"], original["params"]["sandboxPolicy"])

    def test_rejects_another_requested_workspace(self):
        self.request["params"]["cwd"] = str(self.root / "GH-3")
        with self.assertRaises(ValueError):
            launcher.grant_git_access(self.request, self.workspace)

    def test_rejects_another_writable_root(self):
        self.request["params"]["sandboxPolicy"]["writableRoots"] = [str(self.root / "GH-1" / ".git")]
        with self.assertRaises(ValueError):
            launcher.grant_git_access(self.request, self.workspace)

    def test_rejects_unrestricted_turn_policy(self):
        self.request["params"]["sandboxPolicy"]["type"] = "dangerFullAccess"
        with self.assertRaises(ValueError):
            launcher.grant_git_access(self.request, self.workspace)

    def test_rejects_root_and_nested_workspaces(self):
        nested = self.workspace / "GH-3"
        nested.mkdir()
        for workspace in (self.root, nested):
            with self.assertRaises(ValueError):
                launcher.validate_workspace(workspace, self.root)

    def test_rejects_git_symlink_and_pointer_file(self):
        git_dir = self.workspace / ".git"
        git_dir.rmdir()
        target = self.root / "external-git"
        target.mkdir()
        git_dir.symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            launcher.validate_workspace(self.workspace, self.root)
        git_dir.unlink()
        git_dir.write_text(f"gitdir: {target}\n")
        with self.assertRaises(ValueError):
            launcher.validate_workspace(self.workspace, self.root)

    def test_unrelated_protocol_messages_are_unchanged(self):
        request = {"id": 42, "result": {"output": "tool result"}}
        self.assertIs(launcher.grant_git_access(request, self.workspace), request)

    def test_browser_configuration_is_scoped_to_the_issue(self):
        command = launcher.app_server_command(self.workspace)
        self.assertEqual(command[:2], ["codex", "app-server"])
        overrides = dict(value.split("=", 1) for value in command[3::2])
        self.assertEqual(json.loads(overrides["mcp_servers.symphony_playwright.default_tools_approval_mode"]), "approve")
        arguments = json.loads(overrides["mcp_servers.symphony_playwright.args"])
        self.assertIn(f"type=bind,src={self.workspace}/.tools/playwright,dst=/artifacts", arguments)
        self.assertIn("--isolated", arguments)
        self.assertIn("obs-symphony-playwright:0.0.83", arguments)
        self.assertNotIn(str(self.workspace), arguments)
        self.assertFalse(any(key.startswith("model") or key.startswith("sandbox") for key in overrides))

    def test_transport_forwards_large_responses_and_exits_on_eof(self):
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_codex = fake_bin / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "for line in sys.stdin.buffer:\n"
            "    sys.stdout.buffer.write(line)\n"
            "    sys.stdout.buffer.flush()\n"
        )
        fake_codex.chmod(0o755)
        other = {"id": 42, "result": {"output": "x" * 80000}}
        result = subprocess.run(
            [sys.executable, str(LAUNCHER), "--workspace-root", str(self.root)],
            cwd=self.workspace,
            env={**os.environ, "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
            input="\n".join(json.dumps(request) for request in (self.request, other)) + "\n",
            text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        received = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(received, [launcher.grant_git_access(self.request, self.workspace), other])


if __name__ == "__main__":
    unittest.main()
