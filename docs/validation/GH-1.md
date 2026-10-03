# GH-1 validation

Date: 2026-10-03. Scope: M0 part 1, container foundation and storage compatibility.
All assigned acceptance checks passed on native Linux ARM64 containers.

## Environment and pins

| Item | Observed value |
| --- | --- |
| Host `uname -m` | `arm64` |
| Docker client / engine | 29.7.2 / 29.7.2 |
| Docker Desktop | 4.88.1 (237512) |
| Compose | v5.4.0 |
| Engine | `linux/arm64` (`aarch64` in `docker info`) |
| Docker allocation | 8 CPUs, 8,319,770,624 bytes (7.75 GiB) |
| Compose project | `obs-gh1-1027023261`, derived from this clone's physical path |
| SeaweedFS | 4.48, source `530be3e37`, `linux arm64` |
| Collector contrib | 0.123.0 |
| Python | 3.12.10, `aarch64` |
| DuckDB | 1.2.2, source `7c039464e4` |
| PyArrow | 19.0.1 |

Image references are pinned by tag and multi-architecture registry digest:

```text
python:3.12.10-slim-bookworm@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
chrislusf/seaweedfs:4.48@sha256:4e61d15fd35994cb1e43e1e553dff106794841fd9a99ade2fc8c8bfce4d7872d
otel/opentelemetry-collector-contrib:0.123.0@sha256:e39311df1f3d941923c00da79ac7ba6269124a870ee87e3c3ad24d60f8aee4d2
```

All service images, the tools image and the Python base were inspected as
`linux/arm64`. No platform override or emulation was used. Intel/AMD64 runtime
checks were **not run** on this ARM64 host.

The container's `pip freeze` exactly matched
[`requirements.lock`](../../tools/foundation/requirements.lock), including all ten
runtime/transitive packages. `pip check` passed during build. DuckDB `httpfs` was
installed and loaded during build from its version/platform-specific official
repository, and loaded again at runtime without installation:

```text
/opt/duckdb/extensions/v1.2.2/linux_arm64/httpfs.duckdb_extension
SHA-256 d717365aa99edd47aec7fe25cd9d5a40b8034e0221e5a0e15f97d929da008a02
```

## Commands and results

Environment checks:

```sh
uname -m
docker version
docker compose version
docker info --format '{{.Architecture}} {{.NCPU}} {{.MemTotal}}'
```

Integration run (exit 0):

```sh
mkdir -p /tmp/obs-gh1-buildx
BUILDX_CONFIG=/tmp/obs-gh1-buildx make test
```

The script executed these checks against actual containers and objects:

| Command / check | Result |
| --- | --- |
| `./tools/configure.sh` | PASS; private ignored credentials, preserved on repeat |
| `./tools/compose.sh build credential-init` | PASS; pinned native wheels, `pip check`, baked `httpfs` |
| `./tools/compose.sh up -d` and `wait storage-init` | PASS; fresh project network/volumes created; initializer reported `Bucket created` and `Bucket readiness PASS` |
| `./tools/check-architecture.sh` | PASS; host, engine and all three service images ARM64 |
| `./tools/check-host-ports.sh` (before and after restart) | PASS; all three loopback bindings; host S3 returned 403 and OTLP HTTP returned 405 |
| `./tools/compose.sh run --rm --no-deps storage-init` | PASS; `Bucket already exists`, readiness passed |
| `./tools/compose.sh run --rm --no-deps otel-gateway validate --config=/etc/otelcol-contrib/config.yaml` | PASS, exit 0 |
| `./tools/compose.sh run --rm tooling foundation.py compatibility` | PASS; results below |
| `./tools/compose.sh run --rm tooling foundation.py collector` | PASS; health and metrics HTTP 200 |
| `./tools/compose.sh run --rm tooling foundation.py seed` | PASS; wrote and read the 1 MiB sentinel |
| `./tools/compose.sh down`, `up -d`, `wait storage-init` | PASS; containers/network recreated, volumes retained |
| `./tools/compose.sh run --rm tooling foundation.py verify` | PASS; sentinel bytes and SHA-256 unchanged |
| `./tools/compose.sh run --rm --no-deps tooling -m pip freeze` | PASS; matches lockfile |
| `./tools/compose.sh exec object-store weed version` | PASS; 4.48, `530be3e37`, Linux ARM64 |
| `./tools/compose.sh run --rm --no-deps otel-gateway --version` | PASS; 0.123.0 |
| `./tools/compose.sh config --quiet`, shell syntax and `git diff --check` | PASS |

Observed compatibility output:

```text
Python 3.12.10, machine aarch64, DuckDB 1.2.2, PyArrow 19.0.1
PASS PUT/immediate GET/HEAD/range 206/paginated LIST (7 objects, 4 pages)
PASS auth: anonymous GET/HEAD/LIST/PUT denied
PASS auth: unknown key GET/HEAD/LIST/PUT denied
PASS auth: wrong secret GET/HEAD/LIST/PUT denied
PASS DuckDB remote S3 Parquet: baked httpfs, downloads disabled, exact INT64/typed attributes
PASS observed DuckDB S3 range requests: 3 (HTTP 206)
PASS Collector health and internal metrics endpoints
PASS persistence seed: sha256=fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83
PASS persistence verify: sha256=fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83
PASS foundation integration checks, including down/up persistence
```

The explicit range check asserted `bytes=13-1036`, HTTP 206, Content-Range and
all 1,024 returned bytes. The listing check asserted every expected key exactly
once over four pages of size two, with continuation on the first three pages.
Every unauthorized operation returned 403 and the original payload was unchanged.

DuckDB queried an explicit S3 object through a local forwarding probe that
preserved signed headers, forwarded to SeaweedFS, and recorded only
method/range/status. Three range responses were 206. Extension auto-install and
auto-load were disabled, and the tools' internal network had no external route. Values
`1780000000123456789` and `1780000000123456790` and typed int64/boolean attributes
round-tripped exactly through Zstandard Parquet.

## Resolved access failures and limits

The previous run on 2026-10-02 failed before implementation:

```text
fatal: cannot lock ref 'refs/heads/symphony/GH-1': unable to create directory for .git/refs/heads/symphony/GH-1
```

The operator granted this clone's Git metadata write access. On this run,
`git switch -c symphony/GH-1` succeeded; no sandbox escalation was used.

The initial unqualified Compose build then failed:

```text
failed to update builder last activity time: open /Users/kasi/.docker/buildx/activity/.tmp-default2315490987: operation not permitted
```

Selecting writable temporary Buildx state with its supported `BUILDX_CONFIG`
setting resolved that failure. Image/package downloads were slow but completed.
No unresolved validation blocker remains.

The final host reachability check found that Docker 29.7.2 did not publish ports
for services attached only to an internal network: `compose port object-store
8333` returned `invalid IP:0`, and host curl failed with exit 7/status 000.
Storage and Collector now also join a workspace-scoped ingress network; tooling
remains only on the internal network. Host S3 returns the expected unsigned 403,
OTLP HTTP returns 405 for GET, and all published bindings use 127.0.0.1. The full
suite was rerun after this correction, including host checks before/after restart.

This evidence covers GH-1 only. End-to-end OTLP delivery, atomic trace block
publication, deduplication, scoped trace lookup, Grafana integration and benchmarks
are **not implemented or validated here**. The gateway's exporter targets the
future writer. No dependent issue was enabled, and no merge or issue closure was
performed. The fixture sentinel remains in this workspace's object-data volume;
no other workspace's containers or data were reset.
