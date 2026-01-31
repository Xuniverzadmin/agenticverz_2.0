# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: system-wide (Worker API)
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: WorkerRun, CostRecord
#   Writes: WorkerRun, CostRecord, CostAnomaly
# Database:
#   Scope: hoc_spine
#   Models: WorkerRun, CostRecord, CostAnomaly
# Role: DB write delegation for Worker API (Phase 2B extraction)
# Callers: api/workers.py
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-250 Phase 2B Batch 4

"""
Worker Write Service (Async) - DB write operations for Worker API.

Phase 2B Batch 4: Extracted from api/workers.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
- Preserve async semantics exactly
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import CostAnomaly, CostRecord
from app.models.tenant import WorkerRun


class WorkerWriteServiceAsync:
    """
    Async DB write operations for Worker API.

    Write-only facade. No policy logic, no branching beyond DB operations.
    All methods preserve existing async execution model.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_worker_run(
        self,
        run_id: str,
        tenant_id: str,
        data: Dict[str, Any],
    ) -> WorkerRun:
        """
        Upsert a WorkerRun record.

        Args:
            run_id: Run identifier
            tenant_id: Tenant identifier
            data: Run data dict with status, artifacts, tokens, etc.

        Returns:
            The created or updated WorkerRun
        """
        result = await self.session.execute(select(WorkerRun).where(WorkerRun.id == run_id))
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing run
            existing.status = data.get("status", existing.status)
            existing.success = data.get("success", existing.success)
            existing.error = data.get("error", existing.error)
            existing.output_json = json.dumps(data.get("artifacts")) if data.get("artifacts") else None
            existing.replay_token_json = json.dumps(data.get("replay_token")) if data.get("replay_token") else None
            existing.total_tokens = data.get("total_tokens_used", existing.total_tokens)
            existing.total_latency_ms = int(data.get("total_latency_ms", 0)) if data.get("total_latency_ms") else None
            existing.policy_violations = len(data.get("policy_violations", [])) if data.get("policy_violations") else 0
            existing.recoveries = len(data.get("recovery_log", [])) if data.get("recovery_log") else 0
            if data.get("cost_cents") is not None:
                existing.cost_cents = data.get("cost_cents")
            if data.get("status") in ("completed", "failed"):
                existing.completed_at = datetime.utcnow()
            if data.get("status") == "running" and not existing.started_at:
                existing.started_at = datetime.utcnow()
            return existing
        else:
            # Create new run
            run = WorkerRun(
                id=run_id,
                tenant_id=tenant_id,
                worker_id="business-builder",
                task=data.get("task", ""),
                status=data.get("status", "queued"),
                success=data.get("success"),
                error=data.get("error"),
                input_json=json.dumps({"task": data.get("task", "")}),
                output_json=(json.dumps(data.get("artifacts")) if data.get("artifacts") else None),
                replay_token_json=(json.dumps(data.get("replay_token")) if data.get("replay_token") else None),
                total_tokens=data.get("total_tokens_used"),
                total_latency_ms=(int(data.get("total_latency_ms", 0)) if data.get("total_latency_ms") else None),
                policy_violations=(len(data.get("policy_violations", [])) if data.get("policy_violations") else 0),
                recoveries=(len(data.get("recovery_log", [])) if data.get("recovery_log") else 0),
                cost_cents=data.get("cost_cents"),
                created_at=datetime.utcnow(),
                started_at=(datetime.utcnow() if data.get("status") == "running" else None),
            )
            self.session.add(run)
            return run

    async def insert_cost_record(
        self,
        run_id: str,
        tenant_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cents: int,
    ) -> CostRecord:
        """
        Insert a cost record for a worker run.

        Args:
            run_id: Run identifier (used as request_id)
            tenant_id: Tenant identifier
            model: LLM model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_cents: Cost in cents

        Returns:
            The created CostRecord
        """
        created_at_naive = datetime.utcnow()
        cost_record = CostRecord(
            tenant_id=tenant_id,
            request_id=run_id,
            workflow_id="business-builder",
            skill_id="llm_invoke",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=float(cost_cents),
            created_at=created_at_naive,
        )
        self.session.add(cost_record)
        return cost_record

    async def insert_cost_advisory(
        self,
        tenant_id: str,
        run_id: str,
        daily_spend: int,
        warn_threshold: float,
        budget_snapshot: Dict[str, Any],
    ) -> CostAnomaly:
        """
        Insert a cost advisory (BUDGET_WARNING anomaly).

        Args:
            tenant_id: Tenant identifier
            run_id: Run that triggered the advisory
            daily_spend: Current daily spend in cents
            warn_threshold: Warning threshold in cents
            budget_snapshot: Budget state at run time

        Returns:
            The created CostAnomaly
        """
        detected_at_naive = datetime.utcnow()
        advisory = CostAnomaly(
            tenant_id=tenant_id,
            anomaly_type="BUDGET_WARNING",
            severity="MEDIUM",
            entity_type="tenant",
            entity_id=tenant_id,
            current_value_cents=float(daily_spend),
            expected_value_cents=float(warn_threshold),
            deviation_pct=(((daily_spend - warn_threshold) / warn_threshold) * 100 if warn_threshold > 0 else 0),
            threshold_pct=float(budget_snapshot.get("warn_threshold_pct", 0)),
            message=f"Daily spend ({daily_spend}¢) exceeds {budget_snapshot.get('warn_threshold_pct', 0)}% warning threshold ({int(warn_threshold)}¢)",
            metadata_json={
                "run_id": run_id,
                "budget_snapshot": budget_snapshot,
            },
            detected_at=detected_at_naive,
        )
        self.session.add(advisory)
        return advisory

    async def delete_worker_run(self, run: WorkerRun) -> None:
        """
        Delete a WorkerRun record.

        Args:
            run: The WorkerRun to delete
        """
        await self.session.delete(run)

    # REMOVED: commit() helper — L6 DOES NOT COMMIT (L4 coordinator owns transaction boundary)

    async def get_worker_run(self, run_id: str) -> Optional[WorkerRun]:
        """
        Get a WorkerRun by ID (read operation for upsert check).

        Args:
            run_id: Run identifier

        Returns:
            WorkerRun if found, None otherwise
        """
        result = await self.session.execute(select(WorkerRun).where(WorkerRun.id == run_id))
        return result.scalar_one_or_none()
