# CostSim V2 Circuit Breaker (M6 - DB-backed)
"""
DB-backed auto-disable circuit breaker for CostSim V2.

Features:
- Centralized state in PostgreSQL (costsim_cb_state table)
- Multi-replica safe via SELECT FOR UPDATE
- TTL-based auto-recovery (disabled_until)
- Alertmanager integration for P1/P2/P3 alerts
- Full audit trail in costsim_cb_incidents table

When drift exceeds thresholds, the circuit breaker:
1. Updates DB state atomically (disabled=True)
2. Creates an incident record for audit
3. Sends P1 alert to Alertmanager
4. Optionally sets TTL for auto-recovery

The circuit breaker can be re-enabled by:
1. Manual reset via /costsim/v2/reset endpoint
2. Auto-recovery after disabled_until expires (if configured)

Usage:
    from app.costsim.circuit_breaker import get_circuit_breaker

    cb = get_circuit_breaker()

    # Check if V2 is disabled
    if await cb.is_disabled():
        return use_v1_only()

    # Report drift after comparison
    incident = await cb.report_drift(drift_score=0.25, sample_count=100)
    if incident:
        logger.error(f"Circuit breaker tripped: {incident.id}")

    # Manual reset
    await cb.reset(reason="Fixed model coefficients", reset_by="admin")
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlmodel import Session, select

from app.costsim.config import get_config
from app.db import (
    CostSimCBIncident,
    CostSimCBState,
    engine,
    log_status_change,
)

logger = logging.getLogger("nova.costsim.circuit_breaker")

# Circuit breaker name constant
CB_NAME = "costsim_v2"


@dataclass
class CircuitBreakerState:
    """Current state of the circuit breaker (in-memory representation)."""

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


class CircuitBreaker:
    """
    DB-backed circuit breaker for CostSim V2 auto-disable.

    Uses PostgreSQL for centralized state management across replicas.
    Sends alerts to Alertmanager when state changes.

    Usage:
        breaker = CircuitBreaker()

        # Check before running V2
        if not await breaker.is_disabled():
            result = await v2_adapter.simulate(plan)

        # Report drift after comparison
        incident = await breaker.report_drift(
            drift_score=0.25,
            sample_count=100,
            details={"kl_divergence": 0.3}
        )

        # Manual reset
        await breaker.reset(reason="Fixed V2 model coefficients", reset_by="admin")
    """

    def __init__(
        self,
        failure_threshold: Optional[int] = None,
        drift_threshold: Optional[float] = None,
        name: str = CB_NAME,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Consecutive failures to trip breaker (default from config)
            drift_threshold: Override drift threshold (default from config)
            name: Circuit breaker name (default: costsim_v2)
        """
        config = get_config()

        self.name = name
        self.failure_threshold = failure_threshold or config.failure_threshold
        self.drift_threshold = drift_threshold or config.drift_threshold
        self.config = config

        # Legacy file paths for backward compatibility
        self.disable_file_path = Path(config.disable_file_path)
        self.incident_dir = Path(config.incident_dir)

        # Ensure incident directory exists (for legacy file-based audit)
        # Fail gracefully if directory cannot be created (e.g., in containers/CI)
        try:
            self.incident_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, FileNotFoundError, OSError):
            # Fall back to COSTSIM_INCIDENT_DIR or /tmp for containers without /var/lib/aos access
            # FileNotFoundError can occur when parent path traversal fails
            # OSError covers other filesystem issues
            import logging
            import os

            logger = logging.getLogger("nova.costsim.circuit_breaker")
            fallback_path = os.environ.get("COSTSIM_INCIDENT_DIR", "/tmp/aos_costsim_incidents")
            fallback_dir = Path(fallback_path)
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.incident_dir = fallback_dir
            logger.warning(f"Cannot create {config.incident_dir}, using fallback: {fallback_dir}")

    def _get_session(self) -> Session:
        """Get a database session."""
        return Session(engine)

    # ========== State Management ==========

    def _get_or_create_state(self, session: Session) -> CostSimCBState:
        """
        Get or create circuit breaker state row.

        Uses SELECT FOR UPDATE to lock the row for atomic updates.
        """
        # Try to select with lock
        statement = select(CostSimCBState).where(CostSimCBState.name == self.name).with_for_update()

        result = session.exec(statement).first()
        # Handle both Row tuple and direct model returns
        if result is None:
            state = None
        elif hasattr(result, "name"):  # Already a model
            state = result
        else:  # Row tuple
            state = result[0]

        if state is None:
            # Create new state
            state = CostSimCBState(
                name=self.name,
                disabled=False,
                consecutive_failures=0,
            )
            session.add(state)
            session.commit()
            session.refresh(state)

        return state

    async def is_disabled(self) -> bool:
        """
        Check if V2 is disabled.

        Returns True if:
        - disabled=True AND disabled_until is None (permanent disable)
        - disabled=True AND disabled_until > now (TTL not expired)

        Returns False if:
        - disabled=False
        - disabled=True AND disabled_until <= now (TTL expired, auto-recover)
        """
        with self._get_session() as session:
            state = self._get_or_create_state(session)

            if not state.disabled:
                return False

            # Check TTL expiration
            if state.disabled_until is not None:
                now = datetime.now(timezone.utc)
                # Convert to naive datetime for comparison if needed
                disabled_until = state.disabled_until
                if disabled_until.tzinfo is None:
                    disabled_until = disabled_until.replace(tzinfo=timezone.utc)

                if now >= disabled_until:
                    # TTL expired - auto-recover
                    if self.config.auto_recover_enabled:
                        await self._auto_recover(session)
                        return False

            return True

    async def _auto_recover(self, session: Session) -> None:
        """Auto-recover circuit breaker after TTL expires."""
        state = self._get_or_create_state(session)

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
        session.commit()

        # Resolve incident
        if old_incident_id:
            self._resolve_incident_db(
                session,
                old_incident_id,
                resolved_by="system-auto-recover",
                resolution_notes="Auto-recovered after TTL expired",
            )

        # Log status change
        log_status_change(
            session=session,
            entity_type="circuit_breaker",
            entity_id=self.name,
            old_status="disabled",
            new_status="enabled",
            actor_type="system",
            actor_id="auto-recover",
            reason="TTL expired, auto-recovery triggered",
        )

        # Send resolved alert
        await self._send_alert_enable(
            enabled_by="system-auto-recover",
            reason="Auto-recovered after TTL expired",
        )

        logger.info(f"Circuit breaker auto-recovered: name={self.name}, " f"old_incident_id={old_incident_id}")

    def is_open(self) -> bool:
        """
        Synchronous check if circuit breaker is open (V2 disabled).

        Note: For async code, use is_disabled() instead.
        """
        with self._get_session() as session:
            state = self._get_or_create_state(session)
            return state.disabled

    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (V2 enabled)."""
        return not self.is_open()

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        with self._get_session() as session:
            db_state = self._get_or_create_state(session)
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
        self,
        drift_score: float,
        sample_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[Incident]:
        """
        Report drift observation.

        If drift exceeds threshold, trips the circuit breaker.

        Args:
            drift_score: Observed drift score (0.0 - 1.0)
            sample_count: Number of samples in observation
            details: Additional details

        Returns:
            Incident if circuit breaker tripped, None otherwise
        """
        with self._get_session() as session:
            state = self._get_or_create_state(session)
            now = datetime.now(timezone.utc)

            # Check if drift exceeds threshold
            if drift_score > self.drift_threshold:
                state.consecutive_failures += 1
                state.last_failure_at = now
                state.updated_at = now
                session.commit()

                logger.warning(
                    f"Drift threshold exceeded: {drift_score:.4f} > {self.drift_threshold}, "
                    f"consecutive_failures={state.consecutive_failures}"
                )

                # Trip breaker after consecutive failures
                if state.consecutive_failures >= self.failure_threshold:
                    return await self._trip(
                        session=session,
                        reason=f"Drift exceeded threshold: {drift_score:.4f} > {self.drift_threshold}",
                        drift_score=drift_score,
                        sample_count=sample_count,
                        details=details,
                        disabled_by="circuit_breaker",
                    )
            else:
                # Reset consecutive failures on success
                if state.consecutive_failures > 0:
                    logger.info("Drift within threshold, resetting consecutive failures")
                    state.consecutive_failures = 0
                    state.updated_at = now
                    session.commit()

            return None

    async def report_schema_error(
        self,
        error_count: int = 1,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[Incident]:
        """
        Report schema validation errors.

        Args:
            error_count: Number of schema errors
            details: Error details

        Returns:
            Incident if threshold exceeded, None otherwise
        """
        if error_count >= self.config.schema_error_threshold:
            with self._get_session() as session:
                return await self._trip(
                    session=session,
                    reason=f"Schema error threshold exceeded: {error_count} >= {self.config.schema_error_threshold}",
                    drift_score=1.0,  # Schema errors are severe
                    sample_count=error_count,
                    details=details,
                    severity="P3",
                    disabled_by="circuit_breaker",
                )

        return None

    # ========== Manual Controls ==========

    async def disable_v2(
        self,
        reason: str,
        disabled_by: str,
        disabled_until: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[Incident]]:
        """
        Manually disable CostSim V2.

        Idempotent: returns False if already disabled with same params.

        Args:
            reason: Reason for disabling
            disabled_by: Who disabled (user_id, system, etc.)
            disabled_until: Optional TTL (None = manual reset required)

        Returns:
            Tuple of (state_changed, incident)
        """
        with self._get_session() as session:
            state = self._get_or_create_state(session)

            # Check if already disabled with same reason
            # Note: We only check reason, not disabled_until, because the TTL may
            # have been defaulted (e.g., 24h) on the first call. Re-disabling with
            # the same reason should be idempotent regardless of TTL differences.
            if state.disabled and state.disabled_reason == reason:
                return False, None

            # Trip the breaker
            incident = await self._trip(
                session=session,
                reason=reason,
                drift_score=0.0,  # Manual disable, not drift-triggered
                sample_count=0,
                details={"manual_disable": True},
                severity="P2",
                disabled_by=disabled_by,
                disabled_until=disabled_until,
            )

            return True, incident

    async def enable_v2(
        self,
        enabled_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Manually enable CostSim V2.

        Idempotent: returns False if already enabled.

        Args:
            enabled_by: Who enabled (user_id, system, etc.)
            reason: Optional reason for enabling

        Returns:
            True if state changed, False otherwise
        """
        return await self.reset(reason=reason or "Manual enable", reset_by=enabled_by)

    async def reset(
        self,
        reason: Optional[str] = None,
        reset_by: Optional[str] = None,
    ) -> bool:
        """
        Reset the circuit breaker.

        Args:
            reason: Reason for reset
            reset_by: Who reset (user_id, system, etc.)

        Returns:
            True if reset successful
        """
        with self._get_session() as session:
            state = self._get_or_create_state(session)

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
            session.commit()

            # Resolve incident
            if old_incident_id:
                self._resolve_incident_db(
                    session,
                    old_incident_id,
                    resolved_by=reset_by or "manual",
                    resolution_notes=reason or "Manual reset",
                )

            # Log status change
            log_status_change(
                session=session,
                entity_type="circuit_breaker",
                entity_id=self.name,
                old_status="disabled",
                new_status="enabled",
                actor_type="user" if reset_by else "system",
                actor_id=reset_by,
                reason=reason or "Manual reset",
                metadata={
                    "old_incident_id": old_incident_id,
                    "old_reason": old_reason,
                },
            )

            logger.info(
                f"Circuit breaker RESET: incident_id={old_incident_id}, "
                f"reason={reason or 'Manual reset'}, reset_by={reset_by}"
            )

            # Send resolved alert
            await self._send_alert_enable(
                enabled_by=reset_by or "manual",
                reason=reason or "Manual reset",
            )

            return True

    # ========== Trip Logic ==========

    async def _trip(
        self,
        session: Session,
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
        now = datetime.now(timezone.utc)
        incident_id = str(uuid.uuid4())[:12]

        # Set default TTL if not specified
        if disabled_until is None and self.config.default_disable_ttl_hours > 0:
            disabled_until = now + timedelta(hours=self.config.default_disable_ttl_hours)

        # Create incident record in DB
        db_incident = CostSimCBIncident(
            id=incident_id,
            circuit_breaker_name=self.name,
            timestamp=now,
            reason=reason,
            severity=severity,
            drift_score=drift_score,
            sample_count=sample_count,
            details_json=json.dumps(details) if details else None,
        )
        session.add(db_incident)

        # Update state
        state = self._get_or_create_state(session)
        state.disabled = True
        state.disabled_by = disabled_by
        state.disabled_reason = reason
        state.disabled_until = disabled_until
        state.incident_id = incident_id
        state.updated_at = now
        session.commit()

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

        # Log status change
        log_status_change(
            session=session,
            entity_type="circuit_breaker",
            entity_id=self.name,
            old_status="enabled",
            new_status="disabled",
            actor_type="system",
            actor_id=disabled_by,
            reason=reason,
            metadata={
                "incident_id": incident_id,
                "severity": severity,
                "drift_score": drift_score,
                "disabled_until": disabled_until.isoformat() if disabled_until else None,
            },
        )

        logger.error(
            f"Circuit breaker TRIPPED: incident_id={incident_id}, "
            f"reason={reason}, severity={severity}, "
            f"disabled_until={disabled_until}"
        )

        # Send alert (async, non-blocking)
        alert_result = await self._send_alert_disable(incident, disabled_until)

        # Update incident with alert status
        if alert_result:
            db_incident.alert_sent = True
            db_incident.alert_sent_at = datetime.now(timezone.utc)
            session.commit()
            incident.alert_sent = True
            incident.alert_sent_at = datetime.now(timezone.utc)

        # Also save to file for backward compatibility
        self._save_incident_file(incident)

        return incident

    # ========== Incident Management ==========

    def _resolve_incident_db(
        self,
        session: Session,
        incident_id: str,
        resolved_by: str,
        resolution_notes: str,
    ) -> None:
        """Resolve an incident in the database."""
        statement = select(CostSimCBIncident).where(CostSimCBIncident.id == incident_id)
        result = session.exec(statement).first()
        # Handle both Row tuple and direct model returns
        if result is None:
            incident = None
        elif hasattr(result, "id"):  # Already a model
            incident = result
        else:  # Row tuple
            incident = result[0]

        if incident:
            incident.resolved = True
            incident.resolved_at = datetime.now(timezone.utc)
            incident.resolved_by = resolved_by
            incident.resolution_notes = resolution_notes
            session.commit()

    def _save_incident_file(self, incident: Incident) -> None:
        """Save incident to file (legacy backup)."""
        try:
            incident_file = self.incident_dir / f"incident_{incident.id}.json"
            with open(incident_file, "w") as f:
                json.dump(incident.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save incident file: {e}")

    def get_incidents(
        self,
        include_resolved: bool = False,
        limit: int = 10,
    ) -> List[Incident]:
        """
        Get recent incidents from database.

        Args:
            include_resolved: Include resolved incidents
            limit: Maximum incidents to return

        Returns:
            List of incidents
        """
        with self._get_session() as session:
            statement = select(CostSimCBIncident).where(CostSimCBIncident.circuit_breaker_name == self.name)

            if not include_resolved:
                statement = statement.where(CostSimCBIncident.resolved == False)

            statement = statement.order_by(CostSimCBIncident.timestamp.desc()).limit(limit)

            result = session.exec(statement)
            incidents = []

            for db_incident in result:
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

    # ========== Alertmanager Integration ==========

    async def _send_alert_disable(
        self,
        incident: Incident,
        disabled_until: Optional[datetime],
    ) -> bool:
        """Send P1/P2/P3 alert when circuit breaker trips."""
        config = self.config

        if not config.alertmanager_url:
            logger.warning("ALERTMANAGER_URL not configured; skipping alert")
            return False

        payload = [
            {
                "labels": {
                    "alertname": "CostSimV2Disabled",
                    "severity": incident.severity.lower(),
                    "component": "costsim",
                    "circuit_breaker": self.name,
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

        return await self._post_alertmanager(payload)

    async def _send_alert_enable(
        self,
        enabled_by: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Send resolved alert when circuit breaker is re-enabled."""
        config = self.config

        if not config.alertmanager_url:
            logger.warning("ALERTMANAGER_URL not configured; skipping resolved alert")
            return False

        now = datetime.now(timezone.utc)
        payload = [
            {
                "labels": {
                    "alertname": "CostSimV2Reenabled",
                    "severity": "info",
                    "component": "costsim",
                    "circuit_breaker": self.name,
                    "instance": config.instance_id,
                },
                "annotations": {
                    "summary": "CostSim V2 circuit breaker re-enabled",
                    "description": (f"Re-enabled by: {enabled_by}\n" f"Reason: {reason or 'Not specified'}"),
                },
                "startsAt": now.isoformat(),
                "endsAt": now.isoformat(),  # Resolved immediately
            }
        ]

        return await self._post_alertmanager(payload)

    async def _post_alertmanager(self, payload: List[Dict[str, Any]]) -> bool:
        """
        Post alert to Alertmanager with retry logic.

        Returns True if alert was sent successfully.
        """
        config = self.config

        if not config.alertmanager_url:
            return False

        last_error = None

        for attempt in range(config.alertmanager_retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=config.alertmanager_timeout_seconds) as client:
                    response = await client.post(
                        config.alertmanager_url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    response.raise_for_status()

                    logger.info(
                        f"Alert posted to Alertmanager: status={response.status_code}, "
                        f"alertname={payload[0]['labels'].get('alertname')}"
                    )
                    return True

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Alertmanager post failed (attempt {attempt + 1}/{config.alertmanager_retry_attempts}): {e}"
                )

                if attempt < config.alertmanager_retry_attempts - 1:
                    await asyncio.sleep(
                        config.alertmanager_retry_delay_seconds * (2**attempt)  # Exponential backoff
                    )

        logger.error(
            f"Failed to post to Alertmanager after {config.alertmanager_retry_attempts} attempts: {last_error}"
        )
        return False


# ========== Global Instance ==========

_circuit_breaker: Optional[CircuitBreaker] = None


def get_circuit_breaker() -> CircuitBreaker:
    """Get the global circuit breaker instance."""
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreaker()
    return _circuit_breaker


# ========== Convenience Functions ==========


async def is_v2_disabled() -> bool:
    """Check if CostSim V2 is disabled."""
    return await get_circuit_breaker().is_disabled()


async def disable_v2(
    reason: str,
    disabled_by: str,
    disabled_until: Optional[datetime] = None,
) -> Tuple[bool, Optional[Incident]]:
    """Disable CostSim V2."""
    return await get_circuit_breaker().disable_v2(
        reason=reason,
        disabled_by=disabled_by,
        disabled_until=disabled_until,
    )


async def enable_v2(
    enabled_by: str,
    reason: Optional[str] = None,
) -> bool:
    """Enable CostSim V2."""
    return await get_circuit_breaker().enable_v2(
        enabled_by=enabled_by,
        reason=reason,
    )
