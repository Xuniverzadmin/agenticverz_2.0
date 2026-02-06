# Layer: L6 — Driver
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: L5 engine call
#   Execution: async
# Role: Guard domain read-only DB queries (tenant state, guardrails, incidents, calls, settings)
# Callers: L5 engines (guard_query_engine)
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: L2 first-principles purity enforcement
# artifact_class: CODE

"""
Guard Read Driver (L6)

Provides async DB read operations for guard/killswitch domain data.
Extracted from L2 files (guard.py, v1_killswitch.py, replay.py) to enforce
L2 first-principles purity (zero sqlalchemy/sqlmodel imports in L2).

All methods accept an AsyncSession and return plain dicts or model instances.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class GuardReadDriver:
    """Async DB read operations for guard/killswitch domain."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # =========================================================================
    # Tenant / KillSwitch State
    # =========================================================================

    async def get_tenant(self, tenant_id: str) -> Optional[Any]:
        """Get tenant by ID."""
        from app.models.tenant import Tenant

        result = await self._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalars().first()

    async def get_killswitch_state(self, entity_type: str, entity_id: str) -> Optional[Any]:
        """Get killswitch state for an entity."""
        from app.models.killswitch import KillSwitchState

        result = await self._session.execute(
            select(KillSwitchState).where(
                and_(
                    KillSwitchState.entity_type == entity_type,
                    KillSwitchState.entity_id == entity_id,
                )
            )
        )
        return result.scalars().first()

    async def get_key_states_for_tenant(self, tenant_id: str) -> List[Any]:
        """Get all key killswitch states for a tenant."""
        from app.models.killswitch import KillSwitchState

        result = await self._session.execute(
            select(KillSwitchState).where(
                and_(
                    KillSwitchState.entity_type == "key",
                    KillSwitchState.tenant_id == tenant_id,
                )
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # Guardrails
    # =========================================================================

    async def get_active_guardrails(self) -> List[Any]:
        """Get all enabled guardrails."""
        from app.models.killswitch import DefaultGuardrail

        result = await self._session.execute(
            select(DefaultGuardrail).where(DefaultGuardrail.is_enabled == True)
        )
        return list(result.scalars().all())

    async def get_all_guardrails_ordered(self) -> List[Any]:
        """Get all guardrails ordered by priority."""
        from app.models.killswitch import DefaultGuardrail

        result = await self._session.execute(
            select(DefaultGuardrail).order_by(DefaultGuardrail.priority)
        )
        return list(result.scalars().all())

    async def get_enabled_guardrails_ordered(self) -> List[Any]:
        """Get enabled guardrails ordered by priority."""
        from app.models.killswitch import DefaultGuardrail

        result = await self._session.execute(
            select(DefaultGuardrail).where(
                DefaultGuardrail.is_enabled == True
            ).order_by(DefaultGuardrail.priority)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Incidents
    # =========================================================================

    async def count_incidents_since(self, tenant_id: str, since: datetime) -> int:
        """Count incidents for tenant since a datetime."""
        from app.models.killswitch import Incident

        result = await self._session.execute(
            select(func.count(Incident.id)).where(
                and_(
                    Incident.tenant_id == tenant_id,
                    Incident.created_at >= since,
                )
            )
        )
        return result.scalar() or 0

    async def get_latest_incident(self, tenant_id: str) -> Optional[Any]:
        """Get the most recent incident for a tenant."""
        from app.models.killswitch import Incident

        result = await self._session.execute(
            select(Incident).where(
                Incident.tenant_id == tenant_id
            ).order_by(desc(Incident.created_at)).limit(1)
        )
        return result.scalars().first()

    async def get_incident_by_id(self, incident_id: str) -> Optional[Any]:
        """Get incident by ID."""
        from app.models.killswitch import Incident

        result = await self._session.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        return result.scalars().first()

    async def get_incident_by_id_and_tenant(self, incident_id: str, tenant_id: str) -> Optional[Any]:
        """Get incident by ID and tenant."""
        from app.models.killswitch import Incident

        result = await self._session.execute(
            select(Incident).where(
                and_(
                    Incident.id == incident_id,
                    Incident.tenant_id == tenant_id,
                )
            )
        )
        return result.scalars().first()

    async def list_incidents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Any], int]:
        """List incidents with filters, returns (items, total)."""
        from app.models.killswitch import Incident

        stmt = select(Incident).where(Incident.tenant_id == tenant_id)
        count_stmt = select(func.count(Incident.id)).where(Incident.tenant_id == tenant_id)

        if status:
            stmt = stmt.where(Incident.status == status)
            count_stmt = count_stmt.where(Incident.status == status)
        if severity:
            stmt = stmt.where(Incident.severity == severity)
            count_stmt = count_stmt.where(Incident.severity == severity)
        if time_from:
            stmt = stmt.where(Incident.started_at >= time_from)
            count_stmt = count_stmt.where(Incident.started_at >= time_from)
        if time_to:
            stmt = stmt.where(Incident.started_at <= time_to)
            count_stmt = count_stmt.where(Incident.started_at <= time_to)
        if query:
            stmt = stmt.where(Incident.title.ilike(f"%{query}%"))
            count_stmt = count_stmt.where(Incident.title.ilike(f"%{query}%"))

        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.order_by(desc(Incident.created_at)).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_incident_events(self, incident_id: str) -> List[Any]:
        """Get incident events ordered by created_at."""
        from app.models.killswitch import IncidentEvent

        result = await self._session.execute(
            select(IncidentEvent).where(
                IncidentEvent.incident_id == incident_id
            ).order_by(IncidentEvent.created_at)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Proxy Calls
    # =========================================================================

    async def get_proxy_call(self, call_id: str) -> Optional[Any]:
        """Get proxy call by ID."""
        from app.models.killswitch import ProxyCall

        result = await self._session.execute(
            select(ProxyCall).where(ProxyCall.id == call_id)
        )
        return result.scalars().first()

    async def get_proxy_calls_in_window(
        self, call_ids: List[str], window_start: datetime, window_end: datetime
    ) -> List[Any]:
        """Get proxy calls within a time window."""
        from app.models.killswitch import ProxyCall

        result = await self._session.execute(
            select(ProxyCall).where(
                and_(
                    ProxyCall.id.in_(call_ids),
                    ProxyCall.created_at >= window_start,
                    ProxyCall.created_at <= window_end,
                )
            ).order_by(ProxyCall.created_at)
        )
        return list(result.scalars().all())

    async def get_proxy_calls_by_ids(self, call_ids: List[str], limit: int = 100) -> List[Any]:
        """Get proxy calls by IDs."""
        from app.models.killswitch import ProxyCall

        result = await self._session.execute(
            select(ProxyCall).where(
                ProxyCall.id.in_(call_ids)
            ).order_by(ProxyCall.created_at).limit(limit)
        )
        return list(result.scalars().all())

    async def get_incident_events_in_window(
        self, incident_id: str, window_start: datetime, window_end: datetime
    ) -> List[Any]:
        """Get incident events within a time window."""
        from app.models.killswitch import IncidentEvent

        result = await self._session.execute(
            select(IncidentEvent).where(
                and_(
                    IncidentEvent.incident_id == incident_id,
                    IncidentEvent.created_at >= window_start,
                    IncidentEvent.created_at <= window_end,
                )
            ).order_by(IncidentEvent.created_at)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Today Snapshot (aggregates)
    # =========================================================================

    async def get_today_request_stats(self, tenant_id: str, today_start: datetime) -> Tuple[int, int]:
        """Get request count and total spend for today. Returns (count, spend_cents)."""
        from app.models.killswitch import ProxyCall

        result = await self._session.execute(
            select(
                func.count(ProxyCall.id),
                func.coalesce(func.sum(ProxyCall.cost_cents), 0),
            ).where(
                and_(
                    ProxyCall.tenant_id == tenant_id,
                    ProxyCall.created_at >= today_start,
                )
            )
        )
        row = result.first()
        return (row[0] if row else 0, row[1] if row else 0)

    async def get_today_blocked_stats(self, tenant_id: str, today_start: datetime) -> Tuple[int, int]:
        """Get blocked request count and cost avoided for today. Returns (count, cost_cents)."""
        from app.models.killswitch import ProxyCall

        result = await self._session.execute(
            select(
                func.count(ProxyCall.id),
                func.coalesce(func.sum(ProxyCall.cost_cents), 0),
            ).where(
                and_(
                    ProxyCall.tenant_id == tenant_id,
                    ProxyCall.created_at >= today_start,
                    ProxyCall.was_blocked == True,
                )
            )
        )
        row = result.first()
        return (row[0] if row else 0, row[1] if row else 0)

    # =========================================================================
    # API Keys
    # =========================================================================

    async def get_api_key(self, key_id: str) -> Optional[Any]:
        """Get API key by ID."""
        from app.models.tenant import APIKey

        result = await self._session.execute(
            select(APIKey).where(APIKey.id == key_id)
        )
        return result.scalars().first()

    # =========================================================================
    # Status History
    # =========================================================================

    async def query_status_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        new_status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Any], int]:
        """Query status history with filters. Returns (items, total)."""
        from app.db import StatusHistory

        query = select(StatusHistory)

        if entity_type:
            query = query.where(StatusHistory.entity_type == entity_type)
        if entity_id:
            query = query.where(StatusHistory.entity_id == entity_id)
        if tenant_id:
            query = query.where(StatusHistory.tenant_id == tenant_id)
        if actor_type:
            query = query.where(StatusHistory.actor_type == actor_type)
        if new_status:
            query = query.where(StatusHistory.new_status == new_status)
        if start_time:
            query = query.where(StatusHistory.created_at >= start_time)
        if end_time:
            query = query.where(StatusHistory.created_at <= end_time)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.order_by(desc(StatusHistory.created_at)).offset(offset).limit(limit)
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_entity_status_history(
        self, entity_type: str, entity_id: str, limit: int = 100
    ) -> List[Any]:
        """Get status history for a specific entity."""
        from app.db import StatusHistory

        result = await self._session.execute(
            select(StatusHistory)
            .where(StatusHistory.entity_type == entity_type)
            .where(StatusHistory.entity_id == entity_id)
            .order_by(StatusHistory.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_status_history(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Any]:
        """Get all status history records matching filters (for export)."""
        from app.db import StatusHistory

        query = select(StatusHistory)

        if entity_type:
            query = query.where(StatusHistory.entity_type == entity_type)
        if entity_id:
            query = query.where(StatusHistory.entity_id == entity_id)
        if tenant_id:
            query = query.where(StatusHistory.tenant_id == tenant_id)
        if start_time:
            query = query.where(StatusHistory.created_at >= start_time)
        if end_time:
            query = query.where(StatusHistory.created_at <= end_time)

        query = query.order_by(StatusHistory.created_at.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_status_history_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status history statistics."""
        from app.db import StatusHistory

        base_filter = StatusHistory.tenant_id == tenant_id if tenant_id else True

        # Total count
        total_result = await self._session.execute(
            select(func.count(StatusHistory.id)).where(base_filter)
        )
        total_records = total_result.scalar() or 0

        # By entity type
        et_result = await self._session.execute(
            select(StatusHistory.entity_type, func.count()).where(base_filter).group_by(StatusHistory.entity_type)
        )
        records_by_entity_type = {et: count for et, count in et_result.all()}

        # By actor type
        at_result = await self._session.execute(
            select(StatusHistory.actor_type, func.count()).where(base_filter).group_by(StatusHistory.actor_type)
        )
        records_by_actor_type = {at: count for at, count in at_result.all()}

        # By status
        st_result = await self._session.execute(
            select(StatusHistory.new_status, func.count()).where(base_filter).group_by(StatusHistory.new_status)
        )
        records_by_status = {s: count for s, count in st_result.all()}

        # Time range
        time_result = await self._session.execute(
            select(func.min(StatusHistory.created_at), func.max(StatusHistory.created_at)).where(base_filter)
        )
        oldest, newest = time_result.first() or (None, None)

        time_range_days = None
        if oldest and newest:
            time_range_days = (newest - oldest).total_seconds() / 86400

        return {
            "total_records": total_records,
            "records_by_entity_type": records_by_entity_type,
            "records_by_actor_type": records_by_actor_type,
            "records_by_status": records_by_status,
            "oldest_record": oldest,
            "newest_record": newest,
            "time_range_days": time_range_days,
        }

    # =========================================================================
    # Customer Visibility
    # =========================================================================

    async def fetch_run_outcome(self, run_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Fetch run data for outcome reconciliation."""
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                SELECT
                    id, agent_id, goal, status,
                    attempts, max_attempts,
                    error_message,
                    started_at, completed_at, duration_ms
                FROM runs
                WHERE id = :run_id AND tenant_id = :tenant_id
            """),
            {"run_id": run_id, "tenant_id": tenant_id},
        )
        row = result.fetchone()
        if not row:
            return None

        return {
            "id": row.id,
            "agent_id": row.agent_id,
            "goal": row.goal,
            "status": row.status,
            "attempts": row.attempts,
            "max_attempts": row.max_attempts,
            "error_message": row.error_message,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
            "duration_ms": row.duration_ms,
        }

    async def fetch_decision_summary(self, run_id: str, tenant_id: str) -> Dict[str, Any]:
        """Fetch decision summary for outcome reconciliation (effects only)."""
        from sqlalchemy import text

        try:
            budget_result = await self._session.execute(
                text("""
                    SELECT COUNT(*) FROM contracts.decision_records
                    WHERE run_id = :run_id
                    AND tenant_id = :tenant_id
                    AND decision_type = 'budget'
                    AND decision_outcome != 'selected'
                """),
                {"run_id": run_id, "tenant_id": tenant_id},
            )
            budget_warnings = budget_result.scalar() or 0

            policy_result = await self._session.execute(
                text("""
                    SELECT COUNT(*) FROM contracts.decision_records
                    WHERE run_id = :run_id
                    AND tenant_id = :tenant_id
                    AND decision_type = 'policy'
                    AND decision_outcome IN ('blocked', 'rejected')
                """),
                {"run_id": run_id, "tenant_id": tenant_id},
            )
            policy_warnings = policy_result.scalar() or 0

            recovery_result = await self._session.execute(
                text("""
                    SELECT COUNT(*) FROM contracts.decision_records
                    WHERE run_id = :run_id
                    AND tenant_id = :tenant_id
                    AND decision_type = 'recovery'
                """),
                {"run_id": run_id, "tenant_id": tenant_id},
            )
            recovery_count = recovery_result.scalar() or 0

            return {
                "budget_warnings": budget_warnings,
                "policy_warnings": policy_warnings,
                "recovery_attempted": recovery_count > 0,
            }
        except Exception:
            return {"budget_warnings": 0, "policy_warnings": 0, "recovery_attempted": False}

    # =========================================================================
    # RBAC Audit
    # =========================================================================

    async def query_rbac_audit(
        self,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        allowed: Optional[bool] = None,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Query RBAC audit logs. Returns (entries, total)."""
        from sqlalchemy import text

        where_clauses = []
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if resource:
            where_clauses.append("resource = :resource")
            params["resource"] = resource
        if action:
            where_clauses.append("action = :action")
            params["action"] = action
        if allowed is not None:
            where_clauses.append("allowed = :allowed")
            params["allowed"] = allowed
        if subject:
            where_clauses.append("subject = :subject")
            params["subject"] = subject
        if tenant_id:
            where_clauses.append("tenant_id = :tenant_id")
            params["tenant_id"] = tenant_id
        if since:
            where_clauses.append("ts >= :since")
            params["since"] = since

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_result = await self._session.execute(
            text(f"SELECT COUNT(*) FROM system.rbac_audit WHERE {where_sql}"),
            params,
        )
        total = count_result.scalar() or 0

        result = await self._session.execute(
            text(f"""
                SELECT id, ts, subject, resource, action, allowed, reason, roles,
                       path, method, tenant_id, latency_ms
                FROM system.rbac_audit
                WHERE {where_sql}
                ORDER BY ts DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )

        entries = []
        for row in result:
            entries.append({
                "id": row.id,
                "ts": row.ts,
                "subject": row.subject,
                "resource": row.resource,
                "action": row.action,
                "allowed": row.allowed,
                "reason": row.reason,
                "roles": row.roles,
                "path": row.path,
                "method": row.method,
                "tenant_id": row.tenant_id,
                "latency_ms": row.latency_ms,
            })

        return entries, total

    # NOTE: cleanup_rbac_audit removed — use RbacAuditDriver instead (PIN-L2-PURITY)

    # =========================================================================
    # Workers / Cost
    # =========================================================================

    async def get_worker_run(self, run_id: str) -> Optional[Any]:
        """Get worker run by ID."""
        from app.models.tenant import WorkerRun

        result = await self._session.execute(
            select(WorkerRun).where(WorkerRun.id == run_id)
        )
        return result.scalars().first()

    async def list_worker_runs(self, limit: int = 20, tenant_id: Optional[str] = None) -> List[Any]:
        """List recent worker runs."""
        from app.models.tenant import WorkerRun

        query = select(WorkerRun).order_by(WorkerRun.created_at.desc()).limit(limit)
        if tenant_id:
            query = query.where(WorkerRun.tenant_id == tenant_id)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_worker_runs(self) -> int:
        """Count total worker runs."""
        from app.models.tenant import WorkerRun

        result = await self._session.execute(
            select(func.count()).select_from(WorkerRun)
        )
        return result.scalar() or 0

    async def get_cost_budget(self, tenant_id: str) -> Optional[Any]:
        """Get active cost budget for a tenant."""
        from app.db import CostBudget

        result = await self._session.execute(
            select(CostBudget).where(
                CostBudget.tenant_id == tenant_id,
                CostBudget.is_active == True,
                CostBudget.budget_type == "tenant",
            )
        )
        return result.scalars().first()

    async def get_daily_spend(self, tenant_id: str, today_start: datetime) -> int:
        """Get daily spend in cents."""
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                SELECT COALESCE(SUM(cost_cents), 0)
                FROM cost_records
                WHERE tenant_id = :tenant_id
                AND created_at >= :today_start
            """),
            {"tenant_id": tenant_id, "today_start": today_start},
        )
        return int(result.scalar() or 0)

    async def check_existing_advisory(self, run_id: str) -> Optional[str]:
        """Check if a cost advisory already exists for a run."""
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                SELECT id FROM cost_anomalies
                WHERE anomaly_type = 'BUDGET_WARNING'
                AND metadata->>'run_id' = :run_id
            """),
            {"run_id": run_id},
        )
        return result.scalar_one_or_none()

    async def count_advisories_for_run(self, tenant_id: str, run_id: str) -> int:
        """Count advisory entries for a run."""
        from sqlalchemy import text

        result = await self._session.execute(
            text("""
                SELECT COUNT(*)
                FROM cost_anomalies
                WHERE tenant_id = :tenant_id
                AND anomaly_type = 'BUDGET_WARNING'
                AND metadata->>'run_id' = :run_id
            """),
            {"tenant_id": tenant_id, "run_id": run_id},
        )
        return int(result.scalar() or 0)

    async def get_run_by_id(self, run_id: str) -> Optional[Any]:
        """Get a Run (not WorkerRun) by ID."""
        from app.db import Run

        result = await self._session.execute(
            select(Run).where(Run.id == run_id)
        )
        return result.scalars().first()

    # =========================================================================
    # Policy Proposals
    # =========================================================================

    async def list_policy_proposals(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        proposal_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Any], int]:
        """List policy proposals with filters. Returns (items, total)."""
        from app.models.policy import PolicyProposal

        query = select(PolicyProposal).order_by(PolicyProposal.created_at.desc())
        if tenant_id:
            query = query.where(PolicyProposal.tenant_id == tenant_id)
        if status:
            query = query.where(PolicyProposal.status == status)
        if proposal_type:
            query = query.where(PolicyProposal.proposal_type == proposal_type)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        query = query.limit(limit).offset(offset)
        result = await self._session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_policy_proposal(self, proposal_id: str) -> Optional[Any]:
        """Get a policy proposal by UUID."""
        from uuid import UUID
        from app.models.policy import PolicyProposal

        result = await self._session.execute(
            select(PolicyProposal).where(PolicyProposal.id == UUID(proposal_id))
        )
        return result.scalars().first()

    async def get_policy_versions(self, proposal_id: str) -> List[Any]:
        """Get policy versions for a proposal."""
        from uuid import UUID
        from app.models.policy import PolicyVersion

        result = await self._session.execute(
            select(PolicyVersion)
            .where(PolicyVersion.proposal_id == UUID(proposal_id))
            .order_by(PolicyVersion.version.desc())
        )
        return list(result.scalars().all())


# =============================================================================
# Sync Guard Read Driver (for L2 APIs using sync session)
# =============================================================================


class SyncGuardReadDriver:
    """
    Synchronous DB read operations for guard/killswitch domain.

    Used by L2 APIs that depend on sync SQLModel Session (via get_sync_session_dep).
    All queries that were previously in L2 guard.py are now here.
    """

    def __init__(self, session: Any):
        """Initialize with a sync SQLModel Session."""
        self._session = session

    # =========================================================================
    # Tenant Operations
    # =========================================================================

    def get_tenant_by_id(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant by ID as a dict. Returns None if not found."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT * FROM tenants WHERE id = :id"),
            {"id": tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_tenant_name(self, tenant_id: str) -> str:
        """Get tenant name by ID. Returns 'Demo Tenant' if not found."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT id, name FROM tenants WHERE id = :tid"),
            {"tid": tenant_id},
        )
        row = result.mappings().first()
        return row["name"] if row and row.get("name") else "Demo Tenant"

    # =========================================================================
    # KillSwitch State Operations
    # =========================================================================

    def get_tenant_killswitch_state(
        self, entity_type: str, entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get killswitch state for an entity as a dict."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT * FROM kill_switch_states "
                "WHERE entity_type = :etype AND entity_id = :eid"
            ),
            {"etype": entity_type, "eid": entity_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    # =========================================================================
    # Guardrail Operations
    # =========================================================================

    def get_active_guardrail_names(self) -> List[str]:
        """Get names of all enabled guardrails."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT name FROM default_guardrails WHERE is_enabled = true"),
        )
        return [r["name"] for r in result.mappings().all()]

    def get_enabled_guardrails_raw(self) -> List[Dict[str, Any]]:
        """Get all enabled guardrails as dicts, ordered by priority."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT * FROM default_guardrails "
                "WHERE is_enabled = true ORDER BY priority"
            ),
        )
        return [dict(r) for r in result.mappings().all()]

    def get_all_guardrails_raw(self) -> List[Dict[str, Any]]:
        """Get all guardrails as dicts, ordered by priority."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT * FROM default_guardrails ORDER BY priority"),
        )
        return [dict(r) for r in result.mappings().all()]

    def get_enabled_guardrail_id_names(self) -> List[Dict[str, Any]]:
        """Get id, name, is_enabled of enabled guardrails."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT id, name, is_enabled FROM default_guardrails "
                "WHERE is_enabled = true"
            ),
        )
        return [dict(r) for r in result.mappings().all()]

    # =========================================================================
    # Incident Operations
    # =========================================================================

    def count_tenant_incidents_since(
        self, tenant_id: str, since: datetime
    ) -> int:
        """Count incidents for tenant since a datetime."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT COUNT(*) AS cnt FROM incidents "
                "WHERE tenant_id = :tid AND created_at >= :since"
            ),
            {"tid": tenant_id, "since": since},
        )
        row = result.mappings().first()
        return row["cnt"] if row else 0

    def get_last_tenant_incident_time(
        self, tenant_id: str
    ) -> Optional[datetime]:
        """Get the created_at time of the most recent incident for a tenant."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT created_at FROM incidents "
                "WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1"
            ),
            {"tid": tenant_id},
        )
        row = result.mappings().first()
        return row["created_at"] if row else None

    def get_incident_by_id_raw(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident by ID as a dict."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT * FROM incidents WHERE id = :id"),
            {"id": incident_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_incident_by_id_and_tenant_raw(
        self, incident_id: str, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get incident by ID and tenant as a dict."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT * FROM incidents WHERE id = :id AND tenant_id = :tid"),
            {"id": incident_id, "tid": tenant_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    def get_incident_events_raw(
        self, incident_id: str
    ) -> List[Dict[str, Any]]:
        """Get incident events ordered by created_at as dicts."""
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT * FROM incident_events "
                "WHERE incident_id = :iid ORDER BY created_at"
            ),
            {"iid": incident_id},
        )
        return [dict(r) for r in result.mappings().all()]

    def search_incidents_raw(
        self,
        tenant_id: str,
        severity: Optional[str] = None,
        time_from: Optional[datetime] = None,
        time_to: Optional[datetime] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Search incidents with filters. Returns (items, total).
        """
        from sqlalchemy import text

        where_clauses = ["tenant_id = :tenant_id"]
        params: Dict[str, Any] = {"tenant_id": tenant_id}

        if severity:
            where_clauses.append("severity = :severity")
            params["severity"] = severity

        if time_from:
            where_clauses.append("started_at >= :time_from")
            params["time_from"] = time_from

        if time_to:
            where_clauses.append("started_at <= :time_to")
            params["time_to"] = time_to

        if query:
            where_clauses.append("title ILIKE :query_pattern")
            params["query_pattern"] = f"%{query}%"

        where_sql = " AND ".join(where_clauses)

        # Count query
        count_sql = f"SELECT COUNT(*) AS cnt FROM incidents WHERE {where_sql}"
        count_result = self._session.execute(text(count_sql), params)
        count_row = count_result.mappings().first()
        total = count_row["cnt"] if count_row else 0

        # Main query
        query_sql = (
            f"SELECT * FROM incidents WHERE {where_sql} "
            "ORDER BY created_at DESC OFFSET :offset LIMIT :lim"
        )
        params["offset"] = offset
        params["lim"] = limit

        result = self._session.execute(text(query_sql), params)
        items = [dict(r) for r in result.mappings().all()]

        return items, total

    # =========================================================================
    # Proxy Call Operations
    # =========================================================================

    def get_proxy_call_by_id_raw(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get proxy call by ID as a dict."""
        from sqlalchemy import text

        result = self._session.execute(
            text("SELECT * FROM proxy_calls WHERE id = :id"),
            {"id": call_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    # =========================================================================
    # Today Snapshot (aggregates)
    # =========================================================================

    def get_tenant_today_request_stats(
        self, tenant_id: str, today_start: datetime
    ) -> Tuple[int, int]:
        """
        Get request count and total spend for today.
        Returns (count, spend_cents).
        """
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(cost_cents), 0) AS total_cost "
                "FROM proxy_calls WHERE tenant_id = :tid AND created_at >= :since"
            ),
            {"tid": tenant_id, "since": today_start},
        )
        row = result.mappings().first()
        return (row["cnt"] if row else 0, row["total_cost"] if row else 0)

    def get_tenant_today_blocked_stats(
        self, tenant_id: str, today_start: datetime
    ) -> Tuple[int, int]:
        """
        Get blocked request count and cost avoided for today.
        Returns (count, cost_cents).
        """
        from sqlalchemy import text

        result = self._session.execute(
            text(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(cost_cents), 0) AS total_cost "
                "FROM proxy_calls WHERE tenant_id = :tid AND created_at >= :since "
                "AND was_blocked = true"
            ),
            {"tid": tenant_id, "since": today_start},
        )
        row = result.mappings().first()
        return (row["cnt"] if row else 0, row["total_cost"] if row else 0)


def get_sync_guard_read_driver(session: Any) -> SyncGuardReadDriver:
    """Factory function to get SyncGuardReadDriver instance."""
    return SyncGuardReadDriver(session)
