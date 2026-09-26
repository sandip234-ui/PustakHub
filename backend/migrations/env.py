"""
Alembic environment configuration for PustakHub.

This file controls how Alembic connects to the database and discovers models.

Key responsibilities:
  1. Load DATABASE_URL exclusively from environment variables (via app.core.config).
     The URL is NEVER read from alembic.ini at runtime to prevent accidental
     credential exposure in committed configuration files.
  2. Import all SQLAlchemy models so that the metadata attached to Base is
     complete before Alembic inspects it for autogenerate.
  3. Configure the target_metadata so Alembic can diff against the live schema.

SECURITY:
  - DATABASE_URL is loaded from the .env file via pydantic-settings.
  - It is never printed, logged, or stored outside of the SQLAlchemy engine.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Ensure the backend/ directory is on sys.path so app.* imports work
# when running `alembic` from the backend/ directory.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Load settings (reads DATABASE_URL from .env)
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Import all models — this populates Base.metadata with every table.
# Any model NOT imported here will be invisible to autogenerate.
# ---------------------------------------------------------------------------
import app.models  # noqa: E402, F401 — side-effect import registers all tables

from app.models.base import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic config object (gives access to alembic.ini values)
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Set the database URL from environment — overrides alembic.ini at runtime.
# ---------------------------------------------------------------------------
if settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
else:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Add DATABASE_URL to your .env file before running Alembic."
    )

# ---------------------------------------------------------------------------
# Configure Python logging from alembic.ini [loggers] section
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target metadata — used by autogenerate to compare against live schema
# ---------------------------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    In offline mode, Alembic does not require an active database connection.
    It generates SQL that can be applied manually. Useful for reviewing
    changes before applying them or for environments without direct DB access.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include schemas — important for multi-schema setups (single schema here)
        include_schemas=False,
        # Render AS_BOOL for server_default booleans
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In online mode, Alembic connects to the database and applies migrations
    within a transaction. This is the standard mode for development and CI.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Fresh connection per migration run
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=False,
            # Compare server_defaults so autogenerate detects default changes
            compare_server_default=True,
            # Compare column types for drift detection
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
