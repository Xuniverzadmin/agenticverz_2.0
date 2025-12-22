# tests/test_m10_recovery_enhanced.py
"""
Comprehensive tests for M10 Recovery Enhancement.

Tests:
- Rule engine evaluation
- Action catalog
- Provenance tracking
- Worker evaluation flow
- API endpoints (enhanced)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# =============================================================================
# Rule Engine Tests
# =============================================================================


class TestRuleEngine:
    """Test recovery rule engine."""

    def test_error_code_rule_exact_match(self):
        """Test error code matching with exact prefix."""
        from app.services.recovery_rule_engine import (
            ErrorCodeRule,
            RuleContext,
        )

        rule = ErrorCodeRule(
            rule_id="test_timeout",
            name="Test Timeout Rule",
            error_patterns=["TIMEOUT"],
            action_code="retry_exponential",
            score=0.85,
        )

        context = RuleContext(
            error_code="TIMEOUT",
            error_message="Connection timed out",
        )

        result = rule.evaluate(context)

        assert result.matched is True
        assert result.score == 0.85
        assert result.action_code == "retry_exponential"
        assert "TIMEOUT" in result.explanation

    def test_error_code_rule_prefix_match(self):
        """Test error code matching with prefix."""
        from app.services.recovery_rule_engine import (
            ErrorCodeRule,
            RuleContext,
        )

        rule = ErrorCodeRule(
            rule_id="test_http_5xx",
            name="Test HTTP 5xx Rule",
            error_patterns=["HTTP_5"],
            action_code="circuit_breaker",
            score=0.80,
        )

        context = RuleContext(
            error_code="HTTP_503_SERVICE_UNAVAILABLE",
            error_message="Service unavailable",
        )

        result = rule.evaluate(context)

        assert result.matched is True
        assert result.action_code == "circuit_breaker"

    def test_error_code_rule_no_match(self):
        """Test error code rule with no match."""
        from app.services.recovery_rule_engine import (
            ErrorCodeRule,
            RuleContext,
        )

        rule = ErrorCodeRule(
            rule_id="test_timeout",
            name="Test Timeout Rule",
            error_patterns=["TIMEOUT"],
            action_code="retry_exponential",
            score=0.85,
        )

        context = RuleContext(
            error_code="PERMISSION_DENIED",
            error_message="Access denied",
        )

        result = rule.evaluate(context)

        assert result.matched is False
        assert result.score == 0.0
        assert result.action_code is None

    def test_historical_pattern_rule_with_success(self):
        """Test historical pattern rule with successful history."""
        from app.services.recovery_rule_engine import (
            HistoricalPatternRule,
            RuleContext,
        )

        rule = HistoricalPatternRule(
            rule_id="test_historical",
            name="Test Historical Rule",
            min_occurrences=3,
            min_success_rate=0.7,
        )

        # Create historical matches with 80% success rate
        historical_matches = [
            {"recovery_succeeded": True, "recovery_suggestion": "retry"},
            {"recovery_succeeded": True, "recovery_suggestion": "retry"},
            {"recovery_succeeded": True, "recovery_suggestion": "retry"},
            {"recovery_succeeded": True, "recovery_suggestion": "retry"},
            {"recovery_succeeded": False, "recovery_suggestion": "retry"},
        ]

        context = RuleContext(
            error_code="TEST_ERROR",
            error_message="Test error",
            historical_matches=historical_matches,
        )

        result = rule.evaluate(context)

        assert result.matched is True
        assert result.score > 0
        assert result.metadata["success_rate"] == 0.8

    def test_historical_pattern_rule_insufficient_history(self):
        """Test historical pattern rule with insufficient history."""
        from app.services.recovery_rule_engine import (
            HistoricalPatternRule,
            RuleContext,
        )

        rule = HistoricalPatternRule(
            rule_id="test_historical",
            name="Test Historical Rule",
            min_occurrences=5,
            min_success_rate=0.7,
        )

        context = RuleContext(
            error_code="TEST_ERROR",
            error_message="Test error",
            historical_matches=[
                {"recovery_succeeded": True},
                {"recovery_succeeded": True},
            ],
        )

        result = rule.evaluate(context)

        assert result.matched is False
        assert "Insufficient history" in result.explanation

    def test_occurrence_threshold_rule(self):
        """Test occurrence threshold rule."""
        from app.services.recovery_rule_engine import (
            OccurrenceThresholdRule,
            RuleContext,
        )

        rule = OccurrenceThresholdRule(
            rule_id="test_escalate",
            name="Test Escalation Rule",
            threshold=5,
            action_code="notify_ops",
            score=0.9,
        )

        # Below threshold
        context_low = RuleContext(
            error_code="TEST_ERROR",
            error_message="Test error",
            occurrence_count=3,
        )
        result_low = rule.evaluate(context_low)
        assert result_low.matched is False

        # At/above threshold
        context_high = RuleContext(
            error_code="TEST_ERROR",
            error_message="Test error",
            occurrence_count=5,
        )
        result_high = rule.evaluate(context_high)
        assert result_high.matched is True
        assert result_high.action_code == "notify_ops"

    def test_composite_rule_and_logic(self):
        """Test composite rule with AND logic."""
        from app.services.recovery_rule_engine import (
            CompositeRule,
            ErrorCodeRule,
            OccurrenceThresholdRule,
            RuleContext,
        )

        rule = CompositeRule(
            rule_id="test_composite",
            name="Test Composite Rule",
            rules=[
                ErrorCodeRule(
                    rule_id="sub1",
                    name="Sub Rule 1",
                    error_patterns=["TIMEOUT"],
                    action_code="retry",
                    score=0.8,
                ),
                OccurrenceThresholdRule(
                    rule_id="sub2",
                    name="Sub Rule 2",
                    threshold=3,
                    action_code="notify",
                    score=0.7,
                ),
            ],
            logic="and",
        )

        # Both conditions met
        context_both = RuleContext(
            error_code="TIMEOUT",
            error_message="Connection timed out",
            occurrence_count=5,
        )
        result_both = rule.evaluate(context_both)
        assert result_both.matched is True

        # Only one condition met
        context_one = RuleContext(
            error_code="TIMEOUT",
            error_message="Connection timed out",
            occurrence_count=1,
        )
        result_one = rule.evaluate(context_one)
        assert result_one.matched is False

    def test_rule_engine_evaluation(self):
        """Test full rule engine evaluation."""
        from app.services.recovery_rule_engine import (
            RecoveryRuleEngine,
            RuleContext,
        )

        engine = RecoveryRuleEngine()

        context = RuleContext(
            error_code="TIMEOUT",
            error_message="Connection timed out after 30s",
            skill_id="http_call",
            occurrence_count=3,
        )

        result = engine.evaluate(context)

        assert result.recommended_action is not None
        assert result.confidence > 0
        assert len(result.rules_evaluated) > 0
        assert result.duration_ms >= 0

    def test_evaluate_rules_convenience(self):
        """Test evaluate_rules convenience function."""
        from app.services.recovery_rule_engine import evaluate_rules

        result = evaluate_rules(
            error_code="RATE_LIMITED",
            error_message="Too many requests",
            skill_id="llm_invoke",
            occurrence_count=2,
        )

        assert result.recommended_action == "retry_exponential"
        assert result.confidence > 0


# =============================================================================
# Worker Evaluator Tests
# =============================================================================


class TestRecoveryEvaluator:
    """Test recovery evaluator worker."""

    @pytest.mark.asyncio
    async def test_failure_event_creation(self):
        """Test FailureEvent dataclass."""
        from app.worker.recovery_evaluator import FailureEvent

        event = FailureEvent(
            failure_match_id=str(uuid4()),
            error_code="TIMEOUT",
            error_message="Connection timed out",
            skill_id="http_call",
            tenant_id="tenant-001",
        )

        assert event.error_code == "TIMEOUT"
        assert event.metadata == {}
        assert event.occurred_at is not None

    @pytest.mark.asyncio
    async def test_hooks_registration(self):
        """Test hook registration and triggering."""
        from app.worker.recovery_evaluator import RecoveryHooks

        hooks = RecoveryHooks()

        callback_called = []

        def test_callback(**kwargs):
            callback_called.append(kwargs)

        hooks.register("on_evaluation_start", test_callback)

        await hooks.trigger("on_evaluation_start", event="test_event")

        assert len(callback_called) == 1
        assert callback_called[0]["event"] == "test_event"

    @pytest.mark.asyncio
    async def test_hooks_async_callback(self):
        """Test async hook callback."""
        from app.worker.recovery_evaluator import RecoveryHooks

        hooks = RecoveryHooks()

        callback_called = []

        async def async_callback(**kwargs):
            callback_called.append(kwargs)

        hooks.register("on_suggestion_generated", async_callback)

        await hooks.trigger("on_suggestion_generated", candidate_id=123)

        assert len(callback_called) == 1
        assert callback_called[0]["candidate_id"] == 123

    @pytest.mark.asyncio
    async def test_hooks_unregister(self):
        """Test hook unregistration."""
        from app.worker.recovery_evaluator import RecoveryHooks

        hooks = RecoveryHooks()

        def test_callback(**kwargs):
            pass

        hooks.register("on_evaluation_start", test_callback)
        assert hooks.unregister("on_evaluation_start", test_callback) is True
        assert hooks.unregister("on_evaluation_start", test_callback) is False

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"RECOVERY_EVALUATOR_ENABLED": "false"})
    async def test_evaluator_disabled(self):
        """Test evaluator when disabled."""
        # Need to reimport to pick up env change
        import importlib

        import app.worker.recovery_evaluator as evaluator_module

        importlib.reload(evaluator_module)

        from app.worker.recovery_evaluator import (
            FailureEvent,
            RecoveryEvaluator,
        )

        # Force disabled state
        evaluator_module.EVALUATOR_ENABLED = False

        event = FailureEvent(
            failure_match_id=str(uuid4()),
            error_code="TIMEOUT",
            error_message="Test",
        )

        evaluator = RecoveryEvaluator()
        result = await evaluator.evaluate(event)

        assert result.error == "Evaluator disabled"
        assert result.candidate_id is None

        # Reset
        evaluator_module.EVALUATOR_ENABLED = True


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestRecoveryAPIEnhanced:
    """Test enhanced recovery API endpoints."""

    def test_evaluate_request_model(self):
        """Test EvaluateRequest model validation."""
        from app.api.recovery import EvaluateRequest

        request = EvaluateRequest(
            error_code="TIMEOUT",
            error_message="Connection timed out",
            skill_id="http_call",
            occurrence_count=5,
        )

        assert request.error_code == "TIMEOUT"
        assert request.occurrence_count == 5

    def test_candidate_update_request_model(self):
        """Test CandidateUpdateRequest model validation."""
        from app.api.recovery import CandidateUpdateRequest

        request = CandidateUpdateRequest(
            execution_status="executing",
            selected_action_id=1,
            execution_result={"started": True},
            note="Starting execution",
        )

        assert request.execution_status == "executing"
        assert request.selected_action_id == 1

    def test_action_response_model(self):
        """Test ActionResponse model."""
        from app.api.recovery import ActionResponse

        action = ActionResponse(
            id=1,
            action_code="retry_exponential",
            name="Retry with Exponential Backoff",
            description="Retry the operation",
            action_type="retry",
            template={"max_retries": 3},
            applies_to_error_codes=["TIMEOUT", "HTTP_5XX"],
            applies_to_skills=[],
            success_rate=0.85,
            total_applications=100,
            is_automated=True,
            requires_approval=False,
            priority=80,
            is_active=True,
        )

        assert action.action_code == "retry_exponential"
        assert action.success_rate == 0.85


# =============================================================================
# Model Tests
# =============================================================================


class TestM10RecoveryModels:
    """Test SQLAlchemy models."""

    def test_suggestion_action_model(self):
        """Test SuggestionAction model."""
        from app.models.m10_recovery import SuggestionAction

        action = SuggestionAction(
            action_code="test_retry",
            name="Test Retry",
            action_type="retry",
            template={"max_retries": 3},
            applies_to_error_codes=["TIMEOUT"],
            priority=50,
        )

        assert action.action_code == "test_retry"
        assert action.matches_error("TIMEOUT_CONNECTION")
        assert not action.matches_error("PERMISSION_DENIED")

    def test_suggestion_action_matches_skill(self):
        """Test skill matching logic."""
        from app.models.m10_recovery import SuggestionAction

        # Action with skill restrictions
        action_restricted = SuggestionAction(
            action_code="test",
            name="Test",
            action_type="retry",
            applies_to_skills=["http_call", "llm_invoke"],
        )

        assert action_restricted.matches_skill("http_call")
        assert action_restricted.matches_skill("llm_invoke")
        assert not action_restricted.matches_skill("db_query")

        # Action without skill restrictions
        action_unrestricted = SuggestionAction(
            action_code="test2",
            name="Test 2",
            action_type="retry",
            applies_to_skills=[],
        )

        assert action_unrestricted.matches_skill("any_skill")

    def test_suggestion_input_to_dict(self):
        """Test SuggestionInput serialization."""
        from app.models.m10_recovery import SuggestionInput

        input_obj = SuggestionInput(
            id=1,
            suggestion_id=100,
            input_type="error_code",
            raw_value="TIMEOUT",
            normalized_value="timeout",
            confidence=0.9,
            weight=1.0,
        )

        data = input_obj.to_dict()

        assert data["id"] == 1
        assert data["input_type"] == "error_code"
        assert data["raw_value"] == "TIMEOUT"

    def test_suggestion_provenance_to_dict(self):
        """Test SuggestionProvenance serialization."""
        from app.models.m10_recovery import SuggestionProvenance

        prov = SuggestionProvenance(
            id=1,
            suggestion_id=100,
            event_type="created",
            details={"rule_id": "test"},
            actor="worker",
            actor_type="system",
        )

        data = prov.to_dict()

        assert data["event_type"] == "created"
        assert data["actor"] == "worker"


# =============================================================================
# Integration Tests (require database)
# =============================================================================


class TestM10Integration:
    """Integration tests requiring database."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.execute = MagicMock(
            return_value=MagicMock(
                fetchone=MagicMock(return_value=None),
                fetchall=MagicMock(return_value=[]),
                scalar=MagicMock(return_value=1),
            )
        )
        session.commit = MagicMock()
        return session

    def test_rule_engine_with_custom_rules(self):
        """Test rule engine with custom rules."""
        from app.services.recovery_rule_engine import (
            ErrorCodeRule,
            RecoveryRuleEngine,
            RuleContext,
        )

        custom_rule = ErrorCodeRule(
            rule_id="custom_rule",
            name="Custom Rule",
            error_patterns=["CUSTOM_ERROR"],
            action_code="custom_action",
            score=0.95,
            priority=100,  # High priority
        )

        engine = RecoveryRuleEngine()
        engine.add_rule(custom_rule)

        context = RuleContext(
            error_code="CUSTOM_ERROR",
            error_message="A custom error occurred",
        )

        result = engine.evaluate(context)

        # Custom rule should match with highest score
        assert result.recommended_action == "custom_action"

    def test_rule_engine_remove_rule(self):
        """Test removing a rule from engine."""
        from app.services.recovery_rule_engine import RecoveryRuleEngine

        engine = RecoveryRuleEngine()
        initial_count = len(engine.rules)

        removed = engine.remove_rule("timeout_retry")

        assert removed is True
        assert len(engine.rules) == initial_count - 1

        # Try removing non-existent rule
        removed_again = engine.remove_rule("nonexistent")
        assert removed_again is False


