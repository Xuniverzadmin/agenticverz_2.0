# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci, manual
#   Execution: async
# Role: T4 Knowledge Plane Ops Tests (Persisted SSOT authority)
# Callers: pytest, CI
# Allowed Imports: L4 (hoc_spine handlers), L6 (models)
# Forbidden Imports: legacy in-memory lifecycle manager / SDK
# Reference: KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md, PIN-540

import os
import pytest

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import OperationContext, OperationRegistry
from app.hoc.cus.hoc_spine.orchestrator.handlers import knowledge_planes_handler
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState
from app.models.tenant import Tenant


def _check_kp_tables_exist() -> bool:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        return False
    try:
        import psycopg2

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("SELECT to_regclass('public.knowledge_plane_registry') IS NOT NULL")
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        return bool(exists)
    except Exception:
        return False


KP_TABLES_EXIST = _check_kp_tables_exist()

requires_kp_tables = pytest.mark.skipif(
    not KP_TABLES_EXIST,
    reason="knowledge_plane_registry table not created (run: DB_ROLE=staging alembic upgrade 122_knowledge_plane_registry)",
)


@pytest.fixture
def op_registry() -> OperationRegistry:
    registry = OperationRegistry()
    knowledge_planes_handler.register(registry)
    return registry


@pytest.fixture
def async_session_with_commit():
    """
    AsyncSession fixture that tolerates `session.commit()` inside code under test.

    Many hoc_spine L4 handlers own transaction boundaries and commit. The
    default `isolated_async_session` fixture intentionally discourages commit.
    This fixture uses a SAVEPOINT pattern so commits do not leak between tests.
    """
    from contextlib import asynccontextmanager

    from sqlalchemy import event

    @asynccontextmanager
    async def _get_session():
        database_url = os.environ.get("DATABASE_URL", "")
        if not database_url:
            pytest.skip("DATABASE_URL not configured")

        # Convert to asyncpg scheme for async engine creation.
        async_url = database_url
        if async_url.startswith("postgresql://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        needs_ssl = "sslmode=require" in database_url
        connect_args = {"ssl": "require"} if needs_ssl else {}

        engine = create_async_engine(async_url, pool_pre_ping=True, poolclass=NullPool, connect_args=connect_args)
        async with engine.connect() as connection:
            outer = await connection.begin()
            session = AsyncSession(bind=connection, expire_on_commit=False)
            await session.begin_nested()

            @event.listens_for(session.sync_session, "after_transaction_end")
            def _restart_savepoint(sess, transaction):  # type: ignore[no-untyped-def]
                if transaction.nested and not transaction._parent.nested:
                    sess.begin_nested()

            try:
                yield session
            finally:
                await session.close()
                await outer.rollback()
                await engine.dispose()

    return _get_session


async def _ensure_tenant(session: AsyncSession, tenant_id: str, status: str) -> None:
    tenant = Tenant(id=tenant_id, name="Test Tenant", slug=f"tenant-{tenant_id}", status=status)
    session.add(tenant)
    await session.flush()


async def _register_plane(
    registry: OperationRegistry,
    session: AsyncSession,
    tenant_id: str,
    *,
    plane_type: str = "sql",
    plane_name: str = "test_plane",
) -> str:
    result = await registry.execute(
        "knowledge.planes.register",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={
                "plane_type": plane_type,
                "plane_name": plane_name,
                "connector_type": plane_type,
                "connector_id": "connector_1",
                "config": {},
                "created_by": "test",
            },
        ),
    )
    assert result.success, result.error
    return result.data["plane_id"]


async def _transition(
    registry: OperationRegistry,
    session: AsyncSession,
    tenant_id: str,
    plane_id: str,
    *,
    to_state: KnowledgePlaneLifecycleState,
):
    return await registry.execute(
        "knowledge.planes.transition",
        OperationContext(
            session=session,
            tenant_id=tenant_id,
            params={"plane_id": plane_id, "to_state": to_state.name},
        ),
    )


