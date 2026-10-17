#!/bin/sh
# Run the HTTP flow against a bootstrapped SIPRE Compose stack from Linux/WSL.
# Usage: sh scripts/run-phase9-e2e.sh [env-file] [compose-project]
set -eu
cd "$(dirname "$0")/.."
ENV_FILE=${1:-.env}
PROJECT=${2:-sipre}
[ -f "$ENV_FILE" ] || { echo "Missing environment file: $ENV_FILE" >&2; exit 2; }
set -a
. "./$ENV_FILE"
set +a
: "${SIPRE_BOOTSTRAP_PASSWORD:?Missing admin password}"
: "${SIPRE_DEMO_PASSWORD:?Missing demo password}"
docker compose --env-file "$ENV_FILE" -p "$PROJECT" --profile test run --rm --no-deps \
  -e SIPRE_API=http://api:8000 \
  -e SIPRE_BOOTSTRAP_PASSWORD \
  -e SIPRE_DEMO_PASSWORD \
  -v "$(pwd)/scripts/phase9-e2e-check.py:/tmp/phase9-e2e.py:ro" \
  tests python /tmp/phase9-e2e.py
