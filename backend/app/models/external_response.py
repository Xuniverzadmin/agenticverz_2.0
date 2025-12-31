# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: External response data models (DB tables)
# Callers: L3 adapters (write raw), L4 engines (read/interpret)
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-04

"""
External Response Models (Phase E FIX-04)

Models for persisting raw external API responses with explicit interpretation
ownership. L3 adapters write raw data; L4 engines interpret.

Phase E Contract:
- L3 adapters write raw responses to L6
- L4 engines read raw, interpret, write interpreted_value
- L5/L2 consumers read L4's interpretation only
- No implicit interpretation in adapters

Violations Resolved: VIOLATION-007, VIOLATION-008, VIOLATION-009, VIOLATION-010
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

# Import shared Base from costsim_cb to ensure single metadata
from app.models.costsim_cb import Base


class ExternalResponse(Base):
    """
    External response record - raw data with interpretation ownership.

    Phase E FIX-04: Every external response has an explicit interpretation owner.
    L3 adapters write raw_response; L4 engines write interpreted_value.
    """

    __tablename__ = "external_responses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    # Source of external data
    source = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Source: ANTHROPIC, OPENAI, VOYAGEAI, WEBHOOK, OTHER",
    )

    # Request context
    request_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Request ID for correlation",
    )

    run_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Run ID if part of execution",
    )

    # Raw response (untouched external data)
    raw_response = Column(
        JSONB,
        nullable=False,
        comment="Untouched external response data",
    )

    # Interpretation ownership
    interpretation_owner = Column(
        String(100),
        nullable=False,
        index=True,
        comment="L4 engine responsible for interpretation",
    )

    interpretation_contract = Column(
        String(200),
        nullable=True,
        comment="What this data means (contract name)",
    )

    # Interpreted value (filled by L4 engine)
    interpreted_value = Column(
        JSONB,
        nullable=True,
        comment="Domain-meaningful result from L4 interpretation",
    )

    interpreted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When L4 engine interpreted this",
    )

    interpreted_by = Column(
        String(100),
        nullable=True,
        comment="Specific L4 engine instance that interpreted",
    )

    # Timestamps
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When raw response was received",
    )

    # Composite index for pending interpretation queries
    __table_args__ = (
        Index(
            "ix_ext_resp_owner_pending",
            "interpretation_owner",
            "received_at",
            postgresql_where="interpreted_at IS NULL",
        ),
        {"comment": "Phase E FIX-04: Raw external responses with interpretation ownership"},
    )


# Pydantic models for API/Service use


class ExternalResponseCreate(BaseModel):
    """Input model for recording external responses (L3 → L6 write)."""

    source: str  # ANTHROPIC, OPENAI, VOYAGEAI, WEBHOOK
    raw_response: dict  # Untouched external data
    interpretation_owner: str  # L4 engine responsible
    interpretation_contract: Optional[str] = None
    request_id: Optional[str] = None
    run_id: Optional[str] = None


class InterpretationUpdate(BaseModel):
    """Input model for L4 engine interpretation (L4 → L6 write)."""

    interpreted_value: dict  # Domain-meaningful result
    interpreted_by: str  # L4 engine instance name


class ExternalResponseRead(BaseModel):
    """Output model for external responses."""

    id: UUID
    source: str
    request_id: Optional[str]
    run_id: Optional[str]
    raw_response: dict
    interpretation_owner: str
    interpretation_contract: Optional[str]
    interpreted_value: Optional[dict]
    interpreted_at: Optional[datetime]
    interpreted_by: Optional[str]
    received_at: datetime

    class Config:
        from_attributes = True


class InterpretedResponse(BaseModel):
    """
    Output model for consumers (L5/L2) - only the interpreted value.

    Consumers should never see raw_response directly.
    """

    id: UUID
    source: str
    interpretation_owner: str
    interpreted_value: dict
    interpreted_at: datetime
    interpreted_by: str
