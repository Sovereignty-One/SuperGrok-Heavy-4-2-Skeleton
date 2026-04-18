# alembic/env.py
# MIT License - Copyright (c) 2026 APPEL

import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy import create_engine

from alembic import context

# Add project root to Python path so imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import your SQLAlchemy Base and models
from app.core.database import Base  # noqa: E402
from app.models.user import User         # noqa: E402
from app.models.project import Project   # noqa: E402
from app.models.generation import Generation  # noqa: E402
from app.models.media import Media       # noqa: E402

# this is the Alembic Config object
config = context.config

# Setup logging from alembic.ini if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """
    Get database URL.
    Prefer environment variable DATABASE_URL (common in production),
    fall back to sqlalchemy.url in alembic.ini.
    """
    return os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(get_url(), poolclass=pool.NullPool)

    def do_run_migrations(connection: Connection) -> None:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,      # Detect column type changes
            compare_server_default=True,  # Detect default changes
        )

        with context.begin_transaction():
            context.run_migrations()

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