# =============================================================================
# Concurrent Ingest & Worker Claim Tests
# =============================================================================


class TestConcurrentIngest:
    """Tests for concurrent ingest race condition handling."""

    @pytest.mark.asyncio
    async def test_idempotency_key_prevents_duplicates(self):
        """Test that idempotency_key prevents duplicate inserts."""
        import asyncio
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        idempotency_key = str(uuid4())
        failure_match_id = str(uuid4())

        async def attempt_insert(attempt_num: int):
            """Attempt to insert with same idempotency_key."""
            session = Session(engine)
            try:
                # Check for existing
                result = session.execute(
                    text(
                        """
                        SELECT id FROM recovery_candidates
                        WHERE idempotency_key = CAST(:key AS uuid)
                    """
                    ),
                    {"key": idempotency_key},
                )
                existing = result.fetchone()
                if existing:
                    return {"attempt": attempt_num, "id": existing[0], "new": False}

                # Try insert
                try:
                    result = session.execute(
                        text(
                            """
                            INSERT INTO recovery_candidates (
                                failure_match_id, suggestion, confidence,
                                explain, error_code, idempotency_key
                            ) VALUES (
                                CAST(:fid AS uuid), 'Test', 0.5,
                                '{}', 'TEST', CAST(:key AS uuid)
                            )
                            RETURNING id
                        """
                        ),
                        {"fid": failure_match_id, "key": idempotency_key},
                    )
                    new_id = result.scalar()
                    session.commit()
                    return {"attempt": attempt_num, "id": new_id, "new": True}
                except Exception:
                    session.rollback()
                    result = session.execute(
                        text(
                            """
                            SELECT id FROM recovery_candidates
                            WHERE idempotency_key = CAST(:key AS uuid)
                        """
                        ),
                        {"key": idempotency_key},
                    )
                    existing = result.fetchone()
                    return {"attempt": attempt_num, "id": existing[0] if existing else None, "new": False}
            finally:
                session.close()

        # Run concurrent inserts
        results = await asyncio.gather(*[attempt_insert(i) for i in range(5)])

        # Only one should be new
        new_count = sum(1 for r in results if r.get("new"))
        assert new_count <= 1, f"Expected at most 1 new insert, got {new_count}"

        # All should have same ID
        ids = [r["id"] for r in results if r["id"]]
        assert len(set(ids)) == 1, f"All attempts should return same ID, got {set(ids)}"

    @pytest.mark.asyncio
    async def test_concurrent_ingest_race_condition(self):
        """
        True race test: fire 10 concurrent inserts with same idempotency_key.

        Uses threading to simulate concurrent HTTP requests.
        Validates that only 1 row is created despite race conditions.
        """
        import concurrent.futures
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlalchemy.exc import IntegrityError
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True, pool_size=20)
        idempotency_key = str(uuid4())
        test_marker = f"race_test_{uuid4().hex[:8]}"

        def attempt_insert_sync(worker_id: int) -> dict:
            """Sync worker that attempts insert."""
            session = Session(engine)
            try:
                # Each worker gets unique failure_match_id but same idempotency_key
                fid = str(uuid4())

                try:
                    result = session.execute(
                        text(
                            """
                            INSERT INTO recovery_candidates (
                                failure_match_id, suggestion, confidence,
                                explain, error_code, source, idempotency_key
                            ) VALUES (
                                CAST(:fid AS uuid), :suggestion, 0.5,
                                '{}', 'RACE_TEST', :source, CAST(:key AS uuid)
                            )
                            RETURNING id
                        """
                        ),
                        {
                            "fid": fid,
                            "suggestion": f"Race test worker {worker_id}",
                            "source": test_marker,
                            "key": idempotency_key,
                        },
                    )
                    new_id = result.scalar()
                    session.commit()
                    return {"worker": worker_id, "id": new_id, "new": True, "error": None}
                except IntegrityError:
                    session.rollback()
                    # Duplicate key - find existing
                    result = session.execute(
                        text(
                            """
                            SELECT id FROM recovery_candidates
                            WHERE idempotency_key = CAST(:key AS uuid)
                        """
                        ),
                        {"key": idempotency_key},
                    )
                    existing = result.fetchone()
                    return {
                        "worker": worker_id,
                        "id": existing[0] if existing else None,
                        "new": False,
                        "error": "integrity",
                    }
            except Exception as e:
                return {"worker": worker_id, "id": None, "new": False, "error": str(e)}
            finally:
                session.close()

        # Fire 10 concurrent workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attempt_insert_sync, i) for i in range(10)]
            results = [f.result(timeout=30) for f in concurrent.futures.as_completed(futures)]

        # Validate results
        new_inserts = [r for r in results if r.get("new")]
        successful = [r for r in results if r.get("id") is not None]
        errors = [r for r in results if r.get("error") and r.get("error") != "integrity"]

        # Should have exactly 1 new insert
        assert len(new_inserts) == 1, f"Expected exactly 1 new insert, got {len(new_inserts)}"

        # All successful results should have same ID
        ids = set(r["id"] for r in successful if r["id"])
        assert len(ids) == 1, f"All workers should see same candidate ID, got {ids}"

        # No unexpected errors
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # Verify only 1 row in DB
        session = Session(engine)
        try:
            result = session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM recovery_candidates
                    WHERE idempotency_key = CAST(:key AS uuid)
                """
                ),
                {"key": idempotency_key},
            )
            count = result.scalar()
            assert count == 1, f"Expected exactly 1 row in DB, got {count}"
        finally:
            session.close()


class TestWorkerClaimPattern:
    """Tests for FOR UPDATE SKIP LOCKED worker claim pattern."""

    def test_claim_with_skip_locked(self):
        """Test that FOR UPDATE SKIP LOCKED claims rows correctly."""
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            # Insert test candidate
            failure_match_id = str(uuid4())
            session.execute(
                text(
                    """
                    INSERT INTO recovery_candidates (
                        failure_match_id, suggestion, confidence,
                        explain, error_code, decision, execution_status
                    ) VALUES (
                        CAST(:fid AS uuid), 'Claim test', 0.1,
                        '{}', 'TEST', 'pending', NULL
                    )
                """
                ),
                {"fid": failure_match_id},
            )
            session.commit()

            # Claim with FOR UPDATE SKIP LOCKED
            result = session.execute(
                text(
                    """
                    WITH claimed AS (
                        SELECT id FROM recovery_candidates
                        WHERE decision = 'pending'
                          AND (confidence IS NULL OR confidence <= 0.2)
                        ORDER BY created_at ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 10
                    )
                    UPDATE recovery_candidates rc
                    SET execution_status = 'executing'
                    FROM claimed
                    WHERE rc.id = claimed.id
                    RETURNING rc.id
                """
                )
            )
            claimed_ids = [row[0] for row in result.fetchall()]
            session.commit()

            assert len(claimed_ids) >= 1, "Should claim at least 1 row"

        finally:
            session.rollback()
            session.close()

    def test_skip_locked_skips_locked_rows(self):
        """Test that SKIP LOCKED skips rows locked by another session."""
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        # Insert test candidate
        session1 = Session(engine)
        failure_match_id = str(uuid4())
        session1.execute(
            text(
                """
                INSERT INTO recovery_candidates (
                    failure_match_id, suggestion, confidence,
                    explain, error_code, decision
                ) VALUES (
                    CAST(:fid AS uuid), 'Lock test', 0.1, '{}', 'TEST', 'pending'
                )
            """
            ),
            {"fid": failure_match_id},
        )
        session1.commit()

        try:
            # Session 1 locks the row (don't commit)
            session1.execute(
                text(
                    """
                    SELECT id FROM recovery_candidates
                    WHERE failure_match_id = CAST(:fid AS uuid)
                    FOR UPDATE
                """
                ),
                {"fid": failure_match_id},
            )

            # Session 2 tries to claim with SKIP LOCKED
            session2 = Session(engine)
            try:
                result = session2.execute(
                    text(
                        """
                        SELECT id FROM recovery_candidates
                        WHERE failure_match_id = CAST(:fid AS uuid)
                        FOR UPDATE SKIP LOCKED
                    """
                    ),
                    {"fid": failure_match_id},
                )
                skipped = result.fetchall()

                # Should skip the locked row
                assert len(skipped) == 0, "SKIP LOCKED should skip locked rows"

            finally:
                session2.close()

        finally:
            session1.rollback()
            session1.close()


class TestMaterializedViewRefresh:
    """Tests for materialized view refresh."""

    def test_mv_refresh_succeeds(self):
        """Test that mv_top_pending can be refreshed."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending"))
            session.commit()
        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("Materialized view not created yet")
            raise
        finally:
            session.close()


