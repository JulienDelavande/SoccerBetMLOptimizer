from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import os

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if (DB_TYPE := os.getenv('DB_TYPE')) is None:
    raise ValueError("Missing environment variable: DB_TYPE")
if (DB_PILOT := os.getenv('DB_PILOT')) is None:
    raise ValueError("Missing environment variable: DB_PILOT")
if (DB_USER := os.getenv("DB_USER")) is None:
    raise ValueError("Missing environment variable: DB_USER")
if (DB_PASSWORD := os.getenv("DB_PASSWORD")) is None:
    raise ValueError("Missing environment variable: DB_PASSWORD")
if (DB_HOST := os.getenv("DB_HOST")) is None:
    raise ValueError("Missing environment variable: DB_HOST")
if (DB_PORT := os.getenv("DB_PORT")) is None:
    raise ValueError("Missing environment variable: DB_PORT")
if (DB_NAME := os.getenv("DB_NAME")) is None:
    raise ValueError("Missing environment variable: DB_NAME")
DB_URL = f'{DB_TYPE}+{DB_PILOT}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
config.set_main_option("sqlalchemy.url", DB_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
from base import Base
import models.models_results
import models.optim_results
import models.soccer_odds
import models.sofifa_teams_stats
import models.fbref_results
import models.teams
import models.team_alias
target_metadata = Base.metadata

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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
