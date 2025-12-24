"""
M25 Learning Proof System

This module provides the evidence that the integration loop actually LEARNS,
not just executes. It tracks:

1. PREVENTION PROOF - Did a policy actually prevent a second incident?
2. REGRET TRACKING - Did a policy cause harm? Auto-demote if so.
3. ADAPTIVE CONFIDENCE - Calibrate thresholds based on outcomes, not assumptions.
4. CHECKPOINT PRIORITY - Make human decisions tractable, not noisy.

"A system that can safely attempt to improve itself" is different from
"A system that demonstrably improves itself." This module proves the latter.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

# =============================================================================
# PREVENTION PROOF (Gate 1)
# =============================================================================


class PreventionOutcome(str, Enum):
    """Outcome of a prevention attempt."""

    PREVENTED = "prevented"  # Same pattern, blocked by policy
    MITIGATED = "mitigated"  # Same pattern, reduced severity
    FAILED_TO_PREVENT = "failed"  # Same pattern, still occurred
    NOT_APPLICABLE = "not_applicable"  # Different pattern, unrelated


@dataclass
class PreventionRecord:
    """
    Evidence that a policy prevented a recurrence.

    This is THE critical proof that M25 works. Without this,
    we have plumbing, not learning.
    """

    record_id: str
    policy_id: str
    pattern_id: str
    original_incident_id: str  # The incident that created the policy
    blocked_incident_id: str  # The incident that was prevented
    tenant_id: str
    outcome: PreventionOutcome
    created_at: datetime

    # Evidence
    signature_match_confidence: float  # How similar was the blocked incident?
    time_since_policy: timedelta  # How long policy was active before prevention
    calls_evaluated: int  # How many calls evaluated by policy before block

    @classmethod
    def create_prevention(
        cls,
        policy_id: str,
        pattern_id: str,
        original_incident_id: str,
        blocked_incident_id: str,
        tenant_id: str,
        signature_match: float,
        policy_age: timedelta,
        calls_evaluated: int = 0,
    ) -> "PreventionRecord":
        """Create a prevention record - this is evidence of learning."""
        return cls(
            record_id=f"prev_{uuid.uuid4().hex[:16]}",
            policy_id=policy_id,
            pattern_id=pattern_id,
            original_incident_id=original_incident_id,
            blocked_incident_id=blocked_incident_id,
            tenant_id=tenant_id,
            outcome=PreventionOutcome.PREVENTED,
            created_at=datetime.now(timezone.utc),
            signature_match_confidence=signature_match,
            time_since_policy=policy_age,
            calls_evaluated=calls_evaluated,
        )

    def to_console_timeline(self) -> dict:
        """Format for console timeline visualization."""
        return {
            "type": "prevention",
            "timestamp": self.created_at.isoformat(),
            "headline": "Policy prevented recurrence",
            "details": {
                "original_incident": self.original_incident_id,
                "would_be_incident": self.blocked_incident_id,
                "pattern": self.pattern_id,
                "policy": self.policy_id,
                "confidence": f"{self.signature_match_confidence:.0%}",
                "policy_age": str(self.time_since_policy),
            },
            "is_milestone": True,  # This is a graduation gate event
        }


@dataclass
class PreventionTracker:
    """
    Tracks prevention effectiveness across policies.

    Answers: "Are our policies actually preventing incidents?"
    """

    policies_with_prevention: set[str] = field(default_factory=set)
    prevention_by_pattern: dict[str, list[PreventionRecord]] = field(default_factory=lambda: defaultdict(list))
    total_preventions: int = 0
    total_failures: int = 0

    def record_prevention(self, record: PreventionRecord) -> None:
        """Record a successful prevention."""
        self.policies_with_prevention.add(record.policy_id)
        self.prevention_by_pattern[record.pattern_id].append(record)
        self.total_preventions += 1

    def record_failure(self, policy_id: str, pattern_id: str) -> None:
        """Record a prevention failure (policy didn't stop recurrence)."""
        self.total_failures += 1

    @property
    def prevention_rate(self) -> float:
        """Overall prevention success rate."""
        total = self.total_preventions + self.total_failures
        if total == 0:
            return 0.0
        return self.total_preventions / total

    @property
    def has_proven_prevention(self) -> bool:
        """Gate 1 check: Has at least one policy prevented one incident?"""
        return self.total_preventions >= 1

    def get_top_preventing_patterns(self, n: int = 5) -> list[tuple[str, int]]:
        """Patterns that have been most effectively prevented."""
        counts = [(p, len(recs)) for p, recs in self.prevention_by_pattern.items()]
        return sorted(counts, key=lambda x: -x[1])[:n]


# =============================================================================
# REGRET-DRIVEN ROLLBACK (Gate 2)
# =============================================================================


class RegretType(str, Enum):
    """Types of policy regret."""

    FALSE_POSITIVE = "false_positive"  # Blocked legitimate request
    PERFORMANCE_DEGRADATION = "perf"  # Caused slowdown
    ESCALATION_NOISE = "escalation"  # Created unnecessary alerts
    USER_OVERRIDE = "user_override"  # User had to manually override
    CASCADING_FAILURE = "cascade"  # Triggered other failures


@dataclass
class RegretEvent:
    """
    A single regret event - when a policy caused harm.

    "Regret" is the opposite of prevention. It's when our attempt
    to improve made things worse.
    """

    regret_id: str
    policy_id: str
    tenant_id: str
    regret_type: RegretType
    description: str
    severity: int  # 1-10
    created_at: datetime

    # What went wrong
    affected_calls: int
    affected_users: int
    impact_duration: timedelta

    # Resolution
    was_auto_rolled_back: bool = False
    manual_override_by: Optional[str] = None


@dataclass
class PolicyRegretTracker:
    """
    Tracks regret for individual policies.

    Implements automatic demotion when regret threshold exceeded.
    """

    policy_id: str
    regret_events: list[RegretEvent] = field(default_factory=list)
    regret_score: float = 0.0  # Weighted score
    demoted_at: Optional[datetime] = None
    demoted_reason: Optional[str] = None

    # Thresholds
    auto_demote_score: float = 5.0  # Demote if score exceeds this
    auto_demote_count: int = 3  # Demote if N regret events
    decay_rate: float = 0.1  # Daily decay of regret score

    def add_regret(self, event: RegretEvent) -> bool:
        """
        Add regret event. Returns True if auto-demotion triggered.
        """
        self.regret_events.append(event)

        # Weight by severity
        self.regret_score += event.severity * 0.5

        # Check thresholds
        if self.regret_score >= self.auto_demote_score:
            self._trigger_demotion(f"Regret score {self.regret_score:.1f} exceeded threshold")
            return True

        if len(self.regret_events) >= self.auto_demote_count:
            self._trigger_demotion(f"Regret count {len(self.regret_events)} exceeded threshold")
            return True

        return False

    def _trigger_demotion(self, reason: str) -> None:
        """Auto-demote policy due to excessive regret."""
        self.demoted_at = datetime.now(timezone.utc)
        self.demoted_reason = reason

    def decay_regret(self) -> None:
        """Apply daily decay to regret score."""
        self.regret_score = max(0.0, self.regret_score * (1 - self.decay_rate))

    @property
    def is_demoted(self) -> bool:
        return self.demoted_at is not None

    def to_rollback_timeline(self) -> dict | None:
        """Format for console timeline if demoted."""
        if not self.is_demoted:
            return None
        return {
            "type": "rollback",
            "timestamp": self.demoted_at.isoformat(),
            "headline": "Policy auto-demoted due to regret",
            "details": {
                "policy": self.policy_id,
                "reason": self.demoted_reason,
                "regret_score": f"{self.regret_score:.1f}",
                "regret_events": len(self.regret_events),
            },
            "is_milestone": True,  # Gate 2 event
        }


@dataclass
class GlobalRegretTracker:
    """
    System-wide regret tracking.

    Answers: "Is the system causing harm?"
    """

    policy_trackers: dict[str, PolicyRegretTracker] = field(default_factory=dict)
    total_regret_events: int = 0
    total_auto_demotions: int = 0

    def get_or_create_tracker(self, policy_id: str) -> PolicyRegretTracker:
        if policy_id not in self.policy_trackers:
            self.policy_trackers[policy_id] = PolicyRegretTracker(policy_id=policy_id)
        return self.policy_trackers[policy_id]

    def record_regret(self, policy_id: str, event: RegretEvent) -> bool:
        """Record regret. Returns True if demotion triggered."""
        self.total_regret_events += 1
        tracker = self.get_or_create_tracker(policy_id)
        demoted = tracker.add_regret(event)
        if demoted:
            self.total_auto_demotions += 1
        return demoted

    @property
    def has_proven_rollback(self) -> bool:
        """Gate 2 check: Has at least one policy been auto-demoted?"""
        return self.total_auto_demotions >= 1

    @property
    def system_regret_rate(self) -> float:
        """Overall regret rate across all policies."""
        if not self.policy_trackers:
            return 0.0
        total_score = sum(t.regret_score for t in self.policy_trackers.values())
        return total_score / len(self.policy_trackers)


# =============================================================================
# ADAPTIVE CONFIDENCE (Beyond static thresholds)
# =============================================================================


@dataclass
class PatternCalibration:
    """
    Per-pattern confidence calibration based on actual outcomes.

    Replaces static 0.85/0.60 thresholds with empirical ones.
    """

    pattern_id: str

    # Outcome tracking
    predictions: list[tuple[float, bool]] = field(default_factory=list)  # (confidence, was_correct)

    # Calibrated thresholds
    empirical_strong_threshold: float = 0.85  # Starts at default
    empirical_weak_threshold: float = 0.60

    # Statistics
    total_matches: int = 0
    correct_matches: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    def record_outcome(self, predicted_confidence: float, was_correct: bool) -> None:
        """Record a prediction outcome for calibration."""
        self.predictions.append((predicted_confidence, was_correct))
        self.total_matches += 1

        if was_correct:
            self.correct_matches += 1
        else:
            # Distinguish FP vs FN based on confidence
            if predicted_confidence >= 0.5:
                self.false_positives += 1
            else:
                self.false_negatives += 1

        # Recalibrate after every 10 outcomes
        if len(self.predictions) % 10 == 0:
            self._recalibrate()

    def _recalibrate(self) -> None:
        """Recalibrate thresholds based on outcomes."""
        if len(self.predictions) < 10:
            return

        # Find the confidence level where we achieve 90% accuracy
        sorted_preds = sorted(self.predictions, key=lambda x: -x[0])

        for threshold in [0.95, 0.90, 0.85, 0.80, 0.75, 0.70]:
            above_threshold = [p for p in sorted_preds if p[0] >= threshold]
            if above_threshold:
                accuracy = sum(1 for _, correct in above_threshold if correct) / len(above_threshold)
                if accuracy >= 0.90:
                    self.empirical_strong_threshold = threshold
                    break

        # Find weak threshold (70% accuracy)
        for threshold in [0.70, 0.65, 0.60, 0.55, 0.50]:
            above_threshold = [p for p in sorted_preds if p[0] >= threshold]
            if above_threshold:
                accuracy = sum(1 for _, correct in above_threshold if correct) / len(above_threshold)
                if accuracy >= 0.70:
                    self.empirical_weak_threshold = threshold
                    break

    @property
    def accuracy(self) -> float:
        """Overall accuracy for this pattern."""
        if self.total_matches == 0:
            return 0.0
        return self.correct_matches / self.total_matches

    @property
    def is_calibrated(self) -> bool:
        """Has enough data for reliable calibration?"""
        return len(self.predictions) >= 20

    def get_calibrated_band(self, confidence: float) -> str:
        """Get band using calibrated thresholds."""
        if confidence >= self.empirical_strong_threshold:
            return "strong_match"
        elif confidence >= self.empirical_weak_threshold:
            return "weak_match"
        else:
            return "novel"


@dataclass
class AdaptiveConfidenceSystem:
    """
    System-wide adaptive confidence management.

    Moves from "cargo cult math" to empirical calibration.
    """

    pattern_calibrations: dict[str, PatternCalibration] = field(default_factory=dict)

    # Global statistics
    total_predictions: int = 0
    global_accuracy: float = 0.0

    def get_or_create_calibration(self, pattern_id: str) -> PatternCalibration:
        if pattern_id not in self.pattern_calibrations:
            self.pattern_calibrations[pattern_id] = PatternCalibration(pattern_id=pattern_id)
        return self.pattern_calibrations[pattern_id]

    def record_outcome(self, pattern_id: str, confidence: float, was_correct: bool) -> None:
        """Record prediction outcome for calibration."""
        self.total_predictions += 1
        calibration = self.get_or_create_calibration(pattern_id)
        calibration.record_outcome(confidence, was_correct)

        # Update global accuracy (rolling)
        self.global_accuracy = (
            self.global_accuracy * (self.total_predictions - 1) + (1 if was_correct else 0)
        ) / self.total_predictions

    def get_threshold_for_pattern(self, pattern_id: str) -> tuple[float, float]:
        """Get calibrated strong/weak thresholds for a pattern."""
        if pattern_id in self.pattern_calibrations:
            cal = self.pattern_calibrations[pattern_id]
            if cal.is_calibrated:
                return (cal.empirical_strong_threshold, cal.empirical_weak_threshold)
        # Default thresholds if not calibrated
        return (0.85, 0.60)

    def get_confidence_report(self) -> dict:
        """Report on confidence calibration health."""
        calibrated = [c for c in self.pattern_calibrations.values() if c.is_calibrated]
        return {
            "total_patterns": len(self.pattern_calibrations),
            "calibrated_patterns": len(calibrated),
            "global_accuracy": f"{self.global_accuracy:.1%}",
            "threshold_shifts": [
                {
                    "pattern": c.pattern_id,
                    "default_strong": 0.85,
                    "calibrated_strong": c.empirical_strong_threshold,
                    "shift": c.empirical_strong_threshold - 0.85,
                }
                for c in calibrated
                if abs(c.empirical_strong_threshold - 0.85) > 0.05
            ],
        }


# =============================================================================
# CHECKPOINT PRIORITIZATION
# =============================================================================


class CheckpointPriority(str, Enum):
    """Priority levels for human checkpoints."""

    CRITICAL = "critical"  # Must resolve before system proceeds
    HIGH = "high"  # Should resolve within 1 hour
    NORMAL = "normal"  # Should resolve within 24 hours
    LOW = "low"  # Advisory only, can auto-dismiss
    ADVISORY = "advisory"  # Non-blocking, informational


@dataclass
class CheckpointConfig:
    """
    Per-tenant checkpoint configuration.

    Prevents checkpoint fatigue by allowing customization.
    """

    tenant_id: str

    # Which checkpoints are enabled
    enabled_types: set[str] = field(
        default_factory=lambda: {
            "approve_policy",
            "approve_recovery",
            "simulate_routing",
            "revert_loop",
            "override_guardrail",
        }
    )

    # Priority overrides
    priority_overrides: dict[str, CheckpointPriority] = field(default_factory=dict)

    # Thresholds
    auto_approve_confidence: float = 0.95  # Auto-approve above this
    auto_dismiss_after_hours: int = 48  # Auto-dismiss LOW after 48h
    max_pending_checkpoints: int = 10  # Alert if more than 10 pending

    # Behavior
    blocking_checkpoints: set[str] = field(
        default_factory=lambda: {
            "approve_policy",
            "override_guardrail",  # These block the loop
        }
    )

    def is_blocking(self, checkpoint_type: str) -> bool:
        """Check if checkpoint type blocks loop progress."""
        return checkpoint_type in self.blocking_checkpoints

    def get_priority(self, checkpoint_type: str, confidence: float) -> CheckpointPriority:
        """Get priority for a checkpoint, considering confidence."""
        # Check overrides first
        if checkpoint_type in self.priority_overrides:
            return self.priority_overrides[checkpoint_type]

        # Auto-approve high confidence
        if confidence >= self.auto_approve_confidence:
            return CheckpointPriority.ADVISORY

        # Default priorities by type
        defaults = {
            "approve_policy": CheckpointPriority.HIGH,
            "approve_recovery": CheckpointPriority.NORMAL,
            "simulate_routing": CheckpointPriority.LOW,
            "revert_loop": CheckpointPriority.CRITICAL,
            "override_guardrail": CheckpointPriority.CRITICAL,
        }
        return defaults.get(checkpoint_type, CheckpointPriority.NORMAL)

    def should_auto_dismiss(self, checkpoint_type: str, age_hours: float) -> bool:
        """Check if checkpoint should be auto-dismissed."""
        priority = self.get_priority(checkpoint_type, 0.0)
        if priority == CheckpointPriority.LOW and age_hours > self.auto_dismiss_after_hours:
            return True
        if priority == CheckpointPriority.ADVISORY:
            return True
        return False


@dataclass
class PrioritizedCheckpoint:
    """
    Enhanced checkpoint with priority and configurability.
    """

    checkpoint_id: str
    checkpoint_type: str
    incident_id: str
    tenant_id: str
    description: str
    confidence: float
    priority: CheckpointPriority
    is_blocking: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    auto_dismissed: bool = False

    @classmethod
    def create(
        cls,
        checkpoint_type: str,
        incident_id: str,
        tenant_id: str,
        description: str,
        confidence: float,
        config: CheckpointConfig,
    ) -> "PrioritizedCheckpoint":
        """Create checkpoint with priority from config."""
        priority = config.get_priority(checkpoint_type, confidence)
        is_blocking = config.is_blocking(checkpoint_type)

        # Set expiry for low priority
        expires_at = None
        if priority in (CheckpointPriority.LOW, CheckpointPriority.ADVISORY):
            expires_at = datetime.now(timezone.utc) + timedelta(hours=config.auto_dismiss_after_hours)

        return cls(
            checkpoint_id=f"chk_{uuid.uuid4().hex[:16]}",
            checkpoint_type=checkpoint_type,
            incident_id=incident_id,
            tenant_id=tenant_id,
            description=description,
            confidence=confidence,
            priority=priority,
            is_blocking=is_blocking,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

    def check_auto_dismiss(self) -> bool:
        """Check and apply auto-dismiss if expired."""
        if self.resolved_at or self.auto_dismissed:
            return False

        if self.expires_at and datetime.now(timezone.utc) >= self.expires_at:
            self.auto_dismissed = True
            self.resolved_at = datetime.now(timezone.utc)
            return True
        return False


# =============================================================================
# GRADUATION STATUS
# =============================================================================


@dataclass
class M25GraduationStatus:
    """
    The three gates that graduate M25 from "loop-enabled" to "loop-proven".

    Until all three gates pass, M25 is alpha.
    """

    # Gate 1: Prevention Proof
    prevention_tracker: PreventionTracker = field(default_factory=PreventionTracker)

    # Gate 2: Regret Rollback
    regret_tracker: GlobalRegretTracker = field(default_factory=GlobalRegretTracker)

    # Gate 3: Console Proof (timeline with prevention visible)
    console_proof_incidents: list[str] = field(default_factory=list)

    @property
    def gate1_passed(self) -> bool:
        """Gate 1: At least one prevention recorded."""
        return self.prevention_tracker.has_proven_prevention

    @property
    def gate2_passed(self) -> bool:
        """Gate 2: At least one regret-driven rollback."""
        return self.regret_tracker.has_proven_rollback

    @property
    def gate3_passed(self) -> bool:
        """Gate 3: At least one incident shows timeline with prevention."""
        return len(self.console_proof_incidents) >= 1

    @property
    def is_graduated(self) -> bool:
        """All gates passed - M25 is proven."""
        return self.gate1_passed and self.gate2_passed and self.gate3_passed

    @property
    def status_label(self) -> str:
        """Human-readable status."""
        if self.is_graduated:
            return "M25-COMPLETE"

        gates_passed = sum([self.gate1_passed, self.gate2_passed, self.gate3_passed])
        return f"M25-ALPHA ({gates_passed}/3 gates)"

    def to_dashboard(self) -> dict:
        """Dashboard display of graduation status."""
        return {
            "status": self.status_label,
            "is_graduated": self.is_graduated,
            "gates": {
                "gate1_prevention": {
                    "name": "Prevention Proof",
                    "description": "Policy prevented at least one incident recurrence",
                    "passed": self.gate1_passed,
                    "evidence": {
                        "total_preventions": self.prevention_tracker.total_preventions,
                        "prevention_rate": f"{self.prevention_tracker.prevention_rate:.0%}",
                    },
                },
                "gate2_rollback": {
                    "name": "Regret Rollback",
                    "description": "At least one policy auto-demoted due to causing harm",
                    "passed": self.gate2_passed,
                    "evidence": {
                        "total_demotions": self.regret_tracker.total_auto_demotions,
                        "system_regret_rate": f"{self.regret_tracker.system_regret_rate:.1f}",
                    },
                },
                "gate3_console": {
                    "name": "Console Timeline",
                    "description": "Timeline visibly shows incident A → policy born → incident B prevented",
                    "passed": self.gate3_passed,
                    "evidence": {
                        "proven_incidents": len(self.console_proof_incidents),
                    },
                },
            },
            "next_action": self._get_next_action(),
        }

    def _get_next_action(self) -> str:
        """What to do next to graduate."""
        if self.is_graduated:
            return "M25 is complete. Proceed to M26."

        if not self.gate1_passed:
            return "Wait for or simulate a policy preventing a recurrence"
        if not self.gate2_passed:
            return "Wait for or simulate a policy causing regret (then observe auto-demotion)"
        if not self.gate3_passed:
            return "View a prevention in the console timeline"

        return "Unknown state"


# =============================================================================
# CONSOLE TIMELINE (Gate 3)
# =============================================================================


@dataclass
class PreventionTimeline:
    """
    Console-ready timeline showing the learning loop in action.

    Gate 3 requirement: User must SEE the system learn.
    """

    incident_id: str
    tenant_id: str
    events: list[dict] = field(default_factory=list)

    def add_incident_created(self, timestamp: datetime, details: dict) -> None:
        """Original incident that created the pattern/policy."""
        self.events.append(
            {
                "type": "incident_created",
                "timestamp": timestamp.isoformat(),
                "icon": "🚨",
                "headline": "Incident A detected",
                "description": details.get("title", "Unknown incident"),
                "details": details,
            }
        )

    def add_policy_born(self, timestamp: datetime, policy_id: str, policy_name: str) -> None:
        """Policy was created from this incident."""
        self.events.append(
            {
                "type": "policy_born",
                "timestamp": timestamp.isoformat(),
                "icon": "📋",
                "headline": "Policy born from failure",
                "description": f"Policy '{policy_name}' created to prevent recurrence",
                "details": {"policy_id": policy_id},
            }
        )

    def add_prevention(self, timestamp: datetime, record: PreventionRecord) -> None:
        """The prevention event - this is the proof."""
        self.events.append(
            {
                "type": "prevention",
                "timestamp": timestamp.isoformat(),
                "icon": "🛡️",
                "headline": "Incident B PREVENTED",
                "description": "Same pattern detected, blocked by policy",
                "details": {
                    "blocked_incident": record.blocked_incident_id,
                    "policy": record.policy_id,
                    "confidence": f"{record.signature_match_confidence:.0%}",
                },
                "is_milestone": True,
            }
        )

    def add_regret(self, timestamp: datetime, event: RegretEvent) -> None:
        """Regret event if policy caused harm."""
        self.events.append(
            {
                "type": "regret",
                "timestamp": timestamp.isoformat(),
                "icon": "⚠️",
                "headline": "Policy caused harm (regret)",
                "description": event.description,
                "details": {
                    "regret_type": event.regret_type.value,
                    "severity": event.severity,
                },
            }
        )

    def add_rollback(self, timestamp: datetime, tracker: PolicyRegretTracker) -> None:
        """Auto-rollback event."""
        self.events.append(
            {
                "type": "rollback",
                "timestamp": timestamp.isoformat(),
                "icon": "↩️",
                "headline": "Policy auto-demoted",
                "description": tracker.demoted_reason or "Excessive regret",
                "details": {
                    "policy": tracker.policy_id,
                    "regret_score": f"{tracker.regret_score:.1f}",
                },
                "is_milestone": True,
            }
        )

    def to_console(self) -> dict:
        """Format for console display."""
        # Sort by timestamp
        sorted_events = sorted(self.events, key=lambda e: e["timestamp"])

        # Identify milestones
        has_prevention = any(e["type"] == "prevention" for e in sorted_events)
        has_rollback = any(e["type"] == "rollback" for e in sorted_events)

        return {
            "incident_id": self.incident_id,
            "tenant_id": self.tenant_id,
            "timeline": sorted_events,
            "summary": {
                "event_count": len(sorted_events),
                "has_prevention": has_prevention,
                "has_rollback": has_rollback,
                "is_learning_proof": has_prevention,  # Gate 3 indicator
            },
            "narrative": self._generate_narrative(has_prevention, has_rollback),
        }

    def _generate_narrative(self, has_prevention: bool, has_rollback: bool) -> str:
        """Generate human-readable narrative."""
        if has_prevention and has_rollback:
            return (
                "This incident shows the full learning loop: "
                "failure → policy → prevention → feedback. "
                "The system learned, protected, and self-corrected."
            )
        elif has_prevention:
            return "This incident proves learning: a policy born from failure successfully prevented a recurrence."
        elif has_rollback:
            return "This incident shows self-correction: a policy that caused harm was automatically demoted."
        else:
            return "This incident is part of the feedback loop."
