# Layer: L6 — Platform Substrate (Data Models)
# Product: system-wide
# Temporal:
#   Trigger: n/a (data model)
#   Execution: n/a
# Role: Lessons learned data model for policy domain intelligence
# Callers: LessonsLearnedEngine (L4), API facades (L2)
# Allowed Imports: sqlalchemy, sqlmodel
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11

"""
Lessons Learned Model (L6)

Data model for storing learning signals from:
- Failures (HIGH, MEDIUM, LOW, CRITICAL)
- Near-threshold events
- Critical success events

These lessons can be converted to draft policy proposals.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, SQLModel


class LessonType(str, Enum):
    """Type of lesson learned."""
    FAILURE = "failure"
    NEAR_THRESHOLD = "near_threshold"
    CRITICAL_SUCCESS = "critical_success"


class LessonStatus(str, Enum):
    """Status of a lesson."""
    PENDING = "pending"
    CONVERTED_TO_DRAFT = "converted_to_draft"
    DEFERRED = "deferred"
    DISMISSED = "dismissed"


class LessonSeverity(str, Enum):
    """Severity of the originating event."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"  # For success events


class LessonLearned(SQLModel, table=True):
    """
    Lesson learned from system events.

    This is the memory substrate for the LessonsLearnedEngine.
    Lessons represent learning opportunities that may become policies.
    """

    __tablename__ = "lessons_learned"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True),
    )
    tenant_id: str = Field(max_length=255, index=True)

    # Lesson classification
    lesson_type: str = Field(max_length=50)  # failure, near_threshold, critical_success
    severity: Optional[str] = Field(default=None, max_length=20)  # CRITICAL, HIGH, MEDIUM, LOW, NONE

    # Source event linkage
    source_event_id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    source_event_type: str = Field(max_length=50)  # run, incident
    source_run_id: Optional[UUID] = Field(default=None, sa_column=Column(PG_UUID(as_uuid=True), nullable=True))

    # Lesson content
    title: str = Field(max_length=500)
    description: str = Field(sa_column=Column(Text, nullable=False))
    proposed_action: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    detected_pattern: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Status tracking
    status: str = Field(default="pending", max_length=20)
    draft_proposal_id: Optional[UUID] = Field(default=None, sa_column=Column(PG_UUID(as_uuid=True), nullable=True))

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    converted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    deferred_until: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    dismissed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    dismissed_by: Optional[str] = Field(default=None, max_length=255)
    dismissed_reason: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # SDSR synthetic tracking
    is_synthetic: bool = Field(default=False)
    synthetic_scenario_id: Optional[str] = Field(default=None, max_length=255)

    __table_args__ = (
        Index("ix_lessons_learned_tenant_status", "tenant_id", "status"),
        Index("ix_lessons_learned_lesson_type", "lesson_type"),
        Index("ix_lessons_learned_source_event", "source_event_id", "source_event_type"),
        Index("ix_lessons_learned_created_at", "created_at"),
    )


class LessonSummary(SQLModel):
    """Summary view of a lesson (O2 result shape)."""

    id: UUID
    tenant_id: str
    lesson_type: str
    severity: Optional[str]
    title: str
    status: str
    source_event_type: str
    created_at: datetime
    has_proposed_action: bool


class LessonDetail(SQLModel):
    """Detailed view of a lesson (O3 result shape)."""

    id: UUID
    tenant_id: str
    lesson_type: str
    severity: Optional[str]
    source_event_id: UUID
    source_event_type: str
    source_run_id: Optional[UUID]
    title: str
    description: str
    proposed_action: Optional[str]
    detected_pattern: Optional[dict[str, Any]]
    status: str
    draft_proposal_id: Optional[UUID]
    created_at: datetime
    converted_at: Optional[datetime]
    deferred_until: Optional[datetime]
    dismissed_at: Optional[datetime]
    dismissed_by: Optional[str]
    dismissed_reason: Optional[str]
