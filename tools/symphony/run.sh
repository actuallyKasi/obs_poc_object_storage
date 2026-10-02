#!/bin/sh
set -eu
repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$repo_root"
command -v codex >/dev/null
command -v gh >/dev/null
command -v docker >/dev/null
docker info >/dev/null
if [ -z "${GITHUB_TOKEN:-}" ]; then
  GITHUB_TOKEN=$(gh auth token)
  export GITHUB_TOKEN
fi
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) target=macos_arm64 ;;
  Darwin-x86_64) target=macos_x86_64 ;;
  Linux-aarch64|Linux-arm64) target=linux_arm64 ;;
  Linux-x86_64) target=linux_x86_64 ;;
  *) echo 'Unsupported Symphony platform' >&2; exit 1 ;;
esac
binary="$repo_root/.tools/symphony/symphony-v0.0.3-$target"
if [ ! -x "$binary" ]; then
  echo 'Run python3 tools/symphony/install.py first' >&2
  exit 1
fi
mkdir -p .symphony/logs
exec "$binary" --i-understand-that-this-will-be-running-without-the-usual-guardrails \
  --logs-root "$repo_root/.symphony/logs" "$repo_root/WORKFLOW.md"
