# Container foundation (GH-1)

This slice provides authenticated SeaweedFS S3 storage, an idempotent bucket
initializer, containerized Python compatibility tooling, and a traces-only
Collector configuration. The writer, querier, Grafana plugin and complete OTLP
path belong to later issues. Iceberg and Lance endpoints are disabled.

## Run

Prerequisites: Docker with Compose v2.24 or newer, a POSIX shell, make, curl and standard
shell utilities. No host Python or Python packages are needed.

```sh
make configure      # creates private, ignored .env with random local credentials
make up             # builds tools, starts services, waits for bucket initialization
make test           # real integration checks; includes this workspace's down/up
make down           # retains named volumes and objects
```

Use `./tools/compose.sh` for additional Compose commands. It derives the project
name from this clone's physical path (`obs-gh1-<cksum>`); volumes, networks and the
local tools image stay scoped to that project. It ignores ambient
`COMPOSE_PROJECT_NAME` and `DOCKER_DEFAULT_PLATFORM`. No fixed container names or
external volumes are used. On another host, moving the clone changes its project
name and therefore selects different volumes.

The S3 and OTLP ports bind only to loopback. To run several workspaces at once,
change `S3_PORT`, `OTLP_GRPC_PORT` and `OTLP_HTTP_PORT` in each private `.env` to
unused ports. The tools and initializers use an internal network with no internet
route. Storage and Collector also join an ingress network so Docker can publish
their loopback ports. Image builds fetch dependencies before joining the network.
Keep `.env` for restart continuity and do not paste `docker compose config`
output into tickets: it expands credentials. Credential JSON lives in a named
volume, never the repository. Authentication is local PoC administration, not a
production tenant isolation scheme.

`credential-init` writes S3 configuration before SeaweedFS starts. SeaweedFS does
not auto-create buckets on upload. `storage-init` checks authenticated access,
creates `traces` only on a 404, and fails on other errors. Repeating initialization
preserves existing objects. Both the filer metadata and volume data live under
persisted `/data`. Ordinary `down` does not remove them. No automatic data reset
or cleanup of other projects is provided.

For a sandbox that cannot write Buildx state under `~/.docker`, select a writable
state directory explicitly, for example:

```sh
mkdir -p /tmp/obs-gh1-buildx
BUILDX_CONFIG=/tmp/obs-gh1-buildx make test
```

## Budgets

Starting Docker VM budget: 4 CPUs and 8 GiB RAM. These are development budgets,
not measured throughput or durability guarantees.

| Container | Memory limit | CPU limit |
| --- | --- | --- |
| SeaweedFS | 1 GiB | 1 |
| Collector | 512 MiB | 1 |
| Credential/bucket initializer (each, short lived) | 128 MiB | 0.5 |
| Compatibility tools (on demand) | 1 GiB | 2 |

DuckDB's check uses two threads and a 256 MiB engine memory limit; the container
limit also covers Python/PyArrow. SeaweedFS uses at most eight data volumes with
a 128 MiB volume rollover setting. Rollover settings are not disk quotas. Allow
at least 5 GiB free Docker disk for images, build cache, dependencies and fixtures;
inspect growth with `docker system df` without running global cleanup. Containers
use a 30 second storage shutdown grace period. Laptop/disk loss is not covered
by local Docker volume persistence.

## Collector contract

`config/otel-gateway.yaml` has only the traces pipeline:
OTLP receiver → memory limiter → batch → OTLP HTTP exporter.
The limiter checks every second, with 384 MiB hard and 64 MiB spike allowance.
Batching triggers at 1,000 spans, caps at 2,000 and flushes after two seconds.
For Collector 0.123.0 the exporter queue explicitly uses **requests** (incoming
batches) as its sizing unit: 64 requests, two consumers, 5 second attempt timeout,
1–5 second retry intervals, and 30 second maximum retry duration. These are
bounded in-memory buffers; Collector acceptance does not imply durable storage.
Crashes can lose accepted batches/queued requests.

The exporter points to `http://trace-writer:4318`, reserved for the later writer
issue. Sending traces before that service exists will retry then fail. GH-1
validates the configuration using the pinned binary and checks health/metrics;
it does not claim end-to-end ingestion. Health (`13133`) and internal metrics
(`8888`) are available only on the Compose network. The Collector image has no
shell-based Docker healthcheck; tooling probes its health extension directly.

## Compatibility checks

`make test` fails on any violated assertion. Python checks run in containers;
the shell also checks architecture and host port publishing:

- Actual PUT with immediate GET, object HEAD and custom metadata.
- Seven objects over four LIST pages of size two, verifying continuation and keys.
- Explicit byte range GET with 206, Content-Range and exact byte comparison.
- Anonymous, unknown-key and wrong-secret GET/HEAD/LIST/PUT all rejected with 403.
- DuckDB reads a specific S3 Parquet object through baked `httpfs`, with automatic
  extension installation/loading disabled, on the isolated network. Exact INT64
  nanoseconds and typed attribute JSON survive the read. A local forwarding probe
  records only method/range/status and requires a real DuckDB range GET returning
  206 from SeaweedFS; signed request headers are never printed.
- Collector validates with its own binary; health and metrics return 200.
- Initialization runs twice; a known 1 MiB object survives Compose down/up with
  the same SHA-256. Test cleanup deletes only its random fixture prefix and leaves
  the persistence sentinel.
- Host, Docker engine and service image architectures match (no emulation).
- Loopback S3 and OTLP HTTP ports are reachable before and after restart; all
  three published ports are bound to 127.0.0.1.

See [GH-1 validation](validation/GH-1.md) for pinned digests, environment and actual
results. Python and all transitive runtime packages are pinned in
`tools/foundation/requirements.lock`; no writer/API dependencies are introduced.
The DuckDB extension version follows the pinned DuckDB 1.2.2 release/platform
repository, is installed during image build, and is recorded by checksum.

Version-specific references checked during implementation:

- [SeaweedFS 4.48 mini configuration](https://github.com/seaweedfs/seaweedfs/blob/4.48/weed/command/mini.go)
- [Collector 0.123.0 queue/retry units](https://github.com/open-telemetry/opentelemetry-collector/blob/v0.123.0/exporter/exporterhelper/README.md)
