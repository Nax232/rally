#!/bin/sh
# Validate an already running, isolated SIPRE Compose stack. Run from Linux/WSL.
# Usage: sh scripts/validate-phase9-compose.sh [env-file] [compose-project]
set -eu

cd "$(dirname "$0")/.."
ENV_FILE=${1:-.env}
PROJECT=${2:-sipre}
if [ ! -f "$ENV_FILE" ]; then
  echo "Missing Compose environment file: $ENV_FILE" >&2
  exit 2
fi
set -a
. "./$ENV_FILE"
set +a
: "${SIPRE_MIGRATOR_PASSWORD:?Missing migrator password}"
API_PORT=${SIPRE_API_PORT:-8000}
METABASE_PORT=${SIPRE_METABASE_PORT:-3000}
DB="$PROJECT-db-1"
COUNT=0
compose() { docker compose --env-file "$ENV_FILE" -p "$PROJECT" "$@"; }
pass() { COUNT=$((COUNT + 1)); echo "PASS $COUNT: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }
query() { docker exec "$DB" psql -U postgres -d sipre -tAc "$1"; }

SUFFIX="$(date +%s)_$$"
RESTORE="sipre_f9_restore_$SUFFIX"
FRESH="sipre_f9_fresh_$SUFFIX"
UPGRADE="sipre_f9_upgrade_$SUFFIX"
CREATED=""
cleanup() {
  for name in $CREATED; do
    docker exec "$DB" psql -U postgres -tAc "DROP DATABASE $name WITH (FORCE)" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT HUP INT TERM
new_database() {
  docker exec "$DB" psql -U postgres -tAc \
    "CREATE DATABASE $1 OWNER sipre_migrator" >/dev/null
  CREATED="$CREATED $1"
}
prepare_database() {
  new_database "$1"
  docker exec "$DB" psql -U postgres -d "$1" -tAc \
    "CREATE EXTENSION postgis; CREATE SCHEMA core AUTHORIZATION sipre_migrator; REVOKE CREATE ON SCHEMA public FROM PUBLIC" >/dev/null
  docker exec "$DB" psql -U postgres -tAc \
    "GRANT CONNECT,CREATE ON DATABASE $1 TO sipre_migrator; GRANT CONNECT ON DATABASE $1 TO sipre_app,sipre_worker,sipre_metabase_reader" >/dev/null
}

compose config --quiet && pass "Compose configuration" || fail "Compose configuration"
wget -qO- "http://127.0.0.1:$API_PORT/api/v1/health/live" | grep -q '"status":"alive"' \
  && pass "API liveness" || fail "API liveness"
wget -qO- "http://127.0.0.1:$API_PORT/api/v1/health/ready" | grep -q '"status":"ready"' \
  && pass "PostGIS and migration readiness" || fail "API readiness"
attempt=0
until wget -qO- "http://127.0.0.1:$METABASE_PORT/api/health" | grep -q 'ok'; do
  attempt=$((attempt + 1))
  [ "$attempt" -lt 12 ] || fail "Metabase health"
  sleep 5
done
pass "Metabase health"
[ "$(query 'SELECT version_num FROM core.alembic_version')" = "0008_simulated_assistance" ] \
  && pass "Alembic revision 0008" || fail "Alembic revision"

docker exec "$DB" psql -U sipre_metabase_reader -d sipre -tAc \
  'SELECT count(*) FROM analytics.v_foundation_status' >/dev/null \
  && pass "BI reader can query analytics" || fail "BI reader analytics"
if docker exec "$DB" psql -U sipre_metabase_reader -d sipre -tAc \
  'SELECT count(*) FROM ops.emergencies' >/dev/null 2>&1; then
  fail "BI reader can query domain data"
fi
pass "BI reader denied domain data"
if docker exec "$DB" psql -U sipre_metabase_reader -d sipre -tAc \
  "INSERT INTO analytics.v_foundation_status VALUES('X','Y',1)" >/dev/null 2>&1; then
  fail "BI reader can write"
fi
pass "BI reader denied writes"
if docker exec "$DB" psql -U sipre_app -d sipre -tAc \
  'DELETE FROM audit.events' >/dev/null 2>&1; then
  fail "App can delete audit history"
fi
pass "App denied audit deletion"
if docker exec "$DB" psql -U sipre_app -d sipre -tAc \
  'UPDATE ops.inventory_balances SET quantity=999' >/dev/null 2>&1; then
  fail "App can alter balances directly"
fi
pass "App denied direct balance changes"
if docker exec "$DB" psql -U sipre_worker -d sipre -tAc \
  "INSERT INTO core.users(user_id,login,password_hash) VALUES (gen_random_uuid(),'invalid-worker','invalid')" >/dev/null 2>&1; then
  fail "Worker can create users"
fi
pass "Worker denied user creation"
if docker exec "$DB" psql -U sipre_app -d sipre -tAc \
  'DELETE FROM geo.route_candidate_edges' >/dev/null 2>&1; then
  fail "App can delete route sequences directly"
fi
pass "App denied direct route sequence deletion"

docker exec "$DB" pg_dump -U postgres -Fc -d sipre -f /tmp/sipre-f9-verify.dump
new_database "$RESTORE"
docker exec "$DB" pg_restore -U postgres -d "$RESTORE" --exit-on-error /tmp/sipre-f9-verify.dump
for table in ops.emergencies audit.events geo.road_edges; do
  source_count=$(query "SELECT count(*) FROM $table")
  restored_count=$(docker exec "$DB" psql -U postgres -d "$RESTORE" -tAc "SELECT count(*) FROM $table")
  [ "$source_count" = "$restored_count" ] || fail "Restore mismatch: $table"
done
pass "Backup and restore preserve history and network"

prepare_database "$FRESH"
compose run --rm --no-deps \
  -e "SIPRE_DATABASE_URL=postgresql+psycopg://sipre_migrator:${SIPRE_MIGRATOR_PASSWORD}@db:5432/$FRESH" \
  migrate >/dev/null
[ "$(docker exec "$DB" psql -U postgres -d "$FRESH" -tAc 'SELECT version_num FROM core.alembic_version')" = "0008_simulated_assistance" ] \
  && pass "Fresh database migrates to 0008" || fail "Fresh migration"

prepare_database "$UPGRADE"
compose run --rm --no-deps \
  -e "SIPRE_DATABASE_URL=postgresql+psycopg://sipre_migrator:${SIPRE_MIGRATOR_PASSWORD}@db:5432/$UPGRADE" \
  migrate python -m alembic -c database/alembic.ini upgrade 0003_integrity >/dev/null
compose run --rm --no-deps \
  -e "SIPRE_DATABASE_URL=postgresql+psycopg://sipre_migrator:${SIPRE_MIGRATOR_PASSWORD}@db:5432/$UPGRADE" \
  migrate >/dev/null
[ "$(docker exec "$DB" psql -U postgres -d "$UPGRADE" -tAc 'SELECT version_num FROM core.alembic_version')" = "0008_simulated_assistance" ] \
  && pass "Upgrade 0003 to 0008" || fail "Upgrade migration"

compose run --rm --no-deps worker python -m app.worker --once >/dev/null \
  && pass "Durable worker starts" || fail "Worker"
compose --profile test run --rm tests \
  && pass "Container test suite" || fail "Container test suite"
echo "Validated: $COUNT checks passed. Temporary databases will be removed."
