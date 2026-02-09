# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: hoc_spine coordinator
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: prevention_records, policy_rules
#   Writes: none
# Database:
#   Scope: domain (policies)
# Role: Run-scoped policy evaluation reads (canonical ledger)
# Callers: L4 RunEvidenceCoordinator
# Allowed Imports: L6, sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5

from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class PreventionRecordsReadDriver:
    """Async read driver for prevention_records run-scoped queries."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_policy_evaluations_for_run(
        self,
        tenant_id: str,
        run_id: str,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch prevention_records linked to a run.

        Args:
            tenant_id: Tenant scope
            run_id: Run ID
            max_results: Max records

        Returns:
            List of dicts with policy_id, outcome, created_at, rule_name
        """
        sql = """
            SELECT
                pr.id,
                pr.policy_id,
                pr.outcome,
                pr.created_at,
                pr.pattern_id,
                pr.run_id,
                pr.blocked_incident_id,
                pr.original_incident_id,
                pr.signature_match_confidence,
                pr.tenant_id,
                rules.name AS rule_name
            FROM prevention_records pr
            LEFT JOIN policy_rules rules ON rules.id = pr.policy_id
            WHERE pr.tenant_id = :tenant_id
              AND (
                pr.run_id = :run_id
                OR pr.blocked_incident_id = :run_id
                OR pr.original_incident_id = :run_id
              )
            ORDER BY pr.created_at DESC
            LIMIT :max_results
        """
        result = await self._session.execute(
            text(sql),
            {"tenant_id": tenant_id, "run_id": run_id, "max_results": max_results},
        )
        return [dict(row) for row in result.mappings().all()]


__all__ = ["PreventionRecordsReadDriver"]
