---
tracker:
  kind: github
  provider:
    repo: actuallyKasi/obs_poc_object_storage
    token: $GITHUB_TOKEN
  required_labels:
    - symphony-ready
  active_states:
    - open
  terminal_states:
    - closed
polling:
  interval_ms: 15000
workspace:
  root: /Users/kasi/repos/obs_poc_object_storage-workspaces
hooks:
  after_create: |
    git -c credential.helper='!gh auth git-credential' clone https://github.com/actuallyKasi/obs_poc_object_storage.git .
agent:
  max_concurrent_agents: 1
  max_turns: 20
codex:
  command: python3 /Users/kasi/repos/obs_poc_object_storage/tools/symphony/codex-app-server.py --workspace-root /Users/kasi/repos/obs_poc_object_storage-workspaces
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
    networkAccess: true
server:
  host: 127.0.0.1
  port: 8090
---

Implement GitHub issue {{ issue.identifier }} in this isolated workspace.

Title: {{ issue.title }}
URL: {{ issue.url }}
Description:
{{ issue.description }}

Read AGENTS.md, SPEC.md, and docs/tempo-trace-lifecycle.md. Implement only the assigned issue and its acceptance criteria. Preserve the user's configured Codex model. Do not spawn additional agents.

Use the injected github_api tool for tracker reads and updates in actuallyKasi/obs_poc_object_storage. Issue identifiers are GH-number; issue.id is the numeric issue number. Re-read the issue before beginning. Create or update one progress comment headed '## Symphony workpad' with the implementation plan, validation results, and concrete blockers.

Create branch symphony/{{ issue.identifier }} unless already on that issue branch. Resume existing work on retries. Work only in this clone. Use a workspace-specific Compose project name; avoid fixed container names and global Docker cleanup. Keep local test credentials out of commits and never print real credentials.

Build and run every required acceptance check. Preserve exact time/attribute semantics and explicit trace lookup scope. Do not mark unrun checks as passing. If sandbox/tool access blocks Docker or another required operation, record the exact failure; do not silently relax policies or declare success.

For browser acceptance checks, use the symphony_playwright MCP tools. They run isolated headless Chromium in Docker; reach host-published Grafana at http://host.docker.internal:3000, not localhost. Browser output under /artifacts maps to this clone's .tools/playwright directory. Copy selected screenshots or other evidence into docs/validation when needed for review. Use real rendered UI interactions, console messages, and network requests to verify the issue criteria. Resume any browser checks previously blocked on Computer Use availability. Do not require the desktop Chrome plugin for these checks.

When the issue is implemented and validated, commit the changes, push the issue branch using the existing GitHub CLI credential helper if needed, and create a draft pull request against main. Link the PR and validation evidence in the workpad. Do not use a closing keyword in the PR: the issue remains open for review. Attach any created PR to the Codex chat using the app tool if it is available.

After the branch and PR are safely published, add symphony-review and remove symphony-ready from this issue. Make label removal the final tracker mutation, because it makes this issue ineligible for further dispatch. Do not close the issue or merge the PR. Do not enable any dependent issue.

If genuinely blocked, preserve any changes locally and on the issue branch when possible, record the blocker in the workpad, add symphony-blocked, and remove symphony-ready as the last tracker action. Do not close the issue. Never remove or overwrite another issue's workspace.
