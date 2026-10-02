# Object storage tracing PoC

An implementation specification for a local tracing backend: OTLP ingestion, an OpenTelemetry gateway, Parquet in S3-compatible storage, DuckDB queries, and a custom Grafana trace datasource.

Start with [SPEC.md](SPEC.md). It defines the proposed v1, the Iceberg decision, API and dataframe contracts, implementation milestones, and acceptance criteria.

Status: specification only. The Docker stack and application code have not been implemented or benchmarked.
