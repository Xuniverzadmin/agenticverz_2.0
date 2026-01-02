# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: Verify test isolation mechanisms work correctly
# Reference: PIN-276 (Bucket A/B Permanent Fix)

"""
Test Isolation Mechanism Verification.

These tests verify that PIN-276 isolation mechanisms work correctly:
- Bucket A: Database transaction rollback
- Bucket B: Prometheus metrics isolation

Run with: pytest tests/unit/test_isolation_mechanism.py -v
"""

import pytest
from prometheus_client import Counter


class TestPrometheusIsolation:
    """
    Verify Prometheus metrics are isolated between tests.

    PIN-276 Bucket B: State B Prometheus compliance.
    """

    def test_metrics_factory_creates_counter(self, metrics_factory):
        """Verify metrics_factory creates real Prometheus counters."""
        counter = metrics_factory.counter("test_requests", "Test counter")
        counter.inc()
        counter.inc()

        # Counter names get _total suffix automatically
        value = metrics_factory.get_value("test_requests_total")
        assert value == 2.0

    def test_metrics_factory_creates_gauge(self, metrics_factory):
        """Verify metrics_factory creates real Prometheus gauges."""
        gauge = metrics_factory.gauge("test_active_connections", "Test gauge")
        gauge.set(42)

        value = metrics_factory.get_value("test_active_connections")
        assert value == 42.0

    def test_metrics_factory_creates_histogram(self, metrics_factory):
        """Verify metrics_factory creates real Prometheus histograms."""
        histogram = metrics_factory.histogram(
            "test_request_latency_seconds",
            "Test histogram",
            buckets=[0.1, 0.5, 1.0],
        )
        histogram.observe(0.3)

        # Histogram creates multiple metrics (_bucket, _count, _sum)
        count = metrics_factory.get_value("test_request_latency_seconds_count")
        assert count == 1.0

    def test_prometheus_registry_isolation(self, prometheus_registry):
        """Verify each test gets its own registry."""
        # Create a counter in this test's registry
        counter = Counter("isolation_test_counter", "Test", registry=prometheus_registry)
        counter.inc()

        # Verify it's in this registry (with _total suffix for counters)
        value = prometheus_registry.get_sample_value("isolation_test_counter_total")
        assert value == 1.0

    def test_prometheus_registry_does_not_leak(self, prometheus_registry):
        """
        Verify metrics from other tests don't appear here.

        If isolation works, 'isolation_test_counter' from previous test
        should NOT exist in this test's registry.
        """
        # This counter should not exist in this test's fresh registry
        value = prometheus_registry.get_sample_value("isolation_test_counter_total")
        assert value is None, "Metrics leaked from another test!"


class TestDatabaseIsolation:
    """
    Verify database changes are rolled back between tests.

    PIN-276 Bucket A: Transaction rollback compliance.
    """

    @pytest.mark.skipif(
        "not config.getoption('--run-db-isolation-tests', default=False)",
        reason="Requires --run-db-isolation-tests flag (needs DATABASE_URL)",
    )
    def test_isolated_session_rollback(self, isolated_db_session):
        """Verify isolated_db_session rolls back changes."""
        from sqlalchemy import text

        # Create a temporary test table and insert data
        isolated_db_session.execute(
            text(
                """
            CREATE TEMP TABLE IF NOT EXISTS isolation_test_table (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """
            )
        )
        isolated_db_session.execute(
            text(
                """
            INSERT INTO isolation_test_table (name) VALUES ('test_isolation_row')
        """
            )
        )
        isolated_db_session.flush()  # Use flush, not commit

        # Verify it exists in this session
        result = isolated_db_session.execute(
            text(
                """
            SELECT name FROM isolation_test_table WHERE name = 'test_isolation_row'
        """
            )
        ).fetchone()
        assert result is not None
        assert result[0] == "test_isolation_row"

        # After test: automatic rollback happens
        # The temp table and data are rolled back

    @pytest.mark.skipif(
        "not config.getoption('--run-db-isolation-tests', default=False)",
        reason="Requires --run-db-isolation-tests flag (needs DATABASE_URL)",
    )
    def test_isolated_session_no_leak(self, isolated_db_session):
        """
        Verify previous test's data was rolled back.

        If isolation works, the temp table from previous test should not exist.
        """
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError

        # Try to query the temp table - it should not exist
        try:
            result = isolated_db_session.execute(
                text(
                    """
                SELECT name FROM isolation_test_table WHERE name = 'test_isolation_row'
            """
                )
            ).fetchone()
            # If we get here, the table exists - that's a leak!
            assert result is None, "Database state leaked from another test!"
        except ProgrammingError as e:
            # Table doesn't exist - this is the expected behavior
            if 'relation "isolation_test_table" does not exist' in str(e):
                pass  # Good - temp table was rolled back
            else:
                raise


# pytest_addoption is in conftest.py (--run-db-isolation-tests)
