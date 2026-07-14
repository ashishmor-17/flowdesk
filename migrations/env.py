import os
import sys
# Add project root to sys.path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


import app.models
target_metadata = app.models.Base.metadata

from app.core.config import get_settings
settings = get_settings()

# Overwrite the URL in Alembic's config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.get_secret_value())



# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

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

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()
async def run_migrations_online() -> None:
    # Get database URL from our settings
    connectable = create_async_engine(
        settings.DATABASE_URL.get_secret_value(),
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        # run_sync executes a sync function inside the async context
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async runner
    asyncio.run(run_migrations_online())