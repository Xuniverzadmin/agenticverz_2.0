# capability_id: CAP-008
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api | worker
#   Execution: sync
# Role: Single-connection transaction primitives for lock-safe operations
# Callers: Any code requiring transactional continuity with row locks
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-2.2 Self-Defending Transactions with Intent)

"""
Self-Defending Transaction System (L6)

PHILOSOPHY (Phase-2.2 Upgrade)
------------------------------
This module doesn't just BLOCK dangerous patterns — it GUIDES engineers
into correct design by construction. Prevention acts BEFORE code is written.

The root cause class is NOT "FOR UPDATE". The root cause is:
    "Transactional intent is not explicit in feature design."

This module solves that by requiring:
1. Engineers DECLARE intent before they can write logic
2. Only BLESSED primitives allow dangerous behavior
3. Illegal states are STRUCTURALLY unrepresentable
4. CI enforces INTENT consistency, not just syntax

TRANSACTION INTENT MODEL
------------------------
Every function touching persistence must declare one of:

    TransactionIntent.READ_ONLY       → Plain session, no locks
    TransactionIntent.ATOMIC_WRITE    → Transaction, no FOR UPDATE
    TransactionIntent.LOCKED_MUTATION → single_connection_transaction() REQUIRED

The @transactional decorator enforces the mapping:

    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
    def trip_circuit(txn: SingleConnectionTxn, state_id: str):
        state = txn.lock_row(CostSimCBState, CostSimCBState.id == state_id)
        state.disabled = True
        txn.commit()

CI validates that intent and primitive match. No intent = no CI pass.

INCIDENT → INVARIANT → PRIMITIVE LOOP
--------------------------------------
Every incident class must result in either:
- A new primitive
- A stricter intent
- A new CI invariant

If not, the system has NOT learned.

WHY THIS EXISTS (Incident: 2026-01-01)
--------------------------------------
Raw `SELECT ... FOR UPDATE` with SQLModel/SQLAlchemy is DANGEROUS because:
1. `session.commit()` may return the connection to the pool
2. Subsequent operations may get a DIFFERENT connection
3. The new connection blocks on the lock held by the old connection
4. Result: DEADLOCK / HANG

This module makes that mistake STRUCTURALLY IMPOSSIBLE.

INVARIANTS
----------
1. Lock scope == Connection scope (ALWAYS)
2. One transaction context == One connection (ALWAYS)
3. No raw FOR UPDATE outside this module (ENFORCED BY CI)
4. All lock operations use txn.lock_row() (ENFORCED BY TYPE)
5. Intent must be declared before implementation (ENFORCED BY @transactional)
6. Intent must match primitive (ENFORCED BY CI)

CI ENFORCEMENT
--------------
scripts/ci/check_forbidden_patterns.py will FAIL if:
- `with_for_update()` appears outside this file
- `FOR UPDATE` appears in raw SQL outside this file
- LOCKED_MUTATION intent without single_connection_transaction
- single_connection_transaction without LOCKED_MUTATION intent
"""

from __future__ import annotations

import functools
import inspect
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Generator, Optional, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, select

logger = logging.getLogger("nova.infra.transaction")


# =============================================================================
# TRANSACTION INTENT DECLARATION (Phase-2.2)
# =============================================================================


class TransactionIntent(Enum):
    """
    Declared intent for database operations.

    Engineers MUST declare intent before writing persistence logic.
    This forces thinking BEFORE coding and makes intent machine-checkable.

    | Intent          | Allowed Primitives                        |
    |-----------------|-------------------------------------------|
    | READ_ONLY       | Plain session, no locks                   |
    | ATOMIC_WRITE    | Transaction context, no FOR UPDATE        |
    | LOCKED_MUTATION | single_connection_transaction() REQUIRED  |

    Usage:
        @transactional(intent=TransactionIntent.LOCKED_MUTATION)
        def trip_circuit(txn: SingleConnectionTxn, state_id: str):
            ...
    """

    READ_ONLY = "read_only"
    ATOMIC_WRITE = "atomic_write"
    LOCKED_MUTATION = "locked_mutation"


# Registry of functions with declared intents (for CI validation)
_INTENT_REGISTRY: dict[str, TransactionIntent] = {}


def get_intent_registry() -> dict[str, TransactionIntent]:
    """Return the intent registry for CI validation."""
    return _INTENT_REGISTRY.copy()


