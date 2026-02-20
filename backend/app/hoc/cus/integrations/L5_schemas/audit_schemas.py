# capability_id: CAP-018
# Layer: L5 — Domain Schemas
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Audit trail dataclasses for integration bridges
# Callers: bridges, engines
# Allowed Imports: stdlib only
# Forbidden Imports: L6, sqlalchemy
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
M25 Audit Schemas

Dataclasses for audit records in the integration bridges.

FROZEN: 2025-12-23
Do NOT modify without explicit approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PolicyActivationAudit:
    """
    Audit record for policy activation.

    Required for:
    - Rollback
    - Blame tracking
    - Trust verification
    """

    policy_id: str
    source_pattern_id: str
    source_recovery_id: str
    confidence_at_activation: float
    confidence_version: str
    approval_path: str  # "auto" | "human:{user_id}" | "threshold"
    loop_trace_id: str
    activated_at: datetime
    tenant_id: str

    def to_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "source_pattern_id": self.source_pattern_id,
            "source_recovery_id": self.source_recovery_id,
            "confidence_at_activation": self.confidence_at_activation,
            "confidence_version": self.confidence_version,
            "approval_path": self.approval_path,
            "loop_trace_id": self.loop_trace_id,
            "activated_at": self.activated_at.isoformat(),
            "tenant_id": self.tenant_id,
        }
