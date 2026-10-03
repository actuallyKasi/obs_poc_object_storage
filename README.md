# Object storage tracing PoC

An implementation specification for a local tracing backend: OTLP ingestion, an OpenTelemetry gateway, Parquet in S3-compatible storage, DuckDB queries, and a custom Grafana trace datasource.

Start with [SPEC.md](SPEC.md). It defines the proposed v1, the Iceberg decision, API and dataframe contracts, implementation milestones, and acceptance criteria.

Symphony setup: [docs/symphony-setup.md](docs/symphony-setup.md). Implementation tasks are tracked in [GitHub Issues](https://github.com/actuallyKasi/obs_poc_object_storage/issues).

Status: container foundation; application implementation and benchmark results are tracked per issue.

## Container foundation

GH-1 provides the storage and Collector compatibility foundation. See
[setup, budgets and checks](docs/container-foundation.md) and
[recorded validation](docs/validation/GH-1.md).

```sh
make up
make test
make down
```

The trace writer, query API and Grafana plugin are not implemented in this slice.
