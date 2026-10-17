"""Non-destructive persistence check: restart isolated cluster and restore to a NEW database."""

import hashlib
import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]


def signature(db):
    tables = db.execute("""SELECT schemaname,tablename FROM pg_tables
        WHERE schemaname IN ('core','ops','geo','model','audit') ORDER BY 1,2""").fetchall()
    result = {}
    for schema, table in tables:
        rows = db.execute(
            sql.SQL("SELECT row_to_json(t)::text FROM {}.{} t").format(
                sql.Identifier(schema), sql.Identifier(table)
            )
        ).fetchall()
        payload = "\n".join(sorted(r[0] for r in rows)).encode()
        result[schema + "." + table] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return result


def main():
    config = json.loads((ROOT / ".tools/phase9-local.json").read_text())
    env = os.environ.copy()
    env["PGPASSWORD"] = config["passwords"]["postgres"]
    common = ["-h", "127.0.0.1", "-p", str(config["port"]), "-U", "postgres"]
    conn = dict(
        host="127.0.0.1",
        port=config["port"],
        user="postgres",
        password=config["passwords"]["postgres"],
    )
    bin_dir = ROOT / ".tools/pgsql/bin"
    with psycopg.connect(**conn, dbname="sipre") as db:
        before = signature(db)
        version = db.execute("SELECT version(),PostGIS_Full_Version()").fetchone()
    archive = ROOT / "artifacts/phase9-backup.dump"
    subprocess.run(
        [str(bin_dir / "pg_dump.exe"), *common, "-d", "sipre", "-Fc", "-f", str(archive)],
        env=env,
        check=True,
    )
    subprocess.run(
        [
            str(bin_dir / "pg_ctl.exe"),
            "-D",
            str(ROOT / ".tools/phase9-db-live"),
            "-l",
            str(ROOT / ".tools/phase9-postgres.log"),
            "-w",
            "restart",
        ],
        env=env,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    with psycopg.connect(**conn, dbname="sipre") as db:
        restarted = signature(db)
    assert before == restarted, "Persistence mismatch after restart"
    restored_name = "sipre_restore_" + uuid4().hex[:12]
    with psycopg.connect(**conn, dbname="postgres", autocommit=True) as db:
        db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(restored_name)))
    subprocess.run(
        [
            str(bin_dir / "pg_restore.exe"),
            *common,
            "-d",
            restored_name,
            "--exit-on-error",
            str(archive),
        ],
        env=env,
        check=True,
    )
    with psycopg.connect(**conn, dbname=restored_name) as db:
        restored = signature(db)
    assert before == restored, "Restore mismatch"
    evidence = {
        "postgres": version[0],
        "postgis": version[1],
        "restart_equal": True,
        "restore_equal": True,
        "restored_database": restored_name,
        "tables": before,
    }
    (ROOT / "artifacts/phase9-persistence.json").write_text(json.dumps(evidence, indent=2))
    print(f"Restart and restore verified: {len(before)} tables. New database: {restored_name}")


if __name__ == "__main__":
    main()
