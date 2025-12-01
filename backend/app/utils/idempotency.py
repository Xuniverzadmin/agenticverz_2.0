# Idempotency Handling
# Prevents duplicate runs using idempotency keys

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from ..db import Run, engine

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

        run = session.exec(query).first()
        return run


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
        age = datetime.utcnow() - run.created_at
        if age.total_seconds() > IDEMPOTENCY_TTL_SECONDS:
            logger.info(
                "idempotency_key_expired",
                extra={
                    "idempotency_key": idempotency_key[:16] + "...",
                    "run_id": run.id,
                    "age_seconds": age.total_seconds(),
                }
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
        }
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
