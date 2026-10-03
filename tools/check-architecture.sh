#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
case "$(uname -m)" in
  arm64|aarch64) expected=arm64 ;;
  x86_64|amd64) expected=amd64 ;;
  *) echo 'Unsupported host architecture' >&2; exit 1 ;;
esac
server=$(docker info --format '{{.Architecture}}')
case "$server" in aarch64) server=arm64 ;; x86_64) server=amd64 ;; esac
[ "$server" = "$expected" ] || { echo 'Docker engine is not native to this host' >&2; exit 1; }
for image_id in $(./tools/compose.sh --profile tools config --images | sort -u); do
  actual=$(docker image inspect --format '{{.Architecture}}' "$image_id")
  [ "$actual" = "$expected" ] || { echo "Non-native image: $image_id" >&2; exit 1; }
  docker image inspect --format 'PASS native image {{.Id}} {{.Os}}/{{.Architecture}}' "$image_id"
done
echo "PASS host and Docker engine: $expected"
