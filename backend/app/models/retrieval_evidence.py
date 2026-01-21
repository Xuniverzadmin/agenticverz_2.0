# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Audit log model for mediated data access
# Callers: RetrievalMediator (GAP-065), export services
# Allowed Imports: L6 (sqlmodel)
# Forbidden Imports: L1, L2, L3
# Reference: GAP-058

"""
Module: retrieval_evidence
Purpose: Audit log for every mediated data access.

Table: retrieval_evidence
Immutability: Write-once (DB trigger prevents UPDATE/DELETE)

Imports (Dependencies):
    - sqlmodel: SQLModel, Field
    - sqlalchemy: Column, JSONB

Exports (Provides):
    - RetrievalEvidence: SQLModel table for audit records

Wiring Points:
    - Created by: RetrievalMediator (GAP-065)
    - Queried by: SOC2 export services, audit dashboards
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class RetrievalEvidence(SQLModel, table=True):
    """
    Audit record for mediated data access.

    PURPOSE:
        Records every access through the mediation layer (GAP-065).
        This provides the audit trail for SOC2 compliance and enables
        forensic analysis of data access patterns.

    SEMANTIC:
        DATA PLANE entity. Records FACTS about what data was accessed.
        Append-only by design - database trigger prevents UPDATE/DELETE.

    INVARIANTS:
        - Once written, records are IMMUTABLE (trigger-enforced)
        - query_hash is deterministic (same request → same hash)
        - doc_ids captures exactly what was returned
        - duration_ms is measured, not estimated

    LIFECYCLE:
        1. RetrievalMediator begins access → creates record with requested_at
        2. Access completes → updates completed_at, duration_ms, doc_ids
        3. No further mutations allowed
    """

    __tablename__ = "retrieval_evidence"

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Tenant ownership (required for isolation)
    tenant_id: str = Field(max_length=100, index=True)

    # Run context
    run_id: str = Field(index=True)

    # What was accessed
    plane_id: str = Field(index=True, description="Data plane identifier")
    connector_id: str = Field(max_length=100, description="Connector that handled the request")
    action: str = Field(max_length=50, description="Action type (query, read, fetch)")
    query_hash: str = Field(max_length=64, description="SHA256 hash of request payload for deduplication")

    # What was returned (JSONB for document IDs list)
    doc_ids: List[str] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False, server_default="[]"))
    token_count: int = Field(ge=0, description="Token count of returned data")

    # Policy context
    policy_snapshot_id: Optional[str] = Field(default=None, max_length=100, description="Policy snapshot active at retrieval time")

    # Timing
    requested_at: datetime = Field(default_factory=utc_now, description="When the retrieval was requested")
    completed_at: Optional[datetime] = Field(default=None, description="When the retrieval completed")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Duration in milliseconds")

    # Immutability marker
    created_at: datetime = Field(default_factory=utc_now)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def is_complete(self) -> bool:
        """Check if the retrieval has completed."""
        return self.completed_at is not None

    @property
    def doc_count(self) -> int:
        """Number of documents returned."""
        return len(self.doc_ids) if self.doc_ids else 0
