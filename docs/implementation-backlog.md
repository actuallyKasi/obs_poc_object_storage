# Symphony implementation backlog

Published as [GitHub issues #1–#6](https://github.com/actuallyKasi/obs_poc_object_storage/issues). SPEC.md remains the detailed contract. Only #1 is initially labeled `symphony-ready`; other issues wait for dependency integration.

Start with one active issue and one Symphony agent. Dispatch the next issue after its dependencies have been integrated into the source branch; merely listing a dependency in issue text is not a scheduler guarantee.

## 01 — Container foundation and storage compatibility (M0, part 1)

Deliver pinned native-architecture images, Compose storage and initialization, containerized Python tooling, a minimal Collector configuration, and documented Docker budgets.

Acceptance:

- Clean startup creates the bucket idempotently; down/up retains objects.
- Actual S3 PUT/GET/HEAD/paginated LIST/range/auth checks pass.
- DuckDB reads remote Parquet through S3 with its extension baked into the image.
- Collector validates the traces-only pipeline with memory limiter and batch processors.
- Record versions, architecture, tested commands, and results.

## 02 — Grafana trace-contract compatibility (M0, part 2)

Depends on 01. Scaffold and provision the custom datasource and a deterministic fixture endpoint. Pin Grafana packages and source contracts.

Acceptance:

- A hand-authored trace renders in Explore and a provisioned dashboard.
- Test IDs, parenting, milliseconds, error tags, events, and links.
- Route requests through Grafana's data proxy; no browser access to Docker hostnames.
- Containerized build and a real browser walkthrough succeed.

## 03 — Durable OTLP ingestion and block publication (M1)

Depends on 01 and 02. Implement writer, typed schema, raw persistence, bounded multi-request block cycles, manifests, and trace fixtures.

Acceptance:

- gRPC and HTTP protobuf/JSON, including gzip, work through the gateway.
- Writer acknowledges only after raw object persistence.
- Blocks group requests and retain span provenance; only manifests publish files.
- Inject crashes after raw persistence and data upload; recover without lost committed spans or publishing a request twice.
- Validate request limits, retries, malformed input, and storage failure behavior.

## 04 — Query API and bounded execution (M2)

Depends on 03. Implement discovery, exact trace metadata index, worker pool, OpenAPI, trace lookup, search, and autocomplete.

Acceptance:

- Deduplication, conflicting copies, typed values, and integer timestamps match fixtures.
- Bounded and all-retained lookup follow SPEC.md; no silent widening or span trimming.
- Late fragments and cross-hour traces work; metadata cache can be rebuilt from storage.
- Query deadlines, file/byte/result limits, cancellation, saturation, and worker recovery are exercised.
- Storage errors are distinguishable from empty results.

## 05 — Connect Grafana to the real query API (M3)

Depends on 04. Replace fixture wiring with production PoC endpoints and implement search/trace editors and links.

Acceptance:

- Search, select trace, inspect waterfall/events, and follow a trace link in the browser.
- Scope selectors, summary-derived bounds, notices, empty results, and failures render correctly.
- Frame contract tests pass against the pinned Grafana release.
- Fresh startup requires no manual plugin installation or datasource provisioning.

## 06 — Recovery smoke tests and baseline benchmark (M4)

Depends on 05. Finish make targets, reproducibility docs, deterministic fixtures, and performance report.

Acceptance:

- make up/down/smoke/test/benchmark work; reset is explicitly destructive and separately invoked.
- Restart and cache-loss recovery tests pass against retained data.
- Run 10,000 traces/about 100,000 spans at concurrency 1, 2, and 4.
- Report visibility, query latency, errors, file counts/sizes, resources, and cache conditions.
- Record measured results honestly against the spec's unverified targets.
