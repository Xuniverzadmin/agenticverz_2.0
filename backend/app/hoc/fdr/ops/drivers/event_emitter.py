# Layer: L6 — Driver
# Product: system-wide
# Callers: Multiple products (founder console, ops console)
# Reference: PIN-240
# NOTE: This layer must not know what a "product" is.
#
# =============================================================================
# EventEmitter - FOUNDER CONSOLE ONLY
# =============================================================================
#
# IMPORTANT: This service writes to ops_events table which is consumed
# EXCLUSIVELY by the Founder Console (api/ops.py).
#
# DO NOT use EventEmitter for Customer Console signal paths.
# Customer Console signals should update the runs table directly via
# RunSignalService, which feeds v_runs_o2 -> api/activity.py.
#
# Signal Audience Map:
# +-----------------+-------------------+---------------------+
# | Signal Type     | Founder Console   | Customer Console    |
# +-----------------+-------------------+---------------------+
# | Threshold Breach| ops_events        | runs.risk_level     |
# | Incident Created| ops_events        | runs.incident_count |
# | Policy Violation| ops_events        | runs.policy_violation|
# +-----------------+-------------------+---------------------+
#
# =============================================================================

"""
Event Emitter Service (M24 Ops Console)

PIN-105: Ops Console - Founder Intelligence System

Provides:
- Event emission to ops_events table (FOUNDER CONSOLE ONLY)
- Background batching for high-throughput scenarios
- Type-safe event creation
- Automatic timestamp and metadata handling

NOTE: This service is for FOUNDER CONSOLE monitoring only.
Customer Console signals use RunSignalService to update runs table.
"""

import json as json_lib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import Session

logger = logging.getLogger("nova.services.event_emitter")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    """Canonical event types (PIN-105 + Phase-2 Friction Events).

    Any new feature MUST emit at least one of these events.

    Phase-2 additions capture FRICTION - where churn is born:
    - *_STARTED vs *_COMPLETED tracks drop-offs
    - *_ABORTED tracks explicit abandonment
    - *_NO_ACTION tracks hesitation
    """

    # API Activity
    API_CALL_RECEIVED = "API_CALL_RECEIVED"

    # Incident Lifecycle (with friction tracking)
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_VIEWED = "INCIDENT_VIEWED"
    INCIDENT_VIEWED_NO_ACTION = "INCIDENT_VIEWED_NO_ACTION"  # Phase-2: viewed but no replay/export

    # Replay Lifecycle (with friction tracking)
    REPLAY_STARTED = "REPLAY_STARTED"  # Phase-2: user initiated replay
    REPLAY_EXECUTED = "REPLAY_EXECUTED"  # Completion
    REPLAY_ABORTED = "REPLAY_ABORTED"  # Phase-2: user cancelled mid-flow
    REPLAY_FAILED = "REPLAY_FAILED"  # Phase-2: system failure during replay

    # Export Lifecycle (with friction tracking)
    EXPORT_STARTED = "EXPORT_STARTED"  # Phase-2: user initiated export
    EXPORT_GENERATED = "EXPORT_GENERATED"  # Completion
    EXPORT_ABORTED = "EXPORT_ABORTED"  # Phase-2: user cancelled
    EXPORT_FAILED = "EXPORT_FAILED"  # Phase-2: system failure

    # Certificate
    CERT_VERIFIED = "CERT_VERIFIED"

    # Policy (with friction tracking)
    POLICY_EVALUATED = "POLICY_EVALUATED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    POLICY_BLOCK_REPEAT = "POLICY_BLOCK_REPEAT"  # Phase-2: same policy blocks repeatedly

    # LLM
    LLM_CALL_MADE = "LLM_CALL_MADE"
    LLM_CALL_FAILED = "LLM_CALL_FAILED"

    # Infrastructure
    INFRA_LIMIT_HIT = "INFRA_LIMIT_HIT"

    # Subscription
    SUBSCRIPTION_STARTED = "SUBSCRIPTION_STARTED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"

    # Safety
    FREEZE_ACTIVATED = "FREEZE_ACTIVATED"

    # Auth
    LOGIN = "LOGIN"

    # Session Tracking (Phase-2)
    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"
    SESSION_IDLE_TIMEOUT = "SESSION_IDLE_TIMEOUT"  # User went idle


