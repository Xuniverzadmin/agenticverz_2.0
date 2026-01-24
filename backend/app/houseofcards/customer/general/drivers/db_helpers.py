# Layer: L5 — Domain Engine (Utility)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Database row extraction utilities (pure computation on Row objects)
# Callers: services, drivers
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB Session)
# Reference: Core Infrastructure
# NOTE: Reclassified L6→L5 (2026-01-24) - Operates on Row objects passed in, no Session imports

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


# =============================================================================
# Enhanced Helpers (v2.0) - Added from M24 RCA (PIN-118)
# =============================================================================


def query_one(
    session: Any,
    statement: Any,
    model_class: Optional[type] = None,
) -> Optional[Any]:
    """
    Safe single-row query with automatic Row/Model detection.

    Handles SQLModel version differences where .first() may return:
    - Row tuple (needs [0] extraction)
    - Model directly (no extraction needed)

    Args:
        session: SQLModel Session
        statement: Select statement
        model_class: Optional model class for isinstance check

    Returns:
        Model instance or None

    Example:
        user = query_one(session, select(User).where(User.email == email), User)
    """
    result = session.exec(statement).first()
    if result is None:
        return None

    # Check if it's already the model
    if model_class and isinstance(result, model_class):
        return result

    # Check for model attributes (duck typing)
    if hasattr(result, "id") or hasattr(result, "__table__"):
        return result

    # Try to extract from Row tuple
    try:
        extracted = result[0]
        if model_class and isinstance(extracted, model_class):
            return extracted
        return extracted
    except (TypeError, IndexError):
        return result


def query_all(
    session: Any,
    statement: Any,
    model_class: Optional[type] = None,
) -> list:
    """
    Safe multi-row query with automatic Row/Model detection.

    Handles SQLModel version differences where .all() may return:
    - List of Row tuples (needs [0] extraction)
    - List of Models directly (no extraction needed)

    Args:
        session: SQLModel Session
        statement: Select statement
        model_class: Optional model class for isinstance check

    Returns:
        List of model instances

    Example:
        users = query_all(session, select(User).where(User.status == 'active'), User)
    """
    results = session.exec(statement).all()
    if not results:
        return []

    # Check first item to determine extraction strategy
    first = results[0]

    if model_class and isinstance(first, model_class):
        return list(results)

    if hasattr(first, "id") or hasattr(first, "__table__"):
        return list(results)

    # Try to extract from Row tuples
    try:
        extracted = [r[0] for r in results]
        return extracted
    except (TypeError, IndexError):
        return list(results)


def model_to_dict(model: Any, include: Optional[list] = None, exclude: Optional[list] = None) -> dict:
    """
    Convert ORM model to dict to prevent DetachedInstanceError.

    Call this BEFORE the session closes to extract values safely.

    Args:
        model: ORM model instance
        include: List of attributes to include (None = all)
        exclude: List of attributes to exclude

    Returns:
        Dictionary with model values

    Example:
        with Session(engine) as session:
            user = session.get(User, user_id)
            user_data = model_to_dict(user, exclude=['password_hash'])
        # user_data is safe to use after session closes
        return user_data
    """
    if model is None:
        return {}

    exclude = exclude or []
    exclude.extend(["_sa_instance_state", "registry", "metadata"])

    result = {}

    # Get attributes from model
    if hasattr(model, "__table__"):
        # SQLModel/SQLAlchemy model
        for column in model.__table__.columns:
            key = column.name
            if include and key not in include:
                continue
            if key in exclude:
                continue
            try:
                value = getattr(model, key, None)
                # Handle datetime serialization
                if hasattr(value, "isoformat"):
                    assert value is not None
                    value = value.isoformat()
                result[key] = value
            except Exception:
                pass
    elif hasattr(model, "__dict__"):
        # Regular object
        for key, value in model.__dict__.items():
            if key.startswith("_"):
                continue
            if include and key not in include:
                continue
            if key in exclude:
                continue
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            result[key] = value

    return result


def models_to_dicts(models: list, include: Optional[list] = None, exclude: Optional[list] = None) -> list:
    """
    Convert list of ORM models to list of dicts.

    Args:
        models: List of ORM model instances
        include: List of attributes to include
        exclude: List of attributes to exclude

    Returns:
        List of dictionaries
    """
    return [model_to_dict(m, include, exclude) for m in models]


def safe_get(
    session: Any,
    model_class: type,
    id: Any,
    to_dict: bool = False,
    include: Optional[list] = None,
    exclude: Optional[list] = None,
) -> Any:
    """
    Safe session.get() wrapper with optional dict conversion.

    Use session.get() for direct ID lookups - it's simpler and always
    returns the model directly (not a Row tuple).

    Args:
        session: SQLModel Session
        model_class: Model class to query
        id: Primary key value
        to_dict: If True, convert to dict before returning
        include: Attributes to include in dict
        exclude: Attributes to exclude from dict

    Returns:
        Model instance, dict, or None

    Example:
        # Simple get
        user = safe_get(session, User, user_id)

        # Get as dict (safe after session closes)
        user_data = safe_get(session, User, user_id, to_dict=True)
    """
    model = session.get(model_class, id)
    if model is None:
        return None

    if to_dict:
        return model_to_dict(model, include, exclude)

    return model


def get_or_create(
    session: Any,
    model_class: type,
    defaults: Optional[dict] = None,
    **kwargs,
) -> tuple:
    """
    Get existing model or create new one.

    Similar to Django's get_or_create, but with proper SQLModel handling.

    Args:
        session: SQLModel Session
        model_class: Model class
        defaults: Dict of fields to set on creation only
        **kwargs: Fields to filter by

    Returns:
        Tuple of (instance, created: bool)

    Example:
        user, created = get_or_create(
            session, User,
            defaults={'status': 'active'},
            email='test@example.com'
        )
    """
    from sqlmodel import select

    # Build filter conditions
    statement = select(model_class)
    for key, value in kwargs.items():
        statement = statement.where(getattr(model_class, key) == value)

    instance = query_one(session, statement, model_class)

    if instance:
        return instance, False

    # Create new instance
    create_kwargs = {**kwargs}
    if defaults:
        create_kwargs.update(defaults)

    instance = model_class(**create_kwargs)
    session.add(instance)
    session.commit()
    session.refresh(instance)

    return instance, True
