"""
Pattern Feedback Models (PB-S3)

Models for storing observed patterns WITHOUT modifying execution history.

PB-S3 Contract:
- Feedback observes but never mutates
- Provenance references runs (read-only)
- No execution data modification allowed
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class PatternFeedback(Base):
    """
    Pattern feedback record - observation without action.

    PB-S3: This is SEPARATE from execution tables.
    Provenance links are READ-ONLY references.
    """

    __tablename__ = "pattern_feedback"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    # tenant_id is VARCHAR to match existing tenants table schema
    tenant_id = Column(String(255), nullable=False, index=True)

    # Pattern classification
    pattern_type = Column(String(50), nullable=False, index=True)  # failure_pattern, cost_spike
    severity = Column(String(20), nullable=False, default="info")  # info, warning, critical

    # Pattern description
    description = Column(Text, nullable=False)
    signature = Column(String(255), nullable=True, index=True)

    # Provenance - READ-ONLY references to source runs (JSONB array)
    provenance = Column(JSONB, nullable=False, default=list)

    # Detection metadata
    occurrence_count = Column(Integer, nullable=False, default=1)
    time_window_minutes = Column(Integer, nullable=True)
    threshold_used = Column(String(100), nullable=True)

    # Additional context (column is named 'metadata' in DB but we use 'extra_data' in Python)
    extra_data = Column("metadata", JSONB, nullable=True)

    # Timestamps
    detected_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Acknowledgement tracking
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)


# Pydantic models for API
class PatternFeedbackCreate(BaseModel):
    """Input model for creating pattern feedback."""

    tenant_id: str  # VARCHAR to match tenants table
    pattern_type: str
    severity: str = "info"
    description: str
    signature: Optional[str] = None
    provenance: list[str] = []  # List of run_id strings
    occurrence_count: int = 1
    time_window_minutes: Optional[int] = None
    threshold_used: Optional[str] = None
    metadata: Optional[dict] = None


class PatternFeedbackResponse(BaseModel):
    """Output model for pattern feedback."""

    id: UUID
    tenant_id: str  # VARCHAR to match tenants table
    pattern_type: str
    severity: str
    description: str
    signature: Optional[str]
    provenance: list
    occurrence_count: int
    time_window_minutes: Optional[int]
    detected_at: datetime
    acknowledged: bool
    acknowledged_at: Optional[datetime]