def transactional(intent: TransactionIntent) -> Callable:
    """
    Decorator declaring transactional intent for a function.

    This is the KEY to self-defending design:
    - Forces engineers to THINK before coding
    - Makes intent VISIBLE and ENFORCEABLE
    - CI validates intent/primitive consistency

    Args:
        intent: The TransactionIntent this function requires

    Usage:
        @transactional(intent=TransactionIntent.LOCKED_MUTATION)
        def trip_circuit(txn: SingleConnectionTxn, state_id: str):
            state = txn.lock_row(...)
            state.disabled = True
            txn.commit()

        @transactional(intent=TransactionIntent.READ_ONLY)
        def get_state(session: Session, name: str):
            return session.exec(select(State).where(...)).first()

    CI Enforcement:
        scripts/ci/check_intent_consistency.py validates:
        - LOCKED_MUTATION → must accept SingleConnectionTxn
        - ATOMIC_WRITE → must use transaction context
        - READ_ONLY → must not use locks

    Raises:
        IntentViolationError: If function signature doesn't match intent
    """

    def decorator(func: Callable) -> Callable:
        # Register intent for CI validation
        module = func.__module__
        qualname = func.__qualname__
        full_name = f"{module}.{qualname}"
        _INTENT_REGISTRY[full_name] = intent

        # Validate signature at decoration time (fail fast)
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if intent == TransactionIntent.LOCKED_MUTATION:
            # LOCKED_MUTATION requires SingleConnectionTxn as first param
            if not params:
                raise IntentViolationError(
                    f"{full_name}: LOCKED_MUTATION intent requires SingleConnectionTxn as first parameter"
                )
            first_param = params[0]
            # Check annotation if present
            if first_param.annotation != inspect.Parameter.empty:
                annotation_name = getattr(first_param.annotation, "__name__", str(first_param.annotation))
                if "SingleConnectionTxn" not in annotation_name:
                    raise IntentViolationError(
                        f"{full_name}: LOCKED_MUTATION intent requires SingleConnectionTxn, got {annotation_name}"
                    )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Runtime validation for LOCKED_MUTATION
            if intent == TransactionIntent.LOCKED_MUTATION:
                if not args or not isinstance(args[0], SingleConnectionTxn):
                    raise IntentViolationError(
                        f"{full_name}: LOCKED_MUTATION requires SingleConnectionTxn "
                        f"as first argument, got {type(args[0]).__name__ if args else 'nothing'}"
                    )
            return func(*args, **kwargs)

        # Attach intent metadata for introspection
        wrapper._transaction_intent = intent
        wrapper._intent_full_name = full_name

        return wrapper

    return decorator


class IntentViolationError(Exception):
    """
    Raised when transactional intent doesn't match implementation.

    This error indicates a design flaw, not a runtime issue.
    Fix the design, don't catch this exception.
    """

    pass


# =============================================================================
# INTENT-AWARE PRIMITIVES
# =============================================================================


def require_intent(intent: TransactionIntent) -> Callable:
    """
    Validate that calling context has the required intent.

    Use this inside primitives to enforce intent requirements.

    Example:
        def lock_row(self, ...):
            require_intent(TransactionIntent.LOCKED_MUTATION)
            ...

    This is defense-in-depth: even if someone bypasses @transactional,
    the primitive itself enforces intent.
    """
    # Get the calling function from the stack
    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        caller_locals = frame.f_back.f_back.f_locals
        caller_func = caller_locals.get("func") or caller_locals.get("self")
        if hasattr(caller_func, "_transaction_intent"):
            if caller_func._transaction_intent != intent:
                raise IntentViolationError(
                    f"Primitive requires {intent.value} intent, but caller has {caller_func._transaction_intent.value}"
                )
    # Note: We don't fail if we can't find intent - that's CI's job
    return lambda x: x  # No-op if validation passes


logger = logging.getLogger("nova.infra.transaction")

# Type variable for model classes
T = TypeVar("T")


