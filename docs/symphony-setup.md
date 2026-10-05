# Symphony setup

Tracker: GitHub Issues in `actuallyKasi/obs_poc_object_storage`. The runnable configuration is [WORKFLOW.md](../WORKFLOW.md). Only open issues labeled `symphony-ready` are dispatched, with one active agent.

## Runtime

Use official Symphony v0.0.3 with the bundled Erlang/Elixir runtime. Install locally with:

```sh
python3 tools/symphony/install.py
```

The installer checks the release's SHA256 and stores the binary under ignored `.tools/symphony/`. Codex CLI and Git must remain on PATH. The application stack runs in Docker; Symphony runs on the Mac so it can use the existing Codex login and Docker CLI.

## Work queue

The upstream implementation supports several trackers; this project uses GitHub Issues. Keep tokens in host environment/credential storage, never in repository files or chat. `tools/symphony/run.sh` obtains a token from the existing GitHub CLI login without printing or persisting it.

The initial queue is drafted in [implementation-backlog.md](implementation-backlog.md). Use one agent initially and only dispatch the first ready issue. For GitHub, explicitly configure open/closed states and a dedicated required label so unrelated issues cannot be selected. Stage dependent issues without the dispatch label until prerequisite code is integrated.

Each issue gets a separate workspace. Bootstrap it from a committed repository snapshot. Preserve results on a branch before closing an issue; Symphony can clean up terminal-issue workspaces. Do not point disposable issue workspaces at the primary checkout.

## Configured workflow

- tracker: selected adapter, exact project/repository, host-side credential reference, active/terminal states, dispatch labels.
- workspace: an isolated directory outside the primary checkout.
- hooks.after_create: clone the agreed source repository and create an issue branch.
- agent.max_concurrent_agents: 1; agent.max_turns: 20.
- codex.command: a local Python stdio launcher for `codex app-server`, retaining the user's configured model. It lives in the primary checkout so existing issue clones can use it without being updated first.
- codex.approval_policy: `never`, compatible with the installed CLI. Symphony v0.0.3's default `reject` object was rejected by Codex CLI 0.159.2; the workspace sandbox remains enabled.
- Codex sandbox: workspace write with network access; verify Docker socket access before assigning integration work. Surface access failures rather than weakening the policy silently.
- `tools/symphony/codex-app-server.py` automatically sets each turn's writable roots to the active clone and its `.git` directory. It validates that the launch directory is a `GH-number` clone directly under the configured workspace root, rejects a different request cwd or additional writable roots, and requires a local `.git` directory. This covers future issue numbers without per-issue configuration. Network access and other turn policy settings remain configured in WORKFLOW.md. The sandbox remains `workspaceWrite`; the launcher does not grant write access to other issue clones. Linked Git worktrees are intentionally unsupported.
- Prompt: read AGENTS.md and SPEC.md, execute the assigned acceptance tests, and preserve work for review.
- Publication/reporting: the agent maintains one issue workpad, pushes its branch, and opens a draft PR. It then removes `symphony-ready` and adds `symphony-review`. Blocked work gets `symphony-blocked`. Issues remain open until review/integration; no automatic merging.

The pinned executable requires its preview acknowledgement flag on launch:

```text
--i-understand-that-this-will-be-running-without-the-usual-guardrails
```

This flag is required by the upstream CLI even though the workflow exposes configurable Codex sandbox policies. Record the actual selected policies in WORKFLOW.md. Keep the optional runtime dashboard on loopback and logs under ignored `.symphony/`.

## References

