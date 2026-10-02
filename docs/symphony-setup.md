# Symphony setup

Status: local preparation; tracker selection and repository/project URL are required before dispatch.

## Runtime

Use official Symphony v0.0.3 with the bundled Erlang/Elixir runtime. Install locally with:

```sh
python3 tools/symphony/install.py
```

The installer checks the release's SHA256 and stores the binary under ignored `.tools/symphony/`. Codex CLI and Git must remain on PATH. The application stack runs in Docker; Symphony runs on the Mac so it can use the existing Codex login and Docker CLI.

## Work queue

The upstream implementation supports Linear, GitHub Issues, Jira Cloud, Asana, and GitLab. Choose a tracker and scope before generating the runnable WORKFLOW.md. Keep tokens in host environment/credential storage, never in repository files or chat.

The initial queue is drafted in [implementation-backlog.md](implementation-backlog.md). Use one agent initially and only dispatch the first ready issue. For GitHub, explicitly configure open/closed states and a dedicated required label so unrelated issues cannot be selected. Stage dependent issues without the dispatch label until prerequisite code is integrated.

Each issue gets a separate workspace. Bootstrap it from a committed repository snapshot. Preserve results on a branch before closing an issue; Symphony can clean up terminal-issue workspaces. Do not point disposable issue workspaces at the primary checkout.

## Workflow to configure once the tracker is selected

- tracker: selected adapter, exact project/repository, host-side credential reference, active/terminal states, dispatch labels.
- workspace: an isolated directory outside the primary checkout.
- hooks.after_create: clone the agreed source repository and create an issue branch.
- agent.max_concurrent_agents: 1; agent.max_turns: 20.
- codex.command: `codex app-server`, retaining the user's configured model.
- Codex sandbox: workspace write with network access; verify Docker socket access before assigning integration work. Surface access failures rather than weakening the policy silently.
- Prompt: read AGENTS.md and SPEC.md, execute the assigned acceptance tests, and preserve work for review.
- Publication/reporting: configure the agreed issue/PR update behavior when connecting the tracker. Local preparation has not posted messages, created issues, or published code.

The pinned executable requires its preview acknowledgement flag on launch:

```text
--i-understand-that-this-will-be-running-without-the-usual-guardrails
```

This flag is required by the upstream CLI even though the workflow exposes configurable Codex sandbox policies. Record the actual selected policies in WORKFLOW.md. Keep the optional runtime dashboard on loopback and logs under ignored `.symphony/`.

## References

- [Pinned setup documentation](https://github.com/openai/symphony/blob/v0.0.3/elixir/README.md)
- [Official release](https://github.com/openai/symphony/releases/tag/v0.0.3)
- [CLI launch requirements](https://github.com/openai/symphony/blob/v0.0.3/elixir/lib/symphony_elixir/cli.ex)
