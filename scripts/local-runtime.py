"""Use isolated workspace credentials without printing connection strings."""

import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["migrate", "test", "serve", "worker", "seed", "backup"])
    args = parser.parse_args()
    config = json.loads((ROOT / ".tools/phase9-local.json").read_text())
    env = os.environ.copy()

    def url(role):
        return f"postgresql+psycopg://{role}:{config['passwords'][role]}@127.0.0.1:{config['port']}/sipre"

    env["PYTHONPATH"] = str(ROOT / "backend")
    env["SIPRE_DATABASE_URL"] = url("sipre_app")
    env["SIPRE_TEST_DATABASE_URL"] = url("sipre_migrator")
    env["SIPRE_TEST_APP_URL"] = url("sipre_app")
    env["SIPRE_TEST_WORKER_URL"] = url("sipre_worker")
    env["SIPRE_TEST_READER_URL"] = url("sipre_metabase_reader")
    commands = {
        "migrate": ["-m", "alembic", "-c", "database/alembic.ini", "upgrade", "head"],
        "test": ["-m", "pytest", "-q", "--junitxml=artifacts/phase9-complete-tests.xml"],
        "serve": [
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--no-access-log",
        ],
        "worker": ["-m", "app.worker", "--once"],
        "seed": ["-m", "app.bootstrap", "--seed"],
    }
    if args.action in ("migrate", "seed"):
        env["SIPRE_DATABASE_URL"] = url("sipre_migrator")
    if args.action == "seed":
        login_file = ROOT / ".tools/phase9-demo-login.json"
        if not login_file.exists():
            login_file.write_text(
                json.dumps(
                    {"admin": secrets.token_urlsafe(24), "demo.operator": secrets.token_urlsafe(24)}
                ),
                encoding="utf-8",
            )
        logins = json.loads(login_file.read_text())
        env["SIPRE_BOOTSTRAP_PASSWORD"] = logins["admin"]
        env["SIPRE_DEMO_PASSWORD"] = logins["demo.operator"]
    if args.action == "worker":
        env["SIPRE_DATABASE_URL"] = url("sipre_worker")
    if args.action == "backup":
        env["PGPASSWORD"] = config["passwords"]["postgres"]
        command = [
            str(ROOT / ".tools/pgsql/bin/pg_dump.exe"),
            "-h",
            "127.0.0.1",
            "-p",
            str(config["port"]),
            "-U",
            "postgres",
            "-d",
            "sipre",
            "-Fc",
            "-f",
            str(ROOT / "artifacts/phase9-backup.dump"),
        ]
    else:
        command = [sys.executable, *commands[args.action]]
    result = subprocess.run(command, cwd=ROOT, env=env)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
