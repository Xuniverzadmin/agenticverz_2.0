# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Integration event definitions
# Callers: integrations/*
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Event System

"""
M25 Integration Loop Events

# =============================================================================
# M25_FROZEN - DO NOT MODIFY
# =============================================================================
# Any changes here require explicit M25 reopen approval.
# Changes invalidate all prior graduation evidence.
# See PIN-140 for freeze rationale.
# =============================================================================

Enhanced with:
- Confidence bands (strong/weak/novel) instead of binary matching
- Loop failure states for unhappy paths
- Policy shadow mode support
- Human checkpoint controls
- Routing guardrails

FROZEN: 2025-12-23
GRADUATION_RULES_VERSION = "1.0.0"
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

# =============================================================================
# FROZEN MECHANICS - DO NOT MODIFY WITHOUT APPROVAL
# =============================================================================

LOOP_MECHANICS_VERSION = "1.0.0"
LOOP_MECHANICS_FROZEN_AT = "2025-12-23"


# =============================================================================
# CONFIDENCE CALCULATION (CENTRALIZED, VERSIONED)
# =============================================================================


class ConfidenceCalculator:
    """
    Centralized confidence calculation.

    FROZEN: All confidence logic must go through this class.
    Version is logged with every confidence value for audit.
    """

    VERSION = "CONFIDENCE_V1"

    # Thresholds - DO NOT MODIFY
    STRONG_MATCH_THRESHOLD = 0.85
    WEAK_MATCH_THRESHOLD = 0.6

    # Occurrence-based boosting - DO NOT MODIFY
    BOOST_2_OCCURRENCES = 0.10
    BOOST_3_OCCURRENCES = 0.20
    MAX_CONFIDENCE = 0.90

    # Auto-apply thresholds - DO NOT MODIFY
    AUTO_APPLY_CONFIDENCE = 0.85
    AUTO_APPLY_MIN_OCCURRENCES = 3

    @classmethod
    def calculate_recovery_confidence(
        cls,
        base_confidence: float,
        occurrence_count: int,
        is_strong_match: bool,
    ) -> tuple[float, str, dict]:
        """
        Calculate recovery confidence with occurrence boosting.

        Returns: (confidence, version, details_dict)
        """
        if is_strong_match:
            effective_base = 0.7
        else:
            effective_base = 0.5

        if occurrence_count >= 3:
            confidence = min(cls.MAX_CONFIDENCE, effective_base + cls.BOOST_3_OCCURRENCES)
        elif occurrence_count >= 2:
            confidence = min(cls.MAX_CONFIDENCE, effective_base + cls.BOOST_2_OCCURRENCES)
        else:
            confidence = effective_base

        details = {
            "version": cls.VERSION,
            "base_confidence": effective_base,
            "occurrence_count": occurrence_count,
            "boost_applied": confidence - effective_base,
            "final_confidence": confidence,
        }

        return confidence, cls.VERSION, details

    @classmethod
    def should_auto_apply(cls, confidence: float, occurrence_count: int) -> bool:
        """Determine if recovery should auto-apply."""
        return confidence >= cls.AUTO_APPLY_CONFIDENCE and occurrence_count >= cls.AUTO_APPLY_MIN_OCCURRENCES

    @classmethod
    def get_confirmation_level(cls, confidence: float) -> int:
        """Get required confirmation level based on confidence."""
        if confidence >= cls.AUTO_APPLY_CONFIDENCE:
            return 0  # Auto-apply
        elif confidence >= cls.WEAK_MATCH_THRESHOLD:
            return 1  # Single confirmation
        else:
            return 2  # Double confirmation


# =============================================================================
# JSON SERIALIZATION GUARD
# =============================================================================


def ensure_json_serializable(obj: Any, path: str = "root") -> Any:
    """
    Guard function to ensure all objects stored in details are JSON-serializable.

    Raises TypeError with clear path if non-serializable object found.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: ensure_json_serializable(v, f"{path}.{k}") for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [ensure_json_serializable(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()

    # Non-serializable object detected
    raise TypeError(
        f"Object at '{path}' of type {type(obj).__name__} is not JSON serializable. "
        f"Add to_dict() method or convert before storing in event.details."
    )


# =============================================================================
# CONFIDENCE BANDS (Replaces binary 80% threshold)
# =============================================================================


class ConfidenceBand(str, Enum):
    """
    Confidence classification for pattern matching.

    - STRONG_MATCH: High confidence (>0.85) - Safe for auto-apply
    - WEAK_MATCH: Medium confidence (0.6-0.85) - Requires review
    - NOVEL: Low confidence (<0.6) - New pattern, needs investigation
    """

    STRONG_MATCH = "strong_match"  # > 0.85 - Auto-apply safe
    WEAK_MATCH = "weak_match"  # 0.6 - 0.85 - Requires review
    NOVEL = "novel"  # < 0.6 - New pattern

    @classmethod
    def from_confidence(cls, confidence: float) -> "ConfidenceBand":
        """Classify confidence score into band."""
        if confidence >= 0.85:
            return cls.STRONG_MATCH
        elif confidence >= 0.6:
            return cls.WEAK_MATCH
        else:
            return cls.NOVEL

    @property
    def allows_auto_apply(self) -> bool:
        """Only strong matches allow auto-apply."""
        return self == ConfidenceBand.STRONG_MATCH

    @property
    def requires_human_review(self) -> bool:
        """Weak and novel patterns require human review."""
        return self in (ConfidenceBand.WEAK_MATCH, ConfidenceBand.NOVEL)


# =============================================================================
# LOOP STAGES AND FAILURE STATES
# =============================================================================


class LoopStage(str, Enum):
    """Stages in the integration feedback loop."""

    INCIDENT_CREATED = "incident_created"
    PATTERN_MATCHED = "pattern_matched"
    RECOVERY_SUGGESTED = "recovery_suggested"
    POLICY_GENERATED = "policy_generated"
    ROUTING_ADJUSTED = "routing_adjusted"
    LOOP_COMPLETE = "loop_complete"


class LoopFailureState(str, Enum):
    """
    Explicit failure states for when the loop doesn't complete.

    Critical for debugging and trust - the unhappy path matters more
    than the happy path.
    """

    MATCH_FAILED = "match_failed"  # Pattern matching failed
    MATCH_LOW_CONFIDENCE = "match_low_confidence"  # Match confidence too low
    RECOVERY_REJECTED = "recovery_rejected"  # Recovery was rejected
    RECOVERY_NOT_APPLICABLE = "recovery_not_applicable"  # No recovery available
    POLICY_LOW_CONFIDENCE = "policy_low_confidence"  # Policy confidence too low
    POLICY_REJECTED = "policy_rejected"  # Policy was rejected
    POLICY_SHADOW_MODE = "policy_shadow_mode"  # Policy in shadow mode
    ROUTING_ADJUSTMENT_SKIPPED = "routing_adjustment_skipped"  # Adjustment skipped
    ROUTING_GUARDRAIL_BLOCKED = "routing_guardrail_blocked"  # Guardrail prevented change
    HUMAN_CHECKPOINT_PENDING = "human_checkpoint_pending"  # Waiting for human
    TIMEOUT = "timeout"  # Loop timed out
    ERROR = "error"  # Unexpected error


class PolicyMode(str, Enum):
    """
    Policy activation modes for safety.

    Shadow mode allows observation without enforcement.
    """

    SHADOW = "shadow"  # Observe only, no enforcement
    PENDING = "pending"  # Waiting for confirmations
    ACTIVE = "active"  # Fully enforced
    DISABLED = "disabled"  # Turned off


class HumanCheckpointType(str, Enum):
    """Types of human intervention points."""

    APPROVE_POLICY = "approve_policy"
    APPROVE_RECOVERY = "approve_recovery"
    SIMULATE_ROUTING = "simulate_routing"
    REVERT_LOOP = "revert_loop"
    OVERRIDE_GUARDRAIL = "override_guardrail"


# =============================================================================
# CORE EVENT TYPES
# =============================================================================


@dataclass
class LoopEvent:
    """
    Base event for integration loop.

    All events flow through the dispatcher and are persisted for durability.
    """

    event_id: str
    incident_id: str
    tenant_id: str
    stage: LoopStage
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)
    failure_state: Optional[LoopFailureState] = None
    confidence_band: Optional[ConfidenceBand] = None
    requires_human_review: bool = False

    @classmethod
    def create(
        cls,
        incident_id: str,
        tenant_id: str,
        stage: LoopStage,
        details: dict[str, Any] | None = None,
        failure_state: LoopFailureState | None = None,
        confidence_band: ConfidenceBand | None = None,
    ) -> "LoopEvent":
        """Factory method to create events with auto-generated ID and timestamp."""
        return cls(
            event_id=f"evt_{uuid.uuid4().hex[:16]}",
            incident_id=incident_id,
            tenant_id=tenant_id,
            stage=stage,
            timestamp=datetime.now(timezone.utc),
            details=details or {},
            failure_state=failure_state,
            confidence_band=confidence_band,
            requires_human_review=confidence_band.requires_human_review if confidence_band else False,
        )

    @property
    def is_success(self) -> bool:
        """Check if event represents successful stage completion."""
        return self.failure_state is None

    @property
    def is_blocked(self) -> bool:
        """Check if loop is blocked at this stage."""
        return self.failure_state in (
            LoopFailureState.HUMAN_CHECKPOINT_PENDING,
            LoopFailureState.POLICY_SHADOW_MODE,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for Redis/JSON."""
        return {
            "event_id": self.event_id,
            "incident_id": self.incident_id,
            "tenant_id": self.tenant_id,
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "failure_state": self.failure_state.value if self.failure_state else None,
            "confidence_band": self.confidence_band.value if self.confidence_band else None,
            "requires_human_review": self.requires_human_review,
            "is_success": self.is_success,
        }


# =============================================================================
# BRIDGE-SPECIFIC RESULT TYPES
# =============================================================================


@dataclass
class PatternMatchResult:
    """
    Result of Bridge 1: Incident → Failure Catalog.

    Enhanced with confidence bands instead of binary matching.
    """

    incident_id: str
    pattern_id: Optional[str]
    confidence: float
    confidence_band: ConfidenceBand
    is_new_pattern: bool
    matched: bool
    signature_hash: str
    match_details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_match(
        cls,
        incident_id: str,
        pattern_id: str,
        confidence: float,
        signature_hash: str,
        is_new: bool = False,
        details: dict[str, Any] | None = None,
    ) -> "PatternMatchResult":
        """Create result from successful match."""
        band = ConfidenceBand.from_confidence(confidence)
        return cls(
            incident_id=incident_id,
            pattern_id=pattern_id,
            confidence=confidence,
            confidence_band=band,
            is_new_pattern=is_new,
            matched=True,
            signature_hash=signature_hash,
            match_details=details or {},
        )

    @classmethod
    def no_match(cls, incident_id: str, signature_hash: str) -> "PatternMatchResult":
        """Create result for no match found."""
        return cls(
            incident_id=incident_id,
            pattern_id=None,
            confidence=0.0,
            confidence_band=ConfidenceBand.NOVEL,
            is_new_pattern=True,  # Will create new pattern
            matched=False,
            signature_hash=signature_hash,
        )

    @property
    def should_auto_proceed(self) -> bool:
        """Only proceed automatically for strong matches."""
        return self.confidence_band.allows_auto_apply

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/Redis."""
        return {
            "incident_id": self.incident_id,
            "pattern_id": self.pattern_id,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band.value,
            "is_new_pattern": self.is_new_pattern,
            "matched": self.matched,
            "signature_hash": self.signature_hash,
            "match_details": self.match_details,
            "should_auto_proceed": self.should_auto_proceed,
        }


@dataclass
class RecoverySuggestion:
    """
    Result of Bridge 2: Pattern → Recovery.

    Enhanced with template vs generated distinction and confidence scoring.
    """

    recovery_id: str
    incident_id: str
    pattern_id: str
    suggestion_type: Literal["template", "generated", "none"]
    confidence: float
    confidence_band: ConfidenceBand
    action_type: str  # e.g., "rate_limit", "block", "retry", "escalate"
    action_params: dict[str, Any]
    status: Literal["pending", "approved", "applied", "rejected"]
    auto_applicable: bool
    requires_confirmation: int  # Number of confirmations needed
    confirmations_received: int = 0
    rejection_reason: Optional[str] = None

    @classmethod
    def create(
        cls,
        incident_id: str,
        pattern_id: str,
        action_type: str,
        action_params: dict[str, Any],
        confidence: float,
        suggestion_type: Literal["template", "generated"] = "generated",
        requires_confirmation: int = 0,
    ) -> "RecoverySuggestion":
        """Factory method for creating recovery suggestions."""
        band = ConfidenceBand.from_confidence(confidence)
        return cls(
            recovery_id=f"rec_{uuid.uuid4().hex[:16]}",
            incident_id=incident_id,
            pattern_id=pattern_id,
            suggestion_type=suggestion_type,
            confidence=confidence,
            confidence_band=band,
            action_type=action_type,
            action_params=action_params,
            status="pending",
            auto_applicable=band.allows_auto_apply and requires_confirmation == 0,
            requires_confirmation=requires_confirmation,
        )

    @classmethod
    def none_available(cls, incident_id: str, pattern_id: str) -> "RecoverySuggestion":
        """Create placeholder when no recovery is available."""
        return cls(
            recovery_id=f"rec_{uuid.uuid4().hex[:16]}",
            incident_id=incident_id,
            pattern_id=pattern_id,
            suggestion_type="none",
            confidence=0.0,
            confidence_band=ConfidenceBand.NOVEL,
            action_type="none",
            action_params={},
            status="rejected",
            auto_applicable=False,
            requires_confirmation=0,
            rejection_reason="No recovery strategy available",
        )

    def add_confirmation(self) -> bool:
        """Add a confirmation. Returns True if threshold reached."""
        self.confirmations_received += 1
        if self.confirmations_received >= self.requires_confirmation:
            self.status = "approved"
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/Redis."""
        return {
            "recovery_id": self.recovery_id,
            "incident_id": self.incident_id,
            "pattern_id": self.pattern_id,
            "suggestion_type": self.suggestion_type,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band.value,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "status": self.status,
            "auto_applicable": self.auto_applicable,
            "requires_confirmation": self.requires_confirmation,
            "confirmations_received": self.confirmations_received,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class PolicyRule:
    """
    Result of Bridge 3: Recovery → Policy.

    Enhanced with:
    - Shadow mode for safe observation
    - Confirmation requirements
    - Policy regret tracking
    """

    policy_id: str
    name: str
    description: str
    category: Literal["safety", "privacy", "operational", "routing", "custom"]
    condition: str  # Policy DSL expression
    action: Literal["block", "warn", "escalate", "route_away", "rate_limit"]
    scope_type: Literal["tenant", "agent", "global"]
    scope_id: Optional[str]  # tenant_id or agent_id
    source_pattern_id: str
    source_recovery_id: str
    confidence: float
    confidence_band: ConfidenceBand
    mode: PolicyMode
    confirmations_required: int
    confirmations_received: int = 0
    regret_count: int = 0  # Times this policy caused an incident
    shadow_evaluations: int = 0  # Times evaluated in shadow mode
    shadow_would_block: int = 0  # Times it would have blocked
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        category: str,
        condition: str,
        action: str,
        source_pattern_id: str,
        source_recovery_id: str,
        confidence: float,
        scope_type: str = "tenant",
        scope_id: str | None = None,
        confirmations_required: int = 3,  # Default: require 3 confirmations
    ) -> "PolicyRule":
        """Factory method for creating policy rules."""
        band = ConfidenceBand.from_confidence(confidence)

        # High confidence + 3+ pattern occurrences = shadow mode (observe first)
        # Everything else starts in pending
        initial_mode = PolicyMode.SHADOW if band == ConfidenceBand.STRONG_MATCH else PolicyMode.PENDING

        return cls(
            policy_id=f"pol_{uuid.uuid4().hex[:16]}",
            name=name,
            description=description,
            category=category,
            condition=condition,
            action=action,
            scope_type=scope_type,
            scope_id=scope_id,
            source_pattern_id=source_pattern_id,
            source_recovery_id=source_recovery_id,
            confidence=confidence,
            confidence_band=band,
            mode=initial_mode,
            confirmations_required=confirmations_required,
        )

    def record_shadow_evaluation(self, would_block: bool) -> None:
        """Track shadow mode evaluations for confidence building."""
        self.shadow_evaluations += 1
        if would_block:
            self.shadow_would_block += 1

    def add_confirmation(self) -> bool:
        """Add confirmation. Returns True if ready to activate."""
        self.confirmations_received += 1
        if self.confirmations_received >= self.confirmations_required:
            self.mode = PolicyMode.ACTIVE
            self.activated_at = datetime.now(timezone.utc)
            return True
        return False

    def record_regret(self) -> None:
        """Record when this policy caused an incident (regret)."""
        self.regret_count += 1
        # Auto-disable if regret exceeds threshold
        if self.regret_count >= 3:
            self.mode = PolicyMode.DISABLED

    @property
    def shadow_block_rate(self) -> float:
        """Percentage of shadow evaluations that would have blocked."""
        if self.shadow_evaluations == 0:
            return 0.0
        return self.shadow_would_block / self.shadow_evaluations

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/Redis."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "condition": self.condition,
            "action": self.action,
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "source_pattern_id": self.source_pattern_id,
            "source_recovery_id": self.source_recovery_id,
            "confidence": self.confidence,
            "confidence_band": self.confidence_band.value,
            "mode": self.mode.value,
            "confirmations_required": self.confirmations_required,
            "confirmations_received": self.confirmations_received,
            "regret_count": self.regret_count,
            "shadow_evaluations": self.shadow_evaluations,
            "shadow_would_block": self.shadow_would_block,
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "shadow_block_rate": self.shadow_block_rate,
        }


@dataclass
class RoutingAdjustment:
    """
    Result of Bridge 4: Policy → CARE Routing.

    Enhanced with guardrails:
    - Max delta per adjustment
    - Decay window
    - Rollback on KPI regression
    """

    adjustment_id: str
    agent_id: str
    capability: Optional[str]
    adjustment_type: Literal["confidence_penalty", "route_block", "escalation_add", "weight_shift"]
    magnitude: float  # -1.0 to +1.0
    reason: str
    source_policy_id: str
    # Guardrails
    max_delta: float = 0.2  # Never adjust more than 20% at once
    decay_days: int = 7  # Adjustment decays over 7 days
    rollback_threshold: float = 0.1  # Rollback if KPI drops 10%
    # State
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = True
    was_rolled_back: bool = False
    rollback_reason: Optional[str] = None
    kpi_baseline: Optional[float] = None
    kpi_current: Optional[float] = None

    @classmethod
    def create(
        cls,
        agent_id: str,
        adjustment_type: str,
        magnitude: float,
        reason: str,
        source_policy_id: str,
        capability: str | None = None,
        max_delta: float = 0.2,
        decay_days: int = 7,
    ) -> "RoutingAdjustment":
        """Factory with guardrail enforcement."""
        # Enforce max delta guardrail
        clamped_magnitude = max(-max_delta, min(max_delta, magnitude))

        expires_at = (
            datetime.now(timezone.utc).replace(day=datetime.now(timezone.utc).day + decay_days)
            if decay_days > 0
            else None
        )

        return cls(
            adjustment_id=f"adj_{uuid.uuid4().hex[:16]}",
            agent_id=agent_id,
            capability=capability,
            adjustment_type=adjustment_type,
            magnitude=clamped_magnitude,
            reason=reason,
            source_policy_id=source_policy_id,
            max_delta=max_delta,
            decay_days=decay_days,
            expires_at=expires_at,
        )

    def check_kpi_regression(self, current_kpi: float) -> bool:
        """
        Check if KPI has regressed past threshold.

        Returns True if rollback should occur.
        """
        if self.kpi_baseline is None:
            return False

        self.kpi_current = current_kpi
        regression = (self.kpi_baseline - current_kpi) / self.kpi_baseline

        if regression > self.rollback_threshold:
            self.rollback(f"KPI regression: {regression:.1%}")
            return True
        return False

    def rollback(self, reason: str) -> None:
        """Rollback this adjustment."""
        self.is_active = False
        self.was_rolled_back = True
        self.rollback_reason = reason

    @property
    def effective_magnitude(self) -> float:
        """Calculate current magnitude with decay applied."""
        if not self.is_active or self.expires_at is None:
            return 0.0

        now = datetime.now(timezone.utc)
        if now >= self.expires_at:
            return 0.0

        # Linear decay
        total_seconds = (self.expires_at - self.created_at).total_seconds()
        elapsed_seconds = (now - self.created_at).total_seconds()
        decay_factor = 1.0 - (elapsed_seconds / total_seconds)

        return self.magnitude * decay_factor

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/Redis."""
        return {
            "adjustment_id": self.adjustment_id,
            "agent_id": self.agent_id,
            "capability": self.capability,
            "adjustment_type": self.adjustment_type,
            "magnitude": self.magnitude,
            "reason": self.reason,
            "source_policy_id": self.source_policy_id,
            "max_delta": self.max_delta,
            "decay_days": self.decay_days,
            "rollback_threshold": self.rollback_threshold,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "was_rolled_back": self.was_rolled_back,
            "rollback_reason": self.rollback_reason,
            "kpi_baseline": self.kpi_baseline,
            "kpi_current": self.kpi_current,
            "effective_magnitude": self.effective_magnitude,
        }


# =============================================================================
# LOOP STATUS AND HUMAN CHECKPOINTS
# =============================================================================


@dataclass
class HumanCheckpoint:
    """
    Human intervention point in the loop.

    Supports: approve, simulate, revert actions.
    """

    checkpoint_id: str
    checkpoint_type: HumanCheckpointType
    incident_id: str
    tenant_id: str
    stage: LoopStage
    target_id: str  # policy_id, recovery_id, etc.
    description: str
    options: list[str]  # Available actions
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # user_id
    resolution: Optional[str] = None  # chosen action

    @classmethod
    def create(
        cls,
        checkpoint_type: HumanCheckpointType,
        incident_id: str,
        tenant_id: str,
        stage: LoopStage,
        target_id: str,
        description: str,
        options: list[str] | None = None,
    ) -> "HumanCheckpoint":
        """Factory for creating checkpoints."""
        default_options = {
            HumanCheckpointType.APPROVE_POLICY: ["approve", "reject", "modify"],
            HumanCheckpointType.APPROVE_RECOVERY: ["apply", "reject", "defer"],
            HumanCheckpointType.SIMULATE_ROUTING: ["apply", "cancel"],
            HumanCheckpointType.REVERT_LOOP: ["confirm_revert", "cancel"],
            HumanCheckpointType.OVERRIDE_GUARDRAIL: ["override", "respect"],
        }

        return cls(
            checkpoint_id=f"chk_{uuid.uuid4().hex[:16]}",
            checkpoint_type=checkpoint_type,
            incident_id=incident_id,
            tenant_id=tenant_id,
            stage=stage,
            target_id=target_id,
            description=description,
            options=options or default_options.get(checkpoint_type, ["approve", "reject"]),
            created_at=datetime.now(timezone.utc),
        )

    def resolve(self, user_id: str, resolution: str) -> None:
        """Resolve checkpoint with user action."""
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = user_id
        self.resolution = resolution

    @property
    def is_pending(self) -> bool:
        return self.resolved_at is None


@dataclass
class LoopStatus:
    """
    Complete status of an integration loop instance.

    Used for console display and debugging.
    """

    loop_id: str
    incident_id: str
    tenant_id: str
    current_stage: LoopStage
    stages_completed: list[str]
    stages_failed: list[str]
    total_stages: int = 5
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    is_complete: bool = False
    is_blocked: bool = False
    failure_state: Optional[LoopFailureState] = None
    pending_checkpoints: list[str] = field(default_factory=list)
    # Stage details
    pattern_match_result: Optional[PatternMatchResult] = None
    recovery_suggestion: Optional[RecoverySuggestion] = None
    policy_rule: Optional[PolicyRule] = None
    routing_adjustment: Optional[RoutingAdjustment] = None

    @property
    def completion_pct(self) -> float:
        """Calculate loop completion percentage."""
        return len(self.stages_completed) / self.total_stages * 100

    def to_console_display(self) -> dict[str, Any]:
        """
        Format for console display:

        Incident → Pattern → Recovery → Policy → Routing
           ✅        ✅         ⏳         ○         ○
        """
        stage_order = [
            ("incident_created", "Incident", "🚨"),
            ("pattern_matched", "Pattern", "🔍"),
            ("recovery_suggested", "Recovery", "🔧"),
            ("policy_generated", "Policy", "📋"),
            ("routing_adjusted", "Routing", "🔀"),
        ]

        stages_display = []
        for stage_key, label, icon in stage_order:
            if stage_key in self.stages_completed:
                status = "✅"
            elif stage_key in self.stages_failed:
                status = "❌"
            elif stage_key == self.current_stage.value:
                status = "⏳"
            else:
                status = "○"

            stages_display.append(
                {
                    "key": stage_key,
                    "label": label,
                    "icon": icon,
                    "status": status,
                }
            )

        return {
            "loop_id": self.loop_id,
            "incident_id": self.incident_id,
            "completion_pct": self.completion_pct,
            "is_complete": self.is_complete,
            "is_blocked": self.is_blocked,
            "failure_state": self.failure_state.value if self.failure_state else None,
            "pending_checkpoints": self.pending_checkpoints,
            "stages": stages_display,
            "narrative": self._generate_narrative(),
        }

    def _generate_narrative(self) -> dict[str, str]:
        """
        Generate narrative artifacts for storytelling.

        - "before_after": Before vs After this incident
        - "policy_origin": Policy born from this failure
        - "agent_improvement": How agent behavior improved
        """
        narrative = {}

        # Before/After
        if self.pattern_match_result:
            narrative["before_after"] = (
                f"Before: Incident '{self.incident_id}' would go undetected. "
                f"After: Pattern '{self.pattern_match_result.pattern_id}' now tracks this failure type."
            )

        # Policy origin story
        if self.policy_rule:
            narrative["policy_origin"] = (
                f"Policy '{self.policy_rule.name}' was born from this failure. "
                f"It will {self.policy_rule.action} similar requests in the future."
            )

        # Agent improvement
        if self.routing_adjustment:
            narrative["agent_improvement"] = (
                f"Agent '{self.routing_adjustment.agent_id}' routing adjusted by "
                f"{self.routing_adjustment.magnitude:+.0%}. "
                f"The system now routes around this failure mode."
            )

        return narrative

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON/Redis storage."""
        return {
            "loop_id": self.loop_id,
            "incident_id": self.incident_id,
            "tenant_id": self.tenant_id,
            "current_stage": self.current_stage.value,
            "stages_completed": self.stages_completed,
            "stages_failed": self.stages_failed,
            "total_stages": self.total_stages,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_complete": self.is_complete,
            "is_blocked": self.is_blocked,
            "failure_state": self.failure_state.value if self.failure_state else None,
            "pending_checkpoints": self.pending_checkpoints,
            "completion_pct": self.completion_pct,
            "pattern_match_result": self.pattern_match_result.to_dict() if self.pattern_match_result else None,
            "recovery_suggestion": self.recovery_suggestion.to_dict() if self.recovery_suggestion else None,
            "policy_rule": self.policy_rule.to_dict() if self.policy_rule else None,
            "routing_adjustment": self.routing_adjustment.to_dict() if self.routing_adjustment else None,
        }
