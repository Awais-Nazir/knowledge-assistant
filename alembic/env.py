import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.models.base import Base

# import all models so Alembic can detect them
import app.models  # noqa: F401
from pgvector.sqlalchemy import Vector  # noqa: F401

config = context.config

# set the database URL from our settings — not from alembic.ini
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# set up Python logging from alembic.ini config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# this is the metadata Alembic compares against the database
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without a real database connection.
    Useful for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,      # detect column type changes
        compare_server_default=True,  # detect default value changes
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations using an async engine.
    Required because we use asyncpg (async PostgreSQL driver).
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling for migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()