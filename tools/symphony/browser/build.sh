#!/bin/sh
set -eu
browser_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$browser_root/../../.." && pwd)
mkdir -p "$repo_root/.tools/buildx"
BUILDX_CONFIG="$repo_root/.tools/buildx" docker build \
  -t obs-symphony-playwright:0.0.83 "$browser_root"
docker image inspect obs-symphony-playwright:0.0.83 --format '{{.Os}}/{{.Architecture}} {{.Id}}'
