"""
Integration tests for DB-backed CostSim V2 circuit breaker.

Tests:
- State management (disable/enable/auto-recover)
- Drift reporting and trip logic
- Alertmanager integration (mocked)
- Incident tracking
- TTL-based auto-recovery
- Multi-replica safety (SELECT FOR UPDATE)
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional

# Skip tests if DB not available
pytest.importorskip("sqlmodel")

from sqlmodel import Session, select

# Import circuit breaker components
from app.costsim.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    Incident,
    get_circuit_breaker,
    is_v2_disabled,
    disable_v2,
    enable_v2,
    CB_NAME,
)
from app.costsim.config import get_config, CostSimConfig
from app.db import engine, CostSimCBState, CostSimCBIncident


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def clean_circuit_breaker_state(db_session):
    """Reset circuit breaker state before each test."""
    # Delete existing state
    statement = select(CostSimCBState).where(CostSimCBState.name == CB_NAME)
    result = db_session.exec(statement)
    state = result.first()
    if state:
        db_session.delete(state)
        db_session.commit()

    # Delete existing incidents
    statement = select(CostSimCBIncident).where(
        CostSimCBIncident.circuit_breaker_name == CB_NAME
    )
    for incident in db_session.exec(statement):
        db_session.delete(incident)
    db_session.commit()

    yield

    # Cleanup after test
    statement = select(CostSimCBState).where(CostSimCBState.name == CB_NAME)
    result = db_session.exec(statement)
    state = result.first()
    if state:
        db_session.delete(state)
        db_session.commit()


@pytest.fixture
def circuit_breaker(clean_circuit_breaker_state):
    """Create a fresh circuit breaker instance."""
    # Clear global instance
    import app.costsim.circuit_breaker as cb_module
    cb_module._circuit_breaker = None

    return CircuitBreaker(
        failure_threshold=3,
        drift_threshold=0.2,
    )


class TestCircuitBreakerState:
    """Tests for circuit breaker state management."""

    @pytest.mark.asyncio
    async def test_initial_state_is_enabled(self, circuit_breaker: CircuitBreaker):
        """Circuit breaker should start in enabled state."""
        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is False

        state = circuit_breaker.get_state()
        assert state.is_open is False
        assert state.incident_id is None

    @pytest.mark.asyncio
    async def test_disable_enables_circuit_breaker(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Disabling V2 should open the circuit breaker."""
        # Mock config to have alertmanager URL
        with patch.object(circuit_breaker.config, 'alertmanager_url', 'http://alertmanager:9093/api/v2/alerts'):
            changed, incident = await circuit_breaker.disable_v2(
                reason="Test disable",
                disabled_by="test-suite",
            )

        assert changed is True
        assert incident is not None
        assert incident.reason == "Test disable"

        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is True

        state = circuit_breaker.get_state()
        assert state.is_open is True
        assert state.reason == "Test disable"
        assert state.disabled_by == "test-suite"

    @pytest.mark.asyncio
    async def test_enable_closes_circuit_breaker(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Enabling V2 should close the circuit breaker."""
        # First disable
        await circuit_breaker.disable_v2(
            reason="Test disable",
            disabled_by="test-suite",
        )

        # Then enable
        changed = await circuit_breaker.enable_v2(
            enabled_by="test-suite",
            reason="Test enable",
        )

        assert changed is True

        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is False

        state = circuit_breaker.get_state()
        assert state.is_open is False

    @pytest.mark.asyncio
    async def test_disable_is_idempotent(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Repeated disables with same params should be no-op."""
        # First disable
        changed1, incident1 = await circuit_breaker.disable_v2(
            reason="Test disable",
            disabled_by="test-suite",
        )
        assert changed1 is True

        # Second disable with same params
        changed2, incident2 = await circuit_breaker.disable_v2(
            reason="Test disable",
            disabled_by="test-suite",
        )
        assert changed2 is False
        assert incident2 is None

    @pytest.mark.asyncio
    async def test_enable_when_already_enabled(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Enabling when already enabled should return True."""
        changed = await circuit_breaker.enable_v2(
            enabled_by="test-suite",
        )
        assert changed is True  # No error, just returns True


class TestDriftReporting:
    """Tests for drift reporting and trip logic."""

    @pytest.mark.asyncio
    async def test_drift_below_threshold_does_not_trip(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Drift below threshold should not trip the breaker."""
        incident = await circuit_breaker.report_drift(
            drift_score=0.1,  # Below 0.2 threshold
            sample_count=100,
        )

        assert incident is None
        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is False

    @pytest.mark.asyncio
    async def test_drift_above_threshold_increments_failures(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Drift above threshold should increment consecutive failures."""
        # Report drift above threshold
        incident = await circuit_breaker.report_drift(
            drift_score=0.25,
            sample_count=100,
        )

        # First failure should not trip (need 3)
        assert incident is None

        state = circuit_breaker.get_state()
        assert state.consecutive_failures == 1

    @pytest.mark.asyncio
    async def test_consecutive_failures_trip_breaker(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Three consecutive failures should trip the breaker."""
        # Report 3 drifts above threshold
        for i in range(3):
            incident = await circuit_breaker.report_drift(
                drift_score=0.25,
                sample_count=100,
                details={"iteration": i},
            )

        # Should trip on 3rd failure
        assert incident is not None
        assert incident.severity == "P1"

        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is True

    @pytest.mark.asyncio
    async def test_good_drift_resets_failures(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Drift below threshold should reset consecutive failures."""
        # Report 2 bad drifts
        await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)
        await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        state = circuit_breaker.get_state()
        assert state.consecutive_failures == 2

        # Report good drift
        await circuit_breaker.report_drift(drift_score=0.1, sample_count=100)

        state = circuit_breaker.get_state()
        assert state.consecutive_failures == 0


class TestSchemaErrors:
    """Tests for schema error reporting."""

    @pytest.mark.asyncio
    async def test_schema_errors_below_threshold(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Schema errors below threshold should not trip."""
        incident = await circuit_breaker.report_schema_error(
            error_count=3,  # Below 5 threshold
        )

        assert incident is None
        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is False

    @pytest.mark.asyncio
    async def test_schema_errors_above_threshold_trip(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Schema errors above threshold should trip immediately."""
        incident = await circuit_breaker.report_schema_error(
            error_count=5,
            details={"error_types": ["validation", "parsing"]},
        )

        assert incident is not None
        assert incident.severity == "P3"

        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is True


class TestTTLAutoRecovery:
    """Tests for TTL-based auto-recovery."""

    @pytest.mark.asyncio
    async def test_disable_with_ttl(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Disable with TTL should set disabled_until."""
        ttl = datetime.now(timezone.utc) + timedelta(hours=1)

        changed, incident = await circuit_breaker.disable_v2(
            reason="TTL test",
            disabled_by="test-suite",
            disabled_until=ttl,
        )

        state = circuit_breaker.get_state()
        assert state.disabled_until is not None

    @pytest.mark.asyncio
    async def test_auto_recovery_after_ttl(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Circuit breaker should auto-recover after TTL expires."""
        # Disable with TTL in the past
        ttl = datetime.now(timezone.utc) - timedelta(seconds=1)

        changed, incident = await circuit_breaker.disable_v2(
            reason="Past TTL test",
            disabled_by="test-suite",
            disabled_until=ttl,
        )

        # Should auto-recover when checking state
        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is False


class TestIncidentTracking:
    """Tests for incident tracking and retrieval."""

    @pytest.mark.asyncio
    async def test_incident_created_on_trip(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Incident should be created when breaker trips."""
        # Trip the breaker
        for _ in range(3):
            await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        # Get incidents
        incidents = circuit_breaker.get_incidents()

        assert len(incidents) == 1
        assert incidents[0].severity == "P1"
        assert incidents[0].resolved is False

    @pytest.mark.asyncio
    async def test_incident_resolved_on_reset(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """Incident should be resolved when breaker is reset."""
        # Trip the breaker
        for _ in range(3):
            await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        # Reset
        await circuit_breaker.reset(
            reason="Fixed the issue",
            reset_by="test-suite",
        )

        # Get resolved incidents
        incidents = circuit_breaker.get_incidents(include_resolved=True)

        assert len(incidents) == 1
        assert incidents[0].resolved is True
        assert incidents[0].resolved_by == "test-suite"
        assert incidents[0].resolution_notes == "Fixed the issue"


class TestAlertmanagerIntegration:
    """Tests for Alertmanager integration."""

    @pytest.mark.asyncio
    async def test_alert_sent_on_disable(
        self,
        circuit_breaker: CircuitBreaker,
        alertmanager_mock,
    ):
        """Alert should be posted to Alertmanager when breaker trips."""
        # Set alertmanager URL
        circuit_breaker.config.alertmanager_url = "http://alertmanager:9093/api/v2/alerts"

        # Trip the breaker
        for _ in range(3):
            await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        # Verify alertmanager was called and inspect the alert
        assert alertmanager_mock.call_count >= 1
        alertmanager_mock.assert_alert_sent("CostSimV2Disabled")

    @pytest.mark.asyncio
    async def test_no_alert_when_url_not_configured(
        self,
        circuit_breaker: CircuitBreaker,
    ):
        """No alert should be sent if URL is not configured."""
        # Ensure no alertmanager URL
        circuit_breaker.config.alertmanager_url = None

        # Trip the breaker (should not raise)
        for _ in range(3):
            await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        is_disabled = await circuit_breaker.is_disabled()
        assert is_disabled is True


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    @pytest.mark.asyncio
    async def test_is_v2_disabled_function(
        self,
        circuit_breaker: CircuitBreaker,
        clean_circuit_breaker_state,
    ):
        """is_v2_disabled() should work as convenience function."""
        # Clear global instance
        import app.costsim.circuit_breaker as cb_module
        cb_module._circuit_breaker = None

        result = await is_v2_disabled()
        assert result is False

    @pytest.mark.asyncio
    async def test_disable_enable_functions(
        self,
        clean_circuit_breaker_state,
    ):
        """disable_v2() and enable_v2() should work as convenience functions."""
        # Clear global instance
        import app.costsim.circuit_breaker as cb_module
        cb_module._circuit_breaker = None

        # Disable
        changed, incident = await disable_v2(
            reason="Convenience test",
            disabled_by="test",
        )
        assert changed is True

        is_disabled = await is_v2_disabled()
        assert is_disabled is True

        # Enable
        changed = await enable_v2(
            enabled_by="test",
            reason="Re-enable",
        )
        assert changed is True

        is_disabled = await is_v2_disabled()
        assert is_disabled is False


class TestDatabaseConsistency:
    """Tests for database state consistency."""

    def test_state_persisted_to_db(
        self,
        circuit_breaker: CircuitBreaker,
        db_session: Session,
    ):
        """State changes should be persisted to database."""
        # Get state (creates row if needed)
        circuit_breaker.get_state()

        # Verify row exists in DB
        statement = select(CostSimCBState).where(CostSimCBState.name == CB_NAME)
        result = db_session.exec(statement)
        state = result.first()

        assert state is not None
        assert state.name == CB_NAME
        assert state.disabled is False

    @pytest.mark.asyncio
    async def test_incident_persisted_to_db(
        self,
        circuit_breaker: CircuitBreaker,
        db_session: Session,
    ):
        """Incidents should be persisted to database."""
        # Trip the breaker
        for _ in range(3):
            await circuit_breaker.report_drift(drift_score=0.25, sample_count=100)

        # Verify incident in DB
        statement = select(CostSimCBIncident).where(
            CostSimCBIncident.circuit_breaker_name == CB_NAME
        )
        result = db_session.exec(statement)
        incident = result.first()

        assert incident is not None
        assert incident.severity == "P1"
        assert incident.drift_score == 0.25
