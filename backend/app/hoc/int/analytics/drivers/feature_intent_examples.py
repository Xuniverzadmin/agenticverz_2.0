# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any
#   Execution: sync
# Role: Golden examples for feature intent patterns
# Callers: Reference for engineers implementing features
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-2.3 Feature Intent System)

"""
Feature Intent Golden Examples

This module contains REFERENCE IMPLEMENTATIONS for proper use of
the FeatureIntent + TransactionIntent hierarchy.

INTENT HIERARCHY
----------------

    FeatureIntent (module-level)
         ↓ constrains
    TransactionIntent (function-level)
         ↓ constrains
    Primitive (implementation-level)

VALID COMBINATIONS
------------------

| FeatureIntent           | TransactionIntent        | RetryPolicy    |
|-------------------------|--------------------------|----------------|
| PURE_QUERY              | READ_ONLY                | any            |
| STATE_MUTATION          | ATOMIC_WRITE             | any            |
| STATE_MUTATION          | LOCKED_MUTATION          | any            |
| EXTERNAL_SIDE_EFFECT    | ATOMIC_WRITE             | NEVER required |
| RECOVERABLE_OPERATION   | LOCKED_MUTATION          | SAFE required  |

USAGE PATTERN
-------------
Every feature module should:

1. Declare FEATURE_INTENT at module level
2. Declare RETRY_POLICY if required
3. Use @feature decorator on functions (optional but recommended)
4. Use @transactional decorator on persistence functions
5. Call validate_module_intent(globals()) at end (optional but recommended)

EXAMPLES BELOW
--------------
"""

from typing import Any, Dict, Optional

# =============================================================================
# MODULE-LEVEL DECLARATIONS
# These go at the TOP of every feature module
# =============================================================================
from app.infra.feature_intent import (
    FeatureIntent,
    RetryPolicy,
    feature,
)
from app.infra.transaction import (
    SingleConnectionTxn,
    TransactionIntent,
    transactional,
)

# This module demonstrates all patterns - use STATE_MUTATION as default
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE


# =============================================================================
# EXAMPLE 1: PURE_QUERY Feature
# =============================================================================


