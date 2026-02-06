# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Audit emission for auth gateway events
# Callers: gateway_middleware
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-306 (Capability Registry), CAP-006 (Authentication)
# capability_id: CAP-006

"""
Gateway Audit Emission

Emits audit events for every authentication attempt through the gateway.
Provides visibility into authentication patterns and security events.

EVENTS:
- auth.success.human - Successful JWT authentication
- auth.success.machine - Successful API key authentication
- auth.failure - Authentication failure (any type)

INVARIANTS:
1. Every gateway call emits an audit event
2. Audit failures do not block requests
3. Events are non-blocking (async emission)
4. Sensitive data (tokens, keys) are NOT logged
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .contexts import (
    AuthPlane,
    GatewayContext,
    HumanAuthContext,
    MachineCapabilityContext,
)
from .gateway_types import GatewayAuthError

logger = logging.getLogger("nova.auth.gateway_audit")


class AuditEventType(str, Enum):
    """Types of gateway audit events."""

    AUTH_SUCCESS_HUMAN = "auth.success.human"
    AUTH_SUCCESS_MACHINE = "auth.success.machine"
    AUTH_FAILURE = "auth.failure"


@dataclass
class GatewayAuditEvent:
    """
    Audit event for gateway authentication.

    Contains all information needed for security audit trail.
    Sensitive data (tokens, keys) are NOT included.
    """

    # Event metadata
    event_type: str
    timestamp: str
    request_id: Optional[str]

    # Request info
    request_path: str
    request_method: str
    client_ip: str

    # Authentication result
    success: bool
    auth_plane: Optional[str]  # "human" or "machine"
    auth_source: Optional[str]  # "clerk", "stub", "api_key"

    # Actor info (success only)
    actor_id: Optional[str]
    tenant_id: Optional[str]

    # Error info (failure only)
    error_code: Optional[str]
    error_message: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for logging/storage."""
        return {k: v for k, v in asdict(self).items() if v is not None}


async def emit_auth_audit(
    request_path: str,
    request_method: str,
    context: GatewayContext,
    client_ip: str,
    request_id: Optional[str] = None,
) -> None:
    """
    Emit audit event for successful authentication.

    Called by gateway middleware after successful auth.
    """
    try:
        if isinstance(context, HumanAuthContext):
            event = GatewayAuditEvent(
                event_type=AuditEventType.AUTH_SUCCESS_HUMAN.value,
                timestamp=datetime.utcnow().isoformat(),
                request_id=request_id,
                request_path=request_path,
                request_method=request_method,
                client_ip=client_ip,
                success=True,
                auth_plane=AuthPlane.HUMAN.value,
                auth_source=context.auth_source.value,
                actor_id=context.actor_id,
                tenant_id=context.tenant_id,
                error_code=None,
                error_message=None,
            )
        elif isinstance(context, MachineCapabilityContext):
            event = GatewayAuditEvent(
                event_type=AuditEventType.AUTH_SUCCESS_MACHINE.value,
                timestamp=datetime.utcnow().isoformat(),
                request_id=request_id,
                request_path=request_path,
                request_method=request_method,
                client_ip=client_ip,
                success=True,
                auth_plane=AuthPlane.MACHINE.value,
                auth_source=context.auth_source.value,
                actor_id=context.key_id,  # Use key_id as actor for machine
                tenant_id=context.tenant_id,
                error_code=None,
                error_message=None,
            )
        else:
            return

        await _emit_event(event)

    except Exception as e:
        # Audit failures should never break the request
        logger.warning(f"Failed to emit auth audit: {e}")


async def emit_auth_failure_audit(
    request_path: str,
    request_method: str,
    error: GatewayAuthError,
    client_ip: str,
    request_id: Optional[str] = None,
) -> None:
    """
    Emit audit event for failed authentication.

    Called by gateway middleware on auth failure.
    """
    try:
        event = GatewayAuditEvent(
            event_type=AuditEventType.AUTH_FAILURE.value,
            timestamp=datetime.utcnow().isoformat(),
            request_id=request_id,
            request_path=request_path,
            request_method=request_method,
            client_ip=client_ip,
            success=False,
            auth_plane=None,
            auth_source=None,
            actor_id=None,
            tenant_id=None,
            error_code=error.error_code.value,
            error_message=error.message,
        )

        await _emit_event(event)

    except Exception as e:
        logger.warning(f"Failed to emit auth failure audit: {e}")


async def _emit_event(event: GatewayAuditEvent) -> None:
    """
    Emit an audit event.

    Currently logs to structured logger.
    Can be extended to write to database or external audit service.
    """
    # Log as structured JSON
    logger.info(
        "gateway_audit",
        extra={"audit_event": event.to_dict()},
    )

    # Optionally write to database
    await _write_to_db(event)


async def _write_to_db(event: GatewayAuditEvent) -> None:
    """
    Write audit event to database.

    Uses the AuditLog model from tenant models.
    Non-blocking - failures don't affect request.
    """
    try:
        # Import here to avoid circular dependency
        import asyncio

        from ..db import engine

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _sync_write_audit_log,
            engine,
            event,
        )

    except Exception as e:
        logger.debug(f"Failed to write audit to DB: {e}")


def _sync_write_audit_log(engine, event: GatewayAuditEvent) -> None:
    """Synchronous audit log write."""
    from sqlmodel import Session

    from ..models.tenant import AuditLog

    try:
        with Session(engine) as session:
            audit_log = AuditLog(
                tenant_id=event.tenant_id,
                action=event.event_type,
                resource_type="gateway_auth",
                resource_id=event.actor_id,
                ip_address=event.client_ip,
                request_id=event.request_id,
            )
            session.add(audit_log)
            session.commit()
    except Exception as e:
        # Log but don't raise
        logger.debug(f"Audit DB write failed: {e}")


# =============================================================================
# Metrics Integration
# =============================================================================

# Prometheus metrics for auth events
try:
    from prometheus_client import Counter

    AUTH_SUCCESS_COUNTER = Counter(
        "nova_auth_success_total",
        "Total successful authentications",
        ["plane", "source"],
    )

    AUTH_FAILURE_COUNTER = Counter(
        "nova_auth_failure_total",
        "Total failed authentications",
        ["error_code"],
    )

    def record_auth_success_metric(plane: str, source: str) -> None:
        """Record successful auth metric."""
        AUTH_SUCCESS_COUNTER.labels(plane=plane, source=source).inc()

    def record_auth_failure_metric(error_code: str) -> None:
        """Record failed auth metric."""
        AUTH_FAILURE_COUNTER.labels(error_code=error_code).inc()

except ImportError:
    # Prometheus not installed
    def record_auth_success_metric(plane: str, source: str) -> None:
        pass

    def record_auth_failure_metric(error_code: str) -> None:
        pass
