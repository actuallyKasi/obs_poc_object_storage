#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./tools/configure.sh
./tools/compose.sh build credential-init
./tools/compose.sh up -d
./tools/compose.sh wait storage-init
./tools/check-architecture.sh
./tools/check-host-ports.sh
./tools/compose.sh run --rm --no-deps storage-init
./tools/compose.sh run --rm --no-deps otel-gateway validate --config=/etc/otelcol-contrib/config.yaml
./tools/compose.sh run --rm tooling foundation.py compatibility
./tools/compose.sh run --rm tooling foundation.py collector
./tools/compose.sh run --rm tooling foundation.py seed
# Deliberately omit --volumes: restart must retain the object and metadata.
./tools/compose.sh down
./tools/compose.sh up -d
./tools/compose.sh wait storage-init
./tools/compose.sh run --rm tooling foundation.py verify
./tools/check-host-ports.sh
echo 'PASS foundation integration checks, including down/up persistence'
