"""Alembic environment configuration for AOS."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Import SQLModel metadata
from sqlmodel import SQLModel

from alembic import context


# =============================================================================
# DB AUTHORITY GATE (MANDATORY)
# Reference: docs/architecture/contracts/AUTHORITY_CONTRACT.md
# =============================================================================

def validate_db_authority() -> tuple[str, str]:
    """
    Validate database authority before any migration runs.

    Rules:
    - DB_AUTHORITY must be explicitly set (no inference)
    - Only 'neon' authority is allowed for migrations
    - DATABASE_URL must match declared authority

    Returns:
        Tuple of (db_authority, database_url)

    Raises:
        RuntimeError if authority validation fails
    """
    db_authority = os.getenv("DB_AUTHORITY")
    database_url = os.getenv("DATABASE_URL", "")

    # Rule 1: Authority must be declared
    if not db_authority:
        print("\n" + "=" * 60)
        print("DB AUTHORITY GATE: BLOCKED")
        print("=" * 60)
        print("\nDB_AUTHORITY environment variable is not set.")
        print("\nMigrations require explicit authority declaration:")
        print("  export DB_AUTHORITY=neon")
        print("  export DATABASE_URL=<your-neon-connection-string>")
        print("\nAllowed values: neon, local (local blocked for migrations), test")
        print("=" * 60 + "\n")
        raise RuntimeError("DB_AUTHORITY must be set (neon|local|test)")

    # Rule 2: Only 'neon' allowed for migrations
    if db_authority not in ("neon", "local", "test"):
        raise RuntimeError(f"DB_AUTHORITY={db_authority} is not valid. Use: neon|local|test")

    if db_authority != "neon":
        print("\n" + "=" * 60)
        print("DB AUTHORITY GATE: BLOCKED")
        print("=" * 60)
        print(f"\nDB_AUTHORITY={db_authority}")
        print("\nMigrations are only allowed against authoritative database (neon).")
        print("Local and test databases are for development, not migrations.")
        print("\nTo run migrations:")
        print("  export DB_AUTHORITY=neon")
        print("  export DATABASE_URL=<your-neon-connection-string>")
        print("=" * 60 + "\n")
        raise RuntimeError(
            f"Alembic blocked: DB_AUTHORITY={db_authority} is not allowed for migrations. "
            "Only DB_AUTHORITY=neon is permitted."
        )

    # Rule 3: DATABASE_URL must match authority
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set when DB_AUTHORITY=neon")

    # Verify it's actually a Neon URL
    url_lower = database_url.lower()
    is_neon = "neon" in url_lower or "neon.tech" in url_lower
    is_local = "localhost" in url_lower or "127.0.0.1" in url_lower or ":5432" in url_lower or ":5433" in url_lower

    if is_local:
        print("\n" + "=" * 60)
        print("DB AUTHORITY GATE: BLOCKED")
        print("=" * 60)
        print(f"\nDB_AUTHORITY=neon but DATABASE_URL points to localhost:")
        print(f"  {database_url[:60]}...")
        print("\nAuthority mismatch. Set correct DATABASE_URL for Neon.")
        print("=" * 60 + "\n")
        raise RuntimeError(
            "DB_AUTHORITY=neon but DATABASE_URL contains localhost. "
            "Authority and URL must match."
        )

    if not is_neon:
        print("\n" + "=" * 60)
        print("DB AUTHORITY GATE: WARNING")
        print("=" * 60)
        print(f"\nDB_AUTHORITY=neon but DATABASE_URL doesn't contain 'neon':")
        print(f"  {database_url[:60]}...")
        print("\nProceeding, but verify this is the correct authoritative database.")
        print("=" * 60 + "\n")

    # Log authority for visibility
    print("\n" + "=" * 60)
    print("MIGRATION AUTHORITY CONFIRMED")
    print("=" * 60)
    print(f"  DB_AUTHORITY = {db_authority}")
    # Mask password in URL for logging
    masked_url = database_url
    if "@" in database_url:
        parts = database_url.split("@")
        prefix = parts[0].rsplit(":", 1)[0]  # Remove password
        masked_url = f"{prefix}:****@{parts[1]}"
    print(f"  DATABASE_URL = {masked_url[:70]}...")
    print("=" * 60 + "\n")

    return db_authority, database_url


# Validate authority BEFORE any migration work
db_authority, database_url = validate_db_authority()


# Import all models to ensure they're registered

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from validated environment
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = SQLModel.metadata


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
        version_table_pk=False,
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
            connection=connection,
            target_metadata=target_metadata,
            version_table_pk=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
