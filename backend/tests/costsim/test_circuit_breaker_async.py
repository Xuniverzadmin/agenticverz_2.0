# Tests for Async Circuit Breaker
"""
Test suite for the async DB-backed circuit breaker.

Requires PostgreSQL with the costsim_cb_state table.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip if dependencies not available
pytest.importorskip("asyncpg")


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestAsyncCircuitBreakerWithMock:
    """Tests using mocked database."""

    @pytest.mark.asyncio
    async def test_is_v2_disabled_returns_false_when_not_disabled(self):
        """Test that is_v2_disabled returns False when circuit is closed."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session:
            # Mock the session and result
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = None

            mock_sess_instance = AsyncMock()
            mock_sess_instance.execute.return_value = mock_result
            mock_sess_instance.close = AsyncMock()
            mock_session.return_value = mock_sess_instance

            from app.costsim.circuit_breaker_async import is_v2_disabled

            result = await is_v2_disabled()
            assert result is False

    @pytest.mark.asyncio
    async def test_is_v2_disabled_returns_true_when_disabled(self):
        """Test that is_v2_disabled returns True when circuit is open."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session:
            # Mock a disabled state
            mock_state = MagicMock()
            mock_state.disabled = True
            mock_state.disabled_until = None

            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_state

            mock_sess_instance = AsyncMock()
            mock_sess_instance.execute.return_value = mock_result
            mock_sess_instance.close = AsyncMock()
            mock_session.return_value = mock_sess_instance

            from app.costsim.circuit_breaker_async import is_v2_disabled

            result = await is_v2_disabled()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_v2_disabled_auto_recovers_on_ttl_expiry(self):
        """Test that circuit auto-recovers when TTL expires."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session:
            # Mock a disabled state with expired TTL
            mock_state = MagicMock()
            mock_state.id = 1
            mock_state.disabled = True
            mock_state.disabled_until = datetime.now(timezone.utc) - timedelta(hours=1)

            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_state

            mock_sess_instance = AsyncMock()
            mock_sess_instance.execute.return_value = mock_result
            mock_sess_instance.close = AsyncMock()
            mock_session.return_value = mock_sess_instance

            # Mock config
            with patch("app.costsim.circuit_breaker_async.get_config") as mock_config:
                mock_config.return_value.auto_recover_enabled = True

                # Mock _try_auto_recover to avoid full implementation
                with patch(
                    "app.costsim.circuit_breaker_async._try_auto_recover", new_callable=AsyncMock
                ) as mock_recover:
                    mock_recover.return_value = True  # Indicates successful recovery
                    from app.costsim.circuit_breaker_async import is_v2_disabled

                    result = await is_v2_disabled()
                    # After auto-recover, should return False
                    assert result is False
                    mock_recover.assert_called_once_with(mock_state.id)

    @pytest.mark.asyncio
    async def test_report_drift_increments_consecutive_failures(self):
        """Test that report_drift increments failure count on high drift."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session_local:
            # Mock state with 0 failures
            mock_state = MagicMock()
            mock_state.disabled = False
            mock_state.consecutive_failures = 0

            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_state

            # Create proper async context manager for session.begin()
            mock_begin_cm = MagicMock()
            mock_begin_cm.__aenter__ = AsyncMock(return_value=None)
            mock_begin_cm.__aexit__ = AsyncMock(return_value=None)

            # Create session instance that will be returned from context manager
            mock_sess_instance = MagicMock()
            mock_sess_instance.execute = AsyncMock(return_value=mock_result)
            mock_sess_instance.begin = MagicMock(return_value=mock_begin_cm)
            mock_sess_instance.close = AsyncMock()

            # AsyncSessionLocal() returns an async context manager
            mock_outer_cm = MagicMock()
            mock_outer_cm.__aenter__ = AsyncMock(return_value=mock_sess_instance)
            mock_outer_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_outer_cm

            # Mock config with low threshold
            with patch("app.costsim.circuit_breaker_async.get_config") as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.drift_threshold = 0.1
                mock_cfg.failure_threshold = 3
                mock_config.return_value = mock_cfg

                from app.costsim.circuit_breaker_async import report_drift

                # High drift should increment failures
                result = await report_drift(drift_score=0.5, sample_count=1)

                # Should not trip yet (only 1 failure, need 3)
                assert result is None
                assert mock_state.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_disable_v2_creates_incident(self):
        """Test that disable_v2 creates an incident record."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session_local:
            mock_state = MagicMock()
            mock_state.disabled = False

            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_state

            # Create proper async context manager for session.begin()
            mock_begin_cm = MagicMock()
            mock_begin_cm.__aenter__ = AsyncMock(return_value=None)
            mock_begin_cm.__aexit__ = AsyncMock(return_value=None)

            # Create session instance that will be returned from context manager
            mock_sess_instance = MagicMock()
            mock_sess_instance.execute = AsyncMock(return_value=mock_result)
            mock_sess_instance.begin = MagicMock(return_value=mock_begin_cm)
            mock_sess_instance.add = MagicMock()
            mock_sess_instance.flush = AsyncMock()
            mock_sess_instance.close = AsyncMock()

            # AsyncSessionLocal() returns an async context manager
            mock_outer_cm = MagicMock()
            mock_outer_cm.__aenter__ = AsyncMock(return_value=mock_sess_instance)
            mock_outer_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_outer_cm

            with patch("app.costsim.circuit_breaker_async.get_config") as mock_config:
                mock_cfg = MagicMock()
                mock_cfg.default_disable_ttl_hours = 24
                mock_cfg.instance_id = "test-instance"
                mock_config.return_value = mock_cfg

                with patch("app.costsim.circuit_breaker_async._enqueue_alert", new_callable=AsyncMock):
                    from app.costsim.circuit_breaker_async import disable_v2

                    changed, incident = await disable_v2(
                        reason="Test disable",
                        disabled_by="test-user",
                    )

                    assert changed is True
                    assert incident is not None
                    assert incident.reason == "Test disable"
                    assert mock_state.disabled is True

    @pytest.mark.asyncio
    async def test_enable_v2_resolves_incident(self):
        """Test that enable_v2 resolves the incident and resets state."""
        with patch("app.costsim.circuit_breaker_async.AsyncSessionLocal") as mock_session_local:
            mock_state = MagicMock()
            mock_state.disabled = True
            mock_state.incident_id = "inc_123"
            mock_state.disabled_reason = "Test"

            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = mock_state

            # Create proper async context manager for session.begin()
            mock_begin_cm = MagicMock()
            mock_begin_cm.__aenter__ = AsyncMock(return_value=None)
            mock_begin_cm.__aexit__ = AsyncMock(return_value=None)

            # Create session instance that will be returned from context manager
            mock_sess_instance = MagicMock()
            mock_sess_instance.execute = AsyncMock(return_value=mock_result)
            mock_sess_instance.begin = MagicMock(return_value=mock_begin_cm)
            mock_sess_instance.close = AsyncMock()

            # AsyncSessionLocal() returns an async context manager
            mock_outer_cm = MagicMock()
            mock_outer_cm.__aenter__ = AsyncMock(return_value=mock_sess_instance)
            mock_outer_cm.__aexit__ = AsyncMock(return_value=None)
            mock_session_local.return_value = mock_outer_cm

            with patch("app.costsim.circuit_breaker_async._resolve_incident", new_callable=AsyncMock):
                with patch("app.costsim.circuit_breaker_async._enqueue_alert", new_callable=AsyncMock):
                    from app.costsim.circuit_breaker_async import enable_v2

                    result = await enable_v2(
                        enabled_by="test-admin",
                        reason="Test recovery",
                    )

                    assert result is True
                    assert mock_state.disabled is False
                    assert mock_state.incident_id is None


