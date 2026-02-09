# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch)
#   Execution: async
# Role: Knowledge plane registry + evidence query handler (Phase 3)
# Callers: OperationRegistry (L4), founder retrieval admin routes
# Allowed Imports: hoc_spine (drivers), app.models (facts)
# Forbidden Imports: L1, L2, L5 (domain engines), sqlalchemy (except via session)
# Reference: docs/architecture/hoc/KNOWLEDGE_PLANE_CONTRACTS_V1.md
# artifact_class: CODE

"""
Knowledge Planes Handler (L4 Orchestrator)

Phase 3 goal: move plane registry + evidence query behind L4 operations so
L2 surfaces do not call hoc_spine services directly.

Operations registered:
- knowledge.planes.register
- knowledge.planes.get
- knowledge.planes.list
- knowledge.planes.transition
- knowledge.planes.bind_policy
- knowledge.planes.unbind_policy
- knowledge.planes.approve_purge
- knowledge.evidence.get
- knowledge.evidence.list

Note: Lifecycle transitions and retrieval mediation rewiring are Phase 4+.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from sqlmodel import select

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.knowledge_planes_handler")

_BOUND_POLICY_IDS_KEY = "bound_policy_ids"
_PURGE_APPROVED_KEY = "purge_approved"


@asynccontextmanager
async def _write_tx(session):
    """
    Transaction helper for L4 handlers.

    - In normal runtime calls, handlers own the commit via `session.begin()`.
    - In tests (or higher-level orchestrations) where a transaction is already active,
      use a SAVEPOINT via `begin_nested()` so we don't commit the caller's outer tx.
    """
    if session.in_transaction():
        async with session.begin_nested():
            yield
    else:
        async with session.begin():
            yield


class KnowledgePlanesRegisterHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        tenant_id = ctx.tenant_id
        plane_type = ctx.params.get("plane_type")
        plane_name = ctx.params.get("plane_name")
        connector_type = ctx.params.get("connector_type")
        connector_id = ctx.params.get("connector_id")
        config = ctx.params.get("config") or {}
        created_by = ctx.params.get("created_by")

        if not plane_type or not plane_name:
            return OperationResult.fail("Missing plane_type/plane_name", "MISSING_IDENTITY")
        if not connector_type or not connector_id:
            return OperationResult.fail("Missing connector_type/connector_id", "MISSING_CONNECTOR")

        driver = KnowledgePlaneRegistryDriver()
        try:
            async with _write_tx(ctx.session):
                record = await driver.create(
                    ctx.session,
                    tenant_id=tenant_id,
                    plane_type=str(plane_type),
                    plane_name=str(plane_name),
                    connector_type=str(connector_type),
                    connector_id=str(connector_id),
                    config=config if isinstance(config, dict) else {"config": config},
                    created_by=str(created_by) if created_by else None,
                )
        except Exception as e:
            return OperationResult.fail(f"Failed to register plane: {e}", "PLANE_REGISTER_FAILED")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "plane_type": record.plane_type,
                "plane_name": record.plane_name,
                "lifecycle_state_value": record.lifecycle_state_value,
                "connector_type": record.connector_type,
                "connector_id": record.connector_id,
                "config": record.config,
                "created_by": record.created_by,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgePlanesGetHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_id = ctx.params.get("plane_id")
        if not plane_id:
            return OperationResult.fail("Missing plane_id", "MISSING_PLANE_ID")

        driver = KnowledgePlaneRegistryDriver()
        record = await driver.get_by_id(
            ctx.session,
            tenant_id=ctx.tenant_id,
            plane_id=str(plane_id),
        )
        if record is None:
            return OperationResult.fail("Plane not found", "NOT_FOUND")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "plane_type": record.plane_type,
                "plane_name": record.plane_name,
                "lifecycle_state_value": record.lifecycle_state_value,
                "connector_type": record.connector_type,
                "connector_id": record.connector_id,
                "config": record.config,
                "created_by": record.created_by,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgePlanesListHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_type = ctx.params.get("plane_type")
        driver = KnowledgePlaneRegistryDriver()
        records = await driver.list_by_tenant(
            ctx.session,
            tenant_id=ctx.tenant_id,
            plane_type=str(plane_type) if plane_type else None,
        )

        data = []
        for record in records:
            data.append(
                {
                    "plane_id": record.plane_id,
                    "tenant_id": record.tenant_id,
                    "plane_type": record.plane_type,
                    "plane_name": record.plane_name,
                    "lifecycle_state_value": record.lifecycle_state_value,
                    "connector_type": record.connector_type,
                    "connector_id": record.connector_id,
                    "config": record.config,
                    "created_by": record.created_by,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat(),
                }
            )

        return OperationResult.ok({"planes": data, "total": len(data)})


class KnowledgePlanesTransitionHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        """
        Transition a governed knowledge plane's lifecycle state (persisted SSOT).

        Inputs (ctx.params):
        - plane_id: str (required)
        - action: str (optional; GAP-089 LifecycleAction string)
        - to_state: str (optional; KnowledgePlaneLifecycleState name)

        Gates:
        - Tenant must be ACTIVE (tenant.status == "active").
        - GAP-089 transition matrix must allow the transition.
        - Protected transitions require minimal persisted intent:
          - → ACTIVE requires config.bound_policy_ids non-empty
          - → PURGED requires config.purge_approved == True
        """
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )
        from app.models.knowledge_lifecycle import (
            KnowledgePlaneLifecycleState,
            get_transition_for_action,
            validate_transition,
        )
        from app.models.tenant import Tenant

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_id = ctx.params.get("plane_id")
        action = ctx.params.get("action")
        to_state = ctx.params.get("to_state")

        if not plane_id:
            return OperationResult.fail("Missing plane_id", "MISSING_PLANE_ID")
        if not action and not to_state:
            return OperationResult.fail("Missing action or to_state", "MISSING_TRANSITION_INTENT")

        # Tenant lifecycle gate (transitive prerequisite).
        tenant_stmt = select(Tenant).where(Tenant.id == ctx.tenant_id)
        tenant_result = await ctx.session.execute(tenant_stmt)
        tenant = tenant_result.scalars().first()
        if tenant is None:
            return OperationResult.fail("Tenant not found", "TENANT_NOT_FOUND")
        if str(tenant.status).lower() != "active":
            return OperationResult.fail(f"Tenant is {tenant.status}", "TENANT_INACTIVE")

        driver = KnowledgePlaneRegistryDriver()
        record = await driver.get_by_id(ctx.session, tenant_id=ctx.tenant_id, plane_id=str(plane_id))
        if record is None:
            return OperationResult.fail("Plane not found", "NOT_FOUND")

        current_state = KnowledgePlaneLifecycleState(record.lifecycle_state_value)
        if action:
            target = get_transition_for_action(str(action), current_state)
            if target is None:
                return OperationResult.fail(
                    f"Action '{action}' not valid from {current_state.name}",
                    "INVALID_ACTION",
                )
            target_state = target
        else:
            try:
                target_state = KnowledgePlaneLifecycleState[str(to_state).upper()]
            except Exception:
                return OperationResult.fail(f"Invalid to_state: {to_state}", "INVALID_TARGET_STATE")

        validation = validate_transition(current_state, target_state)
        if not validation.allowed:
            return OperationResult.fail(validation.reason, "INVALID_TRANSITION")

        config = record.config if isinstance(record.config, dict) else {}
        if target_state == KnowledgePlaneLifecycleState.ACTIVE:
            bound = config.get(_BOUND_POLICY_IDS_KEY) or []
            if not isinstance(bound, list) or len(bound) == 0:
                return OperationResult.fail("No policy bound (bind_policy required)", "POLICY_GATE_BLOCKED")
        if target_state == KnowledgePlaneLifecycleState.PURGED:
            if config.get(_PURGE_APPROVED_KEY) is not True:
                return OperationResult.fail("Purge not approved (approve_purge required)", "POLICY_GATE_PENDING")

        try:
            async with _write_tx(ctx.session):
                record = await driver.set_lifecycle_state_value(
                    ctx.session,
                    tenant_id=ctx.tenant_id,
                    plane_id=str(plane_id),
                    lifecycle_state_value=int(target_state.value),
                )
        except Exception as e:
            return OperationResult.fail(f"Failed to transition plane: {e}", "PLANE_TRANSITION_FAILED")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "from_state_value": int(current_state.value),
                "to_state_value": int(target_state.value),
                "action": str(action) if action else None,
                "lifecycle_state_value": record.lifecycle_state_value,
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgePlanesBindPolicyHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        """
        Mutate governed plane config to bind a policy ID (config-only; no state change).

        Inputs (ctx.params):
        - plane_id: str (required)
        - policy_id: str (required)
        """
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_id = ctx.params.get("plane_id")
        policy_id = ctx.params.get("policy_id")
        if not plane_id:
            return OperationResult.fail("Missing plane_id", "MISSING_PLANE_ID")
        if not policy_id:
            return OperationResult.fail("Missing policy_id", "MISSING_POLICY_ID")

        driver = KnowledgePlaneRegistryDriver()
        record = await driver.get_by_id(ctx.session, tenant_id=ctx.tenant_id, plane_id=str(plane_id))
        if record is None:
            return OperationResult.fail("Plane not found", "NOT_FOUND")

        # Copy so SQLAlchemy sees a new value; JSONB isn't guaranteed to detect in-place mutation.
        config = dict(record.config) if isinstance(record.config, dict) else {}
        bound = config.get(_BOUND_POLICY_IDS_KEY)
        if bound is None:
            bound = []
        if not isinstance(bound, list):
            return OperationResult.fail("Invalid bound_policy_ids (expected list)", "INVALID_CONFIG")

        policy_id_str = str(policy_id)
        if policy_id_str not in bound:
            bound = [*bound, policy_id_str]
        config[_BOUND_POLICY_IDS_KEY] = list(bound)

        try:
            async with _write_tx(ctx.session):
                record = await driver.set_config(
                    ctx.session,
                    tenant_id=ctx.tenant_id,
                    plane_id=str(plane_id),
                    config=config,
                )
        except Exception as e:
            return OperationResult.fail(f"Failed to bind policy: {e}", "BIND_POLICY_FAILED")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "bound_policy_ids": record.config.get(_BOUND_POLICY_IDS_KEY, []),
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgePlanesUnbindPolicyHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        """
        Mutate governed plane config to unbind a policy ID (config-only; no state change).

        Inputs (ctx.params):
        - plane_id: str (required)
        - policy_id: str (required)
        """
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_id = ctx.params.get("plane_id")
        policy_id = ctx.params.get("policy_id")
        if not plane_id:
            return OperationResult.fail("Missing plane_id", "MISSING_PLANE_ID")
        if not policy_id:
            return OperationResult.fail("Missing policy_id", "MISSING_POLICY_ID")

        driver = KnowledgePlaneRegistryDriver()
        record = await driver.get_by_id(ctx.session, tenant_id=ctx.tenant_id, plane_id=str(plane_id))
        if record is None:
            return OperationResult.fail("Plane not found", "NOT_FOUND")

        config = dict(record.config) if isinstance(record.config, dict) else {}
        bound = config.get(_BOUND_POLICY_IDS_KEY) or []
        if not isinstance(bound, list):
            return OperationResult.fail("Invalid bound_policy_ids (expected list)", "INVALID_CONFIG")

        policy_id_str = str(policy_id)
        bound = [p for p in bound if str(p) != policy_id_str]
        config[_BOUND_POLICY_IDS_KEY] = list(bound)

        try:
            async with _write_tx(ctx.session):
                record = await driver.set_config(
                    ctx.session,
                    tenant_id=ctx.tenant_id,
                    plane_id=str(plane_id),
                    config=config,
                )
        except Exception as e:
            return OperationResult.fail(f"Failed to unbind policy: {e}", "UNBIND_POLICY_FAILED")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "bound_policy_ids": record.config.get(_BOUND_POLICY_IDS_KEY, []),
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgePlanesApprovePurgeHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        """
        Mutate governed plane config to approve purge (config-only; no state change).

        Inputs (ctx.params):
        - plane_id: str (required)
        """
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        plane_id = ctx.params.get("plane_id")
        if not plane_id:
            return OperationResult.fail("Missing plane_id", "MISSING_PLANE_ID")

        driver = KnowledgePlaneRegistryDriver()
        record = await driver.get_by_id(ctx.session, tenant_id=ctx.tenant_id, plane_id=str(plane_id))
        if record is None:
            return OperationResult.fail("Plane not found", "NOT_FOUND")

        config = dict(record.config) if isinstance(record.config, dict) else {}
        config[_PURGE_APPROVED_KEY] = True

        try:
            async with _write_tx(ctx.session):
                record = await driver.set_config(
                    ctx.session,
                    tenant_id=ctx.tenant_id,
                    plane_id=str(plane_id),
                    config=config,
                )
        except Exception as e:
            return OperationResult.fail(f"Failed to approve purge: {e}", "APPROVE_PURGE_FAILED")

        return OperationResult.ok(
            {
                "plane_id": record.plane_id,
                "tenant_id": record.tenant_id,
                "purge_approved": True,
                "updated_at": record.updated_at.isoformat(),
            }
        )


class KnowledgeEvidenceGetHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import (
            RetrievalEvidenceDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        evidence_id = ctx.params.get("evidence_id")
        if not evidence_id:
            return OperationResult.fail("Missing evidence_id", "MISSING_EVIDENCE_ID")

        driver = RetrievalEvidenceDriver()
        record = await driver.get_by_id(
            ctx.session,
            tenant_id=ctx.tenant_id,
            evidence_id=str(evidence_id),
        )
        if record is None:
            return OperationResult.fail("Evidence not found", "NOT_FOUND")

        return OperationResult.ok(
            {
                "id": record.id,
                "tenant_id": record.tenant_id,
                "run_id": record.run_id,
                "plane_id": record.plane_id,
                "connector_id": record.connector_id,
                "action": record.action,
                "query_hash": record.query_hash,
                "doc_ids": record.doc_ids,
                "token_count": record.token_count,
                "policy_snapshot_id": record.policy_snapshot_id,
                "requested_at": record.requested_at.isoformat(),
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "duration_ms": record.duration_ms,
                "created_at": record.created_at.isoformat(),
            }
        )


class KnowledgeEvidenceListHandler:
    async def execute(self, ctx: OperationContext) -> OperationResult:
        from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import (
            RetrievalEvidenceDriver,
        )

        if ctx.session is None:
            return OperationResult.fail("Missing async session", "MISSING_SESSION")

        run_id = ctx.params.get("run_id")
        plane_id = ctx.params.get("plane_id")
        limit = int(ctx.params.get("limit", 100))
        offset = int(ctx.params.get("offset", 0))

        driver = RetrievalEvidenceDriver()
        records = await driver.list(
            ctx.session,
            tenant_id=ctx.tenant_id,
            run_id=str(run_id) if run_id else None,
            plane_id=str(plane_id) if plane_id else None,
            limit=limit,
            offset=offset,
        )

        data = []
        for record in records:
            data.append(
                {
                    "id": record.id,
                    "tenant_id": record.tenant_id,
                    "run_id": record.run_id,
                    "plane_id": record.plane_id,
                    "connector_id": record.connector_id,
                    "action": record.action,
                    "query_hash": record.query_hash,
                    "doc_ids": record.doc_ids,
                    "token_count": record.token_count,
                    "policy_snapshot_id": record.policy_snapshot_id,
                    "requested_at": record.requested_at.isoformat(),
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                    "duration_ms": record.duration_ms,
                    "created_at": record.created_at.isoformat(),
                }
            )

        return OperationResult.ok({"evidence": data, "total": len(data), "limit": limit, "offset": offset})


def register(registry: OperationRegistry) -> None:
    registry.register("knowledge.planes.register", KnowledgePlanesRegisterHandler())
    registry.register("knowledge.planes.get", KnowledgePlanesGetHandler())
    registry.register("knowledge.planes.list", KnowledgePlanesListHandler())
    registry.register("knowledge.planes.transition", KnowledgePlanesTransitionHandler())
    registry.register("knowledge.planes.bind_policy", KnowledgePlanesBindPolicyHandler())
    registry.register("knowledge.planes.unbind_policy", KnowledgePlanesUnbindPolicyHandler())
    registry.register("knowledge.planes.approve_purge", KnowledgePlanesApprovePurgeHandler())
    registry.register("knowledge.evidence.get", KnowledgeEvidenceGetHandler())
    registry.register("knowledge.evidence.list", KnowledgeEvidenceListHandler())

    logger.info("knowledge planes handler registered")


__all__ = ["register"]
