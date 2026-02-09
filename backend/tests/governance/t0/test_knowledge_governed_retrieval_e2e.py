# Layer: L8 — Tests
# Product: system-wide
# Reference: KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md (P0 proof)
"""
End-to-end governance proof for governed retrieval.

This test is intentionally DB-backed and exercises the real runtime wiring:
- Knowledge plane is persisted (knowledge_plane_registry)
- Plane lifecycle is ACTIVE-gated (connector registry resolves only ACTIVE planes)
- Retrieval is deny-by-default, allowlisted via PolicySnapshot thresholds JSON
- Evidence is persisted (retrieval_evidence)

Skip behavior:
- If required tables are missing (database not migrated), the test is skipped.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

import pytest

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.db import Run
from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import KnowledgePlaneRegistryDriver
from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import RetrievalEvidenceDriver
from app.hoc.cus.hoc_spine.orchestrator.handlers import knowledge_planes_handler
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationContext, OperationRegistry
from app.hoc.cus.hoc_spine.services.knowledge_plane_connector_registry_engine import (
    DbKnowledgePlaneConnectorRegistry,
)
from app.hoc.cus.hoc_spine.services.retrieval_evidence_engine import DbRetrievalEvidenceService
from app.hoc.cus.hoc_spine.services.retrieval_mediator import MediationDeniedError, RetrievalMediator
from app.hoc.cus.hoc_spine.services.retrieval_policy_checker_engine import (
    DbPolicySnapshotPolicyChecker,
)
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
from app.models.policy_snapshot import PolicySnapshot
from app.models.tenant import Tenant


def _tables_exist() -> bool:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        return False
    try:
        import psycopg2

        required = [
            "tenants",
            "runs",
            "policy_snapshots",
            "knowledge_plane_registry",
            "retrieval_evidence",
        ]
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        for name in required:
            cur.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{name}",))
            if not cur.fetchone()[0]:
                cur.close()
                conn.close()
                return False
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


REQUIRED_TABLES_EXIST = _tables_exist()

requires_knowledge_tables = pytest.mark.skipif(
    not REQUIRED_TABLES_EXIST,
    reason="Required knowledge governance tables missing (migrate DB to include knowledge_plane_registry + retrieval_evidence).",
)


def _async_url(database_url: str) -> tuple[str, dict]:
    async_url = database_url
    if async_url.startswith("postgresql://"):
        async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    connect_args = {"ssl": "require"} if "sslmode=require" in database_url else {}
    return async_url, connect_args


@requires_knowledge_tables
@pytest.mark.asyncio
async def test_governed_retrieval_requires_active_plane_and_policy_allowlist():
    database_url = os.environ["DATABASE_URL"]
    async_url, connect_args = _async_url(database_url)

    engine = create_async_engine(async_url, pool_pre_ping=True, poolclass=NullPool, connect_args=connect_args)
    async with engine.connect() as connection:
        outer = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        await session.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def _restart_savepoint(sess, transaction):  # type: ignore[no-untyped-def]
            if transaction.nested and not transaction._parent.nested:
                sess.begin_nested()

        @asynccontextmanager
        async def session_provider():
            yield session

        try:
            # Seed tenant
            tenant_id = "tenant_e2e_knowledge"
            session.add(
                Tenant(
                    id=tenant_id,
                    name="E2E Tenant",
                    slug="e2e-tenant-knowledge",
                    status="active",
                )
            )
            await session.flush()

            # Register plane via L4 operation and keep it in DRAFT initially.
            registry = OperationRegistry()
            knowledge_planes_handler.register(registry)
            reg = await registry.execute(
                "knowledge.planes.register",
                OperationContext(
                    session=session,
                    tenant_id=tenant_id,
                    params={
                        "plane_type": "sql_gateway",
                        "plane_name": "e2e_sql_plane",
                        "connector_type": "sql_gateway",
                        "connector_id": "sqlgw_1",
                        "config": {
                            # Use the test DB as the governed "RAG" source via env ref.
                            "connection_string_ref": "env://DEV_DATABASE_URL",
                            "templates": {
                                "query": {
                                    "name": "Query",
                                    "description": "E2E query template",
                                    "sql": "SELECT 1 AS ok",
                                    "parameters": [],
                                    "read_only": True,
                                    "max_rows": 1,
                                    "timeout_seconds": 5,
                                }
                            },
                            "allowed_templates": ["query"],
                            "read_only": True,
                        },
                        "created_by": "test",
                    },
                ),
            )
            assert reg.success, reg.error
            plane_id = reg.data["plane_id"]

            # Create a policy snapshot that allowlists this plane_id.
            thresholds = {"knowledge_access": {"allowed_planes": [plane_id]}}
            snapshot = PolicySnapshot.create_snapshot(
                tenant_id=tenant_id,
                policies=[],
                thresholds=thresholds,
                policy_version="test",
            )
            session.add(snapshot)
            await session.flush()

            # Create a run that references the snapshot.
            run_id = "run_e2e_knowledge"
            session.add(
                Run(
                    id=run_id,
                    agent_id="agent_e2e",
                    goal="e2e governed retrieval",
                    tenant_id=tenant_id,
                    policy_snapshot_id=snapshot.snapshot_id,
                )
            )
            await session.flush()

            # Wire mediator with real DB-backed components but test-injected session provider.
            mediator = RetrievalMediator(
                policy_checker=DbPolicySnapshotPolicyChecker(session_provider=session_provider),
                connector_registry=DbKnowledgePlaneConnectorRegistry(
                    driver=KnowledgePlaneRegistryDriver(),
                    session_provider=session_provider,
                ),
                evidence_service=DbRetrievalEvidenceService(
                    driver=RetrievalEvidenceDriver(),
                    session_provider=session_provider,
                ),
            )

            # Negative: allowlist exists but plane is not ACTIVE yet -> no connector resolution.
            with pytest.raises(MediationDeniedError) as denied:
                await mediator.access(
                    tenant_id=tenant_id,
                    run_id=run_id,
                    plane_id=plane_id,
                    action="query",
                    payload={},
                    requesting_tenant_id=tenant_id,
                )
            assert "No connector found" in str(denied.value)

            # Bind a policy (activation gate) and transition to ACTIVE.
            bound = await registry.execute(
                "knowledge.planes.bind_policy",
                OperationContext(
                    session=session,
                    tenant_id=tenant_id,
                    params={"plane_id": plane_id, "policy_id": "policy_e2e"},
                ),
            )
            assert bound.success, bound.error

            # Progress through lifecycle to ACTIVE.
            for state in [
                KnowledgePlaneLifecycleState.PENDING_VERIFY,
                KnowledgePlaneLifecycleState.VERIFIED,
                KnowledgePlaneLifecycleState.INGESTING,
                KnowledgePlaneLifecycleState.INDEXED,
                KnowledgePlaneLifecycleState.CLASSIFIED,
                KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
                KnowledgePlaneLifecycleState.ACTIVE,
            ]:
                r = await registry.execute(
                    "knowledge.planes.transition",
                    OperationContext(
                        session=session,
                        tenant_id=tenant_id,
                        params={"plane_id": plane_id, "to_state": state.name},
                    ),
                )
                assert r.success, r.error

            # Positive: ACTIVE + policy allowlist -> access succeeds and evidence is persisted.
            result = await mediator.access(
                tenant_id=tenant_id,
                run_id=run_id,
                plane_id=plane_id,
                action="query",
                payload={},
                requesting_tenant_id=tenant_id,
            )
            assert result.success is True
            assert result.evidence_id not in ("unrecorded", "none", "")

            # Evidence row exists and is keyed by the governed plane_id.
            evidence_driver = RetrievalEvidenceDriver()
            rows = await evidence_driver.list(
                session,
                tenant_id=tenant_id,
                run_id=run_id,
                plane_id=plane_id,
                limit=10,
                offset=0,
            )
            assert len(rows) >= 1
            assert rows[0].plane_id == plane_id

            # Sanity: policy snapshot allowlist is what enabled access.
            thresholds_loaded = json.loads(snapshot.thresholds_json)
            assert plane_id in (thresholds_loaded.get("knowledge_access") or {}).get("allowed_planes", [])
        finally:
            await session.close()
            await outer.rollback()
            await engine.dispose()
