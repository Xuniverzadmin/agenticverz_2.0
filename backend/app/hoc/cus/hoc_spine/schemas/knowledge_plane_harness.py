# capability_id: CAP-012
# Layer: L4 — HOC Spine (Schemas)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Knowledge plane harness kit — protocol interfaces + facts (Phase 1)
# Consumers: hoc_spine, policies, integrations, logs
# Allowed Imports: stdlib only
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md
# artifact_class: CODE

"""
Knowledge Plane Harness Kit (Phase 1)

This module freezes the **stdlib-only** contracts for the knowledge plane
control-plane template owned by hoc_spine.

Scope:
- identity + record facts (what is a governed plane)
- ports that domains can implement (capabilities), without granting them
  lifecycle authority

Non-scope:
- persistence implementation (Phase 2)
- operation registration / audience routing (Phase 3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class KnowledgePlaneKey:
    """
    Canonical plane identity (human key).

    Decision recorded in plan:
    - many planes per tenant, keyed by (tenant_id, plane_type, plane_name)
    """

    tenant_id: str
    plane_type: str
    plane_name: str


@dataclass(frozen=True)
class KnowledgeConnectorBinding:
    """Connector binding for a governed plane (by reference, never secrets)."""

    connector_type: str
    connector_id: str


@dataclass(frozen=True)
class KnowledgePlaneRecord:
    """
    Persisted facts about a governed plane (SSOT).

    Note: lifecycle_state is stringly-typed here to keep this module stdlib-only.
    Implementations must treat it as the canonical name of the lifecycle enum
    defined elsewhere (e.g., GAP-089).
    """

    plane_id: str
    key: KnowledgePlaneKey
    lifecycle_state: str
    connector: KnowledgeConnectorBinding
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeAccessDecision:
    """Deny-by-default policy decision for a retrieval access attempt."""

    allowed: bool
    reason: str
    policy_snapshot_id: Optional[str] = None
    blocking_policy_id: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeTransitionDecision:
    """Policy/authority decision for a lifecycle transition request."""

    allowed: bool
    reason: str
    required_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgePlaneTransitionIntent:
    """
    Transition request envelope (what caller wants).

    hoc_spine remains the transition authority; this intent is evaluated,
    not blindly executed.
    """

    tenant_id: str
    plane_id: str
    action: str
    actor_type: str
    actor_id: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgePlaneTransitionOutcome:
    """Structured outcome for transition attempts."""

    success: bool
    tenant_id: str
    plane_id: str
    from_state: str
    to_state: Optional[str]
    message: str
    job_id: Optional[str] = None
    audit_event_id: Optional[str] = None
    decision: Optional[KnowledgeTransitionDecision] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalEvidenceIntent:
    """Append-only evidence intent for mediated retrieval."""

    tenant_id: str
    run_id: str
    plane_id: str
    connector_id: str
    query_hash: str
    doc_ids: List[str]
    token_count: int
    policy_snapshot_id: Optional[str]
    timestamp: datetime


@dataclass(frozen=True)
class RetrievalEvidenceRecord:
    """Append-only evidence record (post-persistence)."""

    evidence_id: str
    tenant_id: str
    run_id: str
    plane_id: str
    connector_id: str
    query_hash: str
    doc_ids: List[str]
    token_count: int
    policy_snapshot_id: Optional[str]
    timestamp: datetime


@runtime_checkable
class KnowledgePlaneStorePort(Protocol):
    """Durable store port for governed plane records (Phase 2 implementation)."""

    async def get_by_id(self, *, tenant_id: str, plane_id: str) -> Optional[KnowledgePlaneRecord]:
        ...

    async def get_by_key(self, *, key: KnowledgePlaneKey) -> Optional[KnowledgePlaneRecord]:
        ...

    async def list_by_tenant(
        self,
        *,
        tenant_id: str,
        plane_type: Optional[str] = None,
    ) -> List[KnowledgePlaneRecord]:
        ...

    async def create(self, *, record: KnowledgePlaneRecord) -> KnowledgePlaneRecord:
        ...

    async def set_lifecycle_state(
        self,
        *,
        tenant_id: str,
        plane_id: str,
        new_state: str,
        updated_at: datetime,
    ) -> KnowledgePlaneRecord:
        ...


@runtime_checkable
class KnowledgeEvidenceStorePort(Protocol):
    """Durable store port for retrieval evidence (Phase 2 implementation)."""

    async def append(self, *, intent: RetrievalEvidenceIntent) -> RetrievalEvidenceRecord:
        ...


@runtime_checkable
class KnowledgePolicyGatePort(Protocol):
    """
    Port for policy gates.

    Implementations live in the policies domain (capability provider).
    hoc_spine consumes this port for:
    - deny-by-default retrieval access checks
    - protected lifecycle transition checks
    """

    async def check_access(
        self,
        *,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
    ) -> KnowledgeAccessDecision:
        ...

    async def check_transition(
        self,
        *,
        tenant_id: str,
        plane_id: str,
        action: str,
        from_state: str,
        to_state: str,
    ) -> KnowledgeTransitionDecision:
        ...


@runtime_checkable
class KnowledgeConnectorRegistryPort(Protocol):
    """
    Port for resolving a connector binding for a governed plane.

    Implementations live in the integrations domain (capability provider).
    """

    async def resolve_connector(
        self,
        *,
        tenant_id: str,
        plane_id: str,
    ) -> Optional[KnowledgeConnectorBinding]:
        ...


__all__ = [
    "KnowledgePlaneKey",
    "KnowledgeConnectorBinding",
    "KnowledgePlaneRecord",
    "KnowledgeAccessDecision",
    "KnowledgeTransitionDecision",
    "KnowledgePlaneTransitionIntent",
    "KnowledgePlaneTransitionOutcome",
    "RetrievalEvidenceIntent",
    "RetrievalEvidenceRecord",
    "KnowledgePlaneStorePort",
    "KnowledgeEvidenceStorePort",
    "KnowledgePolicyGatePort",
    "KnowledgeConnectorRegistryPort",
]

