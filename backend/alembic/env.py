"""Alembic environment configuration for AOS."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import text
from sqlalchemy import engine_from_config, pool

# Import SQLModel metadata
from sqlmodel import SQLModel

from alembic import context


# =============================================================================
# DB ROLE GATE (MANDATORY)
# Reference: docs/architecture/ENVIRONMENT_CONTRACT.md
#
# Governance Model:
#   - DB_ROLE determines migration eligibility, not DB_AUTHORITY
#   - staging: local/CI rehearsal, migrations allowed
#   - prod: production canonical, migrations require confirmation
#   - replica: read-only, migrations blocked
#
# Mapping:
#   Local (DB_AUTHORITY=local) → DB_ROLE=staging
#   Neon (DB_AUTHORITY=neon)   → DB_ROLE=prod
# =============================================================================

def validate_db_authority() -> tuple[str, str]:
    """
    Validate database role and authority before any migration runs.

    Rules:
    - DB_ROLE must be explicitly set (staging, prod, replica)
    - Only 'staging' and 'prod' roles allow migrations
    - 'prod' role requires CONFIRM_PROD_MIGRATIONS=true
    - 'replica' role always blocked
    - DATABASE_URL must be set

    Returns:
        Tuple of (db_authority, database_url)

    Raises:
        RuntimeError if validation fails
    """
    db_authority = os.getenv("DB_AUTHORITY", "")
    db_role = os.getenv("DB_ROLE", "")
    database_url = os.getenv("DATABASE_URL", "")
    confirm_prod = os.getenv("CONFIRM_PROD_MIGRATIONS", "").lower() == "true"

    # Rule 1: DB_ROLE must be declared
    if not db_role:
        print("\n" + "=" * 60)
        print("DB ROLE GATE: BLOCKED")
        print("=" * 60)
        print("\nDB_ROLE environment variable is not set.")
        print("\nMigrations are governed by DB_ROLE, not just DB_AUTHORITY.")
        print("\nDatabase Roles:")
        print("  staging - Pre-prod/local/CI authority (migrations allowed)")
        print("  prod    - Production canonical (migrations require confirmation)")
        print("  replica - Read-only/analytics (migrations blocked)")
        print("\nExample for local staging:")
        print("  export DB_AUTHORITY=local")
        print("  export DB_ROLE=staging")
        print("  export DATABASE_URL=postgresql://...")
        print("\nExample for production:")
        print("  export DB_AUTHORITY=neon")
        print("  export DB_ROLE=prod")
        print("  export CONFIRM_PROD_MIGRATIONS=true")
        print("  export DATABASE_URL=postgresql://...neon.tech/...")
        print("=" * 60 + "\n")
        raise RuntimeError("DB_ROLE must be set (staging|prod|replica)")

    # Rule 2: Validate DB_ROLE values
    valid_roles = ("staging", "prod", "replica")
    if db_role not in valid_roles:
        raise RuntimeError(f"DB_ROLE={db_role} is not valid. Use: staging|prod|replica")

    # Rule 3: replica is always blocked
    if db_role == "replica":
        print("\n" + "=" * 60)
        print("DB ROLE GATE: BLOCKED")
        print("=" * 60)
        print(f"\nDB_ROLE={db_role}")
        print("\nReplica databases are read-only. Migrations are not allowed.")
        print("=" * 60 + "\n")
        raise RuntimeError("DB_ROLE=replica does not allow migrations (read-only)")

    # Rule 4: prod requires explicit confirmation
    if db_role == "prod" and not confirm_prod:
        print("\n" + "=" * 60)
        print("DB ROLE GATE: BLOCKED (Production Safety)")
        print("=" * 60)
        print(f"\nDB_ROLE={db_role}")
        print("\nProduction migrations require explicit confirmation.")
        print("\nTo proceed:")
        print("  export CONFIRM_PROD_MIGRATIONS=true")
        print("\nThis is a safety measure to prevent accidental prod migrations.")
        print("=" * 60 + "\n")
        raise RuntimeError(
            "DB_ROLE=prod requires CONFIRM_PROD_MIGRATIONS=true for safety"
        )

    # Rule 5: DATABASE_URL must be set
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set for migrations")

    # Optional: Validate authority-URL consistency (warning only)
    url_lower = database_url.lower()
    is_neon = "neon" in url_lower or "neon.tech" in url_lower
    is_local = "localhost" in url_lower or "127.0.0.1" in url_lower or ":5432" in url_lower or ":5433" in url_lower

    # Warn on mismatches (but don't block - trust DB_ROLE)
    if db_role == "prod" and is_local:
        print("\n" + "=" * 60)
        print("DB ROLE GATE: WARNING")
        print("=" * 60)
        print(f"\nDB_ROLE=prod but DATABASE_URL points to localhost.")
        print("Verify this is intentional (e.g., local prod mirror).")
        print("=" * 60 + "\n")

    if db_role == "staging" and is_neon:
        print("\n" + "=" * 60)
        print("DB ROLE GATE: WARNING")
        print("=" * 60)
        print(f"\nDB_ROLE=staging but DATABASE_URL points to Neon.")
        print("If this is production Neon, use DB_ROLE=prod instead.")
        print("=" * 60 + "\n")

    # Log authority for visibility
    print("\n" + "=" * 60)
    print("MIGRATION AUTHORITY CONFIRMED")
    print("=" * 60)
    print(f"  DB_AUTHORITY = {db_authority or '(not set)'}")
    print(f"  DB_ROLE      = {db_role}")
    if db_role == "prod":
        print(f"  CONFIRM_PROD = {confirm_prod}")
    # Mask password in URL for logging
    masked_url = database_url
    if "@" in database_url:
        parts = database_url.split("@")
        prefix = parts[0].rsplit(":", 1)[0]  # Remove password
        masked_url = f"{prefix}:****@{parts[1]}"
    print(f"  DATABASE_URL = {masked_url[:70]}...")
    print("=" * 60 + "\n")

    return db_authority or db_role, database_url


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


def _ensure_alembic_version_column_width(connection) -> None:
    """
    Alembic's default version table uses String(32). This repo uses descriptive
    revision identifiers (e.g. '093_llm_run_records_system_records') that can
    exceed 32 characters, which will hard-fail on version updates.

    Fix: ensure the version table exists and widen `version_num` to a safe size
    before Alembic attempts to update it.
    """
    connection.execute(
        text(
            "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(128) NOT NULL)"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"
        )
    )


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
        _ensure_alembic_version_column_width(connection)
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
