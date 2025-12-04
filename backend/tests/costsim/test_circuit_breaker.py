# Tests for Sync Circuit Breaker
"""
Test suite for the sync DB-backed circuit breaker (legacy).

These tests cover the synchronous circuit breaker implementation.
For async tests, see test_circuit_breaker_async.py.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState dataclass."""

    def test_circuit_breaker_state_creation(self):
        """Test creating a circuit breaker state."""
        from app.costsim.circuit_breaker import CircuitBreakerState

        state = CircuitBreakerState(
            is_open=False,
            consecutive_failures=0,
        )

        assert state.is_open is False
        assert state.consecutive_failures == 0

    def test_circuit_breaker_state_to_dict(self):
        """Test CircuitBreakerState.to_dict method."""
        from app.costsim.circuit_breaker import CircuitBreakerState

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

    def test_incident_creation(self):
        """Test creating an incident."""
        from app.costsim.circuit_breaker import Incident

        now = datetime.now(timezone.utc)
        incident = Incident(
            id="inc_123",
            timestamp=now,
            reason="Drift exceeded",
            severity="P1",
            drift_score=0.35,
            sample_count=100,
        )

        assert incident.id == "inc_123"
        assert incident.reason == "Drift exceeded"
        assert incident.severity == "P1"
        assert incident.drift_score == 0.35
        assert incident.resolved is False

    def test_incident_to_dict(self):
        """Test Incident.to_dict method."""
        from app.costsim.circuit_breaker import Incident

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


class TestCircuitBreakerWithMock:
    """Tests using mocked database."""

    @pytest.mark.asyncio
    async def test_is_v2_disabled_returns_false_when_no_state(self):
        """Test is_v2_disabled returns False when no state exists."""
        with patch("app.costsim.circuit_breaker.get_circuit_breaker") as mock_get_cb:
            mock_cb = AsyncMock()
            mock_cb.is_disabled.return_value = False
            mock_get_cb.return_value = mock_cb

            from app.costsim.circuit_breaker import is_v2_disabled

            result = await is_v2_disabled()
            # Default behavior when no state exists should be False (V2 enabled)
            assert result is False

    def test_circuit_breaker_creation(self):
        """Test CircuitBreaker instantiation."""
        from app.costsim.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(
            failure_threshold=5,
            drift_threshold=0.15,
        )

        assert cb.failure_threshold == 5
        assert cb.drift_threshold == 0.15

    def test_get_circuit_breaker_singleton(self):
        """Test get_circuit_breaker returns singleton."""
        from app.costsim.circuit_breaker import get_circuit_breaker

        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker()

        assert cb1 is cb2


class TestCircuitBreakerConfig:
    """Tests for circuit breaker configuration."""

    def test_config_default_values(self):
        """Test default config values from get_config."""
        from app.costsim.config import get_config

        config = get_config()

        assert hasattr(config, "drift_threshold")
        assert hasattr(config, "failure_threshold")
        assert hasattr(config, "auto_recover_enabled")
        assert config.drift_threshold > 0
        assert config.failure_threshold > 0


# Note: Integration tests requiring live database are in tests/integration/test_circuit_breaker.py
# The following test scenarios are covered there:
# - disable_enable_cycle: TestCircuitBreakerState.test_disable_enables_circuit_breaker, test_enable_closes_circuit_breaker
# - drift_reporting_trips_breaker: TestDriftReporting.test_consecutive_failures_trip_breaker
# - auto_recovery_after_ttl: TestTTLAutoRecovery.test_auto_recovery_after_ttl
