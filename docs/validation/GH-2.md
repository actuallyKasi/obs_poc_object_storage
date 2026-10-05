# GH-2 validation status

Date: 2026-10-05. Branch: `symphony/GH-2`.

## Result

Containerized build, frame contracts, provisioning and HTTP proxy integration
pass. **Acceptance remains incomplete:** the required real browser walkthrough
is blocked by the injected Playwright tool approval policy. No validated draft PR is claimed.

## Environment and isolation

- `uname -m`: `arm64`.
- `docker version`: client/server 29.7.2, Docker Desktop 4.88.1,
  client darwin/arm64, server linux/arm64.
- `docker info --format '{{.Architecture}} {{.NCPU}} {{.MemTotal}}'`:
  `aarch64 8 8319770624` (about 7.75 GiB).
- Project: `obs-gh1-1063179284`, derived by `tools/compose.sh` from this clone's
  physical path. Only this project's Grafana and fixture were started.
  Another workspace's running storage/Collector containers were left alone.
- `docker image inspect obs-gh1-1063179284-grafana:gh2 obs-gh1-1063179284-fixture:gh2 --format '{{.RepoTags}} {{.Os}}/{{.Architecture}}'`:
  both `linux/arm64`. Pinned Node builder also inspected as `linux/arm64`.

## Passing checks

```sh
mkdir -p .tools/buildx
BUILDX_CONFIG="$PWD/.tools/buildx" make test-grafana
```

Exit 0. This runs:

1. Containerized `npm ci` from the committed lockfile.
2. Two Node contract tests: IDs, root/child parenting, equal-length frame arrays,
   numeric field types, millisecond conversion, error display tag, typed values,
   unsafe int64, nested values, base64 bytes, event timestamps/names, reference
   IDs/tags, input immutability, ordering and missing-parent diagnostics.
3. `tsc --noEmit` and webpack 5.99.5 production compilation, successful.
4. Fresh Grafana/fixture startup with health checks and automatic provisioning.
5. `./tools/compose.sh exec -T querier python - < tests/integration/grafana.py`:
   Grafana version, provisioned datasource/dashboard, real Grafana proxy health
   and trace requests, exact canonical nanoseconds and conflicting original
   error attribute, events/links, explicit all-retained/bounded scope, untrimmed
   block results, nanosecond overlap boundaries, malformed/one-sided/reversed/
   oversized ranges, missing trace and linked trace responses.

Output:

```text
PASS Grafana version, provisioning, proxy, exact nanoseconds, typed attributes, events, links, paired scope, block boundaries, and HTTP errors
```

Additional checks:

- `git ls-remote https://github.com/grafana/grafana.git 'refs/tags/v12.2.0*'`:
  peeled commit `92f1fba9b4b6700328e99e97328d6639df8ddc3d`.
- Downloaded `trace.ts`, `data.ts`, `dataFrame.ts` from that commit and `cmp`
  verified each committed snapshot byte-for-byte. Hashes recorded in
  `docs/contracts/grafana-12.2.0/README.md`.
- `./tools/compose.sh port grafana 3000`: `127.0.0.1:3000`.
- Grafana logs confirm plugin `kasi-objecttraces-datasource` registered and
  dashboard provisioning finished. Only the named unsigned plugin is allowed.
- `curl -fsS http://127.0.0.1:3000/api/health`: database `ok`, version `12.2.0`,
  commit `92f1fba9b4b6700328e99e97328d6639df8ddc3d`.
- `git diff --check`: passed.

## Resolved tooling failures

The earlier attempt's Git write restriction is resolved; the issue branch exists.
The initial build in this attempt failed with:

```text
failed to update builder last activity time: open /Users/kasi/.docker/buildx/activity/.tmp-default1553352955: operation not permitted
```

Using a writable, ignored workspace Buildx cache as shown above succeeded.
No sandbox permissions were changed. `.tools` contents and `.env` are untracked
and excluded from the commit and Docker build context.

## Resumed validation on 2026-10-05

The operator's preliminary Docker browser run found a runtime error:
`SystemJS: failed to resolve 'react/jsx-runtime'`, with a 404 for
`/react/jsx-runtime`. TypeScript now compiles classic JSX using the already
imported React API; webpack no longer declares the unavailable JSX runtime as
an external. The resulting AMD bundle lists only Grafana data/runtime/ui,
React and RxJS as externals.

Re-ran `BUILDX_CONFIG="$PWD/.tools/buildx" make test-grafana`: **PASS**, exit 0.
Both frame contract tests passed, TypeScript and webpack compiled successfully,
Grafana was recreated and became healthy, and the containerized provisioning/
data-proxy integration printed the PASS output above. Host remains `arm64`;
Docker reports `aarch64 8 8319770624`. Both rebuilt service images inspect as
`linux/arm64`. `./tools/compose.sh port grafana 3000` reports
`127.0.0.1:3000`. `git diff --check` passed.

## Remaining blocker and unrun checks

The required injected Docker browser tool was called directly:

```text
symphony_playwright.browser_navigate(
  url="http://host.docker.internal:3000/d/trace-contract")
→ MCP tool call requires approval, but approval policy is never
```

The read-only `symphony_playwright.browser_snapshot({})` succeeded but returned
`Page URL: about:blank` with an empty snapshot. Tool discovery/read access does
not establish permission to navigate. No desktop browser was required or used;
no policy override or alternative browser execution was attempted.

Explore/dashboard visual rendering, interactive span/error/event/reference
inspection, and browser console/network acceptance remain **UNRUN** on the
corrected build. No screenshots from this build or validated draft PR are
claimed. HTTP tests establish proxy behavior, not browser acceptance. Resume
with navigation permitted for the injected Playwright tools and follow
`docs/grafana-fixture.md`, fixing any remaining visual compatibility errors
before creating the requested validated draft PR or moving to review.

The unrelated GH-1 foundation suite was not rerun. No full ingestion/storage
query pipeline, search flow, deduplication engine or benchmark is claimed by
this fixture-only milestone. No dependent issue was enabled.
