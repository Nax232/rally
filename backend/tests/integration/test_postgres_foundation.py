"""Read-only integration checks. Never create/delete a test database implicitly."""

import os

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


@pytest.fixture
def engine():
    url = os.environ.get("SIPRE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("SIPRE_TEST_DATABASE_URL absent: real PostgreSQL/PostGIS not available")
    instance = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        yield instance
    finally:
        instance.dispose()


def test_postgis_and_migration_head(engine):
    with engine.connect() as connection:
        assert connection.execute(text("SELECT PostGIS_Version()")).scalar()
        assert connection.execute(
            text("SELECT version_num FROM core.alembic_version")
        ).scalar() == ("0005_gis_network")
        schemas = set(
            connection.execute(
                text("SELECT schema_name FROM information_schema.schemata")
            ).scalars()
        )
        assert {
            "core",
            "ops",
            "geo",
            "model",
            "planning",
            "audit",
            "experiments",
            "analytics",
        } <= schemas


def test_reader_cannot_access_raw_schemas_or_create_in_database(engine):
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT has_schema_privilege('sipre_metabase_reader','analytics','USAGE')")
        ).scalar()
        for schema in ("core", "ops", "geo", "model", "planning", "audit", "experiments"):
            assert not connection.execute(
                text("SELECT has_schema_privilege('sipre_metabase_reader', :schema, 'USAGE')"),
                {"schema": schema},
            ).scalar()
        for role in ("sipre_metabase_reader", "sipre_app", "sipre_worker"):
            assert not connection.execute(
                text("SELECT has_database_privilege(:role, current_database(), 'CREATE')"),
                {"role": role},
            ).scalar()
