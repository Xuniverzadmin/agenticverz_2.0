# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Run
#   Writes: none
# Database:
#   Scope: hoc_spine
#   Models: Run
# Role: Idempotency key utilities
# Callers: API routes, workers
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Idempotency

# Idempotency Handling
# Prevents duplicate runs using idempotency keys

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

# PIN-520 ITER3.3: Fix broken relative import (..db doesn't exist)
from app.db import Run, engine

logger = logging.getLogger("nova.utils.idempotency")

# TTL for idempotency keys (default 24 hours)
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "86400"))


@dataclass
class IdempotencyResult:
    """Result of idempotency check."""

    exists: bool
    run_id: Optional[str] = None
    status: Optional[str] = None
    is_expired: bool = False


def get_existing_run(
    idempotency_key: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Optional[Run]:
    """Check if a run with this idempotency key already exists.

    Args:
        idempotency_key: The idempotency key to check
        tenant_id: Optional tenant filter
        agent_id: Optional agent filter

    Returns:
        Existing Run if found, None otherwise
    """
    with Session(engine) as session:
        query = select(Run).where(Run.idempotency_key == idempotency_key)

        if tenant_id:
            query = query.where(Run.tenant_id == tenant_id)

        if agent_id:
            query = query.where(Run.agent_id == agent_id)

        result = session.exec(query).first()
        # Handle both Row tuple and direct model returns
        if result is None:
            return None
        elif hasattr(result, "id"):  # Already a model
            return result
        else:  # Row tuple
            return result[0]


def check_idempotency(
    idempotency_key: str,
    tenant_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> IdempotencyResult:
    """Check idempotency and return result with status.

    Args:
        idempotency_key: The idempotency key to check
        tenant_id: Optional tenant filter
        agent_id: Optional agent filter

    Returns:
        IdempotencyResult indicating if key exists and its status
    """
    run = get_existing_run(idempotency_key, tenant_id, agent_id)

    if not run:
        return IdempotencyResult(exists=False)

    # Check if expired
    if run.created_at:
        # Handle timezone-naive datetime from PostgreSQL
        created_at = run.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - created_at
        if age.total_seconds() > IDEMPOTENCY_TTL_SECONDS:
            logger.info(
                "idempotency_key_expired",
                extra={
                    "idempotency_key": idempotency_key[:16] + "...",
                    "run_id": run.id,
                    "age_seconds": age.total_seconds(),
                },
            )
            return IdempotencyResult(
                exists=True,
                run_id=run.id,
                status=run.status,
                is_expired=True,
            )

    logger.info(
        "idempotency_key_found",
        extra={
            "idempotency_key": idempotency_key[:16] + "...",
            "run_id": run.id,
            "status": run.status,
        },
    )

    return IdempotencyResult(
        exists=True,
        run_id=run.id,
        status=run.status,
        is_expired=False,
    )


def should_return_cached(result: IdempotencyResult) -> bool:
    """Determine if we should return cached result.

    Returns True if:
    - Key exists and is not expired
    - Status is succeeded, failed, or in progress (queued/running)

    Returns False if:
    - Key doesn't exist
    - Key is expired
    """
    if not result.exists or result.is_expired:
        return False

    # Return cached for terminal and in-progress states
    return result.status in ("succeeded", "failed", "queued", "running", "retry")
