from sqlalchemy import engine_from_config, pool

import src.infrastructure.sqlalchemy.models  # noqa: F401  # pyright:ignore[reportUnusedImport]
from alembic import context
from src.app.settings import settings
from src.common.logging import setup_logging
from src.infrastructure.sqlalchemy.models import Base

setup_logging("INFO")

config = context.config
config.set_main_option("sqlalchemy.url", settings.ALEMBIC_URI)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