class EntityType(str, Enum):
    """Entity types for classification."""

    INCIDENT = "incident"
    REPLAY = "replay"
    EXPORT = "export"
    CERTIFICATE = "certificate"
    POLICY = "policy"
    LLM_CALL = "llm_call"
    API_KEY = "api_key"
    TENANT = "tenant"
    USER = "user"
    SUBSCRIPTION = "subscription"


@dataclass
class OpsEvent:
    """Represents an ops event to be persisted."""

    tenant_id: uuid.UUID
    event_type: EventType

    # Optional identifiers
    user_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    entity_type: Optional[EntityType] = None
    entity_id: Optional[uuid.UUID] = None

    # Metrics
    severity: Optional[int] = None  # 1-5 scale
    latency_ms: Optional[int] = None
    cost_usd: Optional[Decimal] = None

    # Flexible payload
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Auto-generated
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=utc_now)


class EventEmitterError(Exception):
    """Base exception for event emitter errors."""

    pass


class EventEmitter:
    """Service for emitting ops events.

    Usage:
        emitter = EventEmitter(session)
        emitter.emit(OpsEvent(
            tenant_id=tenant_id,
            event_type=EventType.INCIDENT_CREATED,
            entity_type=EntityType.INCIDENT,
            entity_id=incident_id,
            severity=3,
            metadata={"policy_id": "pol-001"}
        ))
    """

    def __init__(self, session: Session):
        self.session = session
        self._batch: List[OpsEvent] = []
        self._batch_mode = False

    def emit(self, event: OpsEvent) -> uuid.UUID:
        """Emit a single event immediately."""
        if self._batch_mode:
            self._batch.append(event)
            return event.event_id

        self._insert_event(event)
        return event.event_id

    def emit_batch(self, events: List[OpsEvent]) -> List[uuid.UUID]:
        """Emit multiple events in a single transaction."""
        for event in events:
            self._insert_event(event)
        return [e.event_id for e in events]

    def start_batch(self) -> None:
        """Start batch mode - events are queued until flush_batch is called."""
        self._batch_mode = True
        self._batch = []

    def flush_batch(self) -> List[uuid.UUID]:
        """Flush all queued events and exit batch mode."""
        if not self._batch:
            self._batch_mode = False
            return []

        event_ids = self.emit_batch(self._batch)
        self._batch = []
        self._batch_mode = False
        return event_ids

    def _insert_event(self, event: OpsEvent) -> None:
        """Insert event into database."""
        from sqlalchemy import text

        # Prepare values
        metadata_json = event.metadata if event.metadata else {}

        self.session.execute(
            text(
                """
            INSERT INTO ops_events (
                event_id, timestamp, tenant_id, user_id, session_id,
                event_type, entity_type, entity_id,
                severity, latency_ms, cost_usd, metadata
            ) VALUES (
                :event_id, :timestamp, :tenant_id, :user_id, :session_id,
                :event_type, :entity_type, :entity_id,
                :severity, :latency_ms, :cost_usd, CAST(:metadata AS jsonb)
            )
        """
            ),
            {
                "event_id": str(event.event_id),
                "timestamp": event.timestamp,
                "tenant_id": str(event.tenant_id),
                "user_id": str(event.user_id) if event.user_id else None,
                "session_id": str(event.session_id) if event.session_id else None,
                "event_type": event.event_type.value,
                "entity_type": event.entity_type.value if event.entity_type else None,
                "entity_id": str(event.entity_id) if event.entity_id else None,
                "severity": event.severity,
                "latency_ms": event.latency_ms,
                "cost_usd": float(event.cost_usd) if event.cost_usd else None,
                "metadata": json_lib.dumps(metadata_json),  # Proper JSON serialization
            },
        )

        logger.debug(
            "event_emitted",
            extra={
                "event_id": str(event.event_id),
                "event_type": event.event_type.value,
                "tenant_id": str(event.tenant_id),
            },
        )

    # ============== Convenience Methods ==============

    def emit_api_call(
        self,
        tenant_id: uuid.UUID,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: int,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit API_CALL_RECEIVED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.API_CALL_RECEIVED,
                user_id=user_id,
                session_id=session_id,
                latency_ms=latency_ms,
                metadata={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                },
            )
        )

    def emit_incident_created(
        self,
        tenant_id: uuid.UUID,
        incident_id: uuid.UUID,
        severity: int,
        policy_id: Optional[str] = None,
        model: Optional[str] = None,
        trigger_type: Optional[str] = None,
    ) -> uuid.UUID:
        """Emit INCIDENT_CREATED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INCIDENT_CREATED,
                entity_type=EntityType.INCIDENT,
                entity_id=incident_id,
                severity=severity,
                metadata={
                    "policy_id": policy_id,
                    "model": model,
                    "trigger_type": trigger_type,
                },
            )
        )

    def emit_incident_viewed(
        self,
        tenant_id: uuid.UUID,
        incident_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        time_on_page_ms: Optional[int] = None,
    ) -> uuid.UUID:
        """Emit INCIDENT_VIEWED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INCIDENT_VIEWED,
                entity_type=EntityType.INCIDENT,
                entity_id=incident_id,
                user_id=user_id,
                metadata={
                    "time_on_page_ms": time_on_page_ms,
                },
            )
        )

    def emit_replay_executed(
        self,
        tenant_id: uuid.UUID,
        replay_id: uuid.UUID,
        incident_id: uuid.UUID,
        match_level: str,
        cost_delta_usd: Optional[Decimal] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit REPLAY_EXECUTED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.REPLAY_EXECUTED,
                entity_type=EntityType.REPLAY,
                entity_id=replay_id,
                user_id=user_id,
                cost_usd=cost_delta_usd,
                metadata={
                    "incident_id": str(incident_id),
                    "match_level": match_level,
                },
            )
        )

    def emit_export_generated(
        self,
        tenant_id: uuid.UUID,
        export_id: uuid.UUID,
        incident_id: uuid.UUID,
        format: str,  # 'pdf', 'json'
        include_flags: Dict[str, bool],
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit EXPORT_GENERATED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.EXPORT_GENERATED,
                entity_type=EntityType.EXPORT,
                entity_id=export_id,
                user_id=user_id,
                metadata={
                    "incident_id": str(incident_id),
                    "format": format,
                    "include_flags": include_flags,
                },
            )
        )

    def emit_cert_verified(
        self,
        tenant_id: uuid.UUID,
        cert_id: uuid.UUID,
        incident_id: uuid.UUID,
        source_ip: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> uuid.UUID:
        """Emit CERT_VERIFIED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.CERT_VERIFIED,
                entity_type=EntityType.CERTIFICATE,
                entity_id=cert_id,
                metadata={
                    "incident_id": str(incident_id),
                    "source_ip": source_ip,
                    "referrer": referrer,
                },
            )
        )

    def emit_llm_call(
        self,
        tenant_id: uuid.UUID,
        call_id: uuid.UUID,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: Decimal,
        latency_ms: int,
        success: bool = True,
        error_type: Optional[str] = None,
        retry_count: int = 0,
    ) -> uuid.UUID:
        """Emit LLM_CALL_MADE or LLM_CALL_FAILED event."""
        event_type = EventType.LLM_CALL_MADE if success else EventType.LLM_CALL_FAILED

        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=event_type,
                entity_type=EntityType.LLM_CALL,
                entity_id=call_id,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                metadata={
                    "model": model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "error_type": error_type,
                    "retry_count": retry_count,
                },
            )
        )

    def emit_policy_decision(
        self,
        tenant_id: uuid.UUID,
        policy_id: str,
        blocked: bool,
        reason: Optional[str] = None,
        latency_ms: Optional[int] = None,
    ) -> uuid.UUID:
        """Emit POLICY_EVALUATED or POLICY_BLOCKED event."""
        event_type = EventType.POLICY_BLOCKED if blocked else EventType.POLICY_EVALUATED

        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=event_type,
                entity_type=EntityType.POLICY,
                latency_ms=latency_ms,
                metadata={
                    "policy_id": policy_id,
                    "result": "blocked" if blocked else "allowed",
                    "reason": reason,
                },
            )
        )

    def emit_infra_limit(
        self,
        tenant_id: uuid.UUID,
        resource: str,  # 'cpu', 'memory', 'connections', 'storage'
        current: float,
        limit: float,
    ) -> uuid.UUID:
        """Emit INFRA_LIMIT_HIT event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INFRA_LIMIT_HIT,
                severity=4,  # High severity
                metadata={
                    "resource": resource,
                    "current": current,
                    "limit": limit,
                    "utilization_pct": round((current / limit) * 100, 2),
                },
            )
        )

    def emit_freeze(
        self,
        tenant_id: uuid.UUID,
        scope: str,  # 'tenant' or 'key'
        entity_id: uuid.UUID,
        reason: str,
        auto_triggered: bool = False,
    ) -> uuid.UUID:
        """Emit FREEZE_ACTIVATED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.FREEZE_ACTIVATED,
                entity_type=EntityType.TENANT if scope == "tenant" else EntityType.API_KEY,
                entity_id=entity_id,
                severity=5,  # Critical
                metadata={
                    "scope": scope,
                    "reason": reason,
                    "auto_triggered": auto_triggered,
                },
            )
        )

    def emit_login(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        source: str,  # 'guard', 'operator'
        session_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit LOGIN event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.LOGIN,
                entity_type=EntityType.USER,
                entity_id=user_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "source": source,
                },
            )
        )

    # ============== Phase-2 Friction Event Methods ==============

    def emit_incident_viewed_no_action(
        self,
        tenant_id: uuid.UUID,
        incident_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        time_on_page_ms: Optional[int] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit INCIDENT_VIEWED_NO_ACTION - user viewed but took no action."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INCIDENT_VIEWED_NO_ACTION,
                entity_type=EntityType.INCIDENT,
                entity_id=incident_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "time_on_page_ms": time_on_page_ms,
                    "friction_signal": "viewed_no_action",
                },
            )
        )

    def emit_replay_started(
        self,
        tenant_id: uuid.UUID,
        replay_id: uuid.UUID,
        incident_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit REPLAY_STARTED - user initiated replay flow."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.REPLAY_STARTED,
                entity_type=EntityType.REPLAY,
                entity_id=replay_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "incident_id": str(incident_id),
                },
            )
        )

    def emit_replay_aborted(
        self,
        tenant_id: uuid.UUID,
        replay_id: uuid.UUID,
        incident_id: uuid.UUID,
        abort_reason: Optional[str] = None,
        step_reached: Optional[int] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit REPLAY_ABORTED - user cancelled mid-flow (friction signal)."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.REPLAY_ABORTED,
                entity_type=EntityType.REPLAY,
                entity_id=replay_id,
                user_id=user_id,
                metadata={
                    "incident_id": str(incident_id),
                    "abort_reason": abort_reason,
                    "step_reached": step_reached,
                    "friction_signal": "user_abort",
                },
            )
        )

    def emit_replay_failed(
        self,
        tenant_id: uuid.UUID,
        replay_id: uuid.UUID,
        incident_id: uuid.UUID,
        error_type: str,
        error_message: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit REPLAY_FAILED - system failure during replay."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.REPLAY_FAILED,
                entity_type=EntityType.REPLAY,
                entity_id=replay_id,
                user_id=user_id,
                severity=4,  # High - system failure
                metadata={
                    "incident_id": str(incident_id),
                    "error_type": error_type,
                    "error_message": error_message,
                    "friction_signal": "system_failure",
                },
            )
        )

    def emit_export_started(
        self,
        tenant_id: uuid.UUID,
        export_id: uuid.UUID,
        incident_id: uuid.UUID,
        format: str,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit EXPORT_STARTED - user initiated export."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.EXPORT_STARTED,
                entity_type=EntityType.EXPORT,
                entity_id=export_id,
                user_id=user_id,
                metadata={
                    "incident_id": str(incident_id),
                    "format": format,
                },
            )
        )

    def emit_export_aborted(
        self,
        tenant_id: uuid.UUID,
        export_id: uuid.UUID,
        incident_id: uuid.UUID,
        abort_reason: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit EXPORT_ABORTED - user cancelled export (friction signal)."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.EXPORT_ABORTED,
                entity_type=EntityType.EXPORT,
                entity_id=export_id,
                user_id=user_id,
                metadata={
                    "incident_id": str(incident_id),
                    "abort_reason": abort_reason,
                    "friction_signal": "user_abort",
                },
            )
        )

    def emit_export_failed(
        self,
        tenant_id: uuid.UUID,
        export_id: uuid.UUID,
        incident_id: uuid.UUID,
        error_type: str,
        error_message: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> uuid.UUID:
        """Emit EXPORT_FAILED - system failure during export."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.EXPORT_FAILED,
                entity_type=EntityType.EXPORT,
                entity_id=export_id,
                user_id=user_id,
                severity=3,  # Medium-high - export failure
                metadata={
                    "incident_id": str(incident_id),
                    "error_type": error_type,
                    "error_message": error_message,
                    "friction_signal": "system_failure",
                },
            )
        )

    def emit_policy_block_repeat(
        self,
        tenant_id: uuid.UUID,
        policy_id: str,
        block_count: int,
        time_window_hours: int = 24,
        reason: Optional[str] = None,
    ) -> uuid.UUID:
        """Emit POLICY_BLOCK_REPEAT - same policy blocking repeatedly (friction signal)."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.POLICY_BLOCK_REPEAT,
                entity_type=EntityType.POLICY,
                severity=3 if block_count < 10 else 4,  # Escalate severity with count
                metadata={
                    "policy_id": policy_id,
                    "block_count": block_count,
                    "time_window_hours": time_window_hours,
                    "reason": reason,
                    "friction_signal": "policy_friction",
                },
            )
        )

    # ============== Session Tracking Methods ==============

    def emit_session_started(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        source: str,  # 'guard', 'operator', 'api'
        user_agent: Optional[str] = None,
    ) -> uuid.UUID:
        """Emit SESSION_STARTED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.SESSION_STARTED,
                entity_type=EntityType.USER,
                entity_id=user_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "source": source,
                    "user_agent": user_agent,
                },
            )
        )

    def emit_session_ended(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        duration_seconds: int,
        events_count: int,
    ) -> uuid.UUID:
        """Emit SESSION_ENDED event."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.SESSION_ENDED,
                entity_type=EntityType.USER,
                entity_id=user_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "duration_seconds": duration_seconds,
                    "events_count": events_count,
                },
            )
        )

    def emit_session_idle_timeout(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        idle_seconds: int,
        last_event_type: Optional[str] = None,
    ) -> uuid.UUID:
        """Emit SESSION_IDLE_TIMEOUT - user went idle (friction signal)."""
        return self.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.SESSION_IDLE_TIMEOUT,
                entity_type=EntityType.USER,
                entity_id=user_id,
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "idle_seconds": idle_seconds,
                    "last_event_type": last_event_type,
                    "friction_signal": "idle_abandon",
                },
            )
        )


# Dependency injection helper
_event_emitter_instance: Optional[EventEmitter] = None


def get_event_emitter(session: Session) -> EventEmitter:
    """Get EventEmitter instance for dependency injection."""
    return EventEmitter(session)
