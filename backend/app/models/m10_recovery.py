# M10 Recovery Suggestion Engine - Async SQLAlchemy Models
"""
SQLAlchemy models for M10 Recovery Suggestion Engine.

Tables:
- SuggestionInput: Structured inputs for rule evaluation
- SuggestionAction: Action catalog with templates
- SuggestionProvenance: Lineage tracking for audit/debugging

Uses asyncpg for async database access.
"""

from typing import Any, Dict

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# =============================================================================
# SuggestionInput Model
# =============================================================================


class SuggestionInput(Base):
    """
    Structured inputs that contributed to a recovery suggestion.

    Tracks all inputs (error codes, messages, context) that were used
    in rule evaluation for provenance and debugging.
    """

    __tablename__ = "suggestion_input"
    __table_args__ = (
        Index("idx_si_suggestion_id", "suggestion_id"),
        Index("idx_si_input_type", "input_type"),
        CheckConstraint(
            "input_type IN ('error_code', 'error_message', 'stack_trace', "
            "'skill_context', 'tenant_context', 'historical_pattern')",
            name="ck_si_input_type",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_si_confidence"),
        CheckConstraint("weight >= 0", name="ck_si_weight"),
        {"schema": "m10_recovery"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_id = Column(Integer, ForeignKey("recovery_candidates.id", ondelete="CASCADE"), nullable=False)

    # Input classification
    input_type = Column(Text, nullable=False)

    # Input content
    raw_value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=True)
    parsed_data = Column(JSONB, default=dict)

    # Quality scoring
    confidence = Column(Float, default=1.0)
    weight = Column(Float, default=1.0)

    # Metadata
    source = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "suggestion_id": self.suggestion_id,
            "input_type": self.input_type,
            "raw_value": self.raw_value,
            "normalized_value": self.normalized_value,
            "parsed_data": self.parsed_data or {},
            "confidence": self.confidence,
            "weight": self.weight,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# SuggestionAction Model
# =============================================================================


class SuggestionAction(Base):
    """
    Catalog of available recovery actions with templates.

    Each action defines:
    - What type of recovery it performs
    - Template for execution
    - Which errors/skills it applies to
    - Historical success rate
    """

    __tablename__ = "suggestion_action"
    __table_args__ = (
        UniqueConstraint("action_code", name="uq_sa_action_code"),
        Index("idx_sa_action_type", "action_type"),
        Index("idx_sa_active", "is_active"),
        Index("idx_sa_priority", "priority"),
        CheckConstraint(
            "action_type IN ('retry', 'fallback', 'escalate', 'notify', "
            "'reconfigure', 'rollback', 'manual', 'skip')",
            name="ck_sa_action_type",
        ),
        CheckConstraint("success_rate >= 0 AND success_rate <= 1", name="ck_sa_success_rate"),
        CheckConstraint("priority >= 0 AND priority <= 100", name="ck_sa_priority"),
        {"schema": "m10_recovery"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Action identification
    action_code = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Action template
    action_type = Column(Text, nullable=False)
    template = Column(JSONB, nullable=False, default=dict)

    # Applicability rules
    applies_to_error_codes = Column(ARRAY(Text), default=list)
    applies_to_skills = Column(ARRAY(Text), default=list)
    preconditions = Column(JSONB, default=dict)

    # Effectiveness tracking
    success_rate = Column(Float, default=0.0)
    total_applications = Column(Integer, default=0)
    successful_applications = Column(Integer, default=0)

    # Configuration
    is_automated = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=True)
    priority = Column(Integer, default=50)

    # Lifecycle
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(Text, nullable=True)
    version = Column(Integer, default=1)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "action_code": self.action_code,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "template": self.template or {},
            "applies_to_error_codes": self.applies_to_error_codes or [],
            "applies_to_skills": self.applies_to_skills or [],
            "preconditions": self.preconditions or {},
            "success_rate": self.success_rate,
            "total_applications": self.total_applications,
            "successful_applications": self.successful_applications,
            "is_automated": self.is_automated,
            "requires_approval": self.requires_approval,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "version": self.version,
        }

    def matches_error(self, error_code: str) -> bool:
        """Check if action applies to given error code."""
        if not self.applies_to_error_codes:
            return True  # No restrictions = applies to all

        return any(error_code.upper().startswith(code.upper()) for code in self.applies_to_error_codes)

    def matches_skill(self, skill_id: str) -> bool:
        """Check if action applies to given skill."""
        if not self.applies_to_skills:
            return True  # No restrictions = applies to all

        return skill_id in self.applies_to_skills


# =============================================================================
# SuggestionProvenance Model
# =============================================================================


class SuggestionProvenance(Base):
    """
    Complete lineage of how a recovery suggestion was generated and processed.

    Records every significant event in the suggestion lifecycle:
    - Creation and input processing
    - Rule evaluation
    - Action selection
    - Approval workflow
    - Execution results
    """

    __tablename__ = "suggestion_provenance"
    __table_args__ = (
        Index("idx_sp_suggestion_id", "suggestion_id"),
        Index("idx_sp_event_type", "event_type"),
        Index("idx_sp_created_at", "created_at"),
        Index("idx_sp_actor", "actor"),
        CheckConstraint(
            "event_type IN ('created', 'input_added', 'rule_evaluated', 'action_selected', "
            "'confidence_updated', 'approved', 'rejected', 'executed', "
            "'success', 'failure', 'rolled_back', 'manual_override')",
            name="ck_sp_event_type",
        ),
        CheckConstraint("actor_type IN ('system', 'human', 'agent')", name="ck_sp_actor_type"),
        {"schema": "m10_recovery"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_id = Column(Integer, ForeignKey("recovery_candidates.id", ondelete="CASCADE"), nullable=False)

    # Provenance event
    event_type = Column(Text, nullable=False)
    details = Column(JSONB, nullable=False, default=dict)

    # Rule/Action reference
    rule_id = Column(Text, nullable=True)
    action_id = Column(Integer, ForeignKey("m10_recovery.suggestion_action.id"), nullable=True)

    # Scores at this point
    confidence_before = Column(Float, nullable=True)
    confidence_after = Column(Float, nullable=True)

    # Actor
    actor = Column(Text, nullable=False, default="system")
    actor_type = Column(Text, nullable=False, default="system")

    # Timing
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    duration_ms = Column(Integer, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "suggestion_id": self.suggestion_id,
            "event_type": self.event_type,
            "details": self.details or {},
            "rule_id": self.rule_id,
            "action_id": self.action_id,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "actor": self.actor,
            "actor_type": self.actor_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_ms": self.duration_ms,
        }


# =============================================================================
# Type Definitions
# =============================================================================

INPUT_TYPES = [
    "error_code",
    "error_message",
    "stack_trace",
    "skill_context",
    "tenant_context",
    "historical_pattern",
]

ACTION_TYPES = [
    "retry",
    "fallback",
    "escalate",
    "notify",
    "reconfigure",
    "rollback",
    "manual",
    "skip",
]

EVENT_TYPES = [
    "created",
    "input_added",
    "rule_evaluated",
    "action_selected",
    "confidence_updated",
    "approved",
    "rejected",
    "executed",
    "success",
    "failure",
    "rolled_back",
    "manual_override",
]

EXECUTION_STATUSES = [
    "pending",
    "executing",
    "succeeded",
    "failed",
    "rolled_back",
    "skipped",
]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "Base",
    "SuggestionInput",
    "SuggestionAction",
    "SuggestionProvenance",
    "INPUT_TYPES",
    "ACTION_TYPES",
    "EVENT_TYPES",
    "EXECUTION_STATUSES",
]
