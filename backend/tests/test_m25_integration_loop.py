"""
M25 Integration Loop Tests

Tests for the 5-pillar integration feedback loop:
Incident → Pattern → Recovery → Policy → Routing

Tests cover:
- Confidence band matching (strong/weak/novel)
- Policy shadow mode and N-confirmation activation
- CARE routing guardrails
- Loop failure states
- Human checkpoint handling
- Narrative artifact generation
"""

import hashlib
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.integrations.bridges import (
    IncidentToCatalogBridge,
    PatternToRecoveryBridge,
    RecoveryToPolicyBridge,
)
from app.integrations.dispatcher import DispatcherConfig, IntegrationDispatcher

# Import the integration module
from app.integrations.events import (
    ConfidenceBand,
    HumanCheckpoint,
    HumanCheckpointType,
    LoopEvent,
    LoopFailureState,
    LoopStage,
    LoopStatus,
    PatternMatchResult,
    PolicyMode,
    PolicyRule,
    RoutingAdjustment,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def dispatcher_config():
    """Standard dispatcher configuration."""
    return DispatcherConfig(
        enable_pattern_matching=True,
        enable_recovery_suggestion=True,
        enable_policy_generation=True,
        enable_routing_adjustment=True,
        strong_match_threshold=0.85,
        weak_match_threshold=0.60,
        policy_confirmations_required=3,
        routing_max_delta=0.2,
        routing_decay_days=7,
        routing_rollback_threshold=0.1,
    )


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.publish = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    return redis


# ============================================================================
# Test Confidence Bands
# ============================================================================


class TestConfidenceBands:
    """Tests for confidence band classification."""

    def test_strong_match_threshold(self, dispatcher_config):
        """Test that matches above 0.85 are classified as STRONG."""
        result = PatternMatchResult(
            incident_id="inc_001",
            pattern_id="pat_001",
            confidence=0.92,
            matched_at=datetime.utcnow(),
        )
        assert result.confidence_band == ConfidenceBand.STRONG

    def test_weak_match_threshold(self, dispatcher_config):
        """Test that matches between 0.60-0.85 are classified as WEAK."""
        result = PatternMatchResult(
            incident_id="inc_001",
            pattern_id="pat_001",
            confidence=0.72,
            matched_at=datetime.utcnow(),
        )
        assert result.confidence_band == ConfidenceBand.WEAK

    def test_novel_match_threshold(self, dispatcher_config):
        """Test that matches below 0.60 are classified as NOVEL."""
        result = PatternMatchResult(
            incident_id="inc_001",
            pattern_id=None,  # No pattern found
            confidence=0.45,
            matched_at=datetime.utcnow(),
        )
        assert result.confidence_band == ConfidenceBand.NOVEL

    def test_edge_case_exactly_strong_threshold(self):
        """Test exact 0.85 boundary - should be STRONG."""
        result = PatternMatchResult(
            incident_id="inc_001",
            pattern_id="pat_001",
            confidence=0.85,
            matched_at=datetime.utcnow(),
        )
        assert result.confidence_band == ConfidenceBand.STRONG

    def test_edge_case_exactly_weak_threshold(self):
        """Test exact 0.60 boundary - should be WEAK."""
        result = PatternMatchResult(
            incident_id="inc_001",
            pattern_id="pat_001",
            confidence=0.60,
            matched_at=datetime.utcnow(),
        )
        assert result.confidence_band == ConfidenceBand.WEAK


# ============================================================================
# Test Policy Shadow Mode
# ============================================================================


class TestPolicyShadowMode:
    """Tests for policy shadow mode and N-confirmation activation."""

    def test_new_policy_starts_in_shadow_mode(self):
        """New auto-generated policies should start in SHADOW mode."""
        policy = PolicyRule(
            id="pol_001",
            tenant_id="tenant_001",
            source_type="recovery",
            source_recovery_id="rec_001",
            condition={"error_type": "timeout"},
            action="block",
            mode=PolicyMode.SHADOW,
            confirmations_required=3,
            confirmations_received=0,
        )
        assert policy.mode == PolicyMode.SHADOW
        assert not policy.is_active()

    def test_policy_promotion_to_pending(self):
        """Policy should move to PENDING after first confirmation."""
        policy = PolicyRule(
            id="pol_001",
            tenant_id="tenant_001",
            source_type="recovery",
            mode=PolicyMode.SHADOW,
            confirmations_required=3,
            confirmations_received=0,
        )
        policy.add_confirmation()
        assert policy.mode == PolicyMode.PENDING
        assert policy.confirmations_received == 1

    def test_policy_activation_after_n_confirmations(self):
        """Policy should become ACTIVE after N confirmations."""
        policy = PolicyRule(
            id="pol_001",
            tenant_id="tenant_001",
            source_type="recovery",
            mode=PolicyMode.SHADOW,
            confirmations_required=3,
            confirmations_received=0,
        )
        # Add N confirmations
        for _ in range(3):
            policy.add_confirmation()
        assert policy.mode == PolicyMode.ACTIVE
        assert policy.is_active()

    def test_policy_regret_tracking(self):
        """Policy should track regret count when it causes incidents."""
        policy = PolicyRule(
            id="pol_001",
            tenant_id="tenant_001",
            mode=PolicyMode.ACTIVE,
            regret_count=0,
        )
        policy.record_regret()
        assert policy.regret_count == 1

    def test_policy_shadow_evaluation_tracking(self):
        """Shadow mode should track what would have been blocked."""
        policy = PolicyRule(
            id="pol_001",
            tenant_id="tenant_001",
            mode=PolicyMode.SHADOW,
            shadow_evaluations=0,
            shadow_would_block=0,
        )
        policy.record_shadow_evaluation(would_block=True)
        policy.record_shadow_evaluation(would_block=False)
        policy.record_shadow_evaluation(would_block=True)
        assert policy.shadow_evaluations == 3
        assert policy.shadow_would_block == 2


# ============================================================================
# Test CARE Routing Guardrails
# ============================================================================


class TestRoutingGuardrails:
    """Tests for CARE routing guardrails."""

    def test_max_delta_guardrail(self):
        """Routing adjustment should be capped at max_delta."""
        adjustment = RoutingAdjustment(
            id="adj_001",
            agent_id="agent_001",
            capability="math_solver",
            adjustment_type="confidence_penalty",
            magnitude=0.5,  # Tries to adjust 50%
            max_delta=0.2,  # But max is 20%
        )
        assert adjustment.effective_magnitude() == 0.2

    def test_decay_window_calculation(self):
        """Adjustment should decay over configured days."""
        adjustment = RoutingAdjustment(
            id="adj_001",
            agent_id="agent_001",
            adjustment_type="confidence_penalty",
            magnitude=0.2,
            decay_days=7,
            created_at=datetime.utcnow() - timedelta(days=3.5),
        )
        # After 3.5 days of 7, should be ~50% decayed
        effective = adjustment.decayed_magnitude()
        assert 0.09 <= effective <= 0.11  # Roughly 0.1

    def test_kpi_regression_triggers_rollback(self):
        """Should rollback when KPI drops below threshold."""
        adjustment = RoutingAdjustment(
            id="adj_001",
            agent_id="agent_001",
            adjustment_type="confidence_penalty",
            magnitude=0.2,
            rollback_threshold=0.1,
            kpi_baseline=0.95,
            kpi_current=0.82,  # Dropped 13.7%
        )
        assert adjustment.should_rollback()

    def test_no_rollback_within_threshold(self):
        """Should not rollback when KPI is within threshold."""
        adjustment = RoutingAdjustment(
            id="adj_001",
            agent_id="agent_001",
            adjustment_type="confidence_penalty",
            magnitude=0.2,
            rollback_threshold=0.1,
            kpi_baseline=0.95,
            kpi_current=0.90,  # Dropped only 5.3%
        )
        assert not adjustment.should_rollback()


# ============================================================================
# Test Loop Failure States
# ============================================================================


class TestLoopFailureStates:
    """Tests for loop failure state handling."""

    def test_match_failed_state(self):
        """Test MATCH_FAILED state when no pattern found."""
        event = LoopEvent(
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.PATTERN_MATCHED,
            failure_state=LoopFailureState.MATCH_FAILED,
            details={"reason": "No similar patterns found"},
        )
        assert event.is_failure()
        assert event.failure_state == LoopFailureState.MATCH_FAILED

    def test_recovery_rejected_state(self):
        """Test RECOVERY_REJECTED state when suggestion is rejected."""
        event = LoopEvent(
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.RECOVERY_SUGGESTED,
            failure_state=LoopFailureState.RECOVERY_REJECTED,
            details={"rejected_by": "user_001"},
        )
        assert event.is_failure()

    def test_policy_shadow_mode_state(self):
        """Test POLICY_SHADOW_MODE state for new policies."""
        event = LoopEvent(
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.POLICY_GENERATED,
            failure_state=LoopFailureState.POLICY_SHADOW_MODE,
            details={"policy_id": "pol_001", "mode": "shadow"},
        )
        assert event.is_blocked()

    def test_routing_guardrail_blocked_state(self):
        """Test ROUTING_GUARDRAIL_BLOCKED state."""
        event = LoopEvent(
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.ROUTING_ADJUSTED,
            failure_state=LoopFailureState.ROUTING_GUARDRAIL_BLOCKED,
            details={"guardrail": "max_delta", "requested": 0.5, "allowed": 0.2},
        )
        assert event.is_blocked()


# ============================================================================
# Test Human Checkpoints
# ============================================================================


class TestHumanCheckpoints:
    """Tests for human checkpoint handling."""

    def test_checkpoint_creation(self):
        """Test creating a human checkpoint."""
        checkpoint = HumanCheckpoint(
            id="chk_001",
            checkpoint_type=HumanCheckpointType.APPROVE_POLICY,
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.POLICY_GENERATED,
            target_id="pol_001",
            description="Approve auto-generated policy: Block timeout errors",
            options=[
                {"action": "approve", "label": "Approve", "is_destructive": False},
                {"action": "reject", "label": "Reject", "is_destructive": True},
            ],
        )
        assert not checkpoint.is_resolved()
        assert len(checkpoint.options) == 2

    def test_checkpoint_resolution(self):
        """Test resolving a checkpoint."""
        checkpoint = HumanCheckpoint(
            id="chk_001",
            checkpoint_type=HumanCheckpointType.APPROVE_POLICY,
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.POLICY_GENERATED,
            target_id="pol_001",
        )
        checkpoint.resolve(resolution="approve", resolved_by="user_001")
        assert checkpoint.is_resolved()
        assert checkpoint.resolution == "approve"
        assert checkpoint.resolved_by == "user_001"

    def test_simulate_routing_checkpoint(self):
        """Test SIMULATE_ROUTING checkpoint type."""
        checkpoint = HumanCheckpoint(
            id="chk_001",
            checkpoint_type=HumanCheckpointType.SIMULATE_ROUTING,
            incident_id="inc_001",
            tenant_id="tenant_001",
            stage=LoopStage.ROUTING_ADJUSTED,
            target_id="adj_001",
            description="Simulate routing change before applying",
            options=[
                {"action": "simulate", "label": "Run Simulation", "is_destructive": False},
                {"action": "apply", "label": "Apply Directly", "is_destructive": False},
                {"action": "skip", "label": "Skip", "is_destructive": True},
            ],
        )
        assert checkpoint.checkpoint_type == HumanCheckpointType.SIMULATE_ROUTING


# ============================================================================
# Test Loop Status and Narrative
# ============================================================================


class TestLoopStatusAndNarrative:
    """Tests for loop status tracking and narrative generation."""

    def test_loop_status_tracking(self):
        """Test tracking loop through stages."""
        loop = LoopStatus(
            id="loop_001",
            incident_id="inc_001",
            tenant_id="tenant_001",
        )

        # Advance through stages
        loop.mark_stage_complete(LoopStage.INCIDENT_DETECTED)
        assert loop.current_stage == LoopStage.INCIDENT_DETECTED

        loop.mark_stage_complete(
            LoopStage.PATTERN_MATCHED,
            confidence_band=ConfidenceBand.STRONG,
            details={"pattern_id": "pat_001"},
        )
        assert loop.current_stage == LoopStage.PATTERN_MATCHED
        assert loop.stages[LoopStage.PATTERN_MATCHED.value]["confidence_band"] == "strong"

    def test_loop_blocked_state(self):
        """Test loop blocking on failure."""
        loop = LoopStatus(
            id="loop_001",
            incident_id="inc_001",
            tenant_id="tenant_001",
        )
        loop.mark_stage_complete(LoopStage.INCIDENT_DETECTED)
        loop.mark_stage_failed(
            LoopStage.PATTERN_MATCHED,
            LoopFailureState.MATCH_FAILED,
        )
        assert loop.is_blocked
        assert loop.failure_state == LoopFailureState.MATCH_FAILED

    def test_narrative_generation(self):
        """Test narrative artifact generation."""
        loop = LoopStatus(
            id="loop_001",
            incident_id="inc_001",
            tenant_id="tenant_001",
        )
        # Complete all stages
        loop.mark_stage_complete(LoopStage.INCIDENT_DETECTED)
        loop.mark_stage_complete(
            LoopStage.PATTERN_MATCHED,
            confidence_band=ConfidenceBand.STRONG,
        )
        loop.mark_stage_complete(LoopStage.RECOVERY_SUGGESTED)
        loop.mark_stage_complete(LoopStage.POLICY_GENERATED)
        loop.mark_stage_complete(LoopStage.ROUTING_ADJUSTED)
        loop.mark_complete()

        narrative = loop.to_console_display()
        assert "what_happened" in narrative
        assert "what_we_learned" in narrative
        assert "what_we_changed" in narrative


# ============================================================================
# Test Bridge Integration
# ============================================================================


class TestBridgeIntegration:
    """Tests for bridge integration between pillars."""

    @pytest.mark.asyncio
    async def test_incident_to_catalog_bridge(self, mock_db_session):
        """Test pattern matching bridge."""
        bridge = IncidentToCatalogBridge(mock_db_session)

        incident_data = {
            "id": "inc_001",
            "tenant_id": "tenant_001",
            "error_code": "TIMEOUT",
            "error_message": "Request timed out after 30s",
            "context": {"endpoint": "/api/v1/chat"},
        }

        # Mock pattern found
        mock_db_session.execute.return_value.fetchone.return_value = {
            "id": "pat_001",
            "signature_hash": "abc123",
            "similarity": 0.92,
        }

        result = await bridge.process(incident_data)
        assert result["confidence_band"] == "strong"
        assert result["pattern_id"] == "pat_001"

    @pytest.mark.asyncio
    async def test_pattern_to_recovery_bridge_template(self, mock_db_session):
        """Test recovery suggestion from template."""
        bridge = PatternToRecoveryBridge(mock_db_session)

        pattern_data = {
            "pattern_id": "pat_001",
            "incident_id": "inc_001",
            "tenant_id": "tenant_001",
            "confidence_band": "strong",
            "recovery_template": {
                "action": "retry",
                "params": {"max_retries": 3, "delay_ms": 1000},
            },
        }

        result = await bridge.process(pattern_data)
        assert result["suggestion_type"] == "template"
        assert result["requires_confirmation"] == 0  # Strong match, no confirmation

    @pytest.mark.asyncio
    async def test_recovery_to_policy_bridge_shadow(self, mock_db_session):
        """Test policy generation in shadow mode."""
        bridge = RecoveryToPolicyBridge(mock_db_session)

        recovery_data = {
            "recovery_id": "rec_001",
            "incident_id": "inc_001",
            "tenant_id": "tenant_001",
            "action": "block",
            "condition": {"error_type": "timeout"},
            "confidence": 0.75,  # Weak confidence
        }

        result = await bridge.process(recovery_data)
        assert result["mode"] == "shadow"
        assert result["confirmations_required"] == 3


# ============================================================================
# Test Signature Hashing
# ============================================================================


class TestSignatureHashing:
    """Tests for pattern signature hashing."""

    def test_deterministic_signature_hash(self):
        """Same incident attributes should produce same hash."""
        incident1 = {
            "error_code": "TIMEOUT",
            "error_message": "Request timed out",
            "context": {"endpoint": "/api/v1/chat"},
        }
        incident2 = {
            "error_code": "TIMEOUT",
            "error_message": "Request timed out",
            "context": {"endpoint": "/api/v1/chat"},
        }

        def compute_signature(incident):
            canonical = json.dumps(incident, sort_keys=True)
            return hashlib.sha256(canonical.encode()).hexdigest()

        assert compute_signature(incident1) == compute_signature(incident2)

    def test_different_incidents_different_hash(self):
        """Different incidents should produce different hashes."""
        incident1 = {
            "error_code": "TIMEOUT",
            "error_message": "Request timed out",
        }
        incident2 = {
            "error_code": "RATE_LIMIT",
            "error_message": "Rate limit exceeded",
        }

        def compute_signature(incident):
            canonical = json.dumps(incident, sort_keys=True)
            return hashlib.sha256(canonical.encode()).hexdigest()

        assert compute_signature(incident1) != compute_signature(incident2)


# ============================================================================
# Test Full Loop Flow
# ============================================================================


class TestFullLoopFlow:
    """Integration tests for complete loop flow."""

    @pytest.mark.asyncio
    async def test_happy_path_strong_match(self, mock_db_session, mock_redis, dispatcher_config):
        """Test complete loop with strong pattern match."""
        dispatcher = IntegrationDispatcher(
            config=dispatcher_config,
            db_session=mock_db_session,
            redis_client=mock_redis,
        )

        incident = {
            "id": "inc_001",
            "tenant_id": "tenant_001",
            "error_code": "TIMEOUT",
            "error_message": "Request timed out after 30s",
        }

        # Mock strong pattern match
        with patch.object(dispatcher, "_match_pattern") as mock_match:
            mock_match.return_value = PatternMatchResult(
                incident_id="inc_001",
                pattern_id="pat_001",
                confidence=0.92,
                matched_at=datetime.utcnow(),
            )

            result = await dispatcher.process_incident(incident)

            # Strong match should flow through all stages
            assert result.is_complete or result.failure_state is None

    @pytest.mark.asyncio
    async def test_weak_match_requires_confirmation(self, mock_db_session, mock_redis, dispatcher_config):
        """Test that weak matches require confirmation."""
        dispatcher = IntegrationDispatcher(
            config=dispatcher_config,
            db_session=mock_db_session,
            redis_client=mock_redis,
        )

        incident = {
            "id": "inc_001",
            "tenant_id": "tenant_001",
            "error_code": "UNKNOWN",
        }

        with patch.object(dispatcher, "_match_pattern") as mock_match:
            mock_match.return_value = PatternMatchResult(
                incident_id="inc_001",
                pattern_id="pat_001",
                confidence=0.68,  # Weak match
                matched_at=datetime.utcnow(),
            )

            result = await dispatcher.process_incident(incident)

            # Weak match should create checkpoint
            assert (
                len(result.pending_checkpoints) > 0
                or result.failure_state == LoopFailureState.RECOVERY_NEEDS_CONFIRMATION
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
