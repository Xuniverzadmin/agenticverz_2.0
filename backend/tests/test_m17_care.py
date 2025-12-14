# M17 CARE Routing Engine Tests
# Tests for Cascade-Aware Routing Engine

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Import CARE components
from app.routing.models import (
    SuccessMetric,
    OrchestratorMode,
    RiskPolicy,
    DifficultyLevel,
    RoutingRequest,
    RoutingStage,
    infer_success_metric,
    infer_orchestrator_mode,
)
from app.routing.care import CAREEngine


# =============================================================================
# Stage 1: Aspiration → Success Metric Tests
# =============================================================================

class TestAspirationMetricInference:
    """Test success metric inference from winning aspiration."""

    def test_cost_keywords(self):
        """Cost-related keywords should map to COST metric."""
        aspirations = [
            "Minimize operational cost for data processing",
            "Budget-efficient email sending",
            "Economical resource usage for batch jobs",
        ]
        for aspiration in aspirations:
            assert infer_success_metric(aspiration) == SuccessMetric.COST

    def test_latency_keywords(self):
        """Speed-related keywords should map to LATENCY metric."""
        aspirations = [
            "Fast response time for user queries",
            "Real-time processing of incoming data",
            "Quick turnaround on validation tasks",
        ]
        for aspiration in aspirations:
            assert infer_success_metric(aspiration) == SuccessMetric.LATENCY

    def test_accuracy_keywords(self):
        """Quality-related keywords should map to ACCURACY metric."""
        aspirations = [
            "Accurate data extraction from documents",
            "Precise validation of user inputs",
            "Thorough verification of compliance",
        ]
        for aspiration in aspirations:
            assert infer_success_metric(aspiration) == SuccessMetric.ACCURACY

    def test_risk_keywords(self):
        """Safety-related keywords should map to RISK_MIN metric."""
        aspirations = [
            "Safe execution of financial transactions",
            "Secure handling of sensitive data",
            "Risk-aware processing of user requests",
        ]
        for aspiration in aspirations:
            assert infer_success_metric(aspiration) == SuccessMetric.RISK_MIN

    def test_no_keywords_returns_balanced(self):
        """Aspirations without keywords should return BALANCED."""
        aspiration = "General purpose data processing agent"
        assert infer_success_metric(aspiration) == SuccessMetric.BALANCED


# =============================================================================
# Stage 5: Orchestrator Mode Inference Tests
# =============================================================================

class TestOrchestratorModeInference:
    """Test orchestrator mode inference."""

    def test_parallel_mode(self):
        """Parallel/swarm orchestrators should use PARALLEL mode."""
        assert infer_orchestrator_mode("parallel_processor", "worker") == OrchestratorMode.PARALLEL
        assert infer_orchestrator_mode("swarm_coordinator", "worker") == OrchestratorMode.PARALLEL

    def test_hierarchical_mode(self):
        """Hierarchical orchestrators should use HIERARCHICAL mode."""
        assert infer_orchestrator_mode("hierarchical_manager", "worker") == OrchestratorMode.HIERARCHICAL
        assert infer_orchestrator_mode("tree_orchestrator", "worker") == OrchestratorMode.HIERARCHICAL

    def test_blackboard_mode(self):
        """Blackboard orchestrators should use BLACKBOARD mode."""
        assert infer_orchestrator_mode("blackboard_controller", "worker") == OrchestratorMode.BLACKBOARD
        assert infer_orchestrator_mode("shared_memory_coordinator", "worker") == OrchestratorMode.BLACKBOARD

    def test_orchestrator_type_inference(self):
        """Orchestrator agent types should default to HIERARCHICAL."""
        assert infer_orchestrator_mode("some_orchestrator", "orchestrator") == OrchestratorMode.HIERARCHICAL

    def test_aggregator_type_inference(self):
        """Aggregator agent types should default to BLACKBOARD."""
        assert infer_orchestrator_mode("data_aggregator", "aggregator") == OrchestratorMode.BLACKBOARD

    def test_default_sequential(self):
        """Default should be SEQUENTIAL for regular workers."""
        assert infer_orchestrator_mode("simple_processor", "worker") == OrchestratorMode.SEQUENTIAL


# =============================================================================
# CARE Engine Stage Tests
# =============================================================================

