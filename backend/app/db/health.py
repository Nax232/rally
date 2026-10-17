"""Readiness checks deliberately expose no connection details."""

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.settings import Settings


def create_database_engine(settings: Settings) -> Engine | None:
    if settings.database_url is None:
        return None
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=0,
        pool_timeout=settings.db_connect_timeout_seconds,
        connect_args={
            "connect_timeout": settings.db_connect_timeout_seconds,
            "options": "-c statement_timeout=3000 -c timezone=UTC",
        },
    )


def database_ready(engine: Engine | None) -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as connection:
            # Verify the actual dependency, not merely an open TCP socket.
            return bool(
                connection.execute(
                    text(
                        "SELECT PostGIS_Version() IS NOT NULL AND "
                        "EXISTS(SELECT 1 FROM core.alembic_version "
                        "WHERE version_num='0005_gis_network')"
                    )
                ).scalar()
            )
    except SQLAlchemyError:
        return False
