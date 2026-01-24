# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api | cli | worker
#   Execution: sync
# Role: Execution envelope generation for implicit authority hardening
# Callers: CLI entry, SDK invocation, auto-execute trigger
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2
# Reference: PIN-330

"""
Execution Envelope - PIN-330 Implicit Authority Hardening

This module provides non-blocking execution envelope generation for:
- CAP-020 (CLI Execution)
- CAP-021 (SDK Execution)
- SUB-019 (Auto-Execute Recovery)

CONSTRAINTS:
- Envelope creation failure MUST NOT block execution
- No enforcement, blocking, or behavior changes
- All fields are evidence, not policy gates
- Preserves execution semantics exactly
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class CapabilityId(str, Enum):
    """Capabilities covered by PIN-330 hardening."""

    CAP_019 = "CAP-019"  # Run Management (PIN-335: Admin retry)
    CAP_020 = "CAP-020"  # CLI Execution
    CAP_021 = "CAP-021"  # SDK Execution
    SUB_019 = "SUB-019"  # Auto-Execute Recovery


class ExecutionVector(str, Enum):
    """Entry points for execution."""

    CLI = "CLI"
    SDK = "SDK"
    AUTO_EXEC = "AUTO_EXEC"
    HTTP_ADMIN = "HTTP_ADMIN"  # PIN-335: Admin HTTP routes


class CallerType(str, Enum):
    """Classification of the caller."""

    HUMAN = "human"
    SERVICE = "service"
    SYSTEM = "system"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CallerIdentity:
    """Who triggered this execution."""

    type: CallerType
    subject: str
    impersonated_subject: Optional[str] = None
    impersonation_declared: bool = False


@dataclass
class TenantContext:
    """Tenant isolation context."""

    tenant_id: str
    account_id: Optional[str] = None
    project_id: Optional[str] = None


@dataclass
class InvocationTracking:
    """Invocation-level tracking."""

    invocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence_number: Optional[int] = None


@dataclass
class PlanIntegrity:
    """Plan integrity evidence (anti-injection)."""

    input_hash: str
    resolved_plan_hash: str
    plan_mutation_detected: bool = False
    original_invocation_id: Optional[str] = None


@dataclass
class ConfidenceContext:
    """Confidence scoring for auto-execute paths."""

    score: Optional[float] = None
    threshold_used: Optional[float] = None
    auto_execute_triggered: bool = False


@dataclass
class Attribution:
    """Attribution and provenance metadata."""

    origin: str = "PIN-330"
    reason_code: Optional[str] = None
    source_command: Optional[str] = None
    sdk_version: Optional[str] = None
    cli_version: Optional[str] = None


@dataclass
class EvidenceMetadata:
    """Evidence emission tracking."""

    emitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    storage_location: Optional[str] = None
    emission_success: bool = True


# =============================================================================
# INVOCATION SAFETY CONTEXT (PIN-332)
# =============================================================================


@dataclass
class InvocationSafetyFlags:
    """
    Safety flags from invocation safety checks (PIN-332).

    Captures safety violations and warnings at invocation boundary.
    DOES NOT block execution (v1: OBSERVE_WARN mode).
    """

    checked: bool = False
    passed: bool = True
    flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None

    @classmethod
    def from_safety_result(cls, result) -> "InvocationSafetyFlags":
        """
        Create from InvocationSafetyResult.

        Args:
            result: InvocationSafetyResult from invocation_safety module

        Returns:
            InvocationSafetyFlags instance
        """
        if result is None:
            return cls(checked=False)

        return cls(
            checked=True,
            passed=result.passed,
            flags=[f.value if hasattr(f, "value") else str(f) for f in result.flags],
            warnings=result.warnings,
            blocked=result.blocked,
            block_reason=result.block_reason,
        )


@dataclass
class ExecutionEnvelope:
    """
    Single canonical envelope used by CLI, SDK, and auto-execute paths.

    Converts implicit authority into explicit, attributable evidence.
    Does NOT grant, deny, or block execution.

    Safety Compliance (PIN-332):
    - invocation_safety field captures safety check results
    - Flags are evidence, not policy gates
    - v1: OBSERVE_WARN mode (no blocking except plan injection)
    """

    envelope_id: str
    capability_id: CapabilityId
    execution_vector: ExecutionVector
    caller_identity: CallerIdentity
    tenant_context: TenantContext
    invocation: InvocationTracking
    plan: PlanIntegrity
    attribution: Attribution
    evidence: EvidenceMetadata
    confidence: Optional[ConfidenceContext] = None
    invocation_safety: Optional[InvocationSafetyFlags] = None  # PIN-332

    def to_dict(self) -> dict[str, Any]:
        """Convert envelope to dictionary for storage."""
        return {
            "envelope_id": self.envelope_id,
            "capability_id": self.capability_id.value,
            "execution_vector": self.execution_vector.value,
            "caller_identity": {
                "type": self.caller_identity.type.value,
                "subject": self.caller_identity.subject,
                "impersonated_subject": self.caller_identity.impersonated_subject,
                "impersonation_declared": self.caller_identity.impersonation_declared,
            },
            "tenant_context": {
                "tenant_id": self.tenant_context.tenant_id,
                "account_id": self.tenant_context.account_id,
                "project_id": self.tenant_context.project_id,
            },
            "invocation": {
                "invocation_id": self.invocation.invocation_id,
                "timestamp": self.invocation.timestamp,
                "sequence_number": self.invocation.sequence_number,
            },
            "plan": {
                "input_hash": self.plan.input_hash,
                "resolved_plan_hash": self.plan.resolved_plan_hash,
                "plan_mutation_detected": self.plan.plan_mutation_detected,
                "original_invocation_id": self.plan.original_invocation_id,
            },
            "confidence": (
                {
                    "score": self.confidence.score,
                    "threshold_used": self.confidence.threshold_used,
                    "auto_execute_triggered": self.confidence.auto_execute_triggered,
                }
                if self.confidence
                else None
            ),
            "attribution": {
                "origin": self.attribution.origin,
                "reason_code": self.attribution.reason_code,
                "source_command": self.attribution.source_command,
                "sdk_version": self.attribution.sdk_version,
                "cli_version": self.attribution.cli_version,
            },
            "evidence": {
                "emitted_at": self.evidence.emitted_at,
                "storage_location": self.evidence.storage_location,
                "emission_success": self.evidence.emission_success,
            },
            # PIN-332: Invocation safety flags
            "invocation_safety": (
                {
                    "checked": self.invocation_safety.checked,
                    "passed": self.invocation_safety.passed,
                    "flags": self.invocation_safety.flags,
                    "warnings": self.invocation_safety.warnings,
                    "blocked": self.invocation_safety.blocked,
                    "block_reason": self.invocation_safety.block_reason,
                }
                if self.invocation_safety
                else None
            ),
        }

    def to_json(self) -> str:
        """Convert envelope to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# =============================================================================
