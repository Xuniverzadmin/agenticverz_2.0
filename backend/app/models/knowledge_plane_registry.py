# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Canonical governed knowledge plane registry (SSOT)
# Callers: hoc_spine knowledge lifecycle + retrieval harness
# Allowed Imports: L6 (sqlmodel)
# Forbidden Imports: L1, L2, L3
# Reference: docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md

"""
Module: knowledge_plane_registry
Purpose: Durable SSOT for governed knowledge planes (control-plane identity + lifecycle state).

This table is intentionally minimal:
- identity: (tenant_id, plane_type, plane_name) and immutable plane_id
- lifecycle_state_value: ordered state machine value (GAP-089)
- connector binding by reference (no secrets)

Non-scope:
- index/runtime operational metadata (belongs to runtime/index substrate)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import sqlalchemy as sa
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_plane_id() -> str:
    # Keep the existing kp_* convention used across hoc_spine lifecycle code.
    return f"kp_{uuid.uuid4().hex[:12]}"


class KnowledgePlaneRegistry(SQLModel, table=True):
    """
    Canonical governed knowledge plane registry record (SSOT).

    Invariants:
    - plane_id is immutable and unique
    - (tenant_id, plane_type, plane_name) is unique
    - lifecycle_state_value stores GAP-089 ordered IntEnum values
    """

    __tablename__ = "knowledge_plane_registry"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plane_type", "plane_name", name="uq_kp_registry_tenant_type_name"),
    )

    # Canonical immutable ID
    plane_id: str = Field(default_factory=generate_plane_id, primary_key=True, index=True, max_length=64)

    # Identity (human key)
    tenant_id: str = Field(index=True, max_length=64)
    plane_type: str = Field(index=True, max_length=64)
    plane_name: str = Field(index=True, max_length=128)

    # Lifecycle (GAP-089 IntEnum value)
    lifecycle_state_value: int = Field(
        default=KnowledgePlaneLifecycleState.DRAFT.value,
        index=True,
        description="GAP-089 ordered state value (e.g., 100..500)",
    )

    # Connector binding (by reference only)
    connector_type: str = Field(max_length=64)
    connector_id: str = Field(max_length=64)

    # Arbitrary config/metadata for the governed plane (no secrets)
    config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )

    created_by: Optional[str] = Field(default=None, max_length=64)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # =========================================================================
    # Computed helpers (no DB access)
    # =========================================================================

    @property
    def lifecycle_state(self) -> KnowledgePlaneLifecycleState:
        return KnowledgePlaneLifecycleState(self.lifecycle_state_value)
