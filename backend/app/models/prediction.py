"""
Prediction Event Models (PB-S5)

Models for storing predictions WITHOUT affecting execution behavior.

PB-S5 Contract:
- Predictions are advisory only
- Predictions have zero side-effects
- Predictions never modify execution, scheduling, or history
- Predictions are clearly labeled as estimates, not facts

Rule: Advise, don't influence.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class PredictionEvent(Base):
    """
    Prediction event record - advisory only, zero side-effects.

    PB-S5: Predictions are INERT. They cannot influence execution.
    subject_id is a reference only, NOT a foreign key.
    """

    __tablename__ = "prediction_events"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    # tenant_id is VARCHAR to match existing tenants table schema
    tenant_id = Column(String(255), nullable=False, index=True)

    # Prediction identification
    prediction_type = Column(String(50), nullable=False, index=True)  # failure_likelihood, cost_overrun
    subject_type = Column(String(50), nullable=False)  # worker, run, tenant
    subject_id = Column(String(255), nullable=False)  # Reference only, NOT FK

    # Prediction content
    confidence_score = Column(Float, nullable=False)  # 0.0 - 1.0
    prediction_value = Column(JSONB, nullable=False)  # Projected outcome
    contributing_factors = Column(JSONB, nullable=False, default=list)  # Features used

    # Validity window (C2 hardening: renamed from valid_until, now NOT NULL)
    expires_at = Column(DateTime, nullable=False)  # Prediction expiry (I-C2-5)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Advisory flag - ALWAYS TRUE (enforced by design)
    is_advisory = Column(Boolean, nullable=False, default=True)

    # Optional notes for context
    notes = Column(Text, nullable=True)


# Pydantic models for API
class PredictionEventCreate(BaseModel):
    """Input model for creating prediction events."""

    tenant_id: str  # VARCHAR to match tenants table
    prediction_type: str
    subject_type: str
    subject_id: str
    confidence_score: float
    prediction_value: dict
    contributing_factors: list = []
    expires_at: datetime  # Required (I-C2-5)
    notes: Optional[str] = None


class PredictionEventResponse(BaseModel):
    """Output model for prediction events."""

    id: UUID
    tenant_id: str
    prediction_type: str
    subject_type: str
    subject_id: str
    confidence_score: float
    prediction_value: dict
    contributing_factors: list
    expires_at: datetime  # Required (I-C2-5)
    created_at: datetime
    is_advisory: bool  # Always True (I-C2-1)
    notes: Optional[str]
