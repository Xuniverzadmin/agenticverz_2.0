# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: hoc_spine coordinator
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: incidents
#   Writes: none
# Database:
#   Scope: domain (incidents)
# Role: Run-scoped incident reads (source_run_id)
# Callers: L4 RunEvidenceCoordinator
# Allowed Imports: L6, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
#
# NOTE: Mirrors IncidentWriteDriver.fetch_incidents_by_run_id semantics,
# but uses AsyncSession for L4 async coordinators.

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class IncidentRunReadDriver:
    """Async L6 driver for run-scoped incident reads."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_incidents_by_run_id(
        self,
        run_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch incidents linked to a run (source_run_id).

        Args:
            run_id: Run ID to match against incidents.source_run_id
            tenant_id: Optional tenant scope for isolation

        Returns:
            List of incident dicts
        """
        base_sql = """
            SELECT id, title, category, severity, status, created_at, is_synthetic
            FROM incidents
            WHERE source_run_id = :run_id
        """
        params: Dict[str, Any] = {"run_id": run_id}
        if tenant_id:
            base_sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id
        base_sql += " ORDER BY created_at DESC"

        result = await self._session.execute(text(base_sql), params)
        return [dict(row) for row in result.mappings().all()]


__all__ = ["IncidentRunReadDriver"]