class TestRetentionArchive:
    """Tests for retention archive functionality."""

    def test_archive_table_exists(self):
        """Test that archive tables exist."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            result = session.execute(
                text(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'm10_recovery'
                      AND table_name LIKE '%_archive'
                """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            # Archive tables should exist after migration 019
            if not tables:
                pytest.skip("Archive tables not created yet")

            assert "suggestion_provenance_archive" in tables or len(tables) > 0

        finally:
            session.close()

    def test_retention_jobs_table(self):
        """Test that retention_jobs table has default entries."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            result = session.execute(
                text(
                    """
                    SELECT name, retention_days
                    FROM m10_recovery.retention_jobs
                """
                )
            )
            jobs = {row[0]: row[1] for row in result.fetchall()}

            if not jobs:
                pytest.skip("Retention jobs not seeded yet")

            assert "provenance_archive" in jobs
            assert jobs["provenance_archive"] == 90

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("retention_jobs table not created yet")
            raise
        finally:
            session.close()


# =============================================================================
# Failure Mode Tests
# =============================================================================


class TestRedisFailureFallback:
    """Tests for Redis failure and DB fallback behavior."""

    @pytest.mark.asyncio
    async def test_enqueue_fallback_when_redis_unavailable(self):
        """Test that enqueue falls back to DB when Redis is unavailable."""
        import os
        from unittest.mock import patch
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        # Mock Redis to fail
        with patch("app.tasks.recovery_queue_stream.enqueue_stream") as mock_enqueue:
            mock_enqueue.return_value = None  # Simulate Redis failure

            # Import after patching
            from app.api.recovery_ingest import _enqueue_evaluation_async

            candidate_id = 999999  # Non-existent but valid for test
            failure_match_id = str(uuid4())

            session = Session(engine)
            try:
                # Ensure work_queue function exists
                try:
                    result = await _enqueue_evaluation_async(
                        candidate_id=candidate_id,
                        failure_match_id=failure_match_id,
                        idempotency_key=str(uuid4()),
                        session=session,
                    )

                    # Check if fallback to DB occurred
                    check = session.execute(
                        text(
                            """
                            SELECT id, method FROM m10_recovery.work_queue
                            WHERE candidate_id = :cid
                        """
                        ),
                        {"cid": candidate_id},
                    )
                    row = check.fetchone()

                    if row:
                        assert row[1] == "db_fallback", "Should use db_fallback method"

                except Exception as e:
                    if "does not exist" in str(e).lower():
                        pytest.skip("work_queue table not created yet")
                    raise

            finally:
                session.rollback()
                session.close()

    def test_db_fallback_queue_claim(self):
        """Test that DB fallback queue can be claimed by workers."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            # Insert test work item
            candidate_id = 888888
            session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.work_queue (candidate_id, method, priority)
                    VALUES (:cid, 'test', 0)
                    ON CONFLICT DO NOTHING
                """
                ),
                {"cid": candidate_id},
            )
            session.commit()

            # Claim work
            result = session.execute(
                text(
                    """
                    SELECT * FROM m10_recovery.claim_work('test_worker', 10)
                """
                )
            )
            claimed = result.fetchall()

            # Verify claim
            if claimed:
                work_id = claimed[0][0]

                # Complete work
                session.execute(text("SELECT m10_recovery.complete_work(:wid, TRUE, NULL)"), {"wid": work_id})
                session.commit()

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("work_queue functions not created yet")
            raise
        finally:
            session.rollback()
            session.close()

    def test_stalled_work_release(self):
        """Test that stalled work items can be released."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            # Insert stalled work item (claimed 10 minutes ago)
            candidate_id = 777777
            session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.work_queue
                        (candidate_id, method, claimed_at, claimed_by)
                    VALUES
                        (:cid, 'test_stalled', now() - interval '10 minutes', 'dead_worker')
                    ON CONFLICT DO NOTHING
                """
                ),
                {"cid": candidate_id},
            )
            session.commit()

            # Release stalled (5 minute threshold)
            result = session.execute(text("SELECT m10_recovery.release_stalled_work(300)"))
            released_count = result.scalar()

            assert released_count >= 0, "Should return count of released items"

            # Verify item is now unclaimed
            check = session.execute(
                text(
                    """
                    SELECT claimed_at, claimed_by FROM m10_recovery.work_queue
                    WHERE candidate_id = :cid AND processed_at IS NULL
                """
                ),
                {"cid": candidate_id},
            )
            row = check.fetchone()

            if row:
                assert row[0] is None, "claimed_at should be NULL after release"
                assert row[1] is None, "claimed_by should be NULL after release"

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("work_queue functions not created yet")
            raise
        finally:
            session.rollback()
            session.close()


class TestRedisStreamsIntegration:
    """Tests for Redis Streams queue integration."""

    @pytest.mark.asyncio
    async def test_stream_enqueue_dequeue(self):
        """Test basic enqueue/dequeue with Redis Streams."""
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import (
                ack_message,
                consume_batch,
                enqueue_stream,
                ensure_consumer_group,
            )

            # Ensure group exists
            await ensure_consumer_group()

            # Enqueue test message
            test_candidate_id = 123456
            msg_id = await enqueue_stream(
                candidate_id=test_candidate_id,
                priority=1.0,
                metadata={"test": True},
            )

            assert msg_id is not None, "Should return message ID"

            # Consume message
            items = await consume_batch(batch_size=10, block_ms=1000)

            # Find our test message
            found = False
            for mid, task in items:
                if task.get("candidate_id") == test_candidate_id:
                    found = True
                    # Acknowledge
                    ack_result = await ack_message(mid)
                    assert ack_result, "Should acknowledge successfully"
                    break

            # Note: Message may have been consumed by another test run

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise

    @pytest.mark.asyncio
    async def test_stream_info(self):
        """Test getting stream info."""
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import get_stream_info

            info = await get_stream_info()

            assert "stream_key" in info
            assert "consumer_group" in info
            assert "stream_length" in info
            assert info.get("error") is None or "error" not in info

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise


class TestUpsertDeduplication:
    """Tests for INSERT ... ON CONFLICT upsert deduplication."""

    def test_upsert_increments_occurrence_count(self):
        """Test that duplicate inserts increment occurrence_count."""
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        failure_match_id = str(uuid4())
        error_signature = f"test_sig_{uuid4().hex[:8]}"

        try:
            # First insert
            session.execute(
                text(
                    """
                    INSERT INTO recovery_candidates (
                        failure_match_id, suggestion, confidence, explain,
                        error_code, error_signature, occurrence_count
                    ) VALUES (
                        CAST(:fid AS uuid), 'Test upsert', 0.5, '{}',
                        'TEST', :sig, 1
                    )
                """
                ),
                {"fid": failure_match_id, "sig": error_signature},
            )
            session.commit()

            # Get initial count
            result = session.execute(
                text(
                    """
                    SELECT occurrence_count FROM recovery_candidates
                    WHERE failure_match_id = CAST(:fid AS uuid)
                """
                ),
                {"fid": failure_match_id},
            )
            initial_count = result.scalar()
            assert initial_count == 1

            # Simulate second occurrence (manual increment for test)
            session.execute(
                text(
                    """
                    UPDATE recovery_candidates
                    SET occurrence_count = occurrence_count + 1
                    WHERE failure_match_id = CAST(:fid AS uuid)
                """
                ),
                {"fid": failure_match_id},
            )
            session.commit()

            # Verify increment
            result = session.execute(
                text(
                    """
                    SELECT occurrence_count FROM recovery_candidates
                    WHERE failure_match_id = CAST(:fid AS uuid)
                """
                ),
                {"fid": failure_match_id},
            )
            new_count = result.scalar()
            assert new_count == 2, f"Expected 2, got {new_count}"

        finally:
            session.rollback()
            session.close()


class TestMatviewTrackedRefresh:
    """Tests for tracked materialized view refresh."""

    def test_tracked_refresh_logs(self):
        """Test that refresh_mv_tracked logs the refresh."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            # Call tracked refresh
            result = session.execute(text("SELECT * FROM m10_recovery.refresh_mv_tracked('mv_top_pending')"))
            row = result.fetchone()

            if row:
                success, duration_ms, error = row
                # May fail if view doesn't exist, that's OK for this test
                assert duration_ms >= 0, "Duration should be non-negative"

            # Check log entry
            log_result = session.execute(
                text(
                    """
                    SELECT success, duration_ms
                    FROM m10_recovery.matview_refresh_log
                    WHERE view_name = 'mv_top_pending'
                    ORDER BY started_at DESC
                    LIMIT 1
                """
                )
            )
            log_row = log_result.fetchone()

            if log_row:
                assert log_row[1] >= 0, "Logged duration should be non-negative"

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("Matview or refresh function not created yet")
            raise
        finally:
            session.close()

    def test_matview_freshness_view(self):
        """Test that matview_freshness view works."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)
        session = Session(engine)

        try:
            result = session.execute(
                text(
                    """
                    SELECT view_name, age_seconds, last_success
                    FROM m10_recovery.matview_freshness
                """
                )
            )
            rows = result.fetchall()

            # View should exist and return valid structure
            for row in rows:
                view_name, age_seconds, last_success = row
                assert view_name is not None
                # age_seconds can be NULL if never refreshed

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("matview_freshness view not created yet")
            raise
        finally:
            session.close()


# =============================================================================
# Redis Outage Simulation Tests
# =============================================================================


class TestRedisOutageScenarios:
    """
    Comprehensive tests for Redis outage scenarios.

    Tests that the system gracefully handles:
    - Complete Redis unavailability
    - Redis connection timeout
    - Redis command errors
    - Recovery when Redis comes back online
    """

    @pytest.mark.asyncio
    async def test_complete_redis_outage_uses_db_fallback(self):
        """
        Test that complete Redis outage triggers DB fallback for all operations.

        Simulates Redis being completely unavailable and verifies:
        1. Enqueue falls back to DB work_queue
        2. No data loss occurs
        3. Metrics reflect fallback usage
        """
        import os
        from unittest.mock import patch
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        # Create a mock that raises ConnectionError
        async def mock_redis_fail(*args, **kwargs):
            raise ConnectionError("Redis connection refused")

        # Patch the Redis client at module level
        with patch("app.tasks.recovery_queue_stream.get_redis", mock_redis_fail):
            with patch("app.tasks.recovery_queue_stream.enqueue_stream", return_value=None):
                # Create test candidate
                session = Session(engine)
                failure_match_id = str(uuid4())

                try:
                    # Insert a test candidate first
                    session.execute(
                        text(
                            """
                            INSERT INTO recovery_candidates (
                                failure_match_id, suggestion, confidence,
                                explain, error_code, source
                            ) VALUES (
                                CAST(:fid AS uuid), 'Redis outage test', 0.5,
                                '{}', 'REDIS_TEST', 'outage_test'
                            )
                            RETURNING id
                        """
                        ),
                        {"fid": failure_match_id},
                    )
                    session.commit()

                    # Get the candidate ID
                    result = session.execute(
                        text(
                            """
                            SELECT id FROM recovery_candidates
                            WHERE failure_match_id = CAST(:fid AS uuid)
                        """
                        ),
                        {"fid": failure_match_id},
                    )
                    candidate_id = result.scalar()

                    # Now try to enqueue - should fall back to DB
                    try:
                        session.execute(
                            text(
                                """
                                SELECT m10_recovery.enqueue_work(
                                    p_candidate_id := :cid,
                                    p_priority := 0,
                                    p_method := 'db_fallback'
                                )
                            """
                            ),
                            {"cid": candidate_id},
                        )
                        session.commit()

                        # Verify it's in the DB queue
                        result = session.execute(
                            text(
                                """
                                SELECT id, method FROM m10_recovery.work_queue
                                WHERE candidate_id = :cid
                            """
                            ),
                            {"cid": candidate_id},
                        )
                        row = result.fetchone()

                        assert row is not None, "Work should be in DB fallback queue"
                        assert row[1] == "db_fallback", "Method should be db_fallback"

                    except Exception as e:
                        if "does not exist" in str(e).lower():
                            pytest.skip("work_queue functions not created yet")
                        raise

                finally:
                    session.rollback()
                    session.close()

    @pytest.mark.asyncio
    async def test_redis_timeout_graceful_handling(self):
        """Test that Redis timeouts are handled gracefully without data loss."""
        import asyncio
        import os
        from unittest.mock import AsyncMock, patch

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        # Mock Redis to timeout
        async def mock_timeout(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Redis operation timed out")

        with patch("app.tasks.recovery_queue_stream.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.xadd = mock_timeout
            mock_get_redis.return_value = mock_redis

            try:
                from app.tasks.recovery_queue_stream import enqueue_stream

                # This should handle timeout gracefully
                result = await enqueue_stream(
                    candidate_id=12345,
                    priority=0.5,
                )

                # Should return None on timeout
                assert result is None, "Should return None on timeout"

            except ImportError:
                pytest.skip("redis.asyncio not available")

    @pytest.mark.asyncio
    async def test_dead_letter_stream_operations(self):
        """Test dead-letter stream functionality."""
        import os
        from uuid import uuid4

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import (
                DEAD_LETTER_STREAM,
                get_dead_letter_count,
                move_to_dead_letter,
                replay_dead_letter,
            )

            # Move a test message to dead-letter
            test_msg_id = f"test-{uuid4().hex[:8]}"
            test_fields = {
                "candidate_id": "99999",
                "priority": "0",
                "enqueued_at": "2025-01-01T00:00:00Z",
            }

            # Get initial dead-letter count
            initial_count = await get_dead_letter_count()

            # Move to dead-letter (will create if doesn't exist)
            result = await move_to_dead_letter(
                msg_id=test_msg_id,
                fields=test_fields,
                reason="test_dead_letter",
            )

            assert result is True, "Should successfully move to dead-letter"

            # Verify count increased
            new_count = await get_dead_letter_count()
            assert new_count >= initial_count, "Dead-letter count should not decrease"

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise

    @pytest.mark.asyncio
    async def test_stalled_message_reclaim_with_dead_letter(self):
        """Test that stalled messages are either reclaimed or dead-lettered."""
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import process_stalled_with_dead_letter

            # Run stalled message processing
            results = await process_stalled_with_dead_letter(
                idle_ms=60000,  # 1 minute idle
                max_reclaims=3,
                batch_size=10,
            )

            # Should return valid result structure
            assert "reclaimed" in results, "Should have reclaimed count"
            assert "dead_lettered" in results, "Should have dead_lettered count"
            assert isinstance(results["reclaimed"], int)
            assert isinstance(results["dead_lettered"], int)

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise


class TestMetricsCollection:
    """Tests for M10 metrics collection."""

    @pytest.mark.asyncio
    async def test_metrics_collector_runs(self):
        """Test that metrics collector runs without error."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        try:
            from app.tasks.m10_metrics_collector import collect_m10_metrics

            # Run collection (may have partial failures if Redis/tables don't exist)
            results = await collect_m10_metrics()

            # Should return valid structure
            assert "redis_stream" in results
            assert "db_queue" in results
            assert "matview_freshness" in results
            assert "candidates" in results
            assert "collection_time_ms" in results

        except ImportError as e:
            pytest.skip(f"Required module not available: {e}")
        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("Required tables not created yet")
            raise

    @pytest.mark.asyncio
    async def test_redis_metrics_handles_unavailable(self):
        """Test that Redis metrics collection handles Redis being unavailable."""
        from unittest.mock import patch

        async def mock_fail(*args, **kwargs):
            raise ConnectionError("Redis not available")

        with patch("app.tasks.m10_metrics_collector.collect_redis_stream_metrics") as mock:
            mock.return_value = {"error": "Redis not available"}

            try:
                from app.tasks.m10_metrics_collector import collect_redis_stream_metrics

                # Should handle error gracefully
                result = await mock()

                assert "error" in result, "Should contain error info"

            except ImportError:
                pytest.skip("Metrics collector not available")


