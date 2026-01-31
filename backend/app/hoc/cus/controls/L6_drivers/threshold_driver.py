# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async/sync
# Lifecycle:
#   Emits: THRESHOLD_SIGNAL
#   Subscribes: none
# Data Access:
#   Reads: Limit, LimitBreach
#   Writes: none (read-only, signals via EventEmitter)
# Database:
#   Scope: domain (activity)
#   Models: Limit, LimitBreach
# Role: Database operations for threshold limits
# Callers: threshold_engine.py (L5)
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, docs/architecture/hoc/INDEX.md → Activity Phase 2.5A
#
# DRIVER CONTRACT:
# - Returns domain objects (LimitSnapshot), not ORM models
# - No business logic (no precedence rules, no evaluation)
# - Pure data access operations

"""
Threshold Driver (L6)

Provides:
- LimitSnapshot: Immutable snapshot returned to engines
- ThresholdDriver: Async DB operations for threshold limits
- ThresholdDriverSync: Sync DB operations for worker context
- Signal emission functions for dual console output

This driver owns the DATA ACCESS logic:
- Query active threshold limits from database
- Emit signals to ops_events table
- Update run risk levels

The driver does NOT own:
- Precedence resolution (delegated to L4 engine)
- Threshold evaluation (delegated to L4 engine)
- Signal determination (delegated to L4 engine)

Reference: ACTIVITY_PHASE2.5_IMPLEMENTATION_PLAN.md
"""

import logging
import uuid as uuid_module
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.policy_control_plane import Limit, LimitCategory, LimitStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Data Transfer Object (L6 → L4 Contract)
# =============================================================================


# Re-export from spine schemas for backward compatibility (PIN-504)
from app.hoc.hoc_spine.schemas.threshold_types import LimitSnapshot  # noqa: F401


# =============================================================================
# Async Driver (for API Context)
# =============================================================================


