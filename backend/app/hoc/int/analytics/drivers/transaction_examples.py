# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Golden examples for self-defending transaction patterns
# Callers: Reference for engineers implementing lock-safe operations
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-2.2 Self-Defending Transactions with Intent)

"""
Transaction Intent Golden Examples

This module contains REFERENCE IMPLEMENTATIONS for proper use of
the TransactionIntent system. Use these as templates when implementing
new lock-safe operations.

PHILOSOPHY (Phase-2.2)
----------------------
These examples demonstrate the correct design pattern:

1. DECLARE intent before implementation
2. Use BLESSED primitives only
3. Make dangerous states STRUCTURALLY IMPOSSIBLE

PATTERN SUMMARY
---------------

| Intent          | First Parameter       | Allowed Operations        |
|-----------------|----------------------|---------------------------|
| READ_ONLY       | Session              | select(), no locks        |
| ATOMIC_WRITE    | Session              | add(), commit(), no locks |
| LOCKED_MUTATION | SingleConnectionTxn  | lock_row(), commit()      |

EXAMPLES BELOW
--------------
"""

from __future__ import annotations

from typing import Optional, Type, TypeVar

from app.infra.transaction import (
    SingleConnectionTxn,
    TransactionIntent,
    single_connection_transaction,
    transactional,
)

T = TypeVar("T")


# =============================================================================
# EXAMPLE 1: Simple Read-Only Query (no locks)
# =============================================================================


@transactional(intent=TransactionIntent.READ_ONLY)
def get_entity_by_id(session, model: Type[T], entity_id: str) -> Optional[T]:
    """
    Read-only query with no locking.

    This is the SIMPLEST pattern. No locks, no transaction context needed.
    Just a plain session query.

    Args:
        session: Database session (plain Session)
        model: SQLModel class to query
        entity_id: ID to look up

    Returns:
        Entity or None

    Example:
        from sqlmodel import Session
        from app.db import engine

        with Session(engine) as session:
            state = get_entity_by_id(session, CostSimCBState, "costsim_v2")
    """
    from sqlmodel import select

    stmt = select(model).where(model.id == entity_id)
    return session.exec(stmt).first()


# =============================================================================
# EXAMPLE 2: Atomic Write (no locks)
# =============================================================================


@transactional(intent=TransactionIntent.ATOMIC_WRITE)
def create_entity(session, model: Type[T], **kwargs) -> T:
    """
    Atomic write without row locking.

    Use this pattern when you're creating NEW entities and don't need
    to lock existing rows. The transaction ensures atomicity.

    Args:
        session: Database session
        model: SQLModel class
        **kwargs: Fields for the new entity

    Returns:
        Created entity

    Example:
        from sqlmodel import Session
        from app.db import engine

        with Session(engine) as session:
            incident = create_entity(
                session,
                CostSimCBIncident,
                reason="Manual test",
                severity="P3",
            )
            session.commit()
    """
    entity = model(**kwargs)
    session.add(entity)
    return entity


# =============================================================================
# EXAMPLE 3: Locked Mutation (THE DANGEROUS ONE, DONE RIGHT)
# =============================================================================


@transactional(intent=TransactionIntent.LOCKED_MUTATION)
def trip_circuit_breaker(
    txn: SingleConnectionTxn,
    name: str,
    reason: str,
    disabled_by: str,
) -> bool:
    """
    Trip a circuit breaker with row locking.

    This is the CRITICAL pattern for state mutations that require:
    - Atomicity: all-or-nothing
    - Isolation: no concurrent modifications
    - Consistency: state transitions are valid

    The @transactional decorator with LOCKED_MUTATION intent:
    1. REQUIRES SingleConnectionTxn as first parameter (enforced at decoration time)
    2. VALIDATES at runtime that we're in the right context
    3. REGISTERS this function for CI validation

    The SingleConnectionTxn guarantees:
    1. Single connection for entire scope (no deadlocks)
    2. Auto-rollback on error
    3. Lock scope == connection scope

    Args:
        txn: Single-connection transaction context
        name: Circuit breaker name to trip
        reason: Why we're tripping it
        disabled_by: Who/what triggered the trip

    Returns:
        True if state changed, False if already tripped

    Example:
        from app.infra import single_connection_transaction

        with single_connection_transaction() as txn:
            changed = trip_circuit_breaker(
                txn,
                name="costsim_v2",
                reason="Drift exceeded threshold",
                disabled_by="canary_runner",
            )
            if changed:
                # State was updated
                txn.commit()
    """
    from datetime import datetime, timezone

    from app.db import CostSimCBState

    # Lock the row (the ONLY blessed way to do FOR UPDATE)
    state = txn.lock_row(CostSimCBState, CostSimCBState.name == name)

    if state is None:
        # Row doesn't exist - create it in disabled state
        state = CostSimCBState(
            name=name,
            disabled=True,
            disabled_reason=reason,
            disabled_by=disabled_by,
            updated_at=datetime.now(timezone.utc),
        )
        txn.add(state)
        txn.commit()
        return True

    if state.disabled:
        # Already disabled
        return False

    # Transition to disabled
    state.disabled = True
    state.disabled_reason = reason
    state.disabled_by = disabled_by
    state.updated_at = datetime.now(timezone.utc)

    # Commit is explicit - caller controls commit timing
    return True