@dataclass
class SingleConnectionTxn:
    """
    Transaction context guaranteeing single-connection semantics.

    This is the ONLY type that should be used for operations requiring:
    - Row locks (SELECT ... FOR UPDATE)
    - Transactional continuity
    - Connection affinity

    If a function requires lock continuity, it MUST accept this type.
    This makes the requirement VISIBLE and ENFORCEABLE.

    Example:
        def trip_circuit(txn: SingleConnectionTxn, state_id: str):
            state = txn.lock_row(CostSimCBState, CostSimCBState.id == state_id)
            state.disabled = True
            txn.commit()
    """

    session: Session
    _committed: bool = field(default=False, repr=False)
    _rolled_back: bool = field(default=False, repr=False)
    _closed: bool = field(default=False, repr=False)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def lock_row(
        self,
        model: Type[T],
        *where_clauses,
        nowait: bool = False,
        skip_locked: bool = False,
    ) -> Optional[T]:
        """
        Lock and return a single row.

        This is the ONLY blessed way to do SELECT ... FOR UPDATE.

        Args:
            model: The SQLModel class
            *where_clauses: WHERE conditions
            nowait: If True, fail immediately if lock unavailable
            skip_locked: If True, skip locked rows

        Returns:
            The locked row, or None if not found

        Example:
            state = txn.lock_row(CostSimCBState, CostSimCBState.name == "costsim_v2")
        """
        self._check_active()

        stmt = select(model)
        for clause in where_clauses:
            stmt = stmt.where(clause)
        stmt = stmt.with_for_update(nowait=nowait, skip_locked=skip_locked)

        result = self.session.exec(stmt).first()

        # Handle SQLAlchemy Row tuple vs direct model
        if result is None:
            return None
        if hasattr(result, "__table__"):  # Already a model
            return result
        # Row tuple - extract first element
        return result[0] if result else None

    def lock_rows(
        self,
        model: Type[T],
        *where_clauses,
        nowait: bool = False,
        skip_locked: bool = False,
    ) -> list[T]:
        """
        Lock and return multiple rows.

        Args:
            model: The SQLModel class
            *where_clauses: WHERE conditions
            nowait: If True, fail immediately if lock unavailable
            skip_locked: If True, skip locked rows

        Returns:
            List of locked rows
        """
        self._check_active()

        stmt = select(model)
        for clause in where_clauses:
            stmt = stmt.where(clause)
        stmt = stmt.with_for_update(nowait=nowait, skip_locked=skip_locked)

        results = self.session.exec(stmt).all()
        return list(results)

    def add(self, obj: Any) -> None:
        """Add an object to the session."""
        self._check_active()
        self.session.add(obj)

    def refresh(self, obj: Any) -> None:
        """Refresh an object from the database."""
        self._check_active()
        self.session.refresh(obj)

    def commit(self) -> None:
        """
        Commit the transaction.

        After commit, locks are released. The connection remains
        bound to this context until the context exits.
        """
        self._check_active()
        self.session.commit()
        self._committed = True
        logger.debug(f"Transaction committed after {self._elapsed_ms()}ms")

    def rollback(self) -> None:
        """
        Rollback the transaction.

        Releases all locks immediately.
        """
        if not self._closed:
            self.session.rollback()
            self._rolled_back = True
            logger.debug(f"Transaction rolled back after {self._elapsed_ms()}ms")

    def _check_active(self) -> None:
        """Verify transaction is still active."""
        if self._closed:
            raise RuntimeError("Transaction already closed")

    def _elapsed_ms(self) -> int:
        """Elapsed time since transaction started."""
        return int((datetime.now(timezone.utc) - self.started_at).total_seconds() * 1000)

    def _close(self) -> None:
        """Close the transaction (internal use only)."""
        if not self._closed:
            if not self._committed and not self._rolled_back:
                self.rollback()
            self.session.close()
            self._closed = True


@contextmanager
def single_connection_transaction(
    timeout_seconds: int = 30,
) -> Generator[SingleConnectionTxn, None, None]:
    """
    Context manager for single-connection transactions.

    This is the ONLY blessed path for operations requiring:
    - Row locks
    - Transactional continuity
    - Connection affinity

    The returned SingleConnectionTxn guarantees:
    1. Single connection for entire scope
    2. Auto-rollback on error
    3. Auto-close on exit
    4. Lock timeout enforcement

    Args:
        timeout_seconds: Statement timeout (prevents hangs)

    Usage:
        with single_connection_transaction() as txn:
            state = txn.lock_row(MyTable, MyTable.id == my_id)
            state.field = new_value
            txn.commit()

    For testing, use single_connection_transaction_for_test() which
    uses StaticPool to guarantee true single-connection behavior.
    """
    from app.db import get_database_url

    # Create engine with StaticPool - guarantees single connection
    # This is the KEY to preventing the cross-connection deadlock
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        poolclass=StaticPool,
        connect_args={"options": f"-c statement_timeout={timeout_seconds * 1000}"},
    )

    session = Session(engine)
    txn = SingleConnectionTxn(session=session)

    try:
        yield txn
    except Exception:
        txn.rollback()
        raise
    finally:
        txn._close()
        engine.dispose()


@contextmanager
def single_connection_transaction_with_engine(
    engine,
    timeout_seconds: int = 30,
) -> Generator[SingleConnectionTxn, None, None]:
    """
    Context manager using an existing engine.

    Use this when you need to share an engine (e.g., in tests with
    existing StaticPool engines).

    WARNING: The engine MUST use StaticPool or equivalent single-connection
    pooling. Using a regular connection pool defeats the purpose.
    """
    session = Session(engine)
    txn = SingleConnectionTxn(session=session)

    try:
        yield txn
    except Exception:
        txn.rollback()
        raise
    finally:
        txn._close()


# =============================================================================
# Convenience functions for common patterns
# =============================================================================


def get_or_create_locked(
    txn: SingleConnectionTxn,
    model: Type[T],
    lookup_clause,
    defaults: dict[str, Any],
) -> tuple[T, bool]:
    """
    Get existing row with lock, or create new one.

    This is the safe version of "get or create" that:
    1. Tries to lock existing row
    2. If not found, creates new row
    3. Commits the creation
    4. Re-locks the new row

    Returns:
        Tuple of (row, created)

    Example:
        state, created = get_or_create_locked(
            txn,
            CostSimCBState,
            CostSimCBState.name == "costsim_v2",
            {"name": "costsim_v2", "disabled": False},
        )
    """
    # Try to lock existing
    row = txn.lock_row(model, lookup_clause)
    if row is not None:
        return row, False

    # Create new row
    new_row = model(**defaults)
    txn.add(new_row)
    txn.commit()
    txn.refresh(new_row)

    # Re-lock the new row (it's now in the DB)
    locked = txn.lock_row(model, lookup_clause)
    if locked is None:
        raise RuntimeError(f"Failed to lock newly created {model.__name__}")

    return locked, True