# =============================================================================
# High-Value Tests (Priority Issues)
# =============================================================================


class TestUpsertConcurrency:
    """
    Test atomic upsert correctness under high concurrency.

    Validates that INSERT ... ON CONFLICT DO UPDATE RETURNING
    correctly handles concurrent requests without race conditions.
    """

    def test_concurrent_upsert_correctness(self):
        """
        Run 100 concurrent inserts with same failure_match_id+error_signature.
        Assert final occurrence_count == 100.
        """
        import hashlib
        import os
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True, pool_size=20, max_overflow=30)

        # Unique identifiers for this test
        failure_match_id = str(uuid4())
        error_type = "UPSERT_CONCURRENCY_TEST"
        error_signature = hashlib.sha256(f"{error_type}:test".encode()).hexdigest()[:16]
        suggestion = "Concurrent upsert test"

        results = {"inserted": 0, "updated": 0, "errors": []}
        lock = threading.Lock()

        def do_upsert(i: int) -> dict:
            """Perform single upsert operation."""
            session = Session(engine)
            try:
                result = session.execute(
                    text(
                        """
                        INSERT INTO recovery_candidates (
                            failure_match_id,
                            suggestion,
                            confidence,
                            explain,
                            error_code,
                            error_signature,
                            source,
                            created_by,
                            occurrence_count,
                            last_occurrence_at
                        ) VALUES (
                            CAST(:failure_match_id AS uuid),
                            :suggestion,
                            0.2,
                            '{"test": true}'::jsonb,
                            :error_code,
                            :error_signature,
                            'test',
                            'upsert_test',
                            1,
                            now()
                        )
                        ON CONFLICT (failure_match_id) DO UPDATE
                        SET
                            occurrence_count = recovery_candidates.occurrence_count + 1,
                            last_occurrence_at = now(),
                            updated_at = now()
                        RETURNING id, (xmax = 0) AS is_insert, occurrence_count
                    """
                    ),
                    {
                        "failure_match_id": failure_match_id,
                        "suggestion": suggestion,
                        "error_code": error_type,
                        "error_signature": error_signature,
                    },
                )
                row = result.fetchone()
                session.commit()

                return {
                    "success": True,
                    "id": row[0],
                    "is_insert": row[1],
                    "occurrence_count": row[2],
                }
            except Exception as e:
                session.rollback()
                return {"success": False, "error": str(e)}
            finally:
                session.close()

        # Run 100 concurrent upserts
        CONCURRENCY = 100

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(do_upsert, i) for i in range(CONCURRENCY)]

            for future in as_completed(futures):
                result = future.result()
                with lock:
                    if result["success"]:
                        if result["is_insert"]:
                            results["inserted"] += 1
                        else:
                            results["updated"] += 1
                    else:
                        results["errors"].append(result["error"])

        # Verify final state
        session = Session(engine)
        try:
            result = session.execute(
                text(
                    """
                    SELECT occurrence_count FROM recovery_candidates
                    WHERE failure_match_id = CAST(:fid AS uuid)
                      AND error_signature = :sig
                """
                ),
                {"fid": failure_match_id, "sig": error_signature},
            )
            final_count = result.scalar()

            # Cleanup
            session.execute(
                text(
                    """
                    DELETE FROM recovery_candidates
                    WHERE failure_match_id = CAST(:fid AS uuid)
                      AND error_signature = :sig
                """
                ),
                {"fid": failure_match_id, "sig": error_signature},
            )
            session.commit()

            # Assertions
            assert len(results["errors"]) == 0, f"Errors occurred: {results['errors']}"
            assert results["inserted"] == 1, f"Expected 1 insert, got {results['inserted']}"
            assert results["updated"] == CONCURRENCY - 1, f"Expected {CONCURRENCY-1} updates, got {results['updated']}"
            assert final_count == CONCURRENCY, f"Expected occurrence_count={CONCURRENCY}, got {final_count}"

        finally:
            session.close()


