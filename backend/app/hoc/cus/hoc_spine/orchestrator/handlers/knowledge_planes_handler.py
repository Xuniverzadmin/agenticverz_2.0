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
- knowledge.evidence.get
- knowledge.evidence.list

Note: Lifecycle transitions and retrieval mediation rewiring are Phase 4+.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)

logger = logging.getLogger("nova.hoc_spine.knowledge_planes_handler")


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
            await ctx.session.commit()
        except Exception as e:
            await ctx.session.rollback()
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
    registry.register("knowledge.evidence.get", KnowledgeEvidenceGetHandler())
    registry.register("knowledge.evidence.list", KnowledgeEvidenceListHandler())

    logger.info("knowledge planes handler registered")


__all__ = ["register"]

