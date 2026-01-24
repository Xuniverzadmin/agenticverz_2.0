# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
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

from fastapi import APIRouter, Query

from app.discovery.ledger import get_signals
from app.schemas.response import wrap_dict

router = APIRouter(prefix="/api/v1/discovery", tags=["discovery"])


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
async def signal_stats():
    """
    Get summary statistics of discovery signals.

    Returns counts by artifact, signal_type, and status.
    """
    try:
        from sqlalchemy import text

        from app.db import get_sync_engine

        engine = get_sync_engine()

        with engine.connect() as conn:
            # Count by artifact
            by_artifact = conn.execute(
                text(
                    """
                SELECT artifact, COUNT(*) as count, SUM(seen_count) as total_seen
                FROM discovery_ledger
                GROUP BY artifact
                ORDER BY total_seen DESC
            """
                )
            ).fetchall()

            # Count by signal_type
            by_signal_type = conn.execute(
                text(
                    """
                SELECT signal_type, COUNT(*) as count, SUM(seen_count) as total_seen
                FROM discovery_ledger
                GROUP BY signal_type
                ORDER BY total_seen DESC
            """
                )
            ).fetchall()

            # Count by status
            by_status = conn.execute(
                text(
                    """
                SELECT status, COUNT(*) as count
                FROM discovery_ledger
                GROUP BY status
            """
                )
            ).fetchall()

            return wrap_dict({
                "by_artifact": [
                    {"artifact": r.artifact, "count": r.count, "total_seen": r.total_seen} for r in by_artifact
                ],
                "by_signal_type": [
                    {"signal_type": r.signal_type, "count": r.count, "total_seen": r.total_seen} for r in by_signal_type
                ],
                "by_status": [{"status": r.status, "count": r.count} for r in by_status],
            })
    except Exception as e:
        return wrap_dict({
            "by_artifact": [],
            "by_signal_type": [],
            "by_status": [],
            "error": str(e),
        })
