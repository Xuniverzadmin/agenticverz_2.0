# Layer: L6 — Domain Driver
# NOTE: Renamed circuit_breaker_async.py → circuit_breaker_async_driver.py (2026-01-31) per BANNED_NAMING rule
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: CostSimCBStateModel, CostSimCBIncidentModel, CostSimAlertQueueModel
#   Writes: CostSimCBStateModel, CostSimCBIncidentModel, CostSimAlertQueueModel
# Database:
#   Scope: domain (analytics)
#   Models: CostSimCBStateModel, CostSimCBIncidentModel, CostSimAlertQueueModel
# Role: Async DB-backed circuit breaker state tracking
# Callers: sandbox.py, canary.py (L5 engines)
# Allowed Imports: L6, L7 (models)
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, M6 CostSim
from __future__ import annotations

from app.infra import FeatureIntent, RetryPolicy

# Phase-2.3: Feature Intent Declaration
# Async DB-backed circuit breaker state tracking with SELECT FOR UPDATE
# State mutations are atomic and recoverable
FEATURE_INTENT = FeatureIntent.STATE_MUTATION
RETRY_POLICY = RetryPolicy.SAFE

# CostSim V2 Circuit Breaker - Async Implementation
"""
Fully async DB-backed circuit breaker for CostSim V2.

This module provides non-blocking database access using SQLAlchemy async
sessions. Use this instead of the sync circuit_breaker.py for all async
code paths (FastAPI endpoints, background tasks, etc.).

Features:
- Non-blocking DB operations (won't hang event loop)
- Centralized state in PostgreSQL with SELECT FOR UPDATE
- TTL-based auto-recovery (disabled_until)
- Alertmanager integration with retry queue
- Full audit trail

Usage:
    from app.costsim.circuit_breaker_async import (
        is_v2_disabled,
        disable_v2,
        enable_v2,
        report_drift,
    )

    # Check if V2 is disabled
    if await is_v2_disabled():
        return use_v1_only()

    # Report drift after comparison
    incident = await report_drift(drift_score=0.25, sample_count=100)

    # Manual controls
    await disable_v2(reason="Maintenance", disabled_by="admin")
    await enable_v2(enabled_by="admin", reason="Maintenance complete")
"""

import asyncio
import concurrent.futures
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import AsyncSessionLocal, async_session_context
from app.models.costsim_cb import (
    CostSimAlertQueueModel,
    CostSimCBIncidentModel,
    CostSimCBStateModel,
)

logger = logging.getLogger("nova.costsim.circuit_breaker_async")


# PIN-504: Lazy imports to avoid E2 cross-domain validator violations
def _get_config():
    from app.hoc.cus.hoc_spine.services.costsim_config import get_config as _cfg
    return _cfg()


def _get_metrics():
    from app.hoc.cus.hoc_spine.services.costsim_metrics import get_metrics as _mtr
    return _mtr()


# ========== Sync Wrapper Utilities (PIN-521) ==========
# Inlined from cb_sync_wrapper_engine to avoid L6→L5 import violation

_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    """Get or create the shared thread pool executor for sync wrappers."""
    global _executor
    if _executor is None:
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="cb_sync_")
    return _executor


def _run_async_in_thread(coro, timeout: float = 5.0):
    """Run an async coroutine in a separate thread with its own event loop."""
    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    executor = _get_executor()
    future = executor.submit(run_in_new_loop)
    return future.result(timeout=timeout)


