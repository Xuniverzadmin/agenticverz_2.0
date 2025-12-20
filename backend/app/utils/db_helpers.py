"""Database helper functions for SQLModel row extraction.

PIN-099: SQLModel Row Extraction Patterns

This module provides helper functions to safely extract values from
SQLModel/SQLAlchemy query results, avoiding common anti-patterns that
cause runtime errors.

Common Issues Prevented:
1. Row objects are truthy even when containing 0/None
2. Row objects don't support direct comparison operators
3. Row objects from .all() are not Python tuples

Usage:
    from app.utils.db_helpers import scalar_or_default, extract_model

    # For scalar queries (COUNT, SUM, AVG, etc.)
    row = session.exec(select(func.count(Model.id))).first()
    count = scalar_or_default(row, default=0)

    # For model queries with potential Row wrapping
    results = session.exec(stmt).all()
    for row in results:
        model = extract_model(row, 'id')
"""
from typing import Any, List, Optional, TypeVar

T = TypeVar("T")


def scalar_or_default(row: Optional[Any], default: Any = 0) -> Any:
    """Extract scalar value from Row or return default.

    SQLModel's session.exec(stmt).first() returns a Row object for scalar
    queries (like func.count, func.sum). This function safely extracts
    the scalar value.

    Args:
        row: The Row object from .first(), or None if no results
        default: Value to return if row is None or contains None

    Returns:
        The scalar value from row[0], or default if unavailable

    Example:
        stmt = select(func.count(Incident.id)).where(...)
        row = session.exec(stmt).first()
        count = scalar_or_default(row, 0)  # Returns int, not Row
    """
    if row is None:
        return default
    try:
        value = row[0]
        return value if value is not None else default
    except (TypeError, IndexError):
        # row might be a scalar already in some edge cases
        return row if row is not None else default


def scalar_or_none(row: Optional[Any]) -> Optional[Any]:
    """Extract scalar value from Row, returning None if unavailable.

    Similar to scalar_or_default but returns None instead of a default.

    Args:
        row: The Row object from .first(), or None

    Returns:
        The scalar value from row[0], or None

    Example:
        stmt = select(func.max(Run.ended_at)).where(...)
        row = session.exec(stmt).first()
        last_time = scalar_or_none(row)  # Returns datetime or None
    """
    if row is None:
        return None
    try:
        return row[0]
    except (TypeError, IndexError):
        return row


def extract_model(row: Any, model_attr: str = "id") -> Any:
    """Extract model instance from Row or return as-is.

    When using session.exec(stmt).all(), results may be:
    1. Model instances directly (single model select)
    2. Row objects (joins, expressions, order_by with expressions)

    This function detects which case and extracts appropriately.

    Args:
        row: A result from .all() iteration
        model_attr: An attribute that exists on the model (for detection)

    Returns:
        The model instance, extracted from Row if necessary

    Example:
        for row in session.exec(select(Incident).order_by(...)).all():
            incident = extract_model(row, 'tenant_id')
            print(incident.title)
    """
    # If row has the model attribute, it's already the model
    if hasattr(row, model_attr):
        return row

    # If row is indexable (Row object), extract first element
    if hasattr(row, "__getitem__"):
        try:
            return row[0]
        except (TypeError, IndexError):
            return row

    # Fallback: return as-is
    return row


def extract_models(results: List[Any], model_attr: str = "id") -> List[Any]:
    """Extract model instances from a list of results.

    Convenience wrapper around extract_model for processing .all() results.

    Args:
        results: List from session.exec(stmt).all()
        model_attr: An attribute that exists on the model

    Returns:
        List of extracted model instances

    Example:
        results = session.exec(select(Tenant).order_by(...)).all()
        tenants = extract_models(results, 'tenant_id')
    """
    return [extract_model(row, model_attr) for row in results]


# Type-safe versions for common cases
def count_or_zero(row: Optional[Any]) -> int:
    """Extract count value, guaranteed to return int."""
    result = scalar_or_default(row, 0)
    return int(result) if result is not None else 0


def sum_or_zero(row: Optional[Any]) -> float:
    """Extract sum value, guaranteed to return numeric."""
    result = scalar_or_default(row, 0)
    return float(result) if result is not None else 0.0