@transactional(intent=TransactionIntent.LOCKED_MUTATION)
def reset_circuit_breaker(
    txn: SingleConnectionTxn,
    name: str,
    reset_by: str,
    reset_reason: Optional[str] = None,
) -> bool:
    """
    Reset a circuit breaker to enabled state.

    Another example of LOCKED_MUTATION. Notice:
    1. SingleConnectionTxn is first parameter
    2. Uses txn.lock_row() not raw with_for_update()
    3. Caller controls commit timing

    Args:
        txn: Single-connection transaction context
        name: Circuit breaker name
        reset_by: Who/what triggered the reset
        reset_reason: Optional reason for reset

    Returns:
        True if state changed, False if already enabled

    Example:
        with single_connection_transaction() as txn:
            changed = reset_circuit_breaker(
                txn,
                name="costsim_v2",
                reset_by="admin",
                reset_reason="Manual reset after fix",
            )
            if changed:
                txn.commit()
    """
    from datetime import datetime, timezone

    from app.db import CostSimCBState

    state = txn.lock_row(CostSimCBState, CostSimCBState.name == name)

    if state is None or not state.disabled:
        return False

    state.disabled = False
    state.disabled_reason = f"Reset: {reset_reason}" if reset_reason else None
    state.disabled_by = None
    state.disabled_until = None
    state.consecutive_failures = 0
    state.updated_at = datetime.now(timezone.utc)

    return True


# =============================================================================
# EXAMPLE 4: Caller Pattern (How to Use LOCKED_MUTATION Functions)
# =============================================================================


def example_caller_pattern():
    """
    This shows how to CALL functions with LOCKED_MUTATION intent.

    The key insight: YOU create the transaction context, then pass it
    to the function. This makes the lock scope VISIBLE at the call site.

    DO NOT copy this pattern:
        # WRONG - hides the lock scope
        def bad_trip():
            with single_connection_transaction() as txn:
                state = session.exec(...).first()  # Uses session, not txn!
                state.disabled = True
                session.commit()  # Different connection - DEADLOCK!

    DO copy this pattern:
        # RIGHT - lock scope is visible
        with single_connection_transaction() as txn:
            changed = trip_circuit_breaker(txn, name, reason, actor)
            if changed:
                txn.commit()
    """
    # Create the transaction context at the call site
    with single_connection_transaction() as txn:
        # Pass txn to the LOCKED_MUTATION function
        changed = trip_circuit_breaker(
            txn,
            name="example_cb",
            reason="Example: drift detected",
            disabled_by="example_caller",
        )

        if changed:
            # Caller controls commit
            txn.commit()
            print("Circuit breaker tripped")
        else:
            print("Already tripped")


# =============================================================================
# ANTI-PATTERNS (What NOT to Do)
# =============================================================================

# These are BLOCKED by CI and the @transactional decorator:
#
# 1. LOCKED_MUTATION without SingleConnectionTxn
#
#    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
#    def bad_example(session: Session, ...):  # FAILS - wrong type
#        stmt = select(Model).with_for_update()  # Also BLOCKED by CI
#        ...
#
# 2. with_for_update() outside blessed primitives
#
#    def dangerous_function(session):
#        # BLOCKED BY CI - this pattern causes deadlocks
#        stmt = select(Model).where(...).with_for_update()
#        row = session.exec(stmt).first()
#        row.field = new_value
#        session.commit()  # May be on DIFFERENT connection!
#        # DEADLOCK: new connection waits for lock held by old connection
#
# 3. Mixing session and txn
#
#    with single_connection_transaction() as txn:
#        state = session.exec(select(Model)).first()  # WRONG - uses session
#        state.field = new_value
#        session.commit()  # Different connection!
