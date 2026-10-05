#!/usr/bin/env python3
"""Give each Symphony clone Git metadata access in its workspace-write sandbox."""

import argparse
import copy
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading


def validate_workspace(workspace, workspace_root):
    workspace = Path(workspace).resolve(strict=True)
    workspace_root = Path(workspace_root).resolve(strict=True)
    if workspace.parent != workspace_root or not re.fullmatch(r"GH-[1-9][0-9]*", workspace.name):
        raise ValueError("Codex must start in a GH-number clone directly under the workspace root")
    git_dir = workspace / ".git"
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise ValueError("Expected a local .git directory; linked Git worktrees are not supported")
    return workspace


def grant_git_access(request, workspace):
    """Change only the current clone's turn policy; never grant another clone."""
    if request.get("method") not in {"thread/start", "turn/start"}:
        return request
    params = request.get("params", {})
    if Path(params.get("cwd", workspace)).resolve() != workspace:
        raise ValueError("Requested cwd differs from the launch workspace")
    if request["method"] == "thread/start":
        return request
    policy = params.get("sandboxPolicy", {})
    if policy.get("type") != "workspaceWrite":
        raise ValueError("Symphony turns must use workspaceWrite")
    roots = [str(workspace), str(workspace / ".git")]
    if any(root not in roots for root in policy.get("writableRoots", [])):
        raise ValueError("Unexpected writable root outside the current clone")
    request = copy.deepcopy(request)
    request["params"]["sandboxPolicy"]["writableRoots"] = roots
    return request


def app_server_command(workspace):
    """Configure a fresh container browser only for this Symphony app server."""
    artifacts = workspace / ".tools" / "playwright"
    artifacts.mkdir(parents=True, exist_ok=True)
    browser_args = [
        "run", "--rm", "-i", "--init", "--shm-size=256m",
        "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--mount", f"type=bind,src={artifacts},dst=/artifacts",
        "--workdir", "/artifacts", "obs-symphony-playwright:0.0.83",
        "--headless", "--browser", "chromium", "--no-sandbox",
        "--isolated", "--output-dir", "/artifacts",
        "--allowed-origins", "http://host.docker.internal:*",
    ]
    command = ["codex", "app-server"]
    for key, value in {
        "command": "docker", "args": browser_args,
        "startup_timeout_sec": 60, "tool_timeout_sec": 120,
        "default_tools_approval_mode": "approve",
    }.items():
        command.extend(["-c", f"mcp_servers.symphony_playwright.{key}={json.dumps(value)}"])
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    args = parser.parse_args()
    workspace = validate_workspace(Path.cwd(), args.workspace_root)
    process = subprocess.Popen(app_server_command(workspace), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    failed = threading.Event()

    def forward_requests():
        try:
            for line in sys.stdin.buffer:
                request = grant_git_access(json.loads(line), workspace)
                process.stdin.write(json.dumps(request).encode() + b"\n")
                process.stdin.flush()
        except (ValueError, TypeError, AttributeError, OSError) as error:
            failed.set()
            print(f"Symphony Codex launcher: {error}", file=sys.stderr, flush=True)
            process.terminate()
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    def stop(_signum, _frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    threading.Thread(target=forward_requests, daemon=True).start()
    try:
        while chunk := os.read(process.stdout.fileno(), 65536):
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        return 1 if failed.is_set() else process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print(f"Symphony Codex launcher: {error}", file=sys.stderr)
        sys.exit(1)