def _is_v2_disabled_sync(timeout: float = 5.0) -> bool:
    """
    Sync wrapper for is_v2_disabled().

    Safe to call from any context. Returns False on error to avoid false-positive disables.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
            return bool(_run_async_in_thread(is_v2_disabled(), timeout))
        except RuntimeError:
            return asyncio.run(is_v2_disabled())
    except concurrent.futures.TimeoutError:
        logger.error("_is_v2_disabled_sync timed out, returning False (enabled)")
        return False
    except Exception as e:
        logger.error(f"_is_v2_disabled_sync error: {e}, returning False (enabled)")
        return False

# Circuit breaker name constant
CB_NAME = "costsim_v2"


@dataclass
class CircuitBreakerState:
    """Current state of the circuit breaker."""

    is_open: bool  # True = V2 disabled
    opened_at: Optional[datetime] = None
    reason: Optional[str] = None
    incident_id: Optional[str] = None
    consecutive_failures: int = 0
    last_failure_at: Optional[datetime] = None
    disabled_until: Optional[datetime] = None
    disabled_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_open": self.is_open,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "reason": self.reason,
            "incident_id": self.incident_id,
            "consecutive_failures": self.consecutive_failures,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "disabled_until": self.disabled_until.isoformat() if self.disabled_until else None,
            "disabled_by": self.disabled_by,
        }


@dataclass
class Incident:
    """Incident record for circuit breaker trip."""

    id: str
    timestamp: datetime
    reason: str
    severity: str  # P1, P2, P3
    drift_score: float
    sample_count: int
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    alert_sent: bool = False
    alert_sent_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "severity": self.severity,
            "drift_score": self.drift_score,
            "sample_count": self.sample_count,
            "details": self.details,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
            "alert_sent": self.alert_sent,
            "alert_sent_at": self.alert_sent_at.isoformat() if self.alert_sent_at else None,
        }


# ========== State Management ==========


async def _get_or_create_state(
    session: AsyncSession,
    lock: bool = False,
) -> CostSimCBStateModel:
    """
    Get or create circuit breaker state row.

    Args:
        session: Async database session
        lock: If True, use SELECT FOR UPDATE to lock the row

    Returns:
        CostSimCBStateModel instance
    """
    statement = select(CostSimCBStateModel).where(CostSimCBStateModel.name == CB_NAME)

    if lock:
        statement = statement.with_for_update()

    result = await session.execute(statement)
    state = result.scalars().first()

    if state is None:
        # Create new state with explicit timestamps for DB compatibility
        now = datetime.now(timezone.utc)
        state = CostSimCBStateModel(
            name=CB_NAME,
            disabled=False,
            consecutive_failures=0,
            updated_at=now,
            created_at=now,
        )
        session.add(state)
        await session.flush()

    return state


async def is_v2_disabled(session: Optional[AsyncSession] = None) -> bool:
    """
    Check if V2 is disabled.

    Non-blocking async check that also handles TTL-based auto-recovery.

    Returns True if:
    - disabled=True AND disabled_until is None (permanent disable)
    - disabled=True AND disabled_until > now (TTL not expired)

    Returns False if:
    - disabled=False
    - disabled=True AND disabled_until <= now (TTL expired, auto-recover)

    Args:
        session: Async session (L4-owned). Creates temporary read session if None.

    Returns:
        True if V2 is disabled
    """
    own_session = session is None

    if own_session:
        session = AsyncSessionLocal()

    try:
        # Fast path: read without lock
        result = await session.execute(select(CostSimCBStateModel).where(CostSimCBStateModel.name == CB_NAME).limit(1))
        state = result.scalars().first()

        if state is None:
            return False

        if not state.disabled:
            return False

        # Check TTL expiration
        if state.disabled_until is not None:
            now = datetime.now(timezone.utc)

            # Ensure timezone-aware comparison
            disabled_until = state.disabled_until
            if disabled_until.tzinfo is None:
                disabled_until = disabled_until.replace(tzinfo=timezone.utc)

            if now >= disabled_until:
                # TTL expired - trigger auto-recovery with proper locking
                config = _get_config()
                if config.auto_recover_enabled:
                    # Auto-recovery uses L4-owned session for state mutations
                    recovered = await _try_auto_recover(session, state.id)
                    if recovered:
                        return False

        return True

    finally:
        if own_session:
            await session.close()


async def _try_auto_recover(session: AsyncSession, state_id: int) -> bool:
    """
    Attempt auto-recovery with proper locking to avoid TOCTOU race.

    Uses SELECT FOR UPDATE to ensure only one worker performs recovery.
    Returns True if recovery was performed (or already done by another worker).

    Transaction Boundary: L4 owns begin/commit (PIN-520).

    Args:
        session: L4-owned async session (already in transaction)
        state_id: ID of the state row to recover

    Returns:
        True if recovered (or already recovered), False if still disabled
    """
    # Re-fetch with lock to check current state
    result = await session.execute(
        select(CostSimCBStateModel)
        .where(CostSimCBStateModel.id == state_id)
        .with_for_update()  # Critical: lock the row
    )
    state = result.scalars().first()

    if state is None:
        return False

    # Another worker may have already recovered
    if not state.disabled:
        return True

    # Re-check TTL (may have changed)
    if state.disabled_until is None:
        # Permanent disable - cannot auto-recover
        return False

    now = datetime.now(timezone.utc)
    disabled_until = state.disabled_until
    if disabled_until.tzinfo is None:
        disabled_until = disabled_until.replace(tzinfo=timezone.utc)

    if now < disabled_until:
        # TTL not yet expired
        return False

    # Perform recovery
    old_incident_id = state.incident_id

    state.disabled = False
    state.disabled_by = None
    state.disabled_reason = None
    state.disabled_until = None
    state.incident_id = None
    state.consecutive_failures = 0
    state.updated_at = now

    await session.flush()

    logger.info(f"Circuit breaker auto-recovered (locked): name={CB_NAME}, old_incident_id={old_incident_id}")

    # Record metrics
    metrics = _get_metrics()
    metrics.record_auto_recovery()
    metrics.record_cb_enabled(reason="auto_recovery")
    metrics.set_circuit_breaker_state(is_open=False)
    metrics.set_consecutive_failures(0)

    # Post-recovery actions (separate session to avoid holding lock)
    if old_incident_id:
        try:
            async with async_session_context() as post_session:
                await _resolve_incident(
                    post_session,
                    old_incident_id,
                    resolved_by="system-auto-recover",
                    resolution_notes="Auto-recovered after TTL expired",
                )

                await _enqueue_alert(
                    post_session,
                    alert_type="enable",
                    payload=_build_enable_alert_payload(
                        enabled_by="system-auto-recover",
                        reason="Auto-recovered after TTL expired",
                    ),
                )
        except Exception as e:
            logger.error(f"Failed post-recovery actions: {e}")

    return True


async def _auto_recover(
    session: AsyncSession,
    state: CostSimCBStateModel,
) -> None:
    """
    Legacy auto-recover function (deprecated).

    Use _try_auto_recover() instead for proper locking.
    """
    if not state.disabled:
        return

    old_incident_id = state.incident_id

    # Reset state
    state.disabled = False
    state.disabled_by = None
    state.disabled_reason = None
    state.disabled_until = None
    state.incident_id = None
    state.consecutive_failures = 0
    state.updated_at = datetime.now(timezone.utc)

    # NO COMMIT — L4 coordinator owns transaction boundary

    # Resolve incident
    if old_incident_id:
        await _resolve_incident(
            session,
            old_incident_id,
            resolved_by="system-auto-recover",
            resolution_notes="Auto-recovered after TTL expired",
        )

    # Enqueue resolved alert
    await _enqueue_alert(
        session,
        alert_type="enable",
        payload=_build_enable_alert_payload(
            enabled_by="system-auto-recover",
            reason="Auto-recovered after TTL expired",
        ),
    )

    logger.info(f"Circuit breaker auto-recovered: name={CB_NAME}, old_incident_id={old_incident_id}")


async def get_state() -> CircuitBreakerState:
    """Get current circuit breaker state."""
    async with async_session_context() as session:
        db_state = await _get_or_create_state(session, lock=False)

        return CircuitBreakerState(
            is_open=db_state.disabled,
            opened_at=db_state.updated_at if db_state.disabled else None,
            reason=db_state.disabled_reason,
            incident_id=db_state.incident_id,
            consecutive_failures=db_state.consecutive_failures,
            last_failure_at=db_state.last_failure_at,
            disabled_until=db_state.disabled_until,
            disabled_by=db_state.disabled_by,
        )


# ========== Drift Reporting ==========


async def report_drift(
    session: AsyncSession,
    drift_score: float,
    sample_count: int = 1,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Incident]:
    """
    Report drift observation.

    If drift exceeds threshold, trips the circuit breaker.

    Transaction Boundary: L4 owns begin/commit (PIN-520).

    Args:
        session: L4-owned async session (already in transaction)
        drift_score: Observed drift score (0.0 - 1.0)
        sample_count: Number of samples in observation
        details: Additional details

    Returns:
        Incident if circuit breaker tripped, None otherwise
    """
    config = _get_config()

    state = await _get_or_create_state(session, lock=True)
    now = datetime.now(timezone.utc)

    # Check if drift exceeds threshold
    if drift_score > config.drift_threshold:
        state.consecutive_failures += 1
        state.last_failure_at = now
        state.updated_at = now

        logger.warning(
            f"Drift threshold exceeded: {drift_score:.4f} > {config.drift_threshold}, "
            f"consecutive_failures={state.consecutive_failures}"
        )

        # Record consecutive failure metric
        metrics = _get_metrics()
        metrics.set_consecutive_failures(state.consecutive_failures)

        # Trip breaker after consecutive failures
        if state.consecutive_failures >= config.failure_threshold:
            incident = await _trip(
                session=session,
                state=state,
                reason=f"Drift exceeded threshold: {drift_score:.4f} > {config.drift_threshold}",
                drift_score=drift_score,
                sample_count=sample_count,
                details=details,
                disabled_by="circuit_breaker",
            )
            return incident
    else:
        # Reset consecutive failures on success
        if state.consecutive_failures > 0:
            logger.info("Drift within threshold, resetting consecutive failures")
            state.consecutive_failures = 0
            state.updated_at = now

    return None


async def report_schema_error(
    session: AsyncSession,
    error_count: int = 1,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Incident]:
    """
    Report schema validation errors.

    Transaction Boundary: L4 owns begin/commit (PIN-520).

    Args:
        session: L4-owned async session (already in transaction)
        error_count: Number of schema errors
        details: Error details

    Returns:
        Incident if threshold exceeded, None otherwise
    """
    config = _get_config()

    if error_count >= config.schema_error_threshold:
        state = await _get_or_create_state(session, lock=True)

        return await _trip(
            session=session,
            state=state,
            reason=f"Schema error threshold exceeded: {error_count} >= {config.schema_error_threshold}",
            drift_score=1.0,
            sample_count=error_count,
            details=details,
            severity="P3",
            disabled_by="circuit_breaker",
        )

    return None


# ========== Manual Controls ==========


async def disable_v2(
    session: AsyncSession,
    reason: str,
    disabled_by: str,
    disabled_until: Optional[datetime] = None,
) -> Tuple[bool, Optional[Incident]]:
    """
    Manually disable CostSim V2.

    Idempotent: returns False if already disabled with same params.

    Transaction Boundary: L4 owns begin/commit (PIN-520).

    Args:
        session: L4-owned async session (already in transaction)
        reason: Reason for disabling
        disabled_by: Who disabled (user_id, system, etc.)
        disabled_until: Optional TTL (None = use default from config)

    Returns:
        Tuple of (state_changed, incident)
    """
    state = await _get_or_create_state(session, lock=True)

    # Check if already disabled with same params
    if state.disabled and state.disabled_reason == reason and state.disabled_until == disabled_until:
        return False, None

    incident = await _trip(
        session=session,
        state=state,
        reason=reason,
        drift_score=0.0,
        sample_count=0,
        details={"manual_disable": True},
        severity="P2",
        disabled_by=disabled_by,
        disabled_until=disabled_until,
    )

    return True, incident


async def enable_v2(
    session: AsyncSession,
    enabled_by: str,
    reason: Optional[str] = None,
) -> bool:
    """
    Manually enable CostSim V2.

    Idempotent: returns False if already enabled.

    Transaction Boundary: L4 owns begin/commit (PIN-520).

    Args:
        session: L4-owned async session (already in transaction)
        enabled_by: Who enabled (user_id, system, etc.)
        reason: Optional reason for enabling

    Returns:
        True if state changed, False otherwise
    """
    state = await _get_or_create_state(session, lock=True)

    if not state.disabled:
        logger.info("Circuit breaker already closed")
        return True

    old_incident_id = state.incident_id
    old_reason = state.disabled_reason

    # Reset state
    state.disabled = False
    state.disabled_by = None
    state.disabled_reason = None
    state.disabled_until = None
    state.incident_id = None
    state.consecutive_failures = 0
    state.updated_at = datetime.now(timezone.utc)

    await session.flush()

    # Resolve incident
    if old_incident_id:
        await _resolve_incident(
            session,
            old_incident_id,
            resolved_by=enabled_by,
            resolution_notes=reason or "Manual reset",
        )

    # Enqueue resolved alert
    await _enqueue_alert(
        session,
        alert_type="enable",
        payload=_build_enable_alert_payload(enabled_by, reason),
    )

    logger.info(
        f"Circuit breaker RESET: incident_id={old_incident_id}, "
        f"reason={reason or 'Manual reset'}, enabled_by={enabled_by}"
    )

    # Record metrics
    metrics = _get_metrics()
    metrics.record_cb_enabled(reason="manual")
    metrics.set_circuit_breaker_state(is_open=False)
    metrics.set_consecutive_failures(0)

    return True


# ========== Trip Logic ==========


async def _trip(
    session: AsyncSession,
    state: CostSimCBStateModel,
    reason: str,
    drift_score: float,
    sample_count: int,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "P1",
    disabled_by: str = "circuit_breaker",
    disabled_until: Optional[datetime] = None,
) -> Incident:
    """
    Trip the circuit breaker.

    Args:
        session: Database session
        state: Circuit breaker state model
        reason: Reason for tripping
        drift_score: Drift score that triggered trip
        sample_count: Number of samples
        details: Additional details
        severity: Alert severity (P1, P2, P3)
        disabled_by: Who disabled
        disabled_until: Optional TTL

    Returns:
        Created Incident
    """
    config = _get_config()
    now = datetime.now(timezone.utc)
    incident_id = str(uuid.uuid4())[:12]

    # Set default TTL if not specified
    if disabled_until is None and config.default_disable_ttl_hours > 0:
        disabled_until = now + timedelta(hours=config.default_disable_ttl_hours)

    # Create incident record
    db_incident = CostSimCBIncidentModel(
        id=incident_id,
        circuit_breaker_name=CB_NAME,
        timestamp=now,
        reason=reason,
        severity=severity,
        drift_score=drift_score,
        sample_count=sample_count,
        details_json=json.dumps(details) if details else None,
    )
    session.add(db_incident)

    # Update state
    state.disabled = True
    state.disabled_by = disabled_by
    state.disabled_reason = reason
    state.disabled_until = disabled_until
    state.incident_id = incident_id
    state.updated_at = now

    await session.flush()

    # Create in-memory incident object
    incident = Incident(
        id=incident_id,
        timestamp=now,
        reason=reason,
        severity=severity,
        drift_score=drift_score,
        sample_count=sample_count,
        details=details or {},
    )

    logger.error(
        f"Circuit breaker TRIPPED: incident_id={incident_id}, "
        f"reason={reason}, severity={severity}, "
        f"disabled_until={disabled_until}"
    )

    # Record metrics
    metrics = _get_metrics()
    metrics.record_cb_disabled(reason="drift" if drift_score > 0 else "manual", severity=severity)
    metrics.record_cb_incident(severity=severity, resolved=False)
    metrics.set_circuit_breaker_state(is_open=True)

    # Enqueue alert (reliable delivery)
    await _enqueue_alert(
        session,
        alert_type="disable",
        incident_id=incident_id,
        payload=_build_disable_alert_payload(incident, disabled_until),
    )

    return incident


# ========== Incident Management ==========


async def _resolve_incident(
    session: AsyncSession,
    incident_id: str,
    resolved_by: str,
    resolution_notes: str,
) -> None:
    """Resolve an incident."""
    result = await session.execute(select(CostSimCBIncidentModel).where(CostSimCBIncidentModel.id == incident_id))
    incident = result.scalars().first()

    if incident:
        incident.resolved = True
        incident.resolved_at = datetime.now(timezone.utc)
        incident.resolved_by = resolved_by
        incident.resolution_notes = resolution_notes
        # NO COMMIT — L4 coordinator owns transaction boundary


async def get_incidents(
    include_resolved: bool = False,
    limit: int = 10,
) -> List[Incident]:
    """
    Get recent incidents.

    Args:
        include_resolved: Include resolved incidents
        limit: Maximum incidents to return

    Returns:
        List of incidents
    """
    async with async_session_context() as session:
        statement = select(CostSimCBIncidentModel).where(CostSimCBIncidentModel.circuit_breaker_name == CB_NAME)

        if not include_resolved:
            statement = statement.where(CostSimCBIncidentModel.resolved == False)

        statement = statement.order_by(CostSimCBIncidentModel.timestamp.desc()).limit(limit)

        result = await session.execute(statement)
        incidents = []

        for db_incident in result.scalars():
            incidents.append(
                Incident(
                    id=db_incident.id,
                    timestamp=db_incident.timestamp,
                    reason=db_incident.reason,
                    severity=db_incident.severity,
                    drift_score=db_incident.drift_score or 0.0,
                    sample_count=db_incident.sample_count or 0,
                    details=db_incident.get_details(),
                    resolved=db_incident.resolved,
                    resolved_at=db_incident.resolved_at,
                    resolved_by=db_incident.resolved_by,
                    resolution_notes=db_incident.resolution_notes,
                    alert_sent=db_incident.alert_sent,
                    alert_sent_at=db_incident.alert_sent_at,
                )
            )

        return incidents


# ========== Alert Queue ==========


async def _enqueue_alert(
    session: AsyncSession,
    alert_type: str,
    payload: List[Dict[str, Any]],
    incident_id: Optional[str] = None,
) -> None:
    """
    Enqueue alert for reliable delivery.

    Args:
        session: Database session
        alert_type: Type of alert (disable, enable, canary_fail)
        payload: Alertmanager payload
        incident_id: Associated incident ID
    """
    alert = CostSimAlertQueueModel(
        payload=payload,
        alert_type=alert_type,
        circuit_breaker_name=CB_NAME,
        incident_id=incident_id,
        status="pending",
    )
    session.add(alert)
    await session.flush()

    logger.debug(f"Alert enqueued: type={alert_type}, incident_id={incident_id}")


def _build_disable_alert_payload(
    incident: Incident,
    disabled_until: Optional[datetime],
) -> List[Dict[str, Any]]:
    """Build Alertmanager payload for disable alert."""
    config = _get_config()

    return [
        {
            "labels": {
                "alertname": "CostSimV2Disabled",
                "severity": incident.severity.lower(),
                "component": "costsim",
                "circuit_breaker": CB_NAME,
                "instance": config.instance_id,
                "incident_id": incident.id,
            },
            "annotations": {
                "summary": f"CostSim V2 circuit breaker tripped ({incident.severity})",
                "description": (
                    f"Reason: {incident.reason}\n"
                    f"Drift score: {incident.drift_score:.4f}\n"
                    f"Sample count: {incident.sample_count}\n"
                    f"Disabled until: {disabled_until.isoformat() if disabled_until else 'manual reset required'}"
                ),
                "runbook_url": "https://docs.aos.internal/runbooks/costsim-circuit-breaker",
            },
            "startsAt": datetime.now(timezone.utc).isoformat(),
        }
    ]


def _build_enable_alert_payload(
    enabled_by: str,
    reason: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Build Alertmanager payload for enable/resolved alert."""
    config = _get_config()
    now = datetime.now(timezone.utc)

    return [
        {
            "labels": {
                "alertname": "CostSimV2Reenabled",
                "severity": "info",
                "component": "costsim",
                "circuit_breaker": CB_NAME,
                "instance": config.instance_id,
            },
            "annotations": {
                "summary": "CostSim V2 circuit breaker re-enabled",
                "description": (f"Re-enabled by: {enabled_by}\nReason: {reason or 'Not specified'}"),
            },
            "startsAt": now.isoformat(),
            "endsAt": now.isoformat(),  # Resolved immediately
        }
    ]


