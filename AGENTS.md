# Implementation rules

Read SPEC.md and docs/tempo-trace-lifecycle.md before implementation. The spec defines the current scope; issue acceptance criteria define the assigned slice.

- Build the Docker Compose PoC with DuckDB, SeaweedFS, OTLP, and the custom Grafana datasource. Defer Iceberg and Trino until a task explicitly introduces them.
- Preserve integer nanoseconds, typed attributes, atomic block publication, deduplication, and explicit lookup scope.
- Use containerized builds and tests. Pin dependencies and images; verify native host architecture.
- Keep unrelated changes and secrets out of commits. Never include .tools or .symphony runtime files.
- Validate the assigned behavior with real integration checks where required. Record commands and results; distinguish unrun checks from passing checks.
- Do not weaken acceptance criteria to get a passing result. Document a concrete blocker when access or tooling prevents validation.
- Scope Compose projects and volumes to the issue workspace. Never reset another workspace's data or run global Docker cleanup.
- Preserve completed changes on a branch before a tracker issue becomes terminal: Symphony may remove terminal-issue workspaces.
- Review and merging are separate from implementation. Do not merge or delete branches unless the assigned task explicitly authorizes it.
