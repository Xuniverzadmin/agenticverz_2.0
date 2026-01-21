# Layer: L8 — Tests
# Product: system-wide
# Reference: GAP-058 (RetrievalEvidence)
"""
Unit tests for GAP-058: RetrievalEvidence Model.

Tests the audit log model for mediated data access, ensuring
immutability and proper field definitions.
"""

import pytest
from datetime import datetime, timezone


class TestRetrievalEvidenceModel:
    """Test suite for RetrievalEvidence model."""

    def test_model_import(self):
        """RetrievalEvidence should be importable."""
        from app.models.retrieval_evidence import RetrievalEvidence

        assert RetrievalEvidence is not None

    def test_model_has_table_name(self):
        """Model should have correct table name."""
        from app.models.retrieval_evidence import RetrievalEvidence

        assert RetrievalEvidence.__tablename__ == "retrieval_evidence"

    def test_model_creation(self):
        """RetrievalEvidence should be creatable with required fields."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="http-conn-001",
            action="query",
            query_hash="abc123def456",
            token_count=500,
        )

        assert evidence.tenant_id == "tenant-001"
        assert evidence.run_id == "run-123"
        assert evidence.plane_id == "plane-001"
        assert evidence.connector_id == "http-conn-001"
        assert evidence.action == "query"
        assert evidence.query_hash == "abc123def456"
        assert evidence.token_count == 500

    def test_model_generates_uuid(self):
        """Model should auto-generate UUID for id field."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="read",
            query_hash="hash123",
            token_count=100,
        )

        assert evidence.id is not None
        assert len(evidence.id) == 36  # UUID format

    def test_model_generates_timestamps(self):
        """Model should auto-generate requested_at and created_at."""
        from app.models.retrieval_evidence import RetrievalEvidence

        before = datetime.now(timezone.utc)

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="fetch",
            query_hash="hash456",
            token_count=200,
        )

        after = datetime.now(timezone.utc)

        assert evidence.requested_at is not None
        assert evidence.created_at is not None
        assert before <= evidence.requested_at <= after
        assert before <= evidence.created_at <= after

    def test_model_doc_ids_default(self):
        """doc_ids should default to empty list."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash789",
            token_count=0,
        )

        assert evidence.doc_ids == []

    def test_model_doc_ids_with_values(self):
        """doc_ids should accept list of document IDs."""
        from app.models.retrieval_evidence import RetrievalEvidence

        doc_ids = ["doc-1", "doc-2", "doc-3"]

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash999",
            token_count=300,
            doc_ids=doc_ids,
        )

        assert evidence.doc_ids == doc_ids
        assert len(evidence.doc_ids) == 3

    def test_model_optional_fields(self):
        """Optional fields should default to None."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash000",
            token_count=0,
        )

        assert evidence.policy_snapshot_id is None
        assert evidence.completed_at is None
        assert evidence.duration_ms is None

    def test_model_with_optional_fields(self):
        """Model should accept optional fields."""
        from app.models.retrieval_evidence import RetrievalEvidence

        completed = datetime.now(timezone.utc)

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash111",
            token_count=100,
            policy_snapshot_id="pol-snap-001",
            completed_at=completed,
            duration_ms=150,
        )

        assert evidence.policy_snapshot_id == "pol-snap-001"
        assert evidence.completed_at == completed
        assert evidence.duration_ms == 150


class TestRetrievalEvidenceProperties:
    """Test computed properties."""

    def test_is_complete_false(self):
        """is_complete should be False when completed_at is None."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash222",
            token_count=0,
        )

        assert evidence.is_complete is False

    def test_is_complete_true(self):
        """is_complete should be True when completed_at is set."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash333",
            token_count=0,
            completed_at=datetime.now(timezone.utc),
        )

        assert evidence.is_complete is True

    def test_doc_count_empty(self):
        """doc_count should be 0 for empty doc_ids."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash444",
            token_count=0,
        )

        assert evidence.doc_count == 0

    def test_doc_count_with_docs(self):
        """doc_count should return count of doc_ids."""
        from app.models.retrieval_evidence import RetrievalEvidence

        evidence = RetrievalEvidence(
            tenant_id="tenant-001",
            run_id="run-123",
            plane_id="plane-001",
            connector_id="conn-001",
            action="query",
            query_hash="hash555",
            token_count=0,
            doc_ids=["doc-1", "doc-2", "doc-3", "doc-4", "doc-5"],
        )

        assert evidence.doc_count == 5


class TestRetrievalEvidenceHelpers:
    """Test helper functions."""

    def test_utc_now(self):
        """utc_now should return timezone-aware UTC datetime."""
        from app.models.retrieval_evidence import utc_now

        now = utc_now()

        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_generate_uuid(self):
        """generate_uuid should return valid UUID string."""
        from app.models.retrieval_evidence import generate_uuid

        uuid1 = generate_uuid()
        uuid2 = generate_uuid()

        assert len(uuid1) == 36
        assert len(uuid2) == 36
        assert uuid1 != uuid2  # Should be unique
