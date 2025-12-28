"""
Policy Proposal Models (PB-S4)

Models for storing policy proposals WITHOUT auto-enforcement.

PB-S4 Contract:
- Policies are proposed based on observed feedback
- Human approval is mandatory
- No policy auto-enforces
- No policy affects past executions

Rule: Propose → Review → Decide (Human)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class PolicyProposal(Base):
    """
    Policy proposal record - recommendation without enforcement.

    PB-S4: Proposals are INERT until human approval.
    triggering_feedback_ids links are READ-ONLY provenance.
    """

    __tablename__ = "policy_proposals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    # tenant_id is VARCHAR to match existing tenants table schema
    tenant_id = Column(String(255), nullable=False, index=True)

    # Proposal identification
    proposal_name = Column(String(255), nullable=False)
    proposal_type = Column(String(50), nullable=False, index=True)  # rate_limit, cost_cap, retry_policy

    # Proposal content
    rationale = Column(Text, nullable=False)
    proposed_rule = Column(JSONB, nullable=False)  # The actual policy rule

    # Provenance - READ-ONLY references to triggering feedback
    triggering_feedback_ids = Column(JSONB, nullable=False, default=list)

    # Status workflow: draft → approved/rejected
    status = Column(String(20), nullable=False, default="draft")

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Review tracking (nullable until reviewed)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Effective date (only set if approved, future-dated)
    effective_from = Column(DateTime, nullable=True)

    # Relationship to versions
    versions = relationship("PolicyVersion", back_populates="proposal")


class PolicyVersion(Base):
    """
    Policy version record - append-only history.

    PB-S4: Versions are never deleted or modified.
    Each approval creates a new version snapshot.
    """

    __tablename__ = "policy_versions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    proposal_id = Column(PGUUID(as_uuid=True), ForeignKey("policy_proposals.id"), nullable=False)

    # Version tracking
    version = Column(Integer, nullable=False)
    rule_snapshot = Column(JSONB, nullable=False)  # Snapshot of the rule at this version

    # Audit trail
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    created_by = Column(String(255), nullable=True)
    change_reason = Column(Text, nullable=True)

    # Relationship
    proposal = relationship("PolicyProposal", back_populates="versions")


# Pydantic models for API
class PolicyProposalCreate(BaseModel):
    """Input model for creating policy proposals."""

    tenant_id: str  # VARCHAR to match tenants table
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict
    triggering_feedback_ids: list[str] = []  # List of feedback ID strings


class PolicyProposalResponse(BaseModel):
    """Output model for policy proposals."""

    id: UUID
    tenant_id: str
    proposal_name: str
    proposal_type: str
    rationale: str
    proposed_rule: dict
    triggering_feedback_ids: list
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    effective_from: Optional[datetime]


class PolicyApprovalRequest(BaseModel):
    """Input model for approving/rejecting a policy proposal."""

    action: str  # "approve" or "reject"
    reviewed_by: str
    review_notes: Optional[str] = None
    effective_from: Optional[datetime] = None  # Only for approval


class PolicyVersionResponse(BaseModel):
    """Output model for policy versions."""

    id: UUID
    proposal_id: UUID
    version: int
    rule_snapshot: dict
    created_at: datetime
    created_by: Optional[str]
    change_reason: Optional[str]
