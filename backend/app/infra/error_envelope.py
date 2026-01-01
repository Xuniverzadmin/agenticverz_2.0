# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any (api|worker|scheduler|external)
#   Execution: sync
# Role: Unified error envelope for forensic diagnostics
# Callers: Any layer emitting errors (L2, L3, L4, L5, L6)
# Allowed Imports: None (pure data structures + stdlib)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-S Error Capture)

"""
Unified Error Envelope — Phase-S Track 1

Every error in the system MUST emit this envelope.
This is the atomic unit of error observability.

Design Principles:
- Immutable: Once created, cannot be modified
- Complete: Contains all information needed for diagnosis
- Safe: No raw secrets, only hashes where needed
- Traceable: Correlation IDs link across system boundaries

Required Fields (PIN-264):
- error_id: Unique identifier for this error instance
- timestamp: When the error occurred (UTC)
- layer: Which layer (L2/L3/L4/L5/L6) produced the error
- component: Module path or service name
- correlation_id: Request/workflow trace ID
- decision_id: Related decision (if any)
- input_hash: Hash of input data (not raw input)
- error_class: Classification of error type
- severity: Error severity level

ARCHITECTURAL CONSTRAINT (MANDATORY):
    ErrorEnvelope is INFRASTRUCTURE-ONLY.
    It must NEVER be:
    - Returned from L2 APIs to clients
    - Rendered in UI components
    - Used as a product contract or public schema
    - Exposed to customers in any form

    If users need error responses, that is a SEPARATE product error model
    defined at L2/L3 boundary. This envelope is for forensics, not UX.

EMISSION RULES BY LAYER:
    | Layer | Allowed error_class prefixes |
    |-------|------------------------------|
    | L2    | infra.*, system.*            |
    | L3    | infra.*, system.*            |
    | L4    | domain.*, system.*           |
    | L5    | infra.*, system.*            |
    | L6    | infra.*, system.*            |

    Workers (L5) should NOT emit domain.* errors.
    Domain engines (L4) should NOT emit infra.* errors.
    This preserves semantic integrity of error classification.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(str, Enum):
    """
    Error severity levels.

    Used for:
    - Alerting thresholds
    - Log filtering
    - Incident prioritization
    """

    DEBUG = "debug"  # Diagnostic information
    INFO = "info"  # Informational, not an error
    WARNING = "warning"  # Potential issue, not blocking
    ERROR = "error"  # Operation failed
    CRITICAL = "critical"  # System-wide impact, requires immediate attention


class ErrorClass(str, Enum):
    """
    Error classification taxonomy.

    Used for:
    - Error aggregation and grouping
    - Pattern detection
    - Playbook selection

    Categories:
    - INFRA_*: Infrastructure/platform errors
    - DOMAIN_*: Business logic errors
    - SYSTEM_*: Internal system errors
    """

    # Infrastructure errors (external dependencies)
    INFRA_NETWORK = "infra.network"
    INFRA_DATABASE = "infra.database"
    INFRA_EXTERNAL_SERVICE = "infra.external_service"
    INFRA_TIMEOUT = "infra.timeout"
    INFRA_RESOURCE_EXHAUSTED = "infra.resource_exhausted"
    INFRA_CONNECTION = "infra.connection"

    # Domain errors (business logic)
    DOMAIN_VALIDATION = "domain.validation"
    DOMAIN_AUTHORIZATION = "domain.authorization"
    DOMAIN_RATE_LIMIT = "domain.rate_limit"
    DOMAIN_BUDGET_EXCEEDED = "domain.budget_exceeded"
    DOMAIN_POLICY_VIOLATION = "domain.policy_violation"
    DOMAIN_CONSTRAINT = "domain.constraint"
    DOMAIN_NOT_FOUND = "domain.not_found"

    # System errors (internal)
    SYSTEM_INTERNAL = "system.internal"
    SYSTEM_CONFIGURATION = "system.configuration"
    SYSTEM_RECOVERY_FAILED = "system.recovery_failed"
    SYSTEM_STATE_CORRUPTION = "system.state_corruption"
    SYSTEM_ASSERTION = "system.assertion"

    # Unknown (should trigger investigation)
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ErrorEnvelope:
    """
    Unified Error Envelope for Phase-S forensic diagnostics.

    Every error in the system must emit this envelope.
    This is the atomic unit of error observability.

    Immutable by design - once created, cannot be modified.

    Usage:
        envelope = ErrorEnvelope.create(
            layer="L4",
            component="app.services.budget_engine",
            error_class=ErrorClass.DOMAIN_BUDGET_EXCEEDED,
            severity=ErrorSeverity.ERROR,
            message="Budget exhausted for run",
            correlation_id=request_id,
            run_id=run.id,
        )
    """

    # === Required Fields (PIN-264) ===
    error_id: str  # Unique identifier: err_<12-char-hex>
    timestamp: datetime  # When error occurred (UTC)
    layer: str  # L2/L3/L4/L5/L6
    component: str  # Module path or service name
    error_class: ErrorClass  # Classification
    severity: ErrorSeverity  # Severity level
    message: str  # Human-readable description

    # === Correlation (Optional but Recommended) ===
    correlation_id: Optional[str] = None  # Request/workflow trace ID
    decision_id: Optional[str] = None  # Related decision ID
    run_id: Optional[str] = None  # Related run ID
    agent_id: Optional[str] = None  # Related agent ID
    tenant_id: Optional[str] = None  # Tenant context

    # === Input Context (Hashed for Security) ===
    input_hash: Optional[str] = None  # SHA256 hash of input (first 16 chars)

    # === Exception Details (Sanitized) ===
    exception_type: Optional[str] = None  # Exception class name
    exception_chain: Optional[List[str]] = None  # Cause chain (truncated)

    # === Arbitrary Context (No Secrets!) ===
    context: Dict[str, Any] = field(default_factory=dict)

    # === Metadata ===
    version: str = "1.0"  # Envelope schema version

    @classmethod
    def create(
        cls,
        layer: str,
        component: str,
        error_class: ErrorClass,
        severity: ErrorSeverity,
        message: str,
        *,  # Force keyword arguments
        correlation_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        run_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        input_data: Optional[str] = None,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "ErrorEnvelope":
        """
        Factory method to create an error envelope with proper defaults.

        Args:
            layer: Layer identifier (L2, L3, L4, L5, L6)
            component: Module path (e.g., "app.services.budget_engine")
            error_class: Error classification
            severity: Severity level
            message: Human-readable error description
            correlation_id: Optional request/workflow trace ID
            decision_id: Optional related decision ID
            run_id: Optional related run ID
            agent_id: Optional related agent ID
            tenant_id: Optional tenant context
            input_data: Optional input data (will be hashed, not stored raw)
            exception: Optional exception to extract type and chain from
            context: Optional additional context (NO SECRETS!)

        Returns:
            Immutable ErrorEnvelope instance
        """
        # Generate unique error ID
        error_id = f"err_{uuid.uuid4().hex[:12]}"

        # Hash input data if provided (never store raw)
        input_hash = None
        if input_data:
            input_hash = hashlib.sha256(input_data.encode()).hexdigest()[:16]

        # Extract exception info if provided
        exception_type = None
        exception_chain = None
        if exception:
            exception_type = type(exception).__name__
            # Build exception chain (sanitized, limited depth)
            chain = []
            current: Optional[BaseException] = exception
            while current and len(chain) < 5:  # Limit chain depth
                # Truncate message to prevent secret leakage
                msg = str(current)[:200]
                chain.append(f"{type(current).__name__}: {msg}")
                current = current.__cause__
            exception_chain = chain if chain else None

        return cls(
            error_id=error_id,
            timestamp=datetime.now(timezone.utc),
            layer=layer,
            component=component,
            error_class=error_class,
            severity=severity,
            message=message,
            correlation_id=correlation_id,
            decision_id=decision_id,
            run_id=run_id,
            agent_id=agent_id,
            tenant_id=tenant_id,
            input_hash=input_hash,
            exception_type=exception_type,
            exception_chain=exception_chain,
            context=context or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for persistence/serialization.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "layer": self.layer,
            "component": self.component,
            "error_class": self.error_class.value,
            "severity": self.severity.value,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "decision_id": self.decision_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "input_hash": self.input_hash,
            "exception_type": self.exception_type,
            "exception_chain": self.exception_chain,
            "context": self.context,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorEnvelope":
        """
        Reconstruct an ErrorEnvelope from a dictionary.

        Used for replay and persistence recovery.

        Args:
            data: Dictionary from to_dict() or JSON deserialization

        Returns:
            ErrorEnvelope instance
        """
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Parse enums
        error_class = ErrorClass(data["error_class"])
        severity = ErrorSeverity(data["severity"])

        return cls(
            error_id=data["error_id"],
            timestamp=timestamp,
            layer=data["layer"],
            component=data["component"],
            error_class=error_class,
            severity=severity,
            message=data["message"],
            correlation_id=data.get("correlation_id"),
            decision_id=data.get("decision_id"),
            run_id=data.get("run_id"),
            agent_id=data.get("agent_id"),
            tenant_id=data.get("tenant_id"),
            input_hash=data.get("input_hash"),
            exception_type=data.get("exception_type"),
            exception_chain=data.get("exception_chain"),
            context=data.get("context", {}),
            version=data.get("version", "1.0"),
        )

    def with_context(self, **kwargs: Any) -> "ErrorEnvelope":
        """
        Create a new envelope with additional context.

        Since ErrorEnvelope is frozen, this returns a new instance.

        Args:
            **kwargs: Additional context key-value pairs

        Returns:
            New ErrorEnvelope with merged context
        """
        new_context = {**self.context, **kwargs}
        return ErrorEnvelope(
            error_id=self.error_id,
            timestamp=self.timestamp,
            layer=self.layer,
            component=self.component,
            error_class=self.error_class,
            severity=self.severity,
            message=self.message,
            correlation_id=self.correlation_id,
            decision_id=self.decision_id,
            run_id=self.run_id,
            agent_id=self.agent_id,
            tenant_id=self.tenant_id,
            input_hash=self.input_hash,
            exception_type=self.exception_type,
            exception_chain=self.exception_chain,
            context=new_context,
            version=self.version,
        )

    def is_critical(self) -> bool:
        """Check if this error requires immediate attention."""
        return self.severity == ErrorSeverity.CRITICAL

    def is_infrastructure_error(self) -> bool:
        """Check if this is an infrastructure-related error."""
        return self.error_class.value.startswith("infra.")

    def is_domain_error(self) -> bool:
        """Check if this is a domain/business logic error."""
        return self.error_class.value.startswith("domain.")

    def is_system_error(self) -> bool:
        """Check if this is an internal system error."""
        return self.error_class.value.startswith("system.")