class TestCAREEngineStages:
    """Test individual CARE pipeline stages."""

    @pytest.fixture
    def care_engine(self):
        """Create CARE engine instance."""
        return CAREEngine()

    @pytest.fixture
    def valid_sba(self):
        """Create a valid SBA for testing."""
        return {
            "winning_aspiration": {
                "description": "Fast and accurate data processing for batch jobs"
            },
            "where_to_play": {
                "domain": "data-processing",
                "allowed_tools": ["extract", "transform", "validate"],
                "allowed_contexts": ["job"],
            },
            "how_to_win": {
                "tasks": ["Extract data", "Transform format", "Validate output"],
                "tests": ["verify_extraction", "verify_transform"],
                "fulfillment_metric": 0.85,
            },
            "capabilities_capacity": {
                "dependencies": [
                    {"type": "tool", "name": "extract", "required": True},
                ],
                "env": {"cpu": "0.5", "memory": "256Mi"},
            },
            "enabling_management_systems": {
                "orchestrator": "batch_orchestrator",
                "governance": "BudgetLLM",
            },
        }

    @pytest.fixture
    def routing_request(self):
        """Create a routing request for testing."""
        return RoutingRequest(
            task_description="Process batch data files",
            task_domain="data-processing",
            required_tools=["extract"],
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

    def test_aspiration_stage_pass(self, care_engine, valid_sba, routing_request):
        """Test aspiration stage passes with valid SBA."""
        result = care_engine._evaluate_aspiration(valid_sba, routing_request)
        assert result.passed is True
        assert result.stage == RoutingStage.ASPIRATION
        assert "success_metric" in result.details

    def test_aspiration_stage_fail_missing(self, care_engine, routing_request):
        """Test aspiration stage fails with missing aspiration."""
        sba = {"winning_aspiration": {}}
        result = care_engine._evaluate_aspiration(sba, routing_request)
        assert result.passed is False
        assert "Missing" in result.reason

    def test_domain_filter_pass(self, care_engine, valid_sba, routing_request):
        """Test domain filter passes when domain matches."""
        result = care_engine._evaluate_domain(valid_sba, routing_request)
        assert result.passed is True
        assert result.stage == RoutingStage.DOMAIN_FILTER

    def test_domain_filter_fail_mismatch(self, care_engine, valid_sba):
        """Test domain filter fails when domain doesn't match."""
        request = RoutingRequest(
            task_description="Process financial data",
            task_domain="finance",
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )
        result = care_engine._evaluate_domain(valid_sba, request)
        assert result.passed is False
        assert "mismatch" in result.reason.lower()

    def test_domain_filter_fail_missing_tools(self, care_engine, valid_sba):
        """Test domain filter fails when required tools not available."""
        request = RoutingRequest(
            task_description="Process data",
            task_domain="data-processing",
            required_tools=["extract", "missing_tool"],
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )
        result = care_engine._evaluate_domain(valid_sba, request)
        assert result.passed is False
        assert "Missing tools" in result.reason

    def test_strategy_stage_pass(self, care_engine, valid_sba, routing_request):
        """Test strategy stage passes with valid config."""
        result = care_engine._evaluate_strategy(valid_sba, routing_request)
        assert result.passed is True
        assert result.stage == RoutingStage.STRATEGY

    def test_strategy_stage_low_fulfillment_warning(self, care_engine, routing_request):
        """Test strategy stage warns on low fulfillment."""
        sba = {
            "how_to_win": {
                "tasks": ["task1"],
                "fulfillment_metric": 0.2,
            },
            "routing_config": {},
        }
        result = care_engine._evaluate_strategy(sba, routing_request)
        assert result.passed is True  # Still passes but with warning
        assert "low_fulfillment_warning" in result.details or "Low fulfillment" in result.reason

    def test_strategy_stage_fail_difficulty(self, care_engine, valid_sba):
        """Test strategy stage fails when task difficulty exceeds threshold."""
        valid_sba["routing_config"] = {"difficulty_threshold": "low"}
        request = RoutingRequest(
            task_description="Complex task",
            difficulty=DifficultyLevel.HIGH,
            risk_tolerance=RiskPolicy.BALANCED,
        )
        result = care_engine._evaluate_strategy(valid_sba, request)
        assert result.passed is False
        assert "difficult" in result.reason.lower()

    def test_orchestrator_stage_pass(self, care_engine, valid_sba):
        """Test orchestrator stage passes with valid config."""
        result = care_engine._evaluate_orchestrator(valid_sba, "worker")
        assert result.passed is True
        assert result.stage == RoutingStage.ORCHESTRATOR
        assert "orchestrator_mode" in result.details


# =============================================================================
# Full Pipeline Tests
# =============================================================================

class TestCAREFullPipeline:
    """Test full CARE routing pipeline."""

    @pytest.fixture
    def care_engine(self):
        return CAREEngine()

    @pytest.mark.asyncio
    async def test_evaluate_agent_all_stages_pass(self, care_engine):
        """Test full pipeline with all stages passing."""
        sba = {
            "winning_aspiration": {"description": "Accurate data extraction from documents"},
            "where_to_play": {
                "domain": "document-processing",
                "allowed_tools": ["ocr", "extract"],
            },
            "how_to_win": {
                "tasks": ["OCR scan", "Extract fields"],
                "fulfillment_metric": 0.9,
            },
            "capabilities_capacity": {"dependencies": [], "env": {}},
            "enabling_management_systems": {
                "orchestrator": "doc_orchestrator",
                "governance": "BudgetLLM",
            },
        }

        request = RoutingRequest(
            task_description="Extract data from PDF",
            task_domain="document-processing",
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

        # Mock capability check to avoid real infra probes
        with patch.object(care_engine, '_evaluate_capabilities', new_callable=AsyncMock) as mock_cap:
            from app.routing.models import CapabilityCheckResult, StageResult
            mock_cap.return_value = (
                StageResult(
                    stage=RoutingStage.CAPABILITY,
                    passed=True,
                    reason="All capabilities available",
                ),
                CapabilityCheckResult(passed=True, probes=[], failed_probes=[])
            )

            result = await care_engine.evaluate_agent(
                agent_id="test_agent",
                agent_name="Test Agent",
                agent_type="worker",
                agent_sba=sba,
                request=request,
            )

        assert result.eligible is True
        assert result.score > 0
        assert len(result.stage_results) == 5  # All 5 stages
        assert all(sr.passed for sr in result.stage_results)

    @pytest.mark.asyncio
    async def test_evaluate_agent_rejected_at_domain(self, care_engine):
        """Test agent rejected at domain filter stage."""
        sba = {
            "winning_aspiration": {"description": "Process financial data safely"},
            "where_to_play": {
                "domain": "finance",
                "allowed_tools": ["ledger"],
            },
            "how_to_win": {"tasks": ["Process ledger"], "fulfillment_metric": 0.8},
            "capabilities_capacity": {"dependencies": []},
            "enabling_management_systems": {"orchestrator": "fin_orch", "governance": "BudgetLLM"},
        }

        request = RoutingRequest(
            task_description="Process healthcare data",
            task_domain="healthcare",  # Mismatch!
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

        result = await care_engine.evaluate_agent(
            agent_id="finance_agent",
            agent_name="Finance Agent",
            agent_type="worker",
            agent_sba=sba,
            request=request,
        )

        assert result.eligible is False
        assert result.rejection_stage == RoutingStage.DOMAIN_FILTER
        assert "mismatch" in result.rejection_reason.lower()


# =============================================================================
# Routing Score Tests
# =============================================================================

class TestRoutingScore:
    """Test routing score calculation."""

    @pytest.fixture
    def care_engine(self):
        return CAREEngine()

    def test_high_fulfillment_high_score(self, care_engine):
        """High fulfillment should result in higher score."""
        sba_high = {"how_to_win": {"fulfillment_metric": 0.95}}
        sba_low = {"how_to_win": {"fulfillment_metric": 0.3}}

        request = RoutingRequest(
            task_description="test",
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

        # Create mock stage results
        from app.routing.models import StageResult
        stages = [
            StageResult(stage=RoutingStage.ASPIRATION, passed=True, reason="ok", details={"success_metric": "balanced"}),
            StageResult(stage=RoutingStage.DOMAIN_FILTER, passed=True, reason="ok"),
            StageResult(stage=RoutingStage.STRATEGY, passed=True, reason="ok"),
            StageResult(stage=RoutingStage.CAPABILITY, passed=True, reason="ok"),
            StageResult(stage=RoutingStage.ORCHESTRATOR, passed=True, reason="ok"),
        ]

        score_high = care_engine._calculate_routing_score(sba_high, stages, request)
        score_low = care_engine._calculate_routing_score(sba_low, stages, request)

        assert score_high > score_low


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestCAREErrorHandling:
    """Test CARE error handling and actionable fixes."""

    @pytest.fixture
    def care_engine(self):
        return CAREEngine()

    def test_no_agent_error_message(self, care_engine):
        """Test error message when no agents eligible."""
        from app.routing.models import RouteEvaluationResult
        evaluated = [
            RouteEvaluationResult(
                agent_id="agent1",
                eligible=False,
                rejection_reason="Domain mismatch",
                rejection_stage=RoutingStage.DOMAIN_FILTER,
            ),
            RouteEvaluationResult(
                agent_id="agent2",
                eligible=False,
                rejection_reason="Domain mismatch",
                rejection_stage=RoutingStage.DOMAIN_FILTER,
            ),
        ]

        request = RoutingRequest(
            task_description="test",
            task_domain="finance",
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

        error = care_engine._build_no_agent_error(evaluated, request)
        assert "domain_filter" in error.lower()

    def test_actionable_fix_domain(self, care_engine):
        """Test actionable fix for domain mismatch."""
        from app.routing.models import RouteEvaluationResult
        evaluated = [
            RouteEvaluationResult(
                agent_id="agent1",
                eligible=False,
                rejection_stage=RoutingStage.DOMAIN_FILTER,
            ),
        ]

        request = RoutingRequest(
            task_description="test",
            task_domain="finance",
            difficulty=DifficultyLevel.MEDIUM,
            risk_tolerance=RiskPolicy.BALANCED,
        )

        fix = care_engine._build_actionable_fix(evaluated, request)
        assert "finance" in fix.lower() or "register" in fix.lower()


# =============================================================================
# Capability Hardness Tests (Soft vs Hard Dependencies)
# =============================================================================

class TestCapabilityHardness:
    """Test hard vs soft dependency classification."""

    def test_hardness_classification(self):
        """Test that probe types are correctly classified as HARD or SOFT."""
        from app.routing.models import ProbeType, CapabilityHardness, PROBE_HARDNESS

        # HARD dependencies - should block routing
        hard_deps = [
            ProbeType.SMTP,
            ProbeType.DNS,
            ProbeType.API_KEY,
            ProbeType.S3,
            ProbeType.DATABASE,
        ]
        for probe in hard_deps:
            assert PROBE_HARDNESS[probe] == CapabilityHardness.HARD, f"{probe} should be HARD"

        # SOFT dependencies - should NOT block routing (degraded mode)
        soft_deps = [
            ProbeType.HTTP,
            ProbeType.REDIS,  # Critical fix - Redis is SOFT
            ProbeType.AGENT,
            ProbeType.SERVICE,
        ]
        for probe in soft_deps:
            assert PROBE_HARDNESS[probe] == CapabilityHardness.SOFT, f"{probe} should be SOFT"

    def test_probe_result_is_blocking(self):
        """Test is_blocking() method for probe results."""
        from app.routing.models import CapabilityProbeResult, ProbeType, CapabilityHardness

        # HARD failure should block
        hard_fail = CapabilityProbeResult(
            probe_type=ProbeType.DATABASE,
            name="db",
            available=False,
            hardness=CapabilityHardness.HARD,
            error="Connection refused",
        )
        assert hard_fail.is_blocking() is True

        # SOFT failure should NOT block
        soft_fail = CapabilityProbeResult(
            probe_type=ProbeType.REDIS,
            name="redis",
            available=False,
            hardness=CapabilityHardness.SOFT,
            error="Connection refused",
        )
        assert soft_fail.is_blocking() is False

        # Success never blocks
        success = CapabilityProbeResult(
            probe_type=ProbeType.DATABASE,
            name="db",
            available=True,
            hardness=CapabilityHardness.HARD,
        )
        assert success.is_blocking() is False

    def test_capability_check_result_degraded(self):
        """Test degraded mode when only soft dependencies fail."""
        from app.routing.models import (
            CapabilityCheckResult,
            CapabilityProbeResult,
            ProbeType,
            CapabilityHardness,
        )

        db_ok = CapabilityProbeResult(
            probe_type=ProbeType.DATABASE,
            name="db",
            available=True,
            hardness=CapabilityHardness.HARD,
        )
        redis_fail = CapabilityProbeResult(
            probe_type=ProbeType.REDIS,
            name="redis",
            available=False,
            hardness=CapabilityHardness.SOFT,
            error="Connection refused",
        )

        result = CapabilityCheckResult(
            passed=True,  # Passes because only soft dep failed
            probes=[db_ok, redis_fail],
            failed_probes=[redis_fail],
            soft_failures=[redis_fail],
            hard_failures=[],
            degraded=True,  # Operating in degraded mode
        )

        assert result.passed is True
        assert result.degraded is True
        assert len(result.soft_failures) == 1
        assert len(result.hard_failures) == 0

    def test_capability_check_result_blocked(self):
        """Test routing blocked when hard dependency fails."""
        from app.routing.models import (
            CapabilityCheckResult,
            CapabilityProbeResult,
            ProbeType,
            CapabilityHardness,
        )

        db_fail = CapabilityProbeResult(
            probe_type=ProbeType.DATABASE,
            name="db",
            available=False,
            hardness=CapabilityHardness.HARD,
            error="Connection refused",
        )

        result = CapabilityCheckResult(
            passed=False,  # Blocked because hard dep failed
            probes=[db_fail],
            failed_probes=[db_fail],
            soft_failures=[],
            hard_failures=[db_fail],
            degraded=False,
        )

        assert result.passed is False
        assert result.degraded is False
        assert len(result.hard_failures) == 1


# =============================================================================
# Fallback Agent Chain Tests
# =============================================================================

class TestFallbackAgentChain:
    """Test fallback agent chain in routing decisions."""

    def test_routing_decision_fallback_agents(self):
        """Test that RoutingDecision includes fallback agents."""
        from app.routing.models import RoutingDecision

        decision = RoutingDecision(
            request_id="test123",
            task_description="Test task",
            selected_agent_id="agent1",
            eligible_agents=["agent1", "agent2", "agent3", "agent4"],
            fallback_agents=["agent2", "agent3", "agent4"],  # Up to 3 fallbacks
            routed=True,
        )

        assert decision.fallback_agents == ["agent2", "agent3", "agent4"]
        assert len(decision.fallback_agents) == 3

    def test_routing_decision_degraded_mode(self):
        """Test that RoutingDecision tracks degraded mode."""
        from app.routing.models import RoutingDecision

        decision = RoutingDecision(
            request_id="test123",
            task_description="Test task",
            selected_agent_id="agent1",
            routed=True,
            degraded=True,
            degraded_reason="Soft dependencies unavailable: redis",
        )

        assert decision.degraded is True
        assert "redis" in decision.degraded_reason

    def test_routing_decision_to_dict_includes_fallbacks(self):
        """Test that to_dict includes fallback and degraded info."""
        from app.routing.models import RoutingDecision

        decision = RoutingDecision(
            request_id="test123",
            task_description="Test task",
            selected_agent_id="agent1",
            fallback_agents=["agent2", "agent3"],
            degraded=True,
            degraded_reason="Redis down",
            routed=True,
        )

        d = decision.to_dict()
        assert "fallback_agents" in d
        assert d["fallback_agents"] == ["agent2", "agent3"]
        assert d["degraded"] is True
        assert d["degraded_reason"] == "Redis down"


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class TestRateLimiting:
    """Test rate limiting per risk policy."""

    def test_rate_limits_per_policy(self):
        """Test different rate limits per risk policy."""
        from app.routing.models import RiskPolicy, RATE_LIMITS

        assert RATE_LIMITS[RiskPolicy.STRICT] < RATE_LIMITS[RiskPolicy.BALANCED]
        assert RATE_LIMITS[RiskPolicy.BALANCED] < RATE_LIMITS[RiskPolicy.FAST]

        # Verify specific values
        assert RATE_LIMITS[RiskPolicy.STRICT] == 10
        assert RATE_LIMITS[RiskPolicy.BALANCED] == 30
        assert RATE_LIMITS[RiskPolicy.FAST] == 100

    def test_routing_decision_rate_limit_fields(self):
        """Test that RoutingDecision has rate limit fields."""
        from app.routing.models import RoutingDecision

        decision = RoutingDecision(
            request_id="test123",
            task_description="Test task",
            rate_limited=True,
            rate_limit_remaining=0,
            routed=False,
            error="Rate limit exceeded",
        )

        assert decision.rate_limited is True
        assert decision.rate_limit_remaining == 0

        d = decision.to_dict()
        assert "rate_limited" in d
        assert "rate_limit_remaining" in d


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
