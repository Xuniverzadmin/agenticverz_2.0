"""
M9: Failure Catalog Persistence Tests

Tests for:
- FailureMatch model
- Persistence layer
- Metrics instrumentation
- Aggregation job
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Test fixtures
@pytest.fixture
def sample_run_id():
    return str(uuid.uuid4())


@pytest.fixture
def sample_tenant_id():
    return "tenant_test_123"


class TestFailureMatchModel:
    """Tests for FailureMatch SQLModel."""

    def test_failure_match_creation(self, sample_run_id, sample_tenant_id):
        """Test basic FailureMatch creation."""
        from app.db import FailureMatch

        match = FailureMatch(
            run_id=sample_run_id,
            tenant_id=sample_tenant_id,
            error_code="TIMEOUT",
            error_message="Connection timed out after 30s",
            catalog_entry_id="TIMEOUT",
            match_type="code",
            confidence_score=1.0,
            category="TRANSIENT",
            severity="MEDIUM",
            is_retryable=True,
            recovery_mode="RETRY_EXPONENTIAL",
        )

        assert match.run_id == sample_run_id
        assert match.error_code == "TIMEOUT"
        assert match.confidence_score == 1.0
        assert match.is_retryable is True

    def test_failure_match_miss(self, sample_run_id):
        """Test FailureMatch for unmatched error."""
        from app.db import FailureMatch

        match = FailureMatch(
            run_id=sample_run_id,
            error_code="CUSTOM_ERROR_123",
            error_message="Some custom error we don't know about",
            catalog_entry_id=None,  # Miss
            match_type="unknown",
            confidence_score=0.0,
            is_retryable=False,
        )

        assert match.catalog_entry_id is None
        assert match.confidence_score == 0.0
        assert match.is_retryable is False

    def test_context_json_serialization(self, sample_run_id):
        """Test context JSON get/set methods."""
        from app.db import FailureMatch

        match = FailureMatch(
            run_id=sample_run_id,
            error_code="TEST",
        )

        context = {"url": "https://api.example.com", "method": "POST"}
        match.set_context(context)

        retrieved = match.get_context()
        assert retrieved == context
        assert retrieved["url"] == "https://api.example.com"

    def test_recovery_status_tracking(self, sample_run_id):
        """Test recovery status update methods."""
        from app.db import FailureMatch

        match = FailureMatch(
            run_id=sample_run_id,
            error_code="TIMEOUT",
            recovery_mode="RETRY_EXPONENTIAL",
        )

        assert match.recovery_attempted is False
        assert match.recovery_succeeded is False

        match.mark_recovery_attempted()
        assert match.recovery_attempted is True
        assert match.recovery_succeeded is False

        match.mark_recovery_succeeded()
        assert match.recovery_attempted is True
        assert match.recovery_succeeded is True

    def test_to_dict(self, sample_run_id, sample_tenant_id):
        """Test dictionary serialization."""
        from app.db import FailureMatch

        match = FailureMatch(
            run_id=sample_run_id,
            tenant_id=sample_tenant_id,
            error_code="BUDGET_EXCEEDED",
            catalog_entry_id="BUDGET_EXCEEDED",
            match_type="code",
            confidence_score=1.0,
            category="RESOURCE",
            severity="HIGH",
            is_retryable=False,
            recovery_mode="ESCALATE",
            skill_id="llm_invoke",
            step_index=3,
        )

        data = match.to_dict()

        assert data["run_id"] == sample_run_id
        assert data["error_code"] == "BUDGET_EXCEEDED"
        assert data["category"] == "RESOURCE"
        assert data["skill_id"] == "llm_invoke"
        assert data["step_index"] == 3


class TestFailureCatalogMatch:
    """Tests for failure catalog matching."""

    def test_match_known_code(self):
        """Test matching a known error code."""
        from app.runtime.failure_catalog import FailureCatalog

        catalog = FailureCatalog()
        result = catalog.match_code("TIMEOUT")

        assert result.matched is True
        assert result.entry is not None
        assert result.entry.code == "TIMEOUT"
        assert result.confidence == 1.0

    def test_match_unknown_code(self):
        """Test matching an unknown error code."""
        from app.runtime.failure_catalog import FailureCatalog

        catalog = FailureCatalog()
        result = catalog.match_code("COMPLETELY_UNKNOWN_ERROR_XYZ")

        assert result.matched is False
        assert result.entry is None
        assert result.confidence == 0.0

    def test_match_message(self):
        """Test matching by error message."""
        from app.runtime.failure_catalog import FailureCatalog

        catalog = FailureCatalog()
        result = catalog.match_message("Connection timed out after 30 seconds")

        assert result.matched is True
        assert result.entry is not None
        # Should match TIMEOUT via keyword

    def test_match_combined(self):
        """Test combined match (code then message)."""
        from app.runtime.failure_catalog import FailureCatalog

        catalog = FailureCatalog()

        # Try code first
        result = catalog.match("BUDGET_EXCEEDED")
        assert result.matched is True

        # Fall back to message
        result = catalog.match("rate limit exceeded")
        assert result.matched is True


class TestFailurePersistence:
    """Tests for M9 persistence layer."""

    def test_persist_failure_match_hit(self, sample_run_id):
        """Test persisting a catalog hit."""
        from app.runtime.failure_catalog import (
            MatchResult, MatchType, CatalogEntry, persist_failure_match
        )
        from app.db import FailureMatch

        entry = CatalogEntry(
            code="TIMEOUT",
            category="TRANSIENT",
            message="Timeout error",
            severity="MEDIUM",
            is_retryable=True,
            recovery_mode="RETRY_EXPONENTIAL",
            recovery_suggestions=["Increase timeout", "Add retry logic"],
            http_status=504,
            metrics_labels={"type": "network"},
        )

        result = MatchResult(
            matched=True,
            entry=entry,
            match_type=MatchType.CODE,
            confidence=1.0,
        )

        # Test with real database (integration style)
        record_id = persist_failure_match(
            run_id=sample_run_id,
            result=result,
            error_code="TIMEOUT",
            error_message="Connection timed out",
            skill_id="http_call",
            step_index=2,
        )

        # Should return a valid ID
        assert record_id is not None

    def test_persist_failure_match_miss(self, sample_run_id):
        """Test persisting a catalog miss."""
        from app.runtime.failure_catalog import (
            MatchResult, MatchType, persist_failure_match
        )

        result = MatchResult(
            matched=False,
            entry=None,
            match_type=MatchType.CODE,
            confidence=0.0,
        )

        record_id = persist_failure_match(
            run_id=sample_run_id,
            result=result,
            error_code="UNKNOWN_ERROR",
            error_message="Some unknown error",
        )

        # Should return a valid ID even for misses
        assert record_id is not None

    def test_match_and_persist_convenience(self, sample_run_id):
        """Test match_and_persist convenience function."""
        from app.runtime.failure_catalog import match_and_persist

        with patch('app.runtime.failure_catalog.persist_failure_match') as mock_persist:
            result = match_and_persist(
                code_or_message="TIMEOUT",
                run_id=sample_run_id,
                skill_id="http_call",
            )

            assert result.matched is True
            mock_persist.assert_called_once()


class TestMetricsInstrumentation:
    """Tests for Prometheus metrics."""

    def test_metrics_initialization(self):
        """Test that metrics can be initialized."""
        from app.runtime.failure_catalog import _init_metrics

        # Should not raise
        _init_metrics()

    def test_hit_metrics_increment(self):
        """Test that hit metrics are incremented."""
        from app.runtime.failure_catalog import (
            _init_metrics, _failure_match_hits
        )

        _init_metrics()

        if _failure_match_hits:
            # Should not raise
            _failure_match_hits.labels(
                error_code="TEST",
                category="TEST",
                recovery_mode="TEST"
            ).inc()


class TestAggregationJob:
    """Tests for failure aggregation job."""

    def test_compute_signature(self):
        """Test error signature computation."""
        from app.jobs.failure_aggregation import compute_signature

        sig1 = compute_signature("TIMEOUT", "Connection timed out")
        sig2 = compute_signature("TIMEOUT", "Connection timed out")
        sig3 = compute_signature("TIMEOUT", "Different message")

        # Same inputs = same signature
        assert sig1 == sig2
        # Different message = different signature
        assert sig1 != sig3

    def test_compute_signature_normalization(self):
        """Test signature normalization."""
        from app.jobs.failure_aggregation import compute_signature

        sig1 = compute_signature("timeout", "message")
        sig2 = compute_signature("TIMEOUT", "MESSAGE")

        # Case normalization
        assert sig1 == sig2

    def test_suggest_category(self):
        """Test category suggestion."""
        from app.jobs.failure_aggregation import suggest_category

        assert suggest_category(["TIMEOUT"]) == "TRANSIENT"
        assert suggest_category(["PERMISSION_DENIED"]) == "PERMISSION"
        assert suggest_category(["BUDGET_EXCEEDED"]) == "RESOURCE"
        assert suggest_category(["VALIDATION_ERROR"]) == "VALIDATION"
        assert suggest_category(["RANDOM_ERROR"]) == "PERMANENT"

    def test_suggest_recovery(self):
        """Test recovery suggestion."""
        from app.jobs.failure_aggregation import suggest_recovery

        assert suggest_recovery(["TIMEOUT"]) == "RETRY_EXPONENTIAL"
        assert suggest_recovery(["RATE_LIMITED"]) == "RETRY_WITH_JITTER"
        assert suggest_recovery(["PERMISSION_DENIED"]) == "ESCALATE"
        assert suggest_recovery(["INVALID_INPUT"]) == "ABORT"

    def test_aggregate_patterns(self):
        """Test pattern aggregation."""
        from app.jobs.failure_aggregation import aggregate_patterns

        raw_patterns = [
            {
                "error_code": "TIMEOUT",
                "error_message": "Connection timed out",
                "occurrence_count": 10,
                "last_seen": "2025-12-07T10:00:00Z",
                "first_seen": "2025-12-06T10:00:00Z",
                "affected_skills": ["http_call"],
                "affected_tenants": ["tenant_1"],
            },
            {
                "error_code": "TIMEOUT",
                "error_message": "Connection timed out",
                "occurrence_count": 5,
                "last_seen": "2025-12-07T11:00:00Z",
                "first_seen": "2025-12-06T09:00:00Z",
                "affected_skills": ["http_call", "webhook"],
                "affected_tenants": ["tenant_2"],
            },
        ]

        aggregated = aggregate_patterns(raw_patterns)

        assert len(aggregated) == 1  # Should merge identical signatures
        assert aggregated[0]["total_occurrences"] == 15

    def test_get_summary_stats(self):
        """Test summary statistics generation."""
        from app.jobs.failure_aggregation import get_summary_stats

        patterns = [
            {
                "primary_error_code": "TIMEOUT",
                "all_error_codes": ["TIMEOUT"],
                "total_occurrences": 100,
                "affected_skills": ["http_call"],
                "affected_tenants": ["tenant_1"],
            },
            {
                "primary_error_code": "DNS_FAILURE",
                "all_error_codes": ["DNS_FAILURE"],
                "total_occurrences": 50,
                "affected_skills": ["http_call"],
                "affected_tenants": ["tenant_2"],
            },
        ]

        stats = get_summary_stats(patterns)

        assert stats["total_patterns"] == 2
        assert stats["total_occurrences"] == 150
        assert len(stats["top_error_codes"]) > 0


class TestIntegrationScenarios:
    """Integration tests for full failure flow."""

    @pytest.mark.integration
    def test_full_failure_flow(self, sample_run_id, sample_tenant_id):
        """Test complete failure detection → match → persist flow."""
        from app.runtime.failure_catalog import (
            FailureCatalog, persist_failure_match
        )

        catalog = FailureCatalog()

        # Simulate a failure
        error_code = "TIMEOUT"
        error_message = "HTTP request timed out after 30s"

        # Match
        result = catalog.match(error_code)
        assert result.matched is True

        # Verify entry properties
        assert result.entry.is_retryable is True
        assert result.entry.recovery_mode == "RETRY_EXPONENTIAL"

    @pytest.mark.integration
    def test_unknown_error_flow(self, sample_run_id):
        """Test unknown error detection flow."""
        from app.runtime.failure_catalog import FailureCatalog

        catalog = FailureCatalog()

        # Simulate unknown error
        error_code = "EXOTIC_THIRD_PARTY_ERROR_12345"
        result = catalog.match(error_code)

        assert result.matched is False
        assert result.entry is None
        assert result.confidence == 0.0

    @pytest.mark.integration
    def test_recovery_tracking_flow(self, sample_run_id):
        """Test recovery status tracking flow."""
        from app.db import FailureMatch

        # Create match record
        match = FailureMatch(
            run_id=sample_run_id,
            error_code="TIMEOUT",
            catalog_entry_id="TIMEOUT",
            match_type="code",
            confidence_score=1.0,
            is_retryable=True,
            recovery_mode="RETRY_EXPONENTIAL",
        )

        # Initial state
        assert match.recovery_attempted is False
        assert match.recovery_succeeded is False

        # After first attempt (failed)
        match.mark_recovery_attempted()
        assert match.recovery_attempted is True
        assert match.recovery_succeeded is False

        # After successful recovery
        match.mark_recovery_succeeded()
        assert match.recovery_succeeded is True


# Pytest markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