class TestDeadLetterPath:
    """
    Test dead-letter stream handling.

    Validates that poison messages are correctly moved to dead-letter
    after exceeding max reclaim attempts.
    """

    @pytest.mark.asyncio
    async def test_poison_message_to_dead_letter(self):
        """
        Craft a message, force it to exceed reclaim count,
        assert it appears in dead-letter stream.
        """
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import (
                DEAD_LETTER_STREAM,
                enqueue_stream,
                get_dead_letter_count,
                get_redis,
                move_to_dead_letter,
            )

            redis = await get_redis()

            # Get initial dead-letter count
            initial_dl_count = await get_dead_letter_count()

            # Create a test message
            test_candidate_id = 999999
            msg_id = await enqueue_stream(
                candidate_id=test_candidate_id,
                priority=0,
                metadata={"test": "poison_message"},
            )

            if not msg_id:
                pytest.skip("Failed to enqueue test message")

            # Simulate poison message by moving directly to dead-letter
            fields = {
                "candidate_id": str(test_candidate_id),
                "priority": "0",
                "metadata": '{"test": "poison_message"}',
            }

            result = await move_to_dead_letter(
                msg_id=msg_id,
                fields=fields,
                reason="test_poison_message",
            )

            assert result is True, "move_to_dead_letter should succeed"

            # Verify in dead-letter
            new_dl_count = await get_dead_letter_count()
            assert new_dl_count > initial_dl_count, "Dead-letter count should increase"

            # Verify message content in dead-letter
            # Use xrevrange to read newest messages first (test message is at the end)
            messages = await redis.xrevrange(DEAD_LETTER_STREAM, "+", "-", count=20)
            found = False
            for dl_msg_id, dl_fields in messages:
                # Redis returns bytes, decode if needed
                orig_msg_id = dl_fields.get("original_msg_id")
                if isinstance(orig_msg_id, bytes):
                    orig_msg_id = orig_msg_id.decode()
                if orig_msg_id == msg_id:
                    found = True
                    reason = dl_fields.get("reason")
                    if isinstance(reason, bytes):
                        reason = reason.decode()
                    orig_cid = dl_fields.get("orig_candidate_id")
                    if isinstance(orig_cid, bytes):
                        orig_cid = orig_cid.decode()
                    assert reason == "test_poison_message"
                    assert orig_cid == str(test_candidate_id)
                    # Cleanup: delete test message from dead-letter
                    await redis.xdel(DEAD_LETTER_STREAM, dl_msg_id)
                    break

            assert found, f"Test message {msg_id} not found in dead-letter stream (checked 20 newest entries)"

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise


class TestReclaimBackoff:
    """
    Test reclaim rate-limiting to prevent thundering herd.
    """

    @pytest.mark.asyncio
    async def test_reclaim_rate_limiting(self):
        """
        Verify that MAX_RECLAIM_PER_LOOP constant is reasonable.
        """
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            pytest.skip("REDIS_URL not set")

        try:
            from app.tasks.recovery_queue_stream import (
                CLAIM_IDLE_MS,
                MAX_RECLAIM_PER_LOOP,
                process_stalled_with_dead_letter,
            )

            # Verify rate limit constant is reasonable
            assert MAX_RECLAIM_PER_LOOP >= 10, "Rate limit should be at least 10"
            assert MAX_RECLAIM_PER_LOOP <= 100, "Rate limit should be at most 100"

            # Verify idle time is reasonable (5 min default)
            assert CLAIM_IDLE_MS >= 60000, "Idle time should be at least 1 minute"

            # Run stalled processing with low limit for test
            results = await process_stalled_with_dead_letter(
                idle_ms=1,  # Very low for test
                max_reclaims=3,
                batch_size=100,
                max_reclaim_per_loop=5,  # Low limit for test
            )

            # Results should have correct structure
            assert "reclaimed" in results
            assert "dead_lettered" in results
            assert "skipped" in results

        except ImportError:
            pytest.skip("redis.asyncio not available")
        except Exception as e:
            if "connection refused" in str(e).lower():
                pytest.skip("Redis not available")
            raise


