# capability_id: CAP-001
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: SQLModel query helpers to prevent Row tuple extraction bugs
# Callers: All DB-accessing code
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Core Infrastructure

"""Database Query Helpers - Prevent SQLModel Row Tuple Issues

SQLModel's session.exec() returns Row tuples, not model instances directly.
These helpers ensure consistent extraction patterns across the codebase.

Usage:
    from app.db_helpers import query_one, query_all, query_scalar

    # Instead of: row = session.exec(stmt).first(); obj = row[0] if row else None
    obj = query_one(session, stmt)

    # Instead of: objs = [r[0] for r in session.exec(stmt).all()]
    objs = query_all(session, stmt)

    # Instead of: result = session.exec(count_query).one()[0]
    count = query_scalar(session, count_query)
"""

from typing import Any, List, Optional, TypeVar

from sqlmodel import Session

T = TypeVar("T")


def query_one(session: Session, stmt) -> Optional[Any]:
    """
    Execute query and return single model instance or None.

    Safely extracts from SQLModel Row tuple.

    Example:
        stmt = select(User).where(User.id == user_id)
        user = query_one(session, stmt)
    """
    row = session.exec(stmt).first()
    return row[0] if row else None


def query_all(session: Session, stmt) -> List[Any]:
    """
    Execute query and return list of model instances.

    Safely extracts from SQLModel Row tuples.

    Example:
        stmt = select(User).where(User.is_active == True)
        users = query_all(session, stmt)
    """
    rows = session.exec(stmt).all()
    return [r[0] for r in rows]


def query_scalar(session: Session, stmt) -> Any:
    """
    Execute query and return scalar value (for COUNT, SUM, etc).

    Safely extracts from SQLModel Row tuple.

    Example:
        stmt = select(func.count(User.id))
        count = query_scalar(session, stmt)
    """
    result = session.exec(stmt).one()
    return result[0] if result else None


def query_exists(session: Session, stmt) -> bool:
    """
    Check if any rows match the query.

    Example:
        stmt = select(User).where(User.email == email)
        exists = query_exists(session, stmt)
    """
    row = session.exec(stmt).first()
    return row is not None
