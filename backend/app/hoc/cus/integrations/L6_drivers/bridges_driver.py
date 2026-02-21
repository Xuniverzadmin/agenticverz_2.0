# capability_id: CAP-018
# Layer: L6 — Drivers
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: Database operations for integration bridges
# Callers: bridges_engine (via L4 handler)
# Allowed Imports: stdlib, sqlalchemy
# Forbidden Imports: L1-L5 business logic
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: HOC_LAYER_TOPOLOGY_V1.md, PIN-520 (L6 Purity)

"""
M25 Bridges Driver

Database operations for integration bridge audit trails.

L6 Contract:
    - Session REQUIRED (passed from L4 handler)
    - L6 does NOT commit (L4 owns transaction boundary)

UNFROZEN: 2026-02-06 (PIN-520 L6 purity compliance)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.integrations.L5_schemas.audit_schemas import PolicyActivationAudit
from app.hoc.cus.integrations.L5_schemas.loop_events import ConfidenceCalculator

logger = logging.getLogger(__name__)


async def record_policy_activation(
    session: AsyncSession,
    policy_id: str,
    source_pattern_id: str,
    source_recovery_id: str,
    confidence: float,
    approval_path: str,
    loop_trace_id: str,
    tenant_id: str,
) -> PolicyActivationAudit:
    """
    Record policy activation for audit trail.

    Every ACTIVE policy must have an audit record.

    Args:
        session: AsyncSession from L4 handler (required)
        policy_id: Policy being activated
        source_pattern_id: Source pattern ID
        source_recovery_id: Source recovery ID
        confidence: Confidence score at activation
        approval_path: Approval workflow path
        loop_trace_id: Loop trace correlation ID
        tenant_id: Tenant scope

    Returns:
        PolicyActivationAudit record

    Note:
        L6 does NOT commit — L4 handler owns transaction boundary.
    """
    audit = PolicyActivationAudit(
        policy_id=policy_id,
        source_pattern_id=source_pattern_id,
        source_recovery_id=source_recovery_id,
        confidence_at_activation=confidence,
        confidence_version=ConfidenceCalculator.VERSION,
        approval_path=approval_path,
        loop_trace_id=loop_trace_id,
        activated_at=datetime.now(timezone.utc),
        tenant_id=tenant_id,
    )

    await session.execute(
        text(
            """
            INSERT INTO policy_activation_audit
            (policy_id, source_pattern_id, source_recovery_id,
             confidence_at_activation, confidence_version, approval_path,
             loop_trace_id, activated_at, tenant_id)
            VALUES (:policy_id, :pattern_id, :recovery_id,
                    :confidence, :version, :approval_path,
                    :trace_id, :activated_at, :tenant_id)
            ON CONFLICT (policy_id) DO UPDATE SET
                confidence_at_activation = :confidence,
                approval_path = :approval_path,
                activated_at = :activated_at
        """
        ),
        {
            "policy_id": audit.policy_id,
            "pattern_id": audit.source_pattern_id,
            "recovery_id": audit.source_recovery_id,
            "confidence": audit.confidence_at_activation,
            "version": audit.confidence_version,
            "approval_path": audit.approval_path,
            "trace_id": audit.loop_trace_id,
            "activated_at": audit.activated_at,
            "tenant_id": audit.tenant_id,
        },
    )
    # L6 does NOT commit — L4 handler owns transaction boundary

    logger.info(f"Policy activation audit recorded: {policy_id} (confidence={confidence:.2f}, path={approval_path})")

    return audit