class PureQueryExample:
    """
    Example of a PURE_QUERY feature.

    PURE_QUERY features:
    - Only read data, never write
    - Only use TransactionIntent.READ_ONLY
    - Can have any RetryPolicy (retries are always safe for reads)

    Module-level declaration:
        FEATURE_INTENT = FeatureIntent.PURE_QUERY
        # RETRY_POLICY is optional for PURE_QUERY
    """

    # In a real module, this would be at module level:
    # FEATURE_INTENT = FeatureIntent.PURE_QUERY

    @staticmethod
    @feature(intent=FeatureIntent.PURE_QUERY)
    @transactional(intent=TransactionIntent.READ_ONLY)
    def get_entity(session, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Read-only query.

        Note the intent stack:
        - FeatureIntent: PURE_QUERY
        - TransactionIntent: READ_ONLY
        - Primitive: session.exec() (no locks, no writes)
        """

        # Only reads allowed - no .add(), no .commit()
        # stmt = select(Model).where(Model.id == entity_id)
        # return session.exec(stmt).first()
        return {"id": entity_id, "example": True}


# =============================================================================
# EXAMPLE 2: STATE_MUTATION with ATOMIC_WRITE
# =============================================================================


class AtomicWriteExample:
    """
    Example of a STATE_MUTATION feature using ATOMIC_WRITE.

    STATE_MUTATION + ATOMIC_WRITE:
    - Writes data but doesn't need row locks
    - Simple inserts, updates without concurrency concerns
    - Can have any RetryPolicy

    Module-level declaration:
        FEATURE_INTENT = FeatureIntent.STATE_MUTATION
        RETRY_POLICY = RetryPolicy.SAFE  # if idempotent
    """

    @staticmethod
    @feature(intent=FeatureIntent.STATE_MUTATION, retry=RetryPolicy.SAFE)
    @transactional(intent=TransactionIntent.ATOMIC_WRITE)
    def create_record(session, data: Dict[str, Any]) -> str:
        """
        Simple write without locking.

        Intent stack:
        - FeatureIntent: STATE_MUTATION
        - TransactionIntent: ATOMIC_WRITE
        - Primitive: session.add(), session.commit()

        This is safe for retries if the operation is idempotent
        (e.g., using ON CONFLICT DO NOTHING).
        """
        # record = Model(**data)
        # session.add(record)
        # session.commit()
        # return record.id
        return "new-record-id"


# =============================================================================
# EXAMPLE 3: STATE_MUTATION with LOCKED_MUTATION
# =============================================================================


class LockedMutationExample:
    """
    Example of a STATE_MUTATION feature using LOCKED_MUTATION.

    STATE_MUTATION + LOCKED_MUTATION:
    - Writes data AND needs row locks
    - Concurrent access must be serialized
    - Requires SingleConnectionTxn

    Module-level declaration:
        FEATURE_INTENT = FeatureIntent.STATE_MUTATION
        RETRY_POLICY = RetryPolicy.SAFE  # if idempotent after lock
    """

    @staticmethod
    @feature(intent=FeatureIntent.STATE_MUTATION, retry=RetryPolicy.SAFE)
    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
    def update_counter(txn: SingleConnectionTxn, counter_id: str, delta: int) -> int:
        """
        Atomic counter update with locking.

        Intent stack:
        - FeatureIntent: STATE_MUTATION
        - TransactionIntent: LOCKED_MUTATION
        - Primitive: txn.lock_row(), txn.commit()

        The lock prevents concurrent updates from causing lost writes.
        """
        # counter = txn.lock_row(Counter, Counter.id == counter_id)
        # counter.value += delta
        # txn.commit()
        # return counter.value
        return delta  # placeholder


# =============================================================================
# EXAMPLE 4: EXTERNAL_SIDE_EFFECT
# =============================================================================


class ExternalSideEffectExample:
    """
    Example of an EXTERNAL_SIDE_EFFECT feature.

    EXTERNAL_SIDE_EFFECT:
    - Calls external services (APIs, webhooks, email)
    - MUST use RetryPolicy.NEVER (side effects can't be safely retried)
    - Only TransactionIntent.ATOMIC_WRITE allowed

    Module-level declaration:
        FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
        RETRY_POLICY = RetryPolicy.NEVER  # REQUIRED
    """

    @staticmethod
    @feature(intent=FeatureIntent.EXTERNAL_SIDE_EFFECT, retry=RetryPolicy.NEVER)
    @transactional(intent=TransactionIntent.ATOMIC_WRITE)
    def send_webhook(session, webhook_url: str, payload: Dict[str, Any]) -> bool:
        """
        Send webhook with no retries.

        Intent stack:
        - FeatureIntent: EXTERNAL_SIDE_EFFECT
        - TransactionIntent: ATOMIC_WRITE
        - Primitive: session.add() for logging, external HTTP call

        CRITICAL: This function must NOT be retried automatically.
        If it fails, the caller must handle the failure explicitly.

        Pattern:
        1. Record intent in DB (idempotency key)
        2. Make external call
        3. Record result in DB
        4. If step 2 fails, the DB shows incomplete state
        """
        # 1. Record intent
        # log = WebhookLog(url=webhook_url, status="pending")
        # session.add(log)
        # session.commit()

        # 2. Make external call (NOT retryable)
        # response = httpx.post(webhook_url, json=payload)

        # 3. Record result
        # log.status = "success" if response.ok else "failed"
        # session.commit()

        return True  # placeholder


# =============================================================================
# EXAMPLE 5: RECOVERABLE_OPERATION
# =============================================================================


class RecoverableOperationExample:
    """
    Example of a RECOVERABLE_OPERATION feature.

    RECOVERABLE_OPERATION:
    - Must be idempotent and resumable
    - MUST use RetryPolicy.SAFE
    - Only TransactionIntent.LOCKED_MUTATION allowed
    - Designed for worker/background tasks

    Module-level declaration:
        FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION
        RETRY_POLICY = RetryPolicy.SAFE  # REQUIRED

    Pattern:
    - Use database state to track progress
    - Lock state before mutation
    - Support resume from any intermediate state
    """

    @staticmethod
    @feature(intent=FeatureIntent.RECOVERABLE_OPERATION, retry=RetryPolicy.SAFE)
    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
    def process_job(txn: SingleConnectionTxn, job_id: str) -> str:
        """
        Process a job with recovery support.

        Intent stack:
        - FeatureIntent: RECOVERABLE_OPERATION
        - TransactionIntent: LOCKED_MUTATION
        - Primitive: txn.lock_row(), txn.commit()

        This function can be safely retried because:
        1. State is locked before reading
        2. Progress is checkpointed after each step
        3. Idempotent operations skip already-completed steps
        """
        # 1. Lock job state
        # job = txn.lock_row(Job, Job.id == job_id)

        # 2. Check current state (resume support)
        # if job.status == "completed":
        #     return "already_completed"

        # 3. Process with checkpoints
        # if job.step < 1:
        #     do_step_1(job)
        #     job.step = 1
        #     txn.commit()

        # if job.step < 2:
        #     do_step_2(job)
        #     job.step = 2
        #     txn.commit()

        # 4. Mark complete
        # job.status = "completed"
        # txn.commit()

        return "completed"  # placeholder


# =============================================================================
# ANTI-PATTERNS (What NOT to Do)
# =============================================================================

"""
ANTI-PATTERN 1: Missing FEATURE_INTENT

    # BAD: Module has persistence but no intent
    from sqlmodel import Session

    def some_function(session: Session):
        session.add(...)  # CI will fail!

ANTI-PATTERN 2: Intent Mismatch

    # BAD: PURE_QUERY with LOCKED_MUTATION
    FEATURE_INTENT = FeatureIntent.PURE_QUERY

    @transactional(intent=TransactionIntent.LOCKED_MUTATION)
    def bad_query(txn):  # CI will fail! PURE_QUERY only allows READ_ONLY
        ...

ANTI-PATTERN 3: Side Effects with Wrong Retry Policy

    # BAD: EXTERNAL_SIDE_EFFECT with SAFE retry
    FEATURE_INTENT = FeatureIntent.EXTERNAL_SIDE_EFFECT
    RETRY_POLICY = RetryPolicy.SAFE  # CI will fail! Must be NEVER

    def send_email(session):
        ...  # Retrying email sends can cause duplicates

ANTI-PATTERN 4: Recoverable without Lock

    # BAD: RECOVERABLE_OPERATION without LOCKED_MUTATION
    FEATURE_INTENT = FeatureIntent.RECOVERABLE_OPERATION

    @transactional(intent=TransactionIntent.ATOMIC_WRITE)
    def bad_job(session):  # CI will fail! Must use LOCKED_MUTATION
        ...
"""


# =============================================================================
# MODULE VALIDATION (Call at end of feature modules)
# =============================================================================

# This validates that the module has all required declarations
# Uncomment in actual feature modules:
# validate_module_intent(globals())
