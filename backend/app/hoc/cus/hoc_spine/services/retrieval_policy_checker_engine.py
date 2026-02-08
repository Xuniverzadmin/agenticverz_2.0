# Layer: L4 — HOC Spine (Engine)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker (mediated retrieval)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: runs, policy_snapshots
#   Writes: none
# Role: Policy gate for RetrievalMediator using persisted policy snapshots (Phase 6)
# Callers: hoc_spine RetrievalMediator wiring
# Allowed Imports: hoc_spine orchestrator session context, app.db (Run), app.models (PolicySnapshot)
# Forbidden Imports: L2 routes

from __future__ import annotations

import json
from typing import Any, Optional

from sqlmodel import select

from app.db import Run
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_async_session_context
from app.models.policy_snapshot import PolicySnapshot


def _extract_allowed_plane_ids(thresholds: dict[str, Any]) -> list[str]:
    """
    Extract allowlist of governed plane_ids from a policy snapshot thresholds dict.

    Deny-by-default contract:
    - missing/empty allowlist => deny

    Supported keys (compat bridge):
    - allowed_plane_ids
    - allowed_rag_sources
    - allowed_knowledge_planes
    - knowledge_access.allowed_planes
    """
    raw = (
        thresholds.get("allowed_plane_ids")
        or thresholds.get("allowed_rag_sources")
        or thresholds.get("allowed_knowledge_planes")
        or (thresholds.get("knowledge_access") or {}).get("allowed_planes")
    )
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x is not None]
    return []


class DbPolicySnapshotPolicyChecker:
    """
    RetrievalMediator PolicyChecker backed by Run.policy_snapshot_id and PolicySnapshot JSON.

    This checker is intentionally minimal:
    - It enforces deny-by-default.
    - It only allows access when the snapshot thresholds include an explicit allowlist for plane_id.

    It does NOT attempt to interpret full policy semantics; it is a stable contract bridge until
    the policies domain provides a richer KnowledgePolicyGatePort implementation.
    """

    async def check_access(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
    ):
        from app.hoc.cus.hoc_spine.services.retrieval_mediator import PolicyCheckResult

        async with get_async_session_context() as session:
            run_stmt = select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
            run_result = await session.execute(run_stmt)
            run = run_result.scalars().first()

            if run is None:
                return PolicyCheckResult(
                    allowed=False,
                    reason="Run not found for tenant (deny-by-default)",
                )

            snapshot_id: Optional[str] = run.policy_snapshot_id
            if not snapshot_id:
                return PolicyCheckResult(
                    allowed=False,
                    reason="Run has no policy_snapshot_id (deny-by-default)",
                )

            snap_stmt = select(PolicySnapshot).where(
                PolicySnapshot.snapshot_id == snapshot_id,
                PolicySnapshot.tenant_id == tenant_id,
            )
            snap_result = await session.execute(snap_stmt)
            snapshot = snap_result.scalars().first()

            if snapshot is None:
                return PolicyCheckResult(
                    allowed=False,
                    reason="Policy snapshot not found (deny-by-default)",
                    snapshot_id=snapshot_id,
                )

        try:
            thresholds = json.loads(snapshot.thresholds_json or "{}")
        except Exception:
            thresholds = {}

        allowed_planes = _extract_allowed_plane_ids(thresholds)
        if not allowed_planes:
            return PolicyCheckResult(
                allowed=False,
                reason="No plane allowlist configured in policy snapshot (deny-by-default)",
                snapshot_id=snapshot.snapshot_id,
            )

        if "*" in allowed_planes or plane_id in allowed_planes:
            return PolicyCheckResult(
                allowed=True,
                reason="Plane allowed by policy snapshot allowlist",
                snapshot_id=snapshot.snapshot_id,
            )

        return PolicyCheckResult(
            allowed=False,
            reason=f"Plane '{plane_id}' not in allowlist (deny-by-default)",
            snapshot_id=snapshot.snapshot_id,
        )


_policy_checker: Optional[DbPolicySnapshotPolicyChecker] = None


def get_db_policy_snapshot_policy_checker() -> DbPolicySnapshotPolicyChecker:
    global _policy_checker
    if _policy_checker is None:
        _policy_checker = DbPolicySnapshotPolicyChecker()
    return _policy_checker


__all__ = [
    "DbPolicySnapshotPolicyChecker",
    "get_db_policy_snapshot_policy_checker",
]