- [Pinned setup documentation](https://github.com/openai/symphony/blob/v0.0.3/elixir/README.md)
- [Official release](https://github.com/openai/symphony/releases/tag/v0.0.3)
- [CLI launch requirements](https://github.com/openai/symphony/blob/v0.0.3/elixir/lib/symphony_elixir/cli.ex)

## Start and inspect

```sh
sh tools/symphony/browser/build.sh
./tools/symphony/run.sh
```

Dashboard: http://127.0.0.1:8090/ . State API: http://127.0.0.1:8090/api/v1/state . Stop the foreground process with Ctrl-C. Removing the dispatch label also makes an issue ineligible to continue; preserve its branch first.

## Browser access

Symphony's launcher configures `symphony_playwright` MCP only for its own Codex app-server process. Each session starts a disposable headless Chromium container, with an isolated browser profile and no host login cookies. The Node base image is pinned by digest; Playwright MCP 0.0.83 and its browser package are pinned in `tools/symphony/browser/package-lock.json`. The build uses the Docker host's native architecture; verify the printed image architecture matches the Mac (linux/arm64 for Apple Silicon).

Use `http://host.docker.internal:3000` for Grafana inside the browser. Docker Desktop routes this to the host-published service. Browser requests are configured to allow HTTP origins on `host.docker.internal`; this is a convenience restriction, not a security boundary. The browser container has no Docker socket, repository, or host home directory mounted. Only the active issue's ignored `.tools/playwright` output directory is mounted at `/artifacts`. Copy selected evidence into `docs/validation` before committing. Profiles and containers are discarded when the MCP session ends; output files remain in the clone.

The worker uses browser snapshots, clicks, console messages, network requests, and screenshots for real Grafana acceptance checks. Desktop Chrome approval is not needed. This configuration preserves the user's model and the existing workspace sandbox. See [Playwright MCP](https://github.com/microsoft/playwright-mcp) for its tools and container limitations.

The launcher explicitly sets `mcp_servers.symphony_playwright.default_tools_approval_mode = "approve"` for this process. Codex's MCP tool approvals are separate from shell approvals: `approval_policy = "never"` alone rejects browser navigation that would need approval. Only the isolated Playwright server receives this setting. Tool discovery and direct MCP navigation do not test this authorization path; verify a real worker's navigation after changes. See the [OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference).

After changing browser dependencies, rebuild the image before starting or resuming workers. Existing sessions retain their original tools; the next Symphony session gets the new configuration. `run.sh` checks that the image is installed.

Validation on 2026-10-05: `sh tools/symphony/browser/build.sh` succeeded and produced a linux/arm64 image on the ARM64 Mac. The containerized launcher suite below passed all nine tests. A real Codex app-server `mcpServerStatus/list` request discovered 25 tools for `symphony_playwright`. MCP `browser_navigate`, `browser_wait_for`, and `browser_take_screenshot` reached the GH-2 Grafana dashboard shell at `http://host.docker.internal:3000/d/trace-contract` and saved artifacts in that clone. The trace itself did **not** render: the browser reported a plugin `react/jsx-runtime` import returning 404. That issue was recorded in the GH-2 workpad for the resumed worker; browser access passing does not mean GH-2 acceptance passes.

Follow-up validation: the first worker fixed the JSX import but hit `MCP tool call requires approval, but approval policy is never`. After adding the explicit MCP approval setting, all nine launcher tests passed again. Resumed worker thread `01a109f5-1d5a-7fa2-a1c3-c38b5d5c4f27` successfully called the injected `symphony_playwright.browser_navigate` on the Grafana dashboard and received a real page title and snapshot on 2026-10-05 at 10:47:56 Singapore time. The worker confirmed the approval blocker was resolved and continued acceptance checks. This verifies navigation through Codex's actual tool approval path.

## Launcher checks

The launcher uses Python's standard library. Validate workspace boundaries, future issue numbers, policy preservation, protocol forwarding, and large responses with the pinned container:

```sh
docker run --rm --network none --read-only --tmpfs /tmp:exec \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD/tools/symphony:/tests:ro" \
  python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db \
  python /tests/test_codex_app_server.py
```

The executable tmpfs is needed only for the fake Codex process used in the transport check. No model calls are made by these tests. After changing the launcher or workflow, verify Git branch creation in an actual Symphony session before declaring the permission failure resolved.