# PLAN HASHING (PHASE 2)
# =============================================================================


def compute_plan_hash(data: Any) -> str:
    """
    Compute deterministic SHA-256 hash of input data.

    Used for:
    - input_hash: Raw input before transformation
    - resolved_plan_hash: Resolved execution plan

    Args:
        data: Any JSON-serializable data

    Returns:
        SHA-256 hex digest
    """
    if data is None:
        data = {}

    # Canonical JSON serialization (sorted keys, no whitespace)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# ENVELOPE FACTORY (PHASE 1.2)
# =============================================================================


class ExecutionEnvelopeFactory:
    """
    Factory for creating execution envelopes.

    INVARIANT: Envelope creation failure MUST NOT block execution.
    """

    @staticmethod
    def create_cli_envelope(
        subject: str,
        tenant_id: str,
        command: str,
        raw_input: Any,
        resolved_plan: Any,
        impersonated_subject: Optional[str] = None,
        reason_code: Optional[str] = None,
        cli_version: Optional[str] = None,
        account_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ExecutionEnvelope:
        """
        Create envelope for CAP-020 (CLI Execution).

        Args:
            subject: Primary identity (user executing CLI)
            tenant_id: Tenant identifier
            command: The CLI command being executed
            raw_input: Raw input before transformation
            resolved_plan: Resolved execution plan
            impersonated_subject: Target identity if --by used
            reason_code: Human-readable reason for impersonation
            cli_version: CLI version string
            account_id: Account identifier
            project_id: Project identifier

        Returns:
            ExecutionEnvelope for CAP-020
        """
        return ExecutionEnvelope(
            envelope_id=str(uuid.uuid4()),
            capability_id=CapabilityId.CAP_020,
            execution_vector=ExecutionVector.CLI,
            caller_identity=CallerIdentity(
                type=CallerType.HUMAN,
                subject=subject,
                impersonated_subject=impersonated_subject,
                impersonation_declared=impersonated_subject is not None and reason_code is not None,
            ),
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                account_id=account_id,
                project_id=project_id,
            ),
            invocation=InvocationTracking(),
            plan=PlanIntegrity(
                input_hash=compute_plan_hash(raw_input),
                resolved_plan_hash=compute_plan_hash(resolved_plan),
            ),
            attribution=Attribution(
                source_command=command,
                reason_code=reason_code,
                cli_version=cli_version,
            ),
            evidence=EvidenceMetadata(),
        )

    @staticmethod
    def create_sdk_envelope(
        subject: str,
        tenant_id: str,
        method_name: str,
        raw_input: Any,
        resolved_plan: Any,
        caller_type: CallerType = CallerType.SERVICE,
        force_skill: Optional[str] = None,
        reason_code: Optional[str] = None,
        sdk_version: Optional[str] = None,
        account_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ExecutionEnvelope:
        """
        Create envelope for CAP-021 (SDK Execution).

        Args:
            subject: Primary identity (service or user using SDK)
            tenant_id: Tenant identifier
            method_name: The SDK method being called
            raw_input: Raw input before transformation
            resolved_plan: Resolved execution plan
            caller_type: Human or service
            force_skill: force_skill parameter if used (planning bypass)
            reason_code: Human-readable reason for force_skill
            sdk_version: SDK version string
            account_id: Account identifier
            project_id: Project identifier

        Returns:
            ExecutionEnvelope for CAP-021
        """
        return ExecutionEnvelope(
            envelope_id=str(uuid.uuid4()),
            capability_id=CapabilityId.CAP_021,
            execution_vector=ExecutionVector.SDK,
            caller_identity=CallerIdentity(
                type=caller_type,
                subject=subject,
                impersonated_subject=force_skill,  # force_skill is a form of bypass
                impersonation_declared=force_skill is not None and reason_code is not None,
            ),
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                account_id=account_id,
                project_id=project_id,
            ),
            invocation=InvocationTracking(),
            plan=PlanIntegrity(
                input_hash=compute_plan_hash(raw_input),
                resolved_plan_hash=compute_plan_hash(resolved_plan),
            ),
            attribution=Attribution(
                source_command=method_name,
                reason_code=reason_code,
                sdk_version=sdk_version,
            ),
            evidence=EvidenceMetadata(),
        )

    @staticmethod
    def create_auto_execute_envelope(
        tenant_id: str,
        confidence_score: float,
        threshold: float,
        proposed_action: Any,
        resolved_plan: Any,
        recovery_candidate_id: Optional[str] = None,
        account_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ExecutionEnvelope:
        """
        Create envelope for SUB-019 (Auto-Execute Recovery).

        Args:
            tenant_id: Tenant identifier
            confidence_score: The confidence score that triggered auto-execute
            threshold: The threshold used (typically 0.8)
            proposed_action: The recovery action being executed
            resolved_plan: Resolved execution plan
            recovery_candidate_id: ID of the recovery candidate
            account_id: Account identifier
            project_id: Project identifier

        Returns:
            ExecutionEnvelope for SUB-019
        """
        return ExecutionEnvelope(
            envelope_id=str(uuid.uuid4()),
            capability_id=CapabilityId.SUB_019,
            execution_vector=ExecutionVector.AUTO_EXEC,
            caller_identity=CallerIdentity(
                type=CallerType.SYSTEM,
                subject="recovery_claim_worker",
                impersonated_subject=None,
                impersonation_declared=False,  # System cannot impersonate
            ),
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                account_id=account_id,
                project_id=project_id,
            ),
            invocation=InvocationTracking(),
            plan=PlanIntegrity(
                input_hash=compute_plan_hash({"candidate_id": recovery_candidate_id, "action": proposed_action}),
                resolved_plan_hash=compute_plan_hash(resolved_plan),
            ),
            confidence=ConfidenceContext(
                score=confidence_score,
                threshold_used=threshold,
                auto_execute_triggered=confidence_score >= threshold,
            ),
            attribution=Attribution(
                source_command="auto_execute_recovery",
                reason_code=f"confidence_score={confidence_score:.2f} >= threshold={threshold:.2f}",
            ),
            evidence=EvidenceMetadata(),
        )

    @staticmethod
    def create_admin_envelope(
        subject: str,
        tenant_id: str,
        route: str,
        raw_input: Any,
        resolved_plan: Any,
        reason_code: Optional[str] = None,
        account_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ExecutionEnvelope:
        """
        Create envelope for CAP-019 (Run Management) admin routes.

        PIN-335: Admin retry creates new run via CAP-019 semantics.

        Args:
            subject: Primary identity (founder executing admin route)
            tenant_id: Tenant identifier
            route: The admin route being executed (e.g., "/admin/retry")
            raw_input: Raw input before transformation
            resolved_plan: Resolved execution plan
            reason_code: Human-readable reason for admin action
            account_id: Account identifier
            project_id: Project identifier

        Returns:
            ExecutionEnvelope for CAP-019 (admin routes)
        """
        return ExecutionEnvelope(
            envelope_id=str(uuid.uuid4()),
            capability_id=CapabilityId.CAP_019,
            execution_vector=ExecutionVector.HTTP_ADMIN,
            caller_identity=CallerIdentity(
                type=CallerType.HUMAN,  # Founder is human
                subject=subject,
                impersonated_subject=None,
                impersonation_declared=False,
            ),
            tenant_context=TenantContext(
                tenant_id=tenant_id,
                account_id=account_id,
                project_id=project_id,
            ),
            invocation=InvocationTracking(),
            plan=PlanIntegrity(
                input_hash=compute_plan_hash(raw_input),
                resolved_plan_hash=compute_plan_hash(resolved_plan),
            ),
            attribution=Attribution(
                origin="PIN-335",
                source_command=route,
                reason_code=reason_code,
            ),
            evidence=EvidenceMetadata(),
        )


# =============================================================================
# MUTATION DETECTION (PHASE 2.2)
# =============================================================================


def detect_plan_mutation(envelope: ExecutionEnvelope, new_plan: Any) -> tuple[bool, Optional[ExecutionEnvelope]]:
    """
    Detect if plan has changed mid-execution.

    If mutation detected:
    - Mark envelope with plan_mutation_detected=True
    - Generate new invocation_id
    - Preserve original_invocation_id
    - Allow execution to continue unchanged

    Args:
        envelope: Current execution envelope
        new_plan: The potentially mutated plan

    Returns:
        Tuple of (mutation_detected, updated_envelope or None)
    """
    new_hash = compute_plan_hash(new_plan)

    if new_hash != envelope.plan.resolved_plan_hash:
        # Mutation detected - create updated envelope
        original_invocation_id = envelope.plan.original_invocation_id or envelope.invocation.invocation_id

        updated_envelope = ExecutionEnvelope(
            envelope_id=envelope.envelope_id,  # Same envelope
            capability_id=envelope.capability_id,
            execution_vector=envelope.execution_vector,
            caller_identity=envelope.caller_identity,
            tenant_context=envelope.tenant_context,
            invocation=InvocationTracking(
                invocation_id=str(uuid.uuid4()),  # New invocation
                timestamp=datetime.now(timezone.utc).isoformat(),
                sequence_number=(envelope.invocation.sequence_number or 0) + 1,
            ),
            plan=PlanIntegrity(
                input_hash=envelope.plan.input_hash,  # Original input
                resolved_plan_hash=new_hash,  # New plan hash
                plan_mutation_detected=True,
                original_invocation_id=original_invocation_id,
            ),
            confidence=envelope.confidence,
            attribution=envelope.attribution,
            evidence=EvidenceMetadata(),
        )

        logger.warning(
            "Plan mutation detected",
            extra={
                "envelope_id": envelope.envelope_id,
                "original_invocation_id": original_invocation_id,
                "new_invocation_id": updated_envelope.invocation.invocation_id,
                "original_hash": envelope.plan.resolved_plan_hash,
                "new_hash": new_hash,
            },
        )

        return True, updated_envelope

    return False, None


# =============================================================================
# EVIDENCE SINK INTERFACE (PHASE 5)
# =============================================================================


class EvidenceSink:
    """
    Abstract interface for envelope storage.

    INVARIANT: Emission failure MUST NOT block execution.
    """

    def emit(self, envelope: ExecutionEnvelope) -> bool:
        """
        Emit envelope to storage.

        Args:
            envelope: The execution envelope to store

        Returns:
            True if emission succeeded, False otherwise
            (False does NOT block execution)
        """
        raise NotImplementedError

    def query_by_capability(self, capability_id: CapabilityId, limit: int = 100) -> list[dict[str, Any]]:
        """Query envelopes by capability."""
        raise NotImplementedError

    def query_by_tenant(self, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Query envelopes by tenant."""
        raise NotImplementedError

    def query_by_invocation(self, invocation_id: str) -> Optional[dict[str, Any]]:
        """Query envelope by invocation_id."""
        raise NotImplementedError


class InMemoryEvidenceSink(EvidenceSink):
    """
    In-memory evidence sink for testing and development.

    NOT suitable for production - use DatabaseEvidenceSink.
    """

    def __init__(self) -> None:
        self._envelopes: list[dict[str, Any]] = []

    def emit(self, envelope: ExecutionEnvelope) -> bool:
        """Store envelope in memory."""
        try:
            self._envelopes.append(envelope.to_dict())
            return True
        except Exception as e:
            logger.error(f"Evidence emission failed (non-blocking): {e}")
            return False

    def query_by_capability(self, capability_id: CapabilityId, limit: int = 100) -> list[dict[str, Any]]:
        return [e for e in self._envelopes if e["capability_id"] == capability_id.value][:limit]

    def query_by_tenant(self, tenant_id: str, limit: int = 100) -> list[dict[str, Any]]:
        return [e for e in self._envelopes if e["tenant_context"]["tenant_id"] == tenant_id][:limit]

    def query_by_invocation(self, invocation_id: str) -> Optional[dict[str, Any]]:
        for e in self._envelopes:
            if e["invocation"]["invocation_id"] == invocation_id:
                return e
        return None

    @property
    def count(self) -> int:
        """Total number of stored envelopes."""
        return len(self._envelopes)


# =============================================================================
# GLOBAL EVIDENCE SINK (CONFIGURABLE)
# =============================================================================

_evidence_sink: Optional[EvidenceSink] = None


def get_evidence_sink() -> EvidenceSink:
    """Get the configured evidence sink."""
    global _evidence_sink
    if _evidence_sink is None:
        # Default to in-memory for development
        _evidence_sink = InMemoryEvidenceSink()
    return _evidence_sink


def set_evidence_sink(sink: EvidenceSink) -> None:
    """Configure the evidence sink."""
    global _evidence_sink
    _evidence_sink = sink


# =============================================================================
# NON-BLOCKING ENVELOPE EMISSION
# =============================================================================


def emit_envelope(envelope: ExecutionEnvelope) -> bool:
    """
    Emit envelope to configured evidence sink.

    INVARIANT: This function NEVER raises exceptions.
    Failure is logged but does NOT block execution.

    Args:
        envelope: The execution envelope to emit

    Returns:
        True if emission succeeded, False otherwise
    """
    try:
        sink = get_evidence_sink()
        envelope.evidence.emitted_at = datetime.now(timezone.utc).isoformat()
        success = sink.emit(envelope)
        envelope.evidence.emission_success = success

        if success:
            logger.info(
                "Execution envelope emitted",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "capability_id": envelope.capability_id.value,
                    "execution_vector": envelope.execution_vector.value,
                    "invocation_id": envelope.invocation.invocation_id,
                },
            )
        else:
            logger.warning(
                "Execution envelope emission failed (non-blocking)",
                extra={
                    "envelope_id": envelope.envelope_id,
                    "capability_id": envelope.capability_id.value,
                },
            )

        return success

    except Exception as e:
        # CRITICAL: Never block execution
        logger.error(
            f"Execution envelope emission error (non-blocking): {e}",
            extra={
                "envelope_id": envelope.envelope_id if envelope else "unknown",
                "error": str(e),
            },
        )
        return False


# =============================================================================
# CONTEXT MANAGER FOR EXECUTION TRACKING
# =============================================================================


@contextmanager
def tracked_execution(
    envelope: ExecutionEnvelope,
) -> Generator[ExecutionEnvelope, None, None]:
    """
    Context manager for tracked execution.

    Emits envelope at entry, allows mutation detection, and updates on exit.
    NEVER blocks execution, even if emission fails.

    Usage:
        envelope = ExecutionEnvelopeFactory.create_cli_envelope(...)
        with tracked_execution(envelope) as env:
            # Execute business logic
            result = do_work()
            # Optionally detect mutation
            mutated, updated = detect_plan_mutation(env, new_plan)
            if mutated:
                env = updated
    """
    # Emit at entry (non-blocking)
    emit_envelope(envelope)

    try:
        yield envelope
    finally:
        # No cleanup needed - envelope is immutable
        pass


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_invocation_id_for_tagging(envelope: Optional[ExecutionEnvelope]) -> Optional[str]:
    """
    Get invocation_id for cross-referencing side-effects.

    Safe to call with None - returns None.
    Used for tagging DB writes, events, logs with invocation_id.
    """
    if envelope is None:
        return None
    return envelope.invocation.invocation_id