class TestAsyncCircuitBreakerClass:
    """Tests for the AsyncCircuitBreaker wrapper class."""

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_is_disabled(self):
        """Test AsyncCircuitBreaker.is_disabled method."""
        with patch("app.costsim.circuit_breaker_async.is_v2_disabled", new_callable=AsyncMock) as mock:
            mock.return_value = False

            from app.costsim.circuit_breaker_async import AsyncCircuitBreaker

            cb = AsyncCircuitBreaker()
            result = await cb.is_disabled()

            assert result is False
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_circuit_breaker_get_state(self):
        """Test AsyncCircuitBreaker.get_state method."""
        with patch("app.costsim.circuit_breaker_async.get_state", new_callable=AsyncMock) as mock:
            from app.costsim.circuit_breaker_async import CircuitBreakerState

            mock.return_value = CircuitBreakerState(
                is_open=False,
                consecutive_failures=0,
            )

            from app.costsim.circuit_breaker_async import AsyncCircuitBreaker

            cb = AsyncCircuitBreaker()
            state = await cb.get_state()

            assert state.is_open is False
            assert state.consecutive_failures == 0


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState dataclass."""

    def test_state_to_dict(self):
        """Test CircuitBreakerState.to_dict method."""
        from app.costsim.circuit_breaker_async import CircuitBreakerState

        now = datetime.now(timezone.utc)
        state = CircuitBreakerState(
            is_open=True,
            opened_at=now,
            reason="Test reason",
            incident_id="inc_123",
            consecutive_failures=5,
        )

        d = state.to_dict()

        assert d["is_open"] is True
        assert d["reason"] == "Test reason"
        assert d["incident_id"] == "inc_123"
        assert d["consecutive_failures"] == 5


class TestIncident:
    """Tests for Incident dataclass."""

    def test_incident_to_dict(self):
        """Test Incident.to_dict method."""
        from app.costsim.circuit_breaker_async import Incident

        now = datetime.now(timezone.utc)
        incident = Incident(
            id="inc_123",
            timestamp=now,
            reason="Drift exceeded",
            severity="P1",
            drift_score=0.35,
            sample_count=100,
            details={"test": "data"},
        )

        d = incident.to_dict()

        assert d["id"] == "inc_123"
        assert d["reason"] == "Drift exceeded"
        assert d["severity"] == "P1"
        assert d["drift_score"] == 0.35
        assert d["sample_count"] == 100
        assert d["details"] == {"test": "data"}
        assert d["resolved"] is False
