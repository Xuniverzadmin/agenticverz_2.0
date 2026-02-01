# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — provenance logging DB operations
# Callers: Sandbox, canary, divergence flows (via L4 handlers)
# Allowed Imports: hoc_spine, hoc.cus.analytics.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A5 Wiring
# artifact_class: CODE

"""
Provenance Coordinator (PIN-513 Batch 3A5 Wiring)

L4 coordinator that owns provenance DB operations.

Wires from analytics/L6_drivers/provenance_driver.py:
- write_provenance(...)
- write_provenance_batch(records, session)
- query_provenance(...)
- count_provenance(...)
- get_drift_stats(start_date, end_date)
- check_duplicate(input_hash)
- compute_input_hash(payload)
- backfill_v1_baseline(records, batch_size)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.hoc_spine.coordinators.provenance")


class ProvenanceCoordinator:
    """L4 coordinator: provenance logging DB operations."""

    async def write(
        self,
        run_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        variant_slug: str = "v2",
        source: str = "sandbox",
        model_version: Optional[str] = None,
        adapter_version: Optional[str] = None,
        commit_sha: Optional[str] = None,
        input_hash: Optional[str] = None,
        output_hash: Optional[str] = None,
        v1_cost: Optional[float] = None,
        v2_cost: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
        runtime_ms: Optional[int] = None,
        session: Optional[Any] = None,
    ) -> int:
        """Write a single provenance record."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            write_provenance,
        )

        return await write_provenance(
            run_id=run_id,
            tenant_id=tenant_id,
            variant_slug=variant_slug,
            source=source,
            model_version=model_version,
            adapter_version=adapter_version,
            commit_sha=commit_sha,
            input_hash=input_hash,
            output_hash=output_hash,
            v1_cost=v1_cost,
            v2_cost=v2_cost,
            payload=payload,
            runtime_ms=runtime_ms,
            session=session,
        )

    async def write_batch(
        self,
        records: List[Dict[str, Any]],
        session: Optional[Any] = None,
    ) -> List[int]:
        """Write a batch of provenance records."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            write_provenance_batch,
        )

        return await write_provenance_batch(records=records, session=session)

    async def query(
        self,
        tenant_id: Optional[str] = None,
        variant_slug: Optional[str] = None,
        source: Optional[str] = None,
        input_hash: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query provenance records."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            query_provenance,
        )

        return await query_provenance(
            tenant_id=tenant_id,
            variant_slug=variant_slug,
            source=source,
            input_hash=input_hash,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    async def count(
        self,
        tenant_id: Optional[str] = None,
        variant_slug: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count provenance records."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            count_provenance,
        )

        return await count_provenance(
            tenant_id=tenant_id,
            variant_slug=variant_slug,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_drift_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get drift statistics from provenance data."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import get_drift_stats

        return await get_drift_stats(
            start_date=start_date,
            end_date=end_date,
        )

    async def check_duplicate(self, input_hash: str) -> bool:
        """Check if an input hash already exists."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import check_duplicate

        return await check_duplicate(input_hash=input_hash)

    def compute_input_hash(self, payload: Dict[str, Any]) -> str:
        """Compute deterministic hash for input payload."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            compute_input_hash,
        )

        return compute_input_hash(payload=payload)

    async def backfill_v1_baseline(
        self,
        records: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, int]:
        """Backfill V1 baseline provenance records."""
        from app.hoc.cus.analytics.L6_drivers.provenance_driver import (
            backfill_v1_baseline,
        )

        result = await backfill_v1_baseline(records=records, batch_size=batch_size)
        logger.info(
            "v1_baseline_backfilled",
            extra={"batch_size": batch_size, "result": result},
        )
        return result
