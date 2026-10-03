#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Bind project/volume/image names to this physical clone, ignoring ambient projects.
workspace_id=$(pwd -P | cksum | awk '{print $1}')
export COMPOSE_PROJECT_NAME="obs-gh1-${workspace_id}"
unset DOCKER_DEFAULT_PLATFORM
exec docker compose --project-name "$COMPOSE_PROJECT_NAME" --env-file .env "$@"