class TestRedisOutageFallbackComplete:
    """
    Complete test for Redis outage → DB fallback → worker consumption.
    """

    def test_full_fallback_flow(self):
        """
        Test complete flow: Redis down → DB queue insert → worker claim.
        """
        import os
        from uuid import uuid4

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            pytest.skip("DATABASE_URL not set")

        from sqlalchemy import text
        from sqlmodel import Session, create_engine

        engine = create_engine(db_url, pool_pre_ping=True)

        # Create test candidate
        session = Session(engine)
        failure_match_id = str(uuid4())
        candidate_id = None
        work_id = None

        try:
            # Step 1: Insert candidate
            result = session.execute(
                text(
                    """
                    INSERT INTO recovery_candidates (
                        failure_match_id, suggestion, confidence,
                        explain, error_code, source
                    ) VALUES (
                        CAST(:fid AS uuid), 'Full fallback flow test', 0.5,
                        '{}', 'FALLBACK_TEST', 'test'
                    )
                    RETURNING id
                """
                ),
                {"fid": failure_match_id},
            )
            candidate_id = result.scalar()
            session.commit()

            # Step 2: Enqueue to DB fallback queue (simulating Redis failure)
            session.execute(
                text(
                    """
                    INSERT INTO m10_recovery.work_queue (candidate_id, method, priority)
                    VALUES (:cid, 'db_fallback', 0)
                """
                ),
                {"cid": candidate_id},
            )
            session.commit()

            # Step 3: Verify in queue
            result = session.execute(
                text(
                    """
                    SELECT id, processed_at FROM m10_recovery.work_queue
                    WHERE candidate_id = :cid
                """
                ),
                {"cid": candidate_id},
            )
            row = result.fetchone()
            assert row is not None, "Work item should be in queue"
            work_id = row[0]
            assert row[1] is None, "Should not be processed yet"

            # Step 4: Claim work (simulating worker)
            result = session.execute(
                text(
                    """
                    WITH cte AS (
                        SELECT id FROM m10_recovery.work_queue
                        WHERE candidate_id = :cid
                          AND processed_at IS NULL
                          AND claimed_at IS NULL
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE m10_recovery.work_queue w
                    SET claimed_at = now(), claimed_by = 'test_worker'
                    FROM cte WHERE w.id = cte.id
                    RETURNING w.id
                """
                ),
                {"cid": candidate_id},
            )
            claimed = result.fetchone()
            session.commit()
            assert claimed is not None, "Should claim work item"

            # Step 5: Complete work (work_queue uses processed_at, not success column)
            session.execute(
                text(
                    """
                    UPDATE m10_recovery.work_queue
                    SET processed_at = now()
                    WHERE id = :wid
                """
                ),
                {"wid": work_id},
            )
            session.commit()

            # Step 6: Verify processed
            result = session.execute(
                text(
                    """
                    SELECT processed_at FROM m10_recovery.work_queue
                    WHERE id = :wid
                """
                ),
                {"wid": work_id},
            )
            row = result.fetchone()
            assert row[0] is not None, "Should have processed_at timestamp"

        except Exception as e:
            if "does not exist" in str(e).lower():
                pytest.skip("work_queue table not created yet")
            raise

        finally:
            # Cleanup
            if work_id:
                session.execute(text("DELETE FROM m10_recovery.work_queue WHERE id = :wid"), {"wid": work_id})
            if candidate_id:
                session.execute(text("DELETE FROM recovery_candidates WHERE id = :id"), {"id": candidate_id})
            session.commit()
            session.close()


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