@requires_kp_tables
@pytest.mark.asyncio
async def test_transition_requires_active_tenant(op_registry, async_session_with_commit):
    async with async_session_with_commit() as session:
        tenant_id = "tenant_kp_inactive"
        await _ensure_tenant(session, tenant_id, status="suspended")
        plane_id = await _register_plane(op_registry, session, tenant_id)

        result = await _transition(
            op_registry,
            session,
            tenant_id,
            plane_id,
            to_state=KnowledgePlaneLifecycleState.PENDING_VERIFY,
        )
        assert not result.success
        assert result.error_code == "TENANT_INACTIVE"


@requires_kp_tables
@pytest.mark.asyncio
async def test_activate_requires_bound_policy(op_registry, async_session_with_commit):
    async with async_session_with_commit() as session:
        tenant_id = "tenant_kp_gate"
        await _ensure_tenant(session, tenant_id, status="active")
        plane_id = await _register_plane(op_registry, session, tenant_id)

        # Progress through the happy path until PENDING_ACTIVATE.
        for state in [
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.INDEXED,
            KnowledgePlaneLifecycleState.CLASSIFIED,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        ]:
            r = await _transition(op_registry, session, tenant_id, plane_id, to_state=state)
            assert r.success, r.error

        denied = await _transition(op_registry, session, tenant_id, plane_id, to_state=KnowledgePlaneLifecycleState.ACTIVE)
        assert not denied.success
        assert denied.error_code == "POLICY_GATE_BLOCKED"

        bound = await op_registry.execute(
            "knowledge.planes.bind_policy",
            OperationContext(
                session=session,
                tenant_id=tenant_id,
                params={"plane_id": plane_id, "policy_id": "policy_1"},
            ),
        )
        assert bound.success, bound.error

        allowed = await _transition(op_registry, session, tenant_id, plane_id, to_state=KnowledgePlaneLifecycleState.ACTIVE)
        assert allowed.success, allowed.error


@requires_kp_tables
@pytest.mark.asyncio
async def test_purge_requires_approval(op_registry, async_session_with_commit):
    async with async_session_with_commit() as session:
        tenant_id = "tenant_kp_purge"
        await _ensure_tenant(session, tenant_id, status="active")
        plane_id = await _register_plane(op_registry, session, tenant_id)

        # Minimal progression to ARCHIVED:
        for state in [
            KnowledgePlaneLifecycleState.PENDING_VERIFY,
            KnowledgePlaneLifecycleState.VERIFIED,
            KnowledgePlaneLifecycleState.INGESTING,
            KnowledgePlaneLifecycleState.INDEXED,
            KnowledgePlaneLifecycleState.CLASSIFIED,
            KnowledgePlaneLifecycleState.PENDING_ACTIVATE,
        ]:
            r = await _transition(op_registry, session, tenant_id, plane_id, to_state=state)
            assert r.success, r.error

        # Activation requires bound policy (gate)
        bound = await op_registry.execute(
            "knowledge.planes.bind_policy",
            OperationContext(session=session, tenant_id=tenant_id, params={"plane_id": plane_id, "policy_id": "policy_1"}),
        )
        assert bound.success, bound.error
        r = await _transition(op_registry, session, tenant_id, plane_id, to_state=KnowledgePlaneLifecycleState.ACTIVE)
        assert r.success, r.error

        for state in [
            KnowledgePlaneLifecycleState.PENDING_DEACTIVATE,
            KnowledgePlaneLifecycleState.DEACTIVATED,
            KnowledgePlaneLifecycleState.ARCHIVED,
        ]:
            r = await _transition(op_registry, session, tenant_id, plane_id, to_state=state)
            assert r.success, r.error

        denied = await _transition(op_registry, session, tenant_id, plane_id, to_state=KnowledgePlaneLifecycleState.PURGED)
        assert not denied.success
        assert denied.error_code == "POLICY_GATE_PENDING"

        approved = await op_registry.execute(
            "knowledge.planes.approve_purge",
            OperationContext(session=session, tenant_id=tenant_id, params={"plane_id": plane_id}),
        )
        assert approved.success, approved.error

        allowed = await _transition(op_registry, session, tenant_id, plane_id, to_state=KnowledgePlaneLifecycleState.PURGED)
        assert allowed.success, allowed.error
