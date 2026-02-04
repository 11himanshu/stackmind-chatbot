from logging.config import fileConfig
from alembic import context

from db import engine, Base  # ← THIS IS CRITICAL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Use app metadata
target_metadata = Base.metadata


def run_migrations_offline():
    raise RuntimeError(
        "Offline migrations are disabled. "
        "Use online migrations with app engine."
    )


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()