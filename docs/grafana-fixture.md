# Grafana trace compatibility fixture (GH-2)

This M0 slice proves the Grafana 12.2.0 trace frame contract before implementing
the ingestion/query pipeline. `querier` currently runs a Python standard-library
fixture server, with no host port. It serves two deterministic trace IDs. It does
not read object storage or claim to implement discovery, deduplication or search.
The hand-authored response already has unique span identities.

## Run and validate

```sh
make configure
make test-grafana
```

This builds the plugin in pinned Node (including contract tests and TypeScript
checks), starts only Grafana and the fixture, and runs HTTP integration checks
inside the fixture container through Grafana's real data proxy. No host Node or
Python is required. If the sandbox prevents Buildx writing its default activity
cache, use `mkdir -p .tools/buildx` followed by
`BUILDX_CONFIG="$PWD/.tools/buildx" make test-grafana`.

`tools/compose.sh` derives its project name from the physical workspace path.
The inherited `obs-gh1-<workspace checksum>` prefix is retained so retries reuse
this workspace's volumes. It never shares another workspace's project. Set
`GRAFANA_PORT` in private `.env` if port 3000 is occupied. Other GH-1 ports are
needed only for the full foundation stack; do not stop other workspaces to free
them. Ordinary `make down` preserves volumes.

Grafana listens on loopback and allows anonymous Editor access (required for Explore) for this local
fixture. Only `kasi-objecttraces-datasource` is permitted unsigned. Provisioning
sets UID `object-storage-traces`, proxy access and internal URL
`http://querier:8080`. The browser uses Grafana's provided datasource proxy URL
through `getBackendSrv().fetch`; it never contacts Docker DNS names or S3.

## Real browser walkthrough

For Symphony browser checks, use the injected `symphony_playwright` MCP tools
and `http://host.docker.internal:3000` as the Grafana origin. Artifacts under
`/artifacts` map to this clone's ignored `.tools/playwright` directory; copy
selected review evidence into `docs/validation`. Desktop Chrome is not needed.

1. Open `http://localhost:3000/d/trace-contract` (or the Docker browser origin above). The provisioned dashboard shows
   `POST /checkout` with a `charge card` child, 10 ms total and 1.5 ms child.
2. Expand `charge card`: inspect the error marker, boolean error tag, `exception`
   event with `Card declined`, and the linked span reference and its `reason` tag.
3. Open Explore, select Object Storage Traces, and enter
   `0123456789abcdef0123456789abcdef`. Choose **All retained data** and Run query.
   Verify the same native waterfall and span details.
4. Choose **Selected time range**. With October 2, 2026 00:00–00:01 UTC the trace
   renders. An unrelated range reports 404 and offers explicit widening; it does
   not silently retry all retained data.
5. In browser developer tools, verify trace requests use
   `/api/datasources/proxy/uid/object-storage-traces/api/v1/traces/...` on the
   Grafana origin. Check `start`/`end` are present only for bounded lookup.

The second fixture ID `abcdef0123456789abcdef0123456789` contains span
`3333333333333333` (`payment attempt`). Link IDs and attributes are passed to
Grafana's native reference view. Native links use Grafana's `query` field, which
the datasource accepts as the target trace ID while preserving lookup scope.
Explore opens the linked trace in a split pane. Search-result links remain M3 work.

## Semantics and pins

The canonical fixture retains decimal-string nanoseconds and typed OTLP values.
Conversion uses integer quotient/remainder arithmetic only at Grafana's
millisecond display boundary. Large int64 values remain decimal strings with
type information; bytes stay base64; booleans, numbers, arrays and maps keep
their value types. For error spans, the display substitutes boolean `error: true`
for any conflicting attribute; the canonical response retains the original
`error: false`. Events become logs and links become references. Scope attributes
and dropped counts are diagnostics, distinct from span attributes.

The editor defaults to the selected range. Bounds are paired, increasing, and
limited to 24 hours. Fixture block overlap returns all its spans, with explicit
scope and unknown completeness; an empty lookup never widens automatically.

See [pinned upstream contracts](contracts/grafana-12.2.0/README.md) and
[validation evidence](validation/GH-2.md). Container image digests and exact npm
dependencies are committed. Browser checks complement the frame and HTTP tests;
the `make` target alone does not claim visual acceptance.

## Browser regression check

`tests/integration/grafana-browser.js` is an async Playwright function for the
injected `symphony_playwright.browser_run_code_unsafe` tool's `code` argument.
Run after `make test-grafana`. It exercises real controls, checks rendering,
console and network traffic, and writes three screenshots to `/artifacts`.
Its returned JSON and selected screenshots are retained in `docs/validation`.
Only the deliberately out-of-range query should produce HTTP 404 console logs.
Use **Run query** after editing the ID or scope; edits do not issue requests.

Image-bundled plugin assets live under `/opt/grafana/plugins`, outside the
persistent `/var/lib/grafana` volume. Rebuilding therefore updates the plugin
without resetting Grafana state. Anonymous Editor access is for this loopback-only
local PoC; it permits Explore and editing dashboards without manual login.