class ThresholdDriver:
    """
    Async database driver for threshold limit operations.

    L6 CONTRACT:
    - Pure data access, no business logic
    - Returns LimitSnapshot objects, not ORM models
    - No precedence resolution (that's L4)
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_threshold_limits(
        self, tenant_id: str
    ) -> list[LimitSnapshot]:
        """
        Query active threshold limits for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of LimitSnapshot ordered by created_at (oldest first)
        """
        stmt = (
            select(Limit)
            .where(Limit.tenant_id == tenant_id)
            .where(Limit.limit_category == LimitCategory.THRESHOLD.value)
            .where(Limit.status == LimitStatus.ACTIVE.value)
            .order_by(Limit.created_at)  # Older limits first
        )

        result = await self._session.execute(stmt)
        limits = result.scalars().all()

        # Convert ORM models to snapshots
        return [
            LimitSnapshot(
                id=str(limit.id),
                tenant_id=str(limit.tenant_id),
                scope=limit.scope,
                scope_id=limit.scope_id,
                params=limit.params or {},
                status=limit.status,
                created_at=limit.created_at,
            )
            for limit in limits
        ]

    async def get_threshold_limit_by_scope(
        self,
        tenant_id: str,
        scope: str,
        scope_id: Optional[str] = None,
    ) -> Optional[LimitSnapshot]:
        """
        Query a single threshold limit by scope.

        Args:
            tenant_id: Tenant identifier
            scope: Limit scope (GLOBAL, TENANT, PROJECT, AGENT)
            scope_id: Optional scope identifier

        Returns:
            LimitSnapshot if found, None otherwise
        """
        stmt = (
            select(Limit)
            .where(Limit.tenant_id == tenant_id)
            .where(Limit.limit_category == LimitCategory.THRESHOLD.value)
            .where(Limit.status == LimitStatus.ACTIVE.value)
            .where(Limit.scope == scope)
        )

        if scope_id:
            stmt = stmt.where(Limit.scope_id == scope_id)

        result = await self._session.execute(stmt)
        limit = result.scalar_one_or_none()

        if limit is None:
            return None

        return LimitSnapshot(
            id=str(limit.id),
            tenant_id=str(limit.tenant_id),
            scope=limit.scope,
            scope_id=limit.scope_id,
            params=limit.params or {},
            status=limit.status,
            created_at=limit.created_at,
        )


# =============================================================================
# Sync Driver (for Worker Context)
# =============================================================================


class ThresholdDriverSync:
    """
    Sync database driver for threshold limit operations.

    Used in worker context (ThreadPoolExecutor) which doesn't support async.

    L6 CONTRACT:
    - Pure data access, no business logic
    - Returns LimitSnapshot objects
    - Uses raw SQL for sync compatibility
    """

    def __init__(self, session: Any):
        """
        Initialize with a sync SQLAlchemy Session.

        Args:
            session: Sync SQLAlchemy Session
        """
        self._session = session

    def get_active_threshold_limits(
        self, tenant_id: str
    ) -> list[LimitSnapshot]:
        """
        Query active threshold limits for a tenant (sync version).

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of LimitSnapshot ordered by created_at (oldest first)
        """
        result = self._session.execute(
            text("""
                SELECT id, tenant_id, scope, scope_id, params, status, created_at
                FROM limits
                WHERE tenant_id = :tenant_id
                  AND limit_category = 'THRESHOLD'
                  AND status = 'ACTIVE'
                ORDER BY created_at
            """),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()

        return [
            LimitSnapshot(
                id=str(row.id),
                tenant_id=str(row.tenant_id),
                scope=row.scope,
                scope_id=row.scope_id,
                params=row.params or {},
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]


# =============================================================================
# Signal Emission (L6 - DB Write Operations)
# =============================================================================


def emit_threshold_signal_sync(
    session: Any,
    tenant_id: str,
    run_id: str,
    state: str,
    signal: Any,  # ThresholdSignal from engine
    params_used: dict,
) -> None:
    """
    Emit a threshold signal to ops_events table (sync).

    For use in sync contexts (e.g., worker callbacks).

    L6 CONTRACT: Pure DB write, no business logic.

    Args:
        session: Sync SQLAlchemy Session
        tenant_id: Tenant identifier
        run_id: Run identifier
        state: Run state (live or completed)
        signal: ThresholdSignal enum value
        params_used: The params that were evaluated against
    """
    from app.hoc.int.agent.drivers.event_emitter import (
        EntityType,
        EventEmitter,
        EventType,
        OpsEvent,
    )

    # Import ThresholdSignal for mapping
    from app.hoc.cus.controls.L5_engines.threshold_engine import (
        ThresholdSignal,
    )

    emitter = EventEmitter(session)

    # Map signal to event type
    event_type_map = {
        ThresholdSignal.EXECUTION_TIME_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.TOKEN_LIMIT_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.COST_LIMIT_EXCEEDED: EventType.INFRA_LIMIT_HIT,
        ThresholdSignal.RUN_FAILED: EventType.LLM_CALL_FAILED,
    }

    event_type = event_type_map.get(signal, EventType.INFRA_LIMIT_HIT)

    event = OpsEvent(
        tenant_id=uuid_module.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id,
        event_type=event_type,
        entity_type=EntityType.LLM_CALL,
        entity_id=uuid_module.UUID(run_id) if isinstance(run_id, str) else run_id,
        severity=3 if signal == ThresholdSignal.RUN_FAILED else 2,
        metadata={
            "signal": signal.value,
            "state": state,
            "params_used": params_used,
            "domain": "llm_runs",
        },
    )

    emitter.emit(event)

    logger.info(
        "Emitted threshold signal %s for run %s (state=%s)",
        signal.value,
        run_id,
        state,
    )


def emit_and_persist_threshold_signal(
    session: Any,
    tenant_id: str,
    run_id: str,
    state: str,
    signals: list,  # list[ThresholdSignal] from engine
    params_used: dict,
) -> None:
    """
    Emit threshold signals to both Founder and Customer consoles.

    PIN-504: Delegates to SignalCoordinator (L4) to avoid cross-domain
    controls→activity import. The coordinator handles dual emission.

    Args:
        session: SQLAlchemy sync session
        tenant_id: Tenant identifier
        run_id: Run identifier
        state: Run state ("live" or "completed")
        signals: List of ThresholdSignal values
        params_used: The threshold params that were evaluated against

    Reference: Threshold Signal Wiring to Customer Console Plan
    """
    from app.hoc.hoc_spine.orchestrator.coordinators.signal_coordinator import (
        get_signal_coordinator,
    )

    coordinator = get_signal_coordinator()
    coordinator.emit_and_update_risk(
        session=session,
        tenant_id=tenant_id,
        run_id=run_id,
        state=state,
        signals=signals,
        params_used=params_used,
    )
