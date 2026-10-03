#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
s3=$(./tools/compose.sh port object-store 8333)
http=$(./tools/compose.sh port otel-gateway 4318)
grpc=$(./tools/compose.sh port otel-gateway 4317)
for binding in "$s3" "$http" "$grpc"; do
  case "$binding" in
    127.0.0.1:*) ;;
    *) echo "Expected loopback port binding, got: $binding" >&2; exit 1 ;;
  esac
done
# Unsigned S3 and the wrong HTTP method must reach the services and be rejected.
[ "$(curl --max-time 5 -s -o /dev/null -w '%{http_code}' "http://$s3/")" = 403 ]
[ "$(curl --max-time 5 -s -o /dev/null -w '%{http_code}' "http://$http/v1/traces")" = 405 ]
echo 'PASS host loopback S3/OTLP HTTP reachability and all three port bindings'
