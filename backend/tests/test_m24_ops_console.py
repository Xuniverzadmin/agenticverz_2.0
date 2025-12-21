"""Tests for M24 Ops Console - Founder Intelligence System

PIN-105: Ops Console - Founder Intelligence System

Tests:
1. Event emission via EventEmitter
2. System Pulse endpoint
3. Customer Intelligence endpoint
4. Stickiness computation
5. Silent churn detection
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.services.event_emitter import (
    EntityType,
    EventEmitter,
    EventType,
    OpsEvent,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestEventEmitter:
    """Test EventEmitter service."""

    def test_emit_single_event(self, session):
        """Test emitting a single event."""
        emitter = EventEmitter(session)
        tenant_id = uuid.uuid4()

        event_id = emitter.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INCIDENT_CREATED,
                entity_type=EntityType.INCIDENT,
                entity_id=uuid.uuid4(),
                severity=3,
                metadata={"policy_id": "pol-001"},
            )
        )

        session.commit()

        # Verify event was stored
        result = session.execute(
            text("SELECT event_type, severity FROM ops_events WHERE event_id = :event_id"), {"event_id": str(event_id)}
        ).first()

        assert result is not None
        assert result[0] == "INCIDENT_CREATED"
        assert result[1] == 3

    def test_emit_api_call(self, session):
        """Test convenience method for API calls."""
        emitter = EventEmitter(session)
        tenant_id = uuid.uuid4()

        event_id = emitter.emit_api_call(
            tenant_id=tenant_id,
            endpoint="/v1/chat/completions",
            method="POST",
            status_code=200,
            latency_ms=150,
        )

        session.commit()

        result = session.execute(
            text("SELECT event_type, latency_ms, metadata FROM ops_events WHERE event_id = :event_id"),
            {"event_id": str(event_id)},
        ).first()

        assert result is not None
        assert result[0] == "API_CALL_RECEIVED"
        assert result[1] == 150

    def test_emit_llm_call(self, session):
        """Test LLM call event emission."""
        emitter = EventEmitter(session)
        tenant_id = uuid.uuid4()

        event_id = emitter.emit_llm_call(
            tenant_id=tenant_id,
            call_id=uuid.uuid4(),
            model="gpt-4o-mini",
            tokens_in=100,
            tokens_out=200,
            cost_usd=Decimal("0.001"),
            latency_ms=500,
            success=True,
        )

        session.commit()

        result = session.execute(
            text("SELECT event_type, cost_usd FROM ops_events WHERE event_id = :event_id"), {"event_id": str(event_id)}
        ).first()

        assert result is not None
        assert result[0] == "LLM_CALL_MADE"
        assert float(result[1]) == pytest.approx(0.001, rel=0.01)

    def test_emit_batch_mode(self, session):
        """Test batch event emission."""
        emitter = EventEmitter(session)
        tenant_id = uuid.uuid4()

        emitter.start_batch()

        # Queue multiple events
        for i in range(5):
            emitter.emit(
                OpsEvent(
                    tenant_id=tenant_id,
                    event_type=EventType.INCIDENT_VIEWED,
                    entity_id=uuid.uuid4(),
                )
            )

        # Nothing committed yet
        count_before = session.execute(
            text("SELECT COUNT(*) FROM ops_events WHERE tenant_id = :tenant_id"), {"tenant_id": str(tenant_id)}
        ).first()

        # Flush batch
        event_ids = emitter.flush_batch()
        session.commit()

        assert len(event_ids) == 5

        # Now events are committed
        count_after = session.execute(
            text("SELECT COUNT(*) FROM ops_events WHERE tenant_id = :tenant_id"), {"tenant_id": str(tenant_id)}
        ).first()

        assert count_after[0] == 5


class TestOpsAPIEndpoints:
    """Test Ops Console API endpoints."""

    def test_system_pulse_returns_healthy(self, client, session):
        """Test system pulse endpoint."""
        response = client.get("/ops/pulse")

        assert response.status_code == 200
        data = response.json()

        assert "active_tenants_24h" in data
        assert "system_state" in data
        assert data["system_state"] in ["healthy", "degraded", "critical"]

    def test_customer_segments_empty(self, client, session):
        """Test customer segments with no data."""
        response = client.get("/ops/customers")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_event_stream(self, client, session):
        """Test event stream endpoint."""
        response = client.get("/ops/events?hours=24&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "events" in data
        assert "total" in data
        assert "window_hours" in data

    def test_stickiness_by_feature(self, client, session):
        """Test stickiness by feature endpoint."""
        response = client.get("/ops/stickiness")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_incident_patterns(self, client, session):
        """Test incident patterns endpoint."""
        response = client.get("/ops/incidents/patterns")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_revenue_risk(self, client, session):
        """Test revenue and risk endpoint."""
        response = client.get("/ops/revenue")

        assert response.status_code == 200
        data = response.json()

        assert "mrr_estimate_usd" in data
        assert "at_risk_tenants" in data
        assert "revenue_alerts" in data

    def test_infra_limits(self, client, session):
        """Test infrastructure limits endpoint."""
        response = client.get("/ops/infra")

        assert response.status_code == 200
        data = response.json()

        assert "db_connections_current" in data
        assert "db_storage_used_gb" in data
        assert "limit_warnings" in data


class TestStickinessComputation:
    """Test stickiness score computation."""

    def test_stickiness_formula(self, session):
        """Test stickiness score formula is correctly applied."""
        tenant_id = uuid.uuid4()
        emitter = EventEmitter(session)

        now = utc_now()

        # Recent events (last 7 days) - higher weight
        for _ in range(5):
            emitter.emit(
                OpsEvent(
                    tenant_id=tenant_id,
                    event_type=EventType.INCIDENT_VIEWED,
                    timestamp=now - timedelta(days=2),
                )
            )

        for _ in range(3):
            emitter.emit(
                OpsEvent(
                    tenant_id=tenant_id,
                    event_type=EventType.REPLAY_EXECUTED,
                    timestamp=now - timedelta(days=3),
                )
            )

        for _ in range(2):
            emitter.emit(
                OpsEvent(
                    tenant_id=tenant_id,
                    event_type=EventType.EXPORT_GENERATED,
                    timestamp=now - timedelta(days=1),
                )
            )

        session.commit()

        # Expected stickiness:
        # Recent views: 5 * 0.2 = 1.0
        # Recent replays: 3 * 0.3 = 0.9
        # Recent exports: 2 * 0.5 = 1.0
        # Total = 2.9

        # Compute stickiness
        result = session.execute(
            text(
                """
            SELECT
                (COUNT(*) FILTER (WHERE event_type = 'INCIDENT_VIEWED') * 0.2) +
                (COUNT(*) FILTER (WHERE event_type = 'REPLAY_EXECUTED') * 0.3) +
                (COUNT(*) FILTER (WHERE event_type = 'EXPORT_GENERATED') * 0.5) as stickiness
            FROM ops_events
            WHERE tenant_id = :tenant_id
        """
            ),
            {"tenant_id": str(tenant_id)},
        ).first()

        assert result is not None
        assert float(result[0]) == pytest.approx(2.9, rel=0.01)


class TestSilentChurnDetection:
    """Test silent churn detection logic."""

    def test_silent_churn_detection_sql(self, session):
        """Test silent churn detection query."""
        tenant_id = uuid.uuid4()
        emitter = EventEmitter(session)

        now = utc_now()

        # API calls in last 48 hours
        for _ in range(5):
            emitter.emit(
                OpsEvent(
                    tenant_id=tenant_id,
                    event_type=EventType.API_CALL_RECEIVED,
                    timestamp=now - timedelta(hours=12),
                )
            )

        # No investigation events in last 7 days
        # (but one 10 days ago)
        emitter.emit(
            OpsEvent(
                tenant_id=tenant_id,
                event_type=EventType.INCIDENT_VIEWED,
                timestamp=now - timedelta(days=10),
            )
        )

        session.commit()

        # Check silent churn detection query
        result = session.execute(
            text(
                """
            SELECT tenant_id
            FROM ops_events
            GROUP BY tenant_id
            HAVING
                MAX(timestamp) FILTER (WHERE event_type = 'API_CALL_RECEIVED') > now() - interval '48 hours'
                AND
                (
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) IS NULL
                    OR
                    MAX(timestamp) FILTER (WHERE event_type IN ('INCIDENT_VIEWED', 'REPLAY_EXECUTED')) < now() - interval '7 days'
                )
        """
            )
        ).first()

        assert result is not None
        assert str(result[0]) == str(tenant_id)


# Fixtures
@pytest.fixture
def client():
    """Create test client."""
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


@pytest.fixture
def session():
    """Create test database session with ops_events table."""
    from sqlmodel import Session

    from app.db import engine

    with Session(engine) as session:
        # Ensure table exists
        try:
            session.execute(text("SELECT 1 FROM ops_events LIMIT 1"))
        except Exception:
            # Table doesn't exist, run migration
            session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS ops_events (
                    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
                    tenant_id UUID NOT NULL,
                    user_id UUID,
                    session_id UUID,
                    event_type TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id UUID,
                    severity INT,
                    latency_ms INT,
                    cost_usd NUMERIC(10,6),
                    metadata JSONB DEFAULT '{}'
                )
            """
                )
            )
            session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS ops_customer_segments (
                    tenant_id UUID PRIMARY KEY,
                    first_action TEXT,
                    first_action_at TIMESTAMPTZ,
                    inferred_buyer_type TEXT,
                    current_stickiness NUMERIC(5,2) DEFAULT 0,
                    peak_stickiness NUMERIC(5,2) DEFAULT 0,
                    stickiness_trend TEXT,
                    last_api_call TIMESTAMPTZ,
                    last_investigation TIMESTAMPTZ,
                    is_silent_churn BOOLEAN DEFAULT false,
                    risk_level TEXT DEFAULT 'low',
                    risk_reason TEXT,
                    time_to_first_replay_m INT,
                    time_to_first_export_m INT,
                    computed_at TIMESTAMPTZ DEFAULT now()
                )
            """
                )
            )
            session.commit()

        yield session

        # Cleanup test data
        session.execute(text("DELETE FROM ops_events"))
        session.execute(text("DELETE FROM ops_customer_segments"))
        session.commit()
