# Layer: TEST
# Role: MCP test fixtures
# Reference: PIN-516
"""MCP Test Fixtures

Provides fixtures for MCP integration tests.
"""

import pytest


@pytest.fixture
def mcp_tables_required(isolated_async_session):
    """Fixture that skips test if MCP tables don't exist.

    Usage:
        @pytest.mark.asyncio
        async def test_something(mcp_tables_required, isolated_async_session):
            async with isolated_async_session() as session:
                ...
    """
    import asyncio

    async def check_tables():
        async with isolated_async_session() as session:
            try:
                from sqlalchemy import text
                await session.execute(text("SELECT 1 FROM mcp_servers LIMIT 0"))
                return True
            except Exception:
                return False

    # Check if tables exist
    loop = asyncio.get_event_loop()
    tables_exist = loop.run_until_complete(check_tables())

    if not tables_exist:
        pytest.skip("MCP tables not created (run: alembic upgrade 119_w2_mcp_servers)")

    return True


# Alternative: Use a marker
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_mcp_tables: mark test as requiring MCP database tables"
    )
