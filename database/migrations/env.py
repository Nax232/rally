"""Credentials only via environment; migrations are a separate process and role."""

from alembic import context
from app.settings import Settings
from sqlalchemy import create_engine, pool

settings = Settings()
if settings.database_url is None:
    raise RuntimeError("SIPRE_DATABASE_URL must be supplied for migrations")

url = settings.database_url.get_secret_value()

if context.is_offline_mode():
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        version_table_schema="core",
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table_schema="core",
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()
