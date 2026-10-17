#!/usr/bin/env bash
set -euo pipefail

# Runs only on first initialization of the Docker volume. No password in CLI arguments.
psql --username "$POSTGRES_USER" --dbname sipre --set ON_ERROR_STOP=1 <<'SQL'
\getenv migrator_password SIPRE_MIGRATOR_PASSWORD
\getenv app_password SIPRE_APP_PASSWORD
\getenv worker_password SIPRE_WORKER_PASSWORD
\getenv reader_password SIPRE_METABASE_READER_PASSWORD
\getenv metabase_password METABASE_APP_PASSWORD

CREATE ROLE sipre_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'migrator_password';
CREATE ROLE sipre_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'app_password';
CREATE ROLE sipre_worker LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'worker_password';
CREATE ROLE sipre_metabase_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'reader_password';
CREATE ROLE metabase_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD :'metabase_password';

REVOKE ALL ON DATABASE sipre FROM PUBLIC;
GRANT CONNECT, CREATE ON DATABASE sipre TO sipre_migrator;
GRANT CONNECT ON DATABASE sipre TO sipre_app, sipre_worker, sipre_metabase_reader;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA core AUTHORIZATION sipre_migrator;

CREATE DATABASE metabase_app OWNER metabase_app;
REVOKE ALL ON DATABASE metabase_app FROM PUBLIC;
GRANT CONNECT ON DATABASE metabase_app TO metabase_app;
SQL
