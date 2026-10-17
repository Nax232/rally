"""One-shot connectivity check, not a job worker or operational engine."""

from app.db.health import create_database_engine, database_ready
from app.settings import Settings


def main() -> int:
    engine = create_database_engine(Settings())
    try:
        ready = database_ready(engine)
        print("database_ready" if ready else "database_unavailable")
        return 0 if ready else 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
