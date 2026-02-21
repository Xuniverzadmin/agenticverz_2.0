# capability_id: CAP-012
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Learning-based suggestion generation
# Callers: API routes, workers
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: C5 Learning

"""
C5 Learning Suggestions Model.

All suggestions are:
- Advisory only (CI-C5-1)
- Versioned and immutable (CI-C5-4)
- Require human approval (CI-C5-2)

Reference: C5_S1_LEARNING_SCENARIO.md, C5_S1_ACCEPTANCE_CRITERIA.md
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional


class SuggestionConfidence(str, Enum):
    """Confidence level for suggestions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SuggestionStatus(str, Enum):
    """
    Lifecycle status for suggestions.

    State transitions:
        pending_review -> acknowledged -> dismissed | applied_externally
    """

    PENDING_REVIEW = "pending_review"
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"
    APPLIED_EXTERNALLY = "applied_externally"


@dataclass
class ObservationWindow:
    """Time window for observation."""

    start: datetime
    end: datetime


@dataclass
class RollbackObservation:
    """
    Observation data for C5-S1 (rollback frequency).

    This is the structured data that C5-S1 produces from
    analyzing coordination_audit_records.
    """

    envelope_class: str
    target_parameter: str
    rollback_count: int
    total_envelopes: int
    rollback_rate: float  # rollback_count / total_envelopes
    avg_time_to_rollback_seconds: float
    trend: str  # "increasing", "stable", "decreasing"


@dataclass
class LearningSuggestion:
    """
    C5 Learning Suggestion - Advisory Only.

    IMMUTABILITY RULES (CI-C5-4, AC-S1-M1):
    - Core fields (observation, suggestion_text, suggestion_confidence)
      CANNOT be updated after creation.
    - Only status-related fields can change.
    - New suggestions must be created for changes.

    ADVISORY RULES (CI-C5-1, AC-S1-I1):
    - suggestion_type is always "advisory" (not configurable)
    - applied is always False by default
    - requires explicit human action to change status

    APPROVAL RULES (CI-C5-2, AC-S1-I2):
    - No auto-approval allowed
    - Status starts as "pending_review"
    - Human action required for any status change
    """

    # Identity (immutable after creation)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1  # Monotonically increasing

    # Scenario identification
    scenario: str = "C5-S1"  # Which learning scenario produced this

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Observation window
    observation_window_start: Optional[datetime] = None
    observation_window_end: Optional[datetime] = None

    # Observation data (IMMUTABLE after creation)
    observation: Optional[Dict[str, Any]] = None

    # Suggestion details (IMMUTABLE after creation)
    # suggestion_type is ALWAYS "advisory" - this is enforced by CI-C5-1
    suggestion_type: Literal["advisory"] = "advisory"
    suggestion_confidence: SuggestionConfidence = SuggestionConfidence.LOW
    suggestion_text: str = ""

    # Status (MUTABLE via human action only)
    status: SuggestionStatus = SuggestionStatus.PENDING_REVIEW

    # Human action tracking (MUTABLE via human action only)
    human_action: Optional[str] = None
    human_action_at: Optional[datetime] = None
    human_actor_id: Optional[str] = None

    # Applied flag (MUTABLE via human action only)
    # This is NEVER set automatically - only by human "mark applied" action
    applied: bool = False

    def acknowledge(self, actor_id: str) -> "LearningSuggestion":
        """
        Human acknowledges the suggestion.

        AC-S1-H1: Status changes to acknowledged, no system change.
        """
        self.status = SuggestionStatus.ACKNOWLEDGED
        self.human_action = "acknowledge"
        self.human_action_at = datetime.now(timezone.utc)
        self.human_actor_id = actor_id
        return self

    def dismiss(self, actor_id: str) -> "LearningSuggestion":
        """
        Human dismisses the suggestion.

        AC-S1-H2: Status changes to dismissed, no system change.
        """
        self.status = SuggestionStatus.DISMISSED
        self.human_action = "dismiss"
        self.human_action_at = datetime.now(timezone.utc)
        self.human_actor_id = actor_id
        return self

    def mark_applied_externally(self, actor_id: str) -> "LearningSuggestion":
        """
        Human marks that they applied changes externally.

        AC-S1-H3: Status changes, applied=True, no system change.
        This does NOT modify any envelope or bound.
        It only records that the human took external action.
        """
        self.status = SuggestionStatus.APPLIED_EXTERNALLY
        self.human_action = "mark_applied"
        self.human_action_at = datetime.now(timezone.utc)
        self.human_actor_id = actor_id
        self.applied = True
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "version": self.version,
            "scenario": self.scenario,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "observation_window_start": (
                self.observation_window_start.isoformat() if self.observation_window_start else None
            ),
            "observation_window_end": (
                self.observation_window_end.isoformat() if self.observation_window_end else None
            ),
            "observation": self.observation,
            "suggestion_type": self.suggestion_type,
            "suggestion_confidence": self.suggestion_confidence.value,
            "suggestion_text": self.suggestion_text,
            "status": self.status.value,
            "human_action": self.human_action,
            "human_action_at": (self.human_action_at.isoformat() if self.human_action_at else None),
            "human_actor_id": self.human_actor_id,
            "applied": self.applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningSuggestion":
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            version=data.get("version", 1),
            scenario=data.get("scenario", "C5-S1"),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc)
            ),
            observation_window_start=(
                datetime.fromisoformat(data["observation_window_start"])
                if data.get("observation_window_start")
                else None
            ),
            observation_window_end=(
                datetime.fromisoformat(data["observation_window_end"]) if data.get("observation_window_end") else None
            ),
            observation=data.get("observation"),
            suggestion_type="advisory",  # Always advisory
            suggestion_confidence=SuggestionConfidence(data.get("suggestion_confidence", "low")),
            suggestion_text=data.get("suggestion_text", ""),
            status=SuggestionStatus(data.get("status", "pending_review")),
            human_action=data.get("human_action"),
            human_action_at=(datetime.fromisoformat(data["human_action_at"]) if data.get("human_action_at") else None),
            human_actor_id=data.get("human_actor_id"),
            applied=data.get("applied", False),
        )


# Forbidden language patterns for suggestion text (CI-C5-1, AC-S1-B4)
FORBIDDEN_LANGUAGE_PATTERNS: List[str] = [
    "should",
    "must",
    "will improve",
    "recommends",
    "apply this",
    "better than",
]


def validate_suggestion_text(text: str) -> bool:
    """
    Validate that suggestion text uses observational language only.

    AC-S1-B4: Text must not contain forbidden language patterns.
    """
    text_lower = text.lower()
    for pattern in FORBIDDEN_LANGUAGE_PATTERNS:
        if pattern in text_lower:
            return False
    return True
