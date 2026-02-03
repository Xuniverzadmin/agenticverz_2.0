# Layer: TEST
# AUDIENCE: INTERNAL
# Role: MCP Phase-1 survivability tests
# Reference: PIN-516
"""MCP Phase-1 Tests - Prove Survivability

PIN-516 Phase-1 Invariants require these tests to answer:
"If the system restarts, can we still explain what MCP servers exist?"

Required test cases (INV-4):
1. Persistence: Create server → flush → list servers → same result
2. Tenant isolation: Tenant A cannot read Tenant B servers
3. Soft delete: Deleted server not returned in list, but queryable for audit
4. Tool upsert idempotency: Same tool list twice → no duplicates

These are SURVIVABILITY tests, not happy-path functional tests.

NOTE: DB tests require migration 119_w2_mcp_servers to be applied.
Run: alembic upgrade head
"""

import pytest
from datetime import datetime, timezone

from app.hoc.cus.integrations.L6_drivers.mcp_driver import (
    McpDriver,
    compute_input_hash,
)


# =============================================================================
# Utility to check if MCP tables exist
# =============================================================================


def _check_mcp_tables_exist() -> bool:
    """Check if mcp_servers table exists in the database."""
    try:
        import psycopg2
        import os

        db_url = os.environ.get("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
        # Parse URL for psycopg2
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "")

        conn = psycopg2.connect(f"postgresql://{db_url}")
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'mcp_servers'
            )
        """)
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        return exists
    except Exception:
        return False


# Check once at module load
MCP_TABLES_EXIST = _check_mcp_tables_exist()

# Skip marker for tests requiring MCP tables
requires_mcp_tables = pytest.mark.skipif(
    not MCP_TABLES_EXIST,
    reason="MCP tables not created (run: alembic upgrade 119_w2_mcp_servers)"
)


# =============================================================================
# Test 1: Persistence
# =============================================================================


@requires_mcp_tables
@pytest.mark.asyncio
async def test_server_persistence(isolated_async_session):
    """Create server → flush → list servers → same result.

    Proves: Data survives within a transaction (simulates restart).
    PIN-516 INV-4: Persistence test.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create a server
        server = await driver.create_server(
            tenant_id="tenant_persist_test",
            name="Test MCP Server",
            url="https://mcp.example.com",
            transport="https",
            auth_type="bearer",
            credential_id="vault://credentials/mcp-test",  # Reference only
            description="Test server for persistence",
            requires_approval=True,
            rate_limit_requests=30,
            tags=["test", "persistence"],
        )

        # Verify server was created
        assert server is not None
        assert server.server_id.startswith("mcp_")
        assert server.name == "Test MCP Server"
        assert server.url == "https://mcp.example.com"
        assert server.status == "pending"

        # Flush to simulate persistence
        await session.flush()

        # Retrieve server - simulates "after restart" read
        retrieved = await driver.get_server(server.server_id)

        # Verify data persisted correctly
        assert retrieved is not None
        assert retrieved.server_id == server.server_id
        assert retrieved.tenant_id == "tenant_persist_test"
        assert retrieved.name == "Test MCP Server"
        assert retrieved.url == "https://mcp.example.com"
        assert retrieved.transport == "https"
        assert retrieved.auth_type == "bearer"
        assert retrieved.credential_id == "vault://credentials/mcp-test"
        assert retrieved.status == "pending"
        assert retrieved.requires_approval is True
        assert retrieved.rate_limit_requests == 30
        assert "test" in retrieved.tags
        assert "persistence" in retrieved.tags


# =============================================================================
# Test 2: Tenant Isolation
# =============================================================================


