#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ -e .env ]; then
  echo '.env already exists; preserving local configuration'
  exit 0
fi
umask 077
# /dev/urandom and standard shell utilities; no host Python installation.
access=$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
secret=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')
cat > .env <<EOF_ENV
LOCAL_S3_ACCESS_KEY=$access
LOCAL_S3_SECRET_KEY=$secret
S3_PORT=8333
OTLP_GRPC_PORT=4317
OTLP_HTTP_PORT=4318
EOF_ENV
echo 'Created private .env with random local credentials'