# ========== Sync Compatibility Layer ==========


class AsyncCircuitBreaker:
    """
    Async circuit breaker class for compatibility with existing code.

    Provides the same interface as the sync CircuitBreaker but uses
    async operations internally.
    """

    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        drift_threshold: Optional[float] = None,
        name: str = CB_NAME,
    ):
        config = _get_config()
        self.name = name
        self.failure_threshold = failure_threshold or config.failure_threshold
        self.drift_threshold = drift_threshold or config.drift_threshold
        self.config = config

    async def is_disabled(self) -> bool:
        """Check if V2 is disabled."""
        return await is_v2_disabled()

    def is_open(self) -> bool:
        """
        Sync check if circuit breaker is open.

        Uses thread-safe wrapper to run async function from any context.
        Returns False (enabled) on error to avoid false-positive disables.
        PIN-521: Uses inlined sync wrapper instead of L5 import.
        """
        return _is_v2_disabled_sync()

    def is_closed(self) -> bool:
        """Check if circuit breaker is closed."""
        return not self.is_open()

    async def get_state(self) -> CircuitBreakerState:
        """Get current state."""
        return await get_state()

    async def report_drift(
        self,
        session: AsyncSession,
        drift_score: float,
        sample_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[Incident]:
        """Report drift observation. L4 owns transaction boundary."""
        return await report_drift(session, drift_score, sample_count, details)

    async def report_schema_error(
        self,
        session: AsyncSession,
        error_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[Incident]:
        """Report schema errors. L4 owns transaction boundary."""
        return await report_schema_error(session, error_count, details)

    async def disable_v2(
        self,
        session: AsyncSession,
        reason: str,
        disabled_by: str,
        disabled_until: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[Incident]]:
        """Disable V2. L4 owns transaction boundary."""
        return await disable_v2(session, reason, disabled_by, disabled_until)

    async def enable_v2(
        self,
        session: AsyncSession,
        enabled_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Enable V2. L4 owns transaction boundary."""
        return await enable_v2(session, enabled_by, reason)

    async def reset(
        self,
        session: AsyncSession,
        reason: Optional[str] = None,
        reset_by: Optional[str] = None,
    ) -> bool:
        """Reset circuit breaker. L4 owns transaction boundary."""
        return await enable_v2(session, reset_by or "manual", reason)

    async def reset_v2(
        self,
        session: AsyncSession,
        reason: Optional[str] = None,
        reset_by: Optional[str] = None,
    ) -> bool:
        """Reset circuit breaker (alias for reset). L4 owns transaction."""
        return await self.reset(session=session, reason=reason, reset_by=reset_by)

    def get_incidents(
        self,
        include_resolved: bool = False,
        limit: int = 10,
    ) -> List[Incident]:
        """Get incidents (runs async in sync context)."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("get_incidents() called from running event loop")
                return []
            return loop.run_until_complete(get_incidents(include_resolved, limit))
        except RuntimeError:
            return asyncio.run(get_incidents(include_resolved, limit))


# Global instance
_async_circuit_breaker: Optional[AsyncCircuitBreaker] = None


def get_async_circuit_breaker() -> AsyncCircuitBreaker:
    """Get the global async circuit breaker instance."""
    global _async_circuit_breaker
    if _async_circuit_breaker is None:
        _async_circuit_breaker = AsyncCircuitBreaker()
    return _async_circuit_breaker


# Alias for drop-in replacement of legacy app.costsim.circuit_breaker.get_circuit_breaker()
get_circuit_breaker = get_async_circuit_breaker