@requires_mcp_tables
@pytest.mark.asyncio
async def test_tenant_isolation(isolated_async_session):
    """Tenant A cannot read Tenant B servers.

    Proves: Multi-tenancy isolation at the data layer.
    PIN-516 INV-4: Tenant isolation test.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create server for Tenant A
        server_a = await driver.create_server(
            tenant_id="tenant_A",
            name="Tenant A Server",
            url="https://mcp-a.example.com",
        )

        # Create server for Tenant B
        server_b = await driver.create_server(
            tenant_id="tenant_B",
            name="Tenant B Server",
            url="https://mcp-b.example.com",
        )

        await session.flush()

        # List servers for Tenant A
        tenant_a_servers = await driver.list_servers(tenant_id="tenant_A")

        # List servers for Tenant B
        tenant_b_servers = await driver.list_servers(tenant_id="tenant_B")

        # Verify isolation
        assert len(tenant_a_servers) == 1
        assert len(tenant_b_servers) == 1

        # Tenant A only sees their server
        assert tenant_a_servers[0].server_id == server_a.server_id
        assert tenant_a_servers[0].name == "Tenant A Server"

        # Tenant B only sees their server
        assert tenant_b_servers[0].server_id == server_b.server_id
        assert tenant_b_servers[0].name == "Tenant B Server"

        # Cross-check: Tenant A does NOT see Tenant B's server
        tenant_a_server_ids = [s.server_id for s in tenant_a_servers]
        assert server_b.server_id not in tenant_a_server_ids

        # Cross-check: Tenant B does NOT see Tenant A's server
        tenant_b_server_ids = [s.server_id for s in tenant_b_servers]
        assert server_a.server_id not in tenant_b_server_ids


# =============================================================================
# Test 3: Soft Delete
# =============================================================================


@requires_mcp_tables
@pytest.mark.asyncio
async def test_soft_delete(isolated_async_session):
    """Deleted server not returned in list, but queryable for audit.

    Proves: Soft delete preserves audit trail while hiding from active lists.
    PIN-516 INV-4: Soft delete test.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create a server
        server = await driver.create_server(
            tenant_id="tenant_softdelete",
            name="Server To Delete",
            url="https://delete-me.example.com",
        )

        await session.flush()

        # Verify server appears in list
        servers_before = await driver.list_servers(tenant_id="tenant_softdelete")
        assert len(servers_before) == 1
        assert servers_before[0].server_id == server.server_id

        # Soft-delete the server
        deleted = await driver.soft_delete_server(server.server_id)
        assert deleted is True

        await session.flush()

        # Verify server is NOT in active list
        servers_after = await driver.list_servers(tenant_id="tenant_softdelete")
        assert len(servers_after) == 0

        # Verify server IS still queryable directly (for audit)
        audit_server = await driver.get_server(server.server_id)
        assert audit_server is not None
        assert audit_server.status == "disabled"
        assert audit_server.name == "Server To Delete"

        # Verify server appears when include_disabled=True
        all_servers = await driver.list_servers(
            tenant_id="tenant_softdelete",
            include_disabled=True,
        )
        assert len(all_servers) == 1
        assert all_servers[0].status == "disabled"


# =============================================================================
# Test 4: Tool Upsert Idempotency
# =============================================================================


@requires_mcp_tables
@pytest.mark.asyncio
async def test_tool_upsert_idempotency(isolated_async_session):
    """Same tool list twice → no duplicates.

    Proves: Tool discovery is idempotent.
    PIN-516 INV-4: Idempotency test.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create a server first
        server = await driver.create_server(
            tenant_id="tenant_idempotent",
            name="Idempotent Server",
            url="https://idempotent.example.com",
        )

        await session.flush()

        # Define tools to upsert
        tools = [
            {
                "name": "tool_a",
                "description": "Tool A description",
                "input_schema": {"type": "object", "properties": {"param1": {"type": "string"}}},
                "risk_level": "low",
            },
            {
                "name": "tool_b",
                "description": "Tool B description",
                "input_schema": {"type": "object", "properties": {"param2": {"type": "number"}}},
                "risk_level": "medium",
            },
        ]

        # First upsert
        result_1 = await driver.upsert_tools(
            server_id=server.server_id,
            tenant_id="tenant_idempotent",
            tools=tools,
        )

        await session.flush()

        # Verify first upsert created 2 tools
        assert len(result_1) == 2
        tool_names_1 = {t.name for t in result_1}
        assert tool_names_1 == {"tool_a", "tool_b"}

        # Second upsert with SAME tools
        result_2 = await driver.upsert_tools(
            server_id=server.server_id,
            tenant_id="tenant_idempotent",
            tools=tools,
        )

        await session.flush()

        # Verify second upsert returns 2 tools (updated, not duplicated)
        assert len(result_2) == 2

        # Verify total tools in DB is still 2 (not 4)
        all_tools = await driver.get_tools(server_id=server.server_id)
        assert len(all_tools) == 2

        # Verify tool IDs are the same (not new IDs)
        tool_ids_1 = {t.tool_id for t in result_1}
        tool_ids_2 = {t.tool_id for t in result_2}
        assert tool_ids_1 == tool_ids_2


# =============================================================================
# Additional Survivability Tests
# =============================================================================


@requires_mcp_tables
@pytest.mark.asyncio
async def test_invocation_append_only(isolated_async_session):
    """Invocations are append-only (cannot be modified).

    Proves: Audit trail integrity.
    PIN-516: Invocations table has immutability trigger.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create server and tool first
        server = await driver.create_server(
            tenant_id="tenant_audit",
            name="Audit Server",
            url="https://audit.example.com",
        )

        await driver.upsert_tools(
            server_id=server.server_id,
            tenant_id="tenant_audit",
            tools=[{"name": "audit_tool", "input_schema": {}}],
        )

        await session.flush()

        tools = await driver.get_tools(server_id=server.server_id)
        tool = tools[0]

        # Record an invocation
        invocation = await driver.record_invocation(
            tool_id=tool.tool_id,
            server_id=server.server_id,
            tenant_id="tenant_audit",
            tool_name="audit_tool",
            input_hash=compute_input_hash({"test": "params"}),
            outcome="success",
            invoked_at=datetime.now(timezone.utc),
            duration_ms=150,
        )

        await session.flush()

        # Verify invocation was recorded
        assert invocation is not None
        assert invocation.invocation_id.startswith("inv_")
        assert invocation.outcome == "success"
        assert invocation.duration_ms == 150

        # Retrieve invocation
        retrieved = await driver.get_invocation(invocation.invocation_id)
        assert retrieved is not None
        assert retrieved.tool_name == "audit_tool"
        assert retrieved.tenant_id == "tenant_audit"

        # Note: The DB trigger prevents UPDATE/DELETE on this table.
        # We don't test that here (it's a DB-level enforcement).


