# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Schema parity checking utilities
# Callers: SDK, API
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Schema Parity

"""
M26 Prevention Mechanism #2: Startup Schema Parity Guard
=========================================================

INVARIANT: SQLModel metadata must match live DB schema exactly.
If not → hard crash on boot.

Why hard-fail?
Because cost integrity errors are worse than downtime.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)


class SchemaParityError(Exception):
    """Raised when model schema doesn't match database schema."""

    pass


def check_schema_parity(
    engine: Engine,
    models: Optional[List[type]] = None,
    hard_fail: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Check that SQLModel definitions match actual database schema.

    Args:
        engine: SQLAlchemy engine
        models: List of SQLModel classes to check (default: all with __tablename__)
        hard_fail: If True, raise exception on mismatch

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []

    if models is None:
        # Get all SQLModel subclasses with table=True
        models = [cls for cls in SQLModel.__subclasses__() if hasattr(cls, "__tablename__") and cls.__tablename__]

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for model in models:
        table_name = model.__tablename__

        # Check table exists
        if table_name not in existing_tables:
            errors.append(f"TABLE_MISSING: {table_name} defined in model but not in database")
            continue

        # Get model columns
        model_columns = {}
        for column_name, column_info in model.__fields__.items():
            # Handle sa_column override
            if hasattr(column_info, "sa_column") and column_info.sa_column is not None:
                db_column_name = column_info.sa_column.name
            else:
                db_column_name = column_name
            model_columns[db_column_name] = column_info

        # Get database columns
        db_columns = {col["name"]: col for col in inspector.get_columns(table_name)}

        # Check for missing columns in database
        for col_name in model_columns:
            if col_name not in db_columns:
                errors.append(f"COLUMN_MISSING: {table_name}.{col_name} defined in model but not in database")

        # Check for extra columns in database (warning only)
        for col_name in db_columns:
            if col_name not in model_columns:
                logger.warning(f"COLUMN_EXTRA: {table_name}.{col_name} exists in database but not in model")

    is_valid = len(errors) == 0

    if not is_valid:
        error_msg = "Schema parity check FAILED:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)

        if hard_fail:
            raise SchemaParityError(error_msg)

    return is_valid, errors


def check_m26_cost_tables(engine: Engine) -> Tuple[bool, List[str]]:
    """
    Specific check for M26 cost tables - the most critical.

    These tables MUST match exactly:
    - feature_tags
    - cost_records
    - cost_anomalies
    - cost_budgets
    - cost_daily_aggregates
    """
    from app.db import (
        CostAnomaly,
        CostBudget,
        CostDailyAggregate,
        CostRecord,
        FeatureTag,
    )

    return check_schema_parity(
        engine,
        models=[FeatureTag, CostRecord, CostAnomaly, CostBudget, CostDailyAggregate],
        hard_fail=True,
    )


def run_startup_parity_check(engine: Engine) -> None:
    """
    Run full schema parity check on startup.
    Call this from main.py before accepting requests.
    """
    logger.info("Running M26 schema parity check...")

    # First check critical M26 tables
    try:
        check_m26_cost_tables(engine)
        logger.info("M26 cost tables: schema parity OK")
    except SchemaParityError as e:
        logger.critical(f"M26 cost tables: SCHEMA MISMATCH - {e}")
        raise

    # Then check all other tables (non-fatal for now)
    try:
        is_valid, errors = check_schema_parity(engine, hard_fail=False)
        if not is_valid:
            logger.warning(f"Schema drift detected in {len(errors)} tables (non-critical)")
    except Exception as e:
        logger.warning(f"Full schema check failed: {e}")

    logger.info("Schema parity check complete")
