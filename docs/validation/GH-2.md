# GH-2 validation

Date: 2026-10-05. Branch: `symphony/GH-2`.

## Result

**PASS**: containerized build, frame contracts, real Grafana proxy integration,
and isolated Docker Chromium walkthrough in Explore and the provisioned dashboard.
No remaining acceptance blocker. This is the M0 fixture slice, not an implemented
storage querier, ingestion pipeline, search flow or deduplication engine.

## Environment and commands

- Host `uname -m`: `arm64`; Docker `aarch64`, 8 CPUs, 8319770624 bytes RAM.
- Grafana and fixture images: `linux/arm64`, verified with `docker image inspect`.
- Project `obs-gh1-1063179284` is derived from this clone's physical path by
  `tools/compose.sh`. The inherited prefix retains this workspace's volumes.
- Only this workspace's Grafana and fixture were started/recreated. No volume
  reset, other-workspace changes, global cleanup, policy override or emulation.
- Grafana host binding: `127.0.0.1:3000`; browser origin:
  `http://host.docker.internal:3000`.

```sh
BUILDX_CONFIG="$PWD/.tools/buildx" make test-grafana
docker image inspect obs-gh1-1063179284-grafana:gh2 obs-gh1-1063179284-fixture:gh2 \
  --format '{{.RepoTags}} {{.Os}}/{{.Architecture}}'
git diff --check
```

All passed. The final build ran both Node contract tests, `tsc --noEmit`, webpack
production compilation, health-checked Compose startup and:

```sh
./tools/compose.sh exec -T querier python - < tests/integration/grafana.py
```

Output:

```text
PASS Grafana version, provisioning, proxy, exact nanoseconds, typed attributes, events, links, paired scope, block boundaries, and HTTP errors
```

The contract tests check IDs, parents, equal-length fields, numerical field types,
1.5 ms duration, event times, boolean error tags, unsafe int64 strings, nested
values, bytes, reference IDs/attributes, input immutability, sorting and missing
parents. HTTP checks retain exact API nanoseconds, the original conflicting
`error: false`, paired bounds, untrimmed blocks, nanosecond overlap boundaries,
malformed/reversed/oversized ranges, missing IDs and linked trace responses.

Grafana 12.2.0 packages and source snapshots are pinned to commit
`92f1fba9b4b6700328e99e97328d6639df8ddc3d`; earlier validation compared committed
snapshots byte-for-byte with upstream. See the [source contract record](../contracts/grafana-12.2.0/README.md).

## Real browser evidence

Executed [the regression function](../../tests/integration/grafana-browser.js)
through injected `symphony_playwright.browser_run_code_unsafe`, using isolated
Docker Chromium. Also used injected navigation, snapshots, console/network tools
and real clicks during diagnosis. No desktop Chrome plugin was needed.

[Structured result](GH-2-browser.json) records **PASS** with rendered text,
all trace response URLs/statuses, console messages and request origins.

- [Dashboard screenshot](GH-2-dashboard.png): native 10 ms root and 1.5 ms child;
  collapse/expand proves parenting; error marker and boolean tag, exception at
  1.25 ms with `Card declined`, parent and linked IDs and link attributes.
- [Explore screenshot](GH-2-explore.png): same native trace and inspected details;
  the first Run click works. The native reference opens `payment attempt` and
  trace `abcdef0123456789abcdef0123456789` in a split pane.
- [Scope error screenshot](GH-2-scope-error.png): default selected-range lookup,
  successful fixed range, then a range excluding the fixture. The 404 shows an
  explicit widening hint; no automatic unbounded request occurs. Choosing
  All retained data and Run query restores the trace.
- Every observed browser request had the Grafana origin. Every trace request
  used `/api/datasources/proxy/uid/object-storage-traces/api/v1/traces/...`.
  Bounded calls carry paired `start`/`end`; all-retained calls omit both.
- Successful views/navigation produced zero console warnings/errors. The
  intentional 404 produced two expected console messages (HTTP 404 and Grafana's
  handled query error). Zero uncaught page errors throughout, including recovery.

## Browser-discovered fixes

1. Classic JSX avoids an unavailable `react/jsx-runtime` AMD external.
2. Plugin assets moved outside the persistent data volume, which had masked the
   rebuilt image with an old bundle. Existing Grafana data was preserved.
3. Anonymous Editor role enables Explore on this local PoC; Viewer redirected
   to Home. No real credentials were needed or committed.
4. Explicit Run avoids overlapping blur/click requests; scope selector has an
   explicit visible size under Grafana styles.
5. Canonical API errors are converted to textual errors for Grafana; passing the
   nested error object directly had caused a React render crash.
6. Native reference `query` IDs override inherited `traceId` without changing
   the chosen scope; editor changes clear the native-link alias.

## Earlier blockers and scope limits

The previous Git/browser approval blockers are resolved. Initial Buildx writes
outside the workspace were denied; the ignored `.tools/buildx` directory solves
that without changing sandbox permissions. No runtime files or local credentials
are included in commits.

The unrelated GH-1 foundation suite was not rerun. Full ingestion, storage-query
semantics, search, cancellation and benchmark acceptance belong to later issues.
No dependent issue was enabled; this issue remains open for review.