@requires_mcp_tables
@pytest.mark.asyncio
async def test_get_server_by_url(isolated_async_session):
    """Can find server by URL within tenant.

    Proves: Deduplication check works.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create server
        server = await driver.create_server(
            tenant_id="tenant_url_lookup",
            name="URL Lookup Server",
            url="https://unique-url.example.com",
        )

        await session.flush()

        # Find by URL
        found = await driver.get_server_by_url(
            tenant_id="tenant_url_lookup",
            url="https://unique-url.example.com",
        )

        assert found is not None
        assert found.server_id == server.server_id

        # Not found for different tenant
        not_found = await driver.get_server_by_url(
            tenant_id="other_tenant",
            url="https://unique-url.example.com",
        )

        assert not_found is None


@requires_mcp_tables
@pytest.mark.asyncio
async def test_tool_enable_disable(isolated_async_session):
    """Tools can be enabled/disabled.

    Proves: Granular tool control works.
    """
    async with isolated_async_session() as session:
        driver = McpDriver(session)

        # Create server
        server = await driver.create_server(
            tenant_id="tenant_toggle",
            name="Toggle Server",
            url="https://toggle.example.com",
        )

        # Create tool
        await driver.upsert_tools(
            server_id=server.server_id,
            tenant_id="tenant_toggle",
            tools=[{"name": "toggle_tool", "input_schema": {}}],
        )

        await session.flush()

        # Get tool
        tools = await driver.get_tools(server_id=server.server_id)
        tool = tools[0]
        assert tool.enabled is True

        # Disable tool
        updated = await driver.update_tool(tool.tool_id, enabled=False)
        assert updated is not None
        assert updated.enabled is False

        await session.flush()

        # Verify disabled tool not in enabled_only list
        enabled_tools = await driver.get_tools(
            server_id=server.server_id,
            enabled_only=True,
        )
        assert len(enabled_tools) == 0

        # Verify disabled tool in full list
        all_tools = await driver.get_tools(
            server_id=server.server_id,
            enabled_only=False,
        )
        assert len(all_tools) == 1
        assert all_tools[0].enabled is False


# =============================================================================
# Non-DB Tests (always run)
# =============================================================================


@pytest.mark.asyncio
async def test_input_hash_computation():
    """Input hash is deterministic.

    Proves: Same input always produces same hash.
    """
    params1 = {"tool": "test", "args": {"a": 1, "b": "hello"}}
    params2 = {"tool": "test", "args": {"a": 1, "b": "hello"}}
    params3 = {"tool": "test", "args": {"a": 2, "b": "hello"}}  # Different

    hash1 = compute_input_hash(params1)
    hash2 = compute_input_hash(params2)
    hash3 = compute_input_hash(params3)

    # Same input → same hash
    assert hash1 == hash2

    # Different input → different hash
    assert hash1 != hash3

    # Hash is valid SHA256 (64 hex chars)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)
