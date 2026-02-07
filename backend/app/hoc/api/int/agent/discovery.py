# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: founder-console
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Discovery ledger API (read-only signal access)
# Callers: Founder Console UI
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1

"""
Discovery Ledger API - Founder Console endpoint.

Read-only access to discovery signals.
Founder/dev only - not customer facing.

Reference: docs/contracts/visibility_lifecycle.yaml
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.discovery.ledger import get_signals

# L4 session dependency + operation registry (L2 must not import sqlalchemy/sqlmodel/app.db directly)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    get_sync_session_dep,
    OperationContext,
)
from app.schemas.response import wrap_dict

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("")
@router.get("/")
async def list_signals(
    artifact: Optional[str] = Query(None, description="Filter by artifact name"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
):
    """
    List discovery signals from the ledger.

    This is a read-only endpoint for the Founder Console.
    Sorted by seen_count (descending), then last_seen_at (descending).

    No actions required - you look at it when you care.
    """
    signals = get_signals(
        artifact=artifact,
        signal_type=signal_type,
        status=status,
        limit=limit,
    )

    return wrap_dict({
        "items": signals,
        "total": len(signals),
        "note": "Discovery Ledger records curiosity, not decisions.",
    })


@router.get("/stats")
async def signal_stats(
    session=Depends(get_sync_session_dep),
):
    """
    Get summary statistics of discovery signals.

    Returns counts by artifact, signal_type, and status.
    """
    try:
        # Dispatch to L4 handler via operation registry
        registry = get_operation_registry()
        result = await registry.execute(
            operation="agent.discovery_stats",
            ctx=OperationContext(
                session=session,  # type: ignore[arg-type]  # sync session passed via params
                tenant_id="system",  # discovery ledger is system-wide, no tenant context
                params={"sync_session": session},
            ),
        )

        if not result.success:
            return wrap_dict({
                "by_artifact": [],
                "by_signal_type": [],
                "by_status": [],
                "error": result.error,
            })

        return wrap_dict(result.data)
    except Exception as e:
        return wrap_dict({
            "by_artifact": [],
            "by_signal_type": [],
            "by_status": [],
            "error": str(e),
        })
