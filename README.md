# Object storage tracing PoC

An implementation specification for a local tracing backend: OTLP ingestion, an OpenTelemetry gateway, Parquet in S3-compatible storage, DuckDB queries, and a custom Grafana trace datasource.

Start with [SPEC.md](SPEC.md). It defines the proposed v1, the Iceberg decision, API and dataframe contracts, implementation milestones, and acceptance criteria.

Symphony setup: [docs/symphony-setup.md](docs/symphony-setup.md). Implementation tasks are tracked in [GitHub Issues](https://github.com/actuallyKasi/obs_poc_object_storage/issues).

Status: specification and orchestration setup. Application implementation and benchmark results are tracked per issue.
