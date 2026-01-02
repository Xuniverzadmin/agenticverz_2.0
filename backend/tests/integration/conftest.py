"""
Integration test fixtures for AOS.

Provides:
- Database session management
- Alertmanager mocking (auto-applied to all async tests)
- Circuit breaker state cleanup
"""

from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ========== Alertmanager Mock ==========


class AlertmanagerMock:
    """
    Mock Alertmanager server that captures all alert payloads.

    Usage:
        def test_something(alertmanager_mock):
            # ... trigger some alerts ...
            assert alertmanager_mock.call_count == 1
            alert = alertmanager_mock.alerts[0]
            assert alert['labels']['alertname'] == 'CostSimV2Disabled'
    """

    def __init__(self):
        self.alerts: list[dict[str, Any]] = []
        self.call_count: int = 0
        self._mock_client = None
        self._patcher = None

    def start(self):
        """Start mocking httpx.AsyncClient for Alertmanager calls."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        async def capture_post(url, json=None, headers=None, **kwargs):
            self.call_count += 1
            if json:
                # json is a list of alerts
                for alert in json:
                    self.alerts.append(alert)
            return mock_response

        mock_instance = AsyncMock()
        mock_instance.post = capture_post
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)

        self._mock_client = MagicMock(return_value=mock_instance)
        self._patcher = patch("app.costsim.circuit_breaker.httpx.AsyncClient", self._mock_client)
        self._patcher.start()

        return self

    def stop(self):
        """Stop mocking."""
        if self._patcher:
            self._patcher.stop()

    def reset(self):
        """Reset captured alerts."""
        self.alerts = []
        self.call_count = 0

    def get_alert_by_name(self, alertname: str) -> dict | None:
        """Get first alert matching the given alertname."""
        for alert in self.alerts:
            if alert.get("labels", {}).get("alertname") == alertname:
                return alert
        return None

    def assert_alert_sent(self, alertname: str, count: int = 1):
        """Assert that an alert with the given name was sent."""
        matching = [a for a in self.alerts if a.get("labels", {}).get("alertname") == alertname]
        assert len(matching) >= count, f"Expected {count} alert(s) with name '{alertname}', found {len(matching)}"


@pytest.fixture
def alertmanager_mock() -> Generator[AlertmanagerMock, None, None]:
    """
    Fixture that mocks Alertmanager HTTP calls and captures payloads.

    This is NOT auto-applied; use it explicitly when you need to inspect alerts.
    """
    mock = AlertmanagerMock()
    mock.start()
    yield mock
    mock.stop()


@pytest.fixture(autouse=True)
def auto_mock_alertmanager():
    """
    Auto-applied fixture that silences Alertmanager HTTP calls.

    This prevents real HTTP calls to Alertmanager during tests.
    If you need to inspect alert payloads, use the `alertmanager_mock` fixture instead.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=None)

    mock_client = MagicMock(return_value=mock_instance)

    with patch("app.costsim.circuit_breaker.httpx.AsyncClient", mock_client):
        yield


# ========== Database Fixtures (PIN-276 Bucket A) ==========
# Transaction rollback per test ensures zero state bleed.


def _reset_db_engines():
    """
    Reset all database engine singletons and dispose connections.

    This is critical for preventing pool exhaustion during test runs.
    PIN-276: Test isolation requires complete engine cleanup.
    """
    import app.db as db_module

    # Dispose sync engine
    if db_module._engine is not None:
        try:
            db_module._engine.dispose()
        except Exception:
            pass
        db_module._engine = None

    # Dispose async engine
    if db_module._async_engine is not None:
        try:
            # For async engine, we need to run dispose in an event loop
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Can't await in sync context, just nullify
                pass
            else:
                # No running loop, safe to create one for cleanup
                try:
                    asyncio.run(db_module._async_engine.dispose())
                except Exception:
                    pass
        except Exception:
            pass
        db_module._async_engine = None

    # Reset async session factory
    db_module._async_session_local = None

    # Also reset db_async module if it exists
    try:
        import app.db_async as db_async_module

        if hasattr(db_async_module, "async_engine") and db_async_module.async_engine is not None:
            try:
                import asyncio

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is None or not loop.is_running():
                    asyncio.run(db_async_module.async_engine.dispose())
            except Exception:
                pass
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def cleanup_db_connections():
    """
    Ensure DB connections are properly cleaned up after each test.

    This fixes hanging tests caused by SELECT FOR UPDATE locks not being
    released properly between tests. The engine.dispose() forces all
    connections back to the pool and releases any lingering locks.

    Phase-2.1: DB session lifecycle fix (PIN-264)
    PIN-276: Enhanced to reset engine singletons and prevent pool exhaustion.
    """
    yield
    # After each test, dispose all connections and reset engines
    _reset_db_engines()


@pytest.fixture
def db_session():
    """
    Database session with automatic rollback - NEVER commits to DB.

    PIN-276 Bucket A: Transaction rollback per test.

    INVARIANT: Any DB changes made during the test are automatically rolled back.
    This ensures tests cannot affect each other through database state.

    Note: Use flush() instead of commit() during tests.
    """
    from sqlmodel import Session

    from app.db import get_engine

    engine = get_engine()

    # Begin a transaction
    connection = engine.connect()
    transaction = connection.begin()

    # Create session bound to this transaction
    session = Session(bind=connection)

    try:
        yield session
    finally:
        # ALWAYS rollback - this is the key to isolation
        session.close()
        transaction.rollback()
        connection.close()


# ========== Circuit Breaker Fixtures ==========


@pytest.fixture
def clean_circuit_breaker_state(db_session):
    """Reset circuit breaker state before and after each test."""
    from sqlmodel import select

    from app.costsim.circuit_breaker import CB_NAME
    from app.db import CostSimCBIncident, CostSimCBState

    def cleanup():
        # Delete existing state
        statement = select(CostSimCBState).where(CostSimCBState.name == CB_NAME)
        result = db_session.exec(statement)
        state = result.first()
        if state:
            db_session.delete(state)
            db_session.commit()

        # Delete existing incidents
        statement = select(CostSimCBIncident).where(CostSimCBIncident.circuit_breaker_name == CB_NAME)
        for incident in db_session.exec(statement):
            db_session.delete(incident)
        db_session.commit()

    # Cleanup before test
    cleanup()

    yield

    # Cleanup after test
    cleanup()
