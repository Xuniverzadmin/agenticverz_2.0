# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: worker (tool invocation)
#   Execution: async
# Lifecycle:
#   Emits: audit_events (MCP tool invocation)
#   Subscribes: none
# Data Access:
#   Reads: policy decisions (via driver)
#   Writes: audit events (via driver)
# Wiring Type: audit
# Parent Gap: GAP-063 (MCPConnector), GAP-081 (AuditDaemon)
# Depends On: GAP-141 (MCPServerRegistry), GAP-142 (MCPPolicyMapper)
# Role: Emit compliance-grade audit for MCP tool calls
# Callers: Runner, skill executor
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-143
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure audit event emission, not SQL driver
#       Remains in drivers/ per Layer ≠ Directory principle

"""
Module: audit_evidence
Purpose: Emit compliance-grade audit for MCP tool calls.

Wires:
    - Source: app/services/mcp/policy_mapper.py (policy decisions)
    - Source: app/services/mcp/server_registry.py (server/tool info)
    - Target: app/events (event bus) / audit storage

This module:
    1. Emits audit events for all MCP tool invocations
    2. Records policy decisions for compliance
    3. Captures input/output for forensic analysis
    4. Provides tamper-evident audit trail

Acceptance Criteria:
    - AC-143-01: All tool invocations are audited
    - AC-143-02: Policy decisions are recorded
    - AC-143-03: Audit events are tamper-evident
    - AC-143-04: Sensitive data is redacted
    - AC-143-05: Events include full context
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.mcp.audit_evidence")


class MCPAuditEventType(str, Enum):
    """Types of MCP audit events."""

    TOOL_INVOCATION_REQUESTED = "tool_invocation_requested"
    TOOL_INVOCATION_ALLOWED = "tool_invocation_allowed"
    TOOL_INVOCATION_DENIED = "tool_invocation_denied"
    TOOL_INVOCATION_STARTED = "tool_invocation_started"
    TOOL_INVOCATION_COMPLETED = "tool_invocation_completed"
    TOOL_INVOCATION_FAILED = "tool_invocation_failed"
    SERVER_REGISTERED = "server_registered"
    SERVER_UNREGISTERED = "server_unregistered"
    SERVER_HEALTH_CHANGED = "server_health_changed"
    POLICY_UPDATED = "policy_updated"


@dataclass
class MCPAuditEvent:
    """
    Compliance-grade audit event for MCP operations.

    Contains full context for forensic analysis and compliance reporting.
    Includes integrity hash for tamper detection.
    """

    event_id: str
    event_type: MCPAuditEventType
    tenant_id: str
    run_id: Optional[str]
    server_id: Optional[str]
    tool_name: Optional[str]
    timestamp: str
    # Policy context
    policy_decision: Optional[str] = None
    policy_id: Optional[str] = None
    deny_reason: Optional[str] = None
    # Execution context
    input_hash: Optional[str] = None  # Hash of input (not raw for privacy)
    output_hash: Optional[str] = None  # Hash of output
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    # Tracing
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    # Integrity
    integrity_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    # Metadata
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Compute integrity hash after initialization."""
        if self.integrity_hash is None:
            self.integrity_hash = self._compute_integrity_hash()

    def _compute_integrity_hash(self) -> str:
        """Compute tamper-evident integrity hash."""
        # Hash key fields for integrity verification
        hash_input = (
            f"{self.event_id}|{self.event_type.value}|{self.tenant_id}|"
            f"{self.run_id or ''}|{self.server_id or ''}|{self.tool_name or ''}|"
            f"{self.timestamp}|{self.policy_decision or ''}|{self.previous_event_hash or ''}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp,
            "policy_decision": self.policy_decision,
            "policy_id": self.policy_id,
            "deny_reason": self.deny_reason,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "integrity_hash": self.integrity_hash,
            "previous_event_hash": self.previous_event_hash,
            "metadata": self.metadata,
        }

    def verify_integrity(self) -> bool:
        """Verify the integrity hash is valid."""
        expected = self._compute_integrity_hash()
        return self.integrity_hash == expected


