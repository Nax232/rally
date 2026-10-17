"""Prepare a new, isolated local PostgreSQL cluster. Never touches installed service data."""

import json
import os
import secrets
import subprocess
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"
BIN = TOOLS / "pgsql" / "bin"
DATA = TOOLS / "phase9-db-live"
CREDS = TOOLS / "phase9-local.json"
PORT = 55439


def command(*args):
    subprocess.run(
        [str(a) for a in args],
        check=True,
        cwd=ROOT,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def main():
    if CREDS.exists() or DATA.exists():
        raise SystemExit(
            "Existing local cluster/config preserved; use pg_ctl start with its data directory."
        )
    passwords = {
        r: secrets.token_hex(24)
        for r in (
            "postgres",
            "sipre_migrator",
            "sipre_app",
            "sipre_worker",
            "sipre_metabase_reader",
            "metabase_app",
        )
    }
    pwfile = TOOLS / "phase9-init-password"
    pwfile.write_text(passwords["postgres"], encoding="utf-8")
    command(
        BIN / "initdb.exe",
        "-D",
        DATA,
        "-U",
        "postgres",
        "-A",
        "scram-sha-256",
        "--pwfile",
        pwfile,
        "--encoding=UTF8",
        "--locale=C",
    )
    with (DATA / "postgresql.conf").open("a", encoding="utf-8") as f:
        f.write("\nlisten_addresses='127.0.0.1'\nport=55439\ntimezone='UTC'\n")
    CREDS.write_text(json.dumps({"port": PORT, "passwords": passwords}), encoding="utf-8")
    command(BIN / "pg_ctl.exe", "-D", DATA, "-l", TOOLS / "phase9-postgres.log", "-w", "start")
    admin = dict(host="127.0.0.1", port=PORT, user="postgres", password=passwords["postgres"])
    with psycopg.connect(**admin, dbname="postgres", autocommit=True) as db:
        for role, password in passwords.items():
            if role != "postgres":
                db.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD {}"
                    ).format(sql.Identifier(role), sql.Literal(password))
                )
        db.execute("CREATE DATABASE sipre")
        db.execute("CREATE DATABASE metabase_app OWNER metabase_app")
        db.execute("REVOKE ALL ON DATABASE metabase_app FROM PUBLIC")
    with psycopg.connect(**admin, dbname="sipre", autocommit=True) as db:
        db.execute("REVOKE ALL ON DATABASE sipre FROM PUBLIC")
        db.execute("GRANT CONNECT,CREATE ON DATABASE sipre TO sipre_migrator")
        db.execute(
            "GRANT CONNECT ON DATABASE sipre TO sipre_app,sipre_worker,sipre_metabase_reader"
        )
        db.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        db.execute("CREATE EXTENSION postgis")
        db.execute("CREATE SCHEMA core AUTHORIZATION sipre_migrator")
    print("Isolated local PostgreSQL/PostGIS ready on 127.0.0.1:55439. Credentials kept in .tools.")


if __name__ == "__main__":
    main()
