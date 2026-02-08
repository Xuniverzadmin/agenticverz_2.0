# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-065 (Retrieval Mediation)
"""
Unit tests for GAP-065: Retrieval Mediation Layer.

Tests the unified mediation layer for all external data access
with deny-by-default and policy enforcement.
"""

import pytest
from app.hoc.cus.hoc_spine.services.retrieval_mediator import (
    RetrievalMediator,
    MediatedResult,
    MediationDeniedError,
    MediationAction,
    PolicyCheckResult,
    EvidenceRecord,
)


class TestRetrievalMediator:
    """Test suite for retrieval mediator."""

    def test_mediator_creation(self):
        """Mediator should be creatable without dependencies."""
        mediator = RetrievalMediator()
        assert mediator is not None

    def test_mediator_has_default_deny(self):
        """Mediator should have deny-by-default invariant."""
        mediator = RetrievalMediator()
        assert hasattr(mediator, "_default_deny")
        assert mediator._default_deny is True

    def test_mediator_accepts_optional_dependencies(self):
        """Mediator should accept optional policy checker and connector registry."""
        mediator = RetrievalMediator(
            policy_checker=None,
            connector_registry=None,
            evidence_service=None,
        )
        assert mediator.policy_checker is None
        assert mediator.connector_registry is None


class TestMediatedResult:
    """Test MediatedResult dataclass."""

    def test_successful_result(self):
        """Successful result should have all required fields."""
        result = MediatedResult(
            success=True,
            data={"key": "value"},
            evidence_id="ev-123",
            connector_id="sql-gateway",
            tokens_consumed=100,
            query_hash="abc123",
            timestamp="2026-01-21T00:00:00Z",
            tenant_id="tenant-001",
            run_id="run-123",
        )

        assert result.success is True
        assert result.data is not None
        assert result.connector_id == "sql-gateway"
        assert result.evidence_id == "ev-123"

    def test_result_includes_token_count(self):
        """Result should include token count for billing."""
        result = MediatedResult(
            success=True,
            data={},
            evidence_id="ev-456",
            connector_id="http-connector",
            tokens_consumed=500,
            query_hash="def456",
            timestamp="2026-01-21T00:00:00Z",
            tenant_id="tenant-001",
            run_id="run-456",
        )

        assert result.tokens_consumed == 500

    def test_result_includes_query_hash(self):
        """Result should include query hash for evidence."""
        result = MediatedResult(
            success=True,
            data={},
            evidence_id="ev-789",
            connector_id="mcp-connector",
            tokens_consumed=0,
            query_hash="hash123",
            timestamp="2026-01-21T00:00:00Z",
            tenant_id="tenant-001",
            run_id="run-789",
        )

        assert result.query_hash == "hash123"


class TestMediationDeniedError:
    """Test MediationDeniedError exception."""

    def test_error_is_exception(self):
        """MediationDeniedError should be an Exception."""
        error = MediationDeniedError("Access denied")
        assert isinstance(error, Exception)

    def test_error_includes_reason(self):
        """Error should include denial reason."""
        error = MediationDeniedError(
            reason="Policy violation",
            policy_id="pol-001",
            tenant_id="tenant-001",
            run_id="run-123",
        )

        assert error.reason == "Policy violation"
        assert error.policy_id == "pol-001"
        assert "Policy violation" in str(error)

    def test_error_with_minimal_fields(self):
        """Error should work with just reason."""
        error = MediationDeniedError(reason="Denied")

        assert error.reason == "Denied"
        assert error.policy_id is None
        assert error.tenant_id is None


class TestMediationAction:
    """Test MediationAction enum."""

    def test_action_values(self):
        """MediationAction should have expected values."""
        assert MediationAction.QUERY.value == "query"
        assert MediationAction.RETRIEVE.value == "retrieve"
        assert MediationAction.SEARCH.value == "search"
        assert MediationAction.LIST.value == "list"


class TestPolicyCheckResult:
    """Test PolicyCheckResult dataclass."""

    def test_allowed_result(self):
        """Allowed policy check should have correct fields."""
        result = PolicyCheckResult(
            allowed=True,
            reason="Policy permits access",
        )

        assert result.allowed is True
        assert result.reason == "Policy permits access"

    def test_denied_result_with_policy(self):
        """Denied policy check should include blocking policy."""
        result = PolicyCheckResult(
            allowed=False,
            reason="Budget exceeded",
            blocking_policy_id="budget-policy-001",
            snapshot_id="snap-001",
        )

        assert result.allowed is False
        assert result.blocking_policy_id == "budget-policy-001"


class TestEvidenceRecord:
    """Test EvidenceRecord dataclass."""

    def test_evidence_creation(self):
        """EvidenceRecord should be creatable with all fields."""
        record = EvidenceRecord(
            id="ev-001",
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="documents",
            connector_id="sql-gateway",
            action="query",
            query_hash="abc123",
            doc_ids=["doc-1", "doc-2"],
            token_count=150,
            policy_snapshot_id="snap-001",
            requested_at="2026-01-21T00:00:00Z",
            completed_at="2026-01-21T00:00:00Z",
            duration_ms=0,
        )

        assert record.id == "ev-001"
        assert record.tenant_id == "tenant-001"
        assert len(record.doc_ids) == 2
        assert record.token_count == 150