# Sensitive field patterns for redaction
SENSITIVE_PATTERNS = [
    "password",
    "secret",
    "token",
    "key",
    "credential",
    "auth",
    "api_key",
    "apikey",
    "bearer",
    "jwt",
    "ssn",
    "credit_card",
    "card_number",
]


def _hash_value(value: Any) -> str:
    """Hash a value for audit purposes."""
    if value is None:
        return ""
    serialized = str(value)
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def _contains_sensitive(key: str) -> bool:
    """Check if key name suggests sensitive data."""
    key_lower = key.lower()
    return any(pattern in key_lower for pattern in SENSITIVE_PATTERNS)


def _redact_sensitive(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive fields from data for logging."""
    if not isinstance(data, dict):
        return data

    redacted = {}
    for key, value in data.items():
        if _contains_sensitive(key):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = _redact_sensitive(value)
        elif isinstance(value, list):
            redacted[key] = [
                _redact_sensitive(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    return redacted


class MCPAuditEmitter:
    """
    Emitter for compliance-grade MCP audit events.

    This service:
    1. Emits audit events to event bus
    2. Maintains chain of audit events (previous hash)
    3. Redacts sensitive data
    4. Provides forensic context

    INVARIANT: All tool invocations must be audited.
    """

    def __init__(self, publisher: Optional[Any] = None):
        """
        Initialize audit emitter.

        Args:
            publisher: Event publisher (lazy loaded if None)
        """
        self._publisher = publisher
        self._last_event_hash: Optional[str] = None
        self._event_counter: int = 0

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid
        self._event_counter += 1
        return f"mcp-audit-{uuid.uuid4().hex[:12]}-{self._event_counter}"

    async def emit_tool_requested(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        input_params: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool invocation is requested.

        Args:
            tenant_id: Tenant requesting invocation
            server_id: MCP server hosting tool
            tool_name: Tool being invoked
            run_id: Run context
            input_params: Tool input parameters (will be hashed)
            trace_id: Trace ID for correlation

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_REQUESTED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_hash=_hash_value(input_params) if input_params else None,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
            metadata={"input_redacted": _redact_sensitive(input_params or {})},
        )

        await self._emit(event)
        return event

    async def emit_tool_allowed(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        policy_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool invocation is allowed.

        Args:
            tenant_id: Tenant
            server_id: MCP server
            tool_name: Tool name
            run_id: Run context
            policy_id: Policy that allowed
            trace_id: Trace ID

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_ALLOWED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            policy_decision="allow",
            policy_id=policy_id,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_tool_denied(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        deny_reason: str,
        policy_id: Optional[str] = None,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool invocation is denied.

        Args:
            tenant_id: Tenant
            server_id: MCP server
            tool_name: Tool name
            run_id: Run context
            deny_reason: Reason for denial
            policy_id: Policy that denied
            message: Denial message
            trace_id: Trace ID

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_DENIED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            policy_decision="deny",
            policy_id=policy_id,
            deny_reason=deny_reason,
            error_message=message,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_tool_started(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool execution starts.

        Args:
            tenant_id: Tenant
            server_id: MCP server
            tool_name: Tool name
            run_id: Run context
            span_id: Span ID for tracing
            trace_id: Trace ID

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_STARTED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            span_id=span_id,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_tool_completed(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        output: Optional[Any] = None,
        duration_ms: Optional[float] = None,
        span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool execution completes successfully.

        Args:
            tenant_id: Tenant
            server_id: MCP server
            tool_name: Tool name
            run_id: Run context
            output: Tool output (will be hashed)
            duration_ms: Execution duration
            span_id: Span ID
            trace_id: Trace ID

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_COMPLETED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            output_hash=_hash_value(output) if output is not None else None,
            duration_ms=duration_ms,
            span_id=span_id,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_tool_failed(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        error_message: str,
        duration_ms: Optional[float] = None,
        span_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> MCPAuditEvent:
        """
        Emit audit event when tool execution fails.

        Args:
            tenant_id: Tenant
            server_id: MCP server
            tool_name: Tool name
            run_id: Run context
            error_message: Error details
            duration_ms: Execution duration before failure
            span_id: Span ID
            trace_id: Trace ID

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.TOOL_INVOCATION_FAILED,
            tenant_id=tenant_id,
            run_id=run_id,
            server_id=server_id,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error_message=error_message,
            duration_ms=duration_ms,
            span_id=span_id,
            trace_id=trace_id,
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def emit_server_registered(
        self,
        tenant_id: str,
        server_id: str,
        server_name: str,
        url: str,
        tool_count: int,
    ) -> MCPAuditEvent:
        """
        Emit audit event when MCP server is registered.

        Args:
            tenant_id: Tenant registering server
            server_id: New server ID
            server_name: Server name
            url: Server URL
            tool_count: Number of tools discovered

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.SERVER_REGISTERED,
            tenant_id=tenant_id,
            run_id=None,
            server_id=server_id,
            tool_name=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            previous_event_hash=self._last_event_hash,
            metadata={
                "server_name": server_name,
                "url": url,
                "tool_count": tool_count,
            },
        )

        await self._emit(event)
        return event

    async def emit_server_unregistered(
        self,
        tenant_id: str,
        server_id: str,
    ) -> MCPAuditEvent:
        """
        Emit audit event when MCP server is unregistered.

        Args:
            tenant_id: Tenant unregistering server
            server_id: Server being removed

        Returns:
            MCPAuditEvent that was emitted
        """
        event = MCPAuditEvent(
            event_id=self._generate_event_id(),
            event_type=MCPAuditEventType.SERVER_UNREGISTERED,
            tenant_id=tenant_id,
            run_id=None,
            server_id=server_id,
            tool_name=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            previous_event_hash=self._last_event_hash,
        )

        await self._emit(event)
        return event

    async def _emit(self, event: MCPAuditEvent) -> None:
        """
        Emit event to event bus and update chain.

        Args:
            event: Event to emit
        """
        logger.debug(
            "mcp_audit.emitting",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "tenant_id": event.tenant_id,
                "server_id": event.server_id,
                "tool_name": event.tool_name,
            },
        )

        try:
            publisher = self._get_publisher()
            if publisher is not None:
                await publisher.publish(
                    f"mcp.audit.{event.event_type.value}",
                    event.to_dict(),
                )

            # Update chain
            self._last_event_hash = event.integrity_hash

            logger.info(
                "mcp_audit.emitted",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "integrity_hash": event.integrity_hash,
                },
            )

        except Exception as e:
            # CRITICAL: Audit failures should be logged but not block execution
            logger.error(
                "mcp_audit.emission_failed",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "error": str(e),
                },
            )

    def _get_publisher(self) -> Optional[Any]:
        """Get event publisher (lazy initialization)."""
        if self._publisher is not None:
            return self._publisher

        try:
            from app.events import get_publisher
            return get_publisher()
        except ImportError:
            logger.debug("mcp_audit.publisher_not_available")
            return None


# =========================
# Singleton Management
# =========================

_mcp_audit_emitter: Optional[MCPAuditEmitter] = None


def get_mcp_audit_emitter() -> MCPAuditEmitter:
    """
    Get or create the singleton MCPAuditEmitter.

    Returns:
        MCPAuditEmitter instance
    """
    global _mcp_audit_emitter

    if _mcp_audit_emitter is None:
        _mcp_audit_emitter = MCPAuditEmitter()
        logger.info("mcp_audit_emitter.created")

    return _mcp_audit_emitter


def configure_mcp_audit_emitter(
    publisher: Optional[Any] = None,
) -> MCPAuditEmitter:
    """
    Configure the singleton MCPAuditEmitter.

    Args:
        publisher: Event publisher to use

    Returns:
        Configured MCPAuditEmitter
    """
    global _mcp_audit_emitter

    _mcp_audit_emitter = MCPAuditEmitter(publisher=publisher)

    logger.info(
        "mcp_audit_emitter.configured",
        extra={"has_publisher": publisher is not None},
    )

    return _mcp_audit_emitter


def reset_mcp_audit_emitter() -> None:
    """Reset the singleton (for testing)."""
    global _mcp_audit_emitter
    _mcp_audit_emitter = None
