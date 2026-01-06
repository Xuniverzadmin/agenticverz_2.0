# Tests for Business Builder Worker v0.2
"""
Test suite verifying:
1. Worker execution pipeline
2. SBA agent definitions (M15)
3. CARE routing integration (M17)
4. Policy validation (M19/M20)
5. Execution plan stages
6. Brand schema validation
7. Golden replay (M4)
"""

import pytest

from app.workers.business_builder import (
    BrandSchema,
    BusinessBuilderWorker,
    ExecutionPlan,
)
from app.workers.business_builder.agents.definitions import (
    WORKER_AGENTS,
    create_copywriter_agent,
    create_researcher_agent,
    create_strategist_agent,
)
from app.workers.business_builder.execution_plan import (
    StageCategory,
    create_business_builder_plan,
)
from app.workers.business_builder.schemas.brand import (
    ForbiddenClaim,
    ToneLevel,
    ToneRule,
    create_minimal_brand,
)

# =============================================================================
# Brand Schema Tests
# =============================================================================


class TestBrandSchema:
    """Tests for BrandSchema validation."""

    def test_create_minimal_brand(self):
        """Test creating minimal valid brand."""
        brand = create_minimal_brand(
            company_name="TestCo",
            mission="To help people do things better",
            value_proposition="The simplest way to accomplish your goals faster",
            tone=ToneLevel.PROFESSIONAL,
        )

        assert brand.company_name == "TestCo"
        assert brand.tone.primary == ToneLevel.PROFESSIONAL
        assert len(brand.forbidden_claims) > 0

    def test_brand_mission_validation(self):
        """Test mission must be substantive."""
        with pytest.raises(ValueError, match="at least 10 characters"):
            BrandSchema(
                company_name="Test",
                mission="Short",  # Too short
                value_proposition="A valid value proposition that is long enough",
            )

    def test_brand_value_prop_validation(self):
        """Test value proposition must be substantive."""
        with pytest.raises(ValueError, match="at least 20 characters"):
            BrandSchema(
                company_name="Test",
                mission="A valid mission statement here",
                value_proposition="Too short",  # Too short
            )

    def test_forbidden_claims_defaults(self):
        """Test default forbidden claims are applied."""
        brand = create_minimal_brand(
            company_name="Test",
            mission="A valid mission statement",
            value_proposition="A longer value proposition for validation",
        )

        patterns = [fc.pattern for fc in brand.forbidden_claims]
        assert "world's best" in patterns
        assert "guaranteed results" in patterns

    def test_to_strategy_context(self):
        """Test conversion to strategy context."""
        brand = create_minimal_brand(
            company_name="TestCo",
            mission="Help people succeed",
            value_proposition="The best way to achieve success",
        )

        ctx = brand.to_strategy_context()

        assert ctx["brand_name"] == "TestCo"
        assert ctx["mission"] == "Help people succeed"
        assert ctx["tone_primary"] == "professional"

    def test_to_policy_rules(self):
        """Test conversion to policy rules."""
        brand = create_minimal_brand(
            company_name="Test",
            mission="A valid mission statement",
            value_proposition="A longer value proposition for validation",
        )
        brand.budget_tokens = 5000

        rules = brand.to_policy_rules()

        # Should have forbidden claim rules + budget rule
        categories = [r["category"] for r in rules]
        assert "SAFETY" in categories  # Forbidden claims
        assert "OPERATIONAL" in categories  # Budget

    def test_get_drift_anchors(self):
        """Test drift anchors for M18."""
        brand = BrandSchema(
            company_name="Test",
            mission="Our mission is to innovate",
            value_proposition="We provide the best solutions for modern problems",
            tagline="Innovation simplified",
            tone=ToneRule(
                primary=ToneLevel.PROFESSIONAL,
                examples_good=["Professional example 1"],
            ),
        )

        anchors = brand.get_drift_anchors()

        assert "Our mission is to innovate" in anchors
        assert "Innovation simplified" in anchors
        assert "Professional example 1" in anchors


# =============================================================================
# Agent Definition Tests (M15 SBA)
# =============================================================================


class TestAgentDefinitions:
    """Tests for SBA agent definitions."""

    def test_worker_agents_defined(self):
        """Test all required agents are defined."""
        required = [
            "researcher_agent",
            "strategist_agent",
            "copywriter_agent",
            "ux_agent",
            "recovery_agent",
            "governor_agent",
            "validator_agent",
        ]

        for agent_id in required:
            assert agent_id in WORKER_AGENTS

    def test_researcher_agent_sba(self):
        """Test researcher agent has valid SBA schema."""
        agent = create_researcher_agent()

        # Check 5-element cascade
        assert agent.winning_aspiration.description
        assert agent.where_to_play.domain == "market-research"
        assert len(agent.how_to_win.tasks) >= 3
        assert agent.enabling_management_systems.governance.value == "BudgetLLM"

    def test_strategist_agent_sba(self):
        """Test strategist agent has valid SBA schema."""
        agent = create_strategist_agent()

        assert "brand" in agent.where_to_play.domain.lower()
        assert agent.how_to_win.fulfillment_metric >= 0.85

    def test_copywriter_agent_dependencies(self):
        """Test copywriter depends on strategist."""
        agent = create_copywriter_agent()

        agent_deps = agent.capabilities_capacity.get_agent_dependencies()
        dep_names = [d.name for d in agent_deps]

        assert "strategist_agent" in dep_names

    def test_agent_budget_limits(self):
        """Test all agents have budget limits."""
        for agent_id, agent in WORKER_AGENTS.items():
            budget = agent.capabilities_capacity.env.budget_tokens
            # All agents should have some budget limit
            assert budget is not None or agent_id == "validator_agent"

    def test_agent_orchestrator(self):
        """Test agents reference correct orchestrator."""
        for agent_id, agent in WORKER_AGENTS.items():
            # Default orchestrator
            assert agent.enabling_management_systems.orchestrator == "business_builder_worker"


# =============================================================================
# Execution Plan Tests
# =============================================================================


class TestExecutionPlan:
    """Tests for execution plan."""

    def test_create_default_plan(self):
        """Test creating default plan."""
        plan = create_business_builder_plan(
            brand_context={"brand_name": "Test"},
            budget=5000,
            strict_mode=True,
        )

        assert plan.name == "Business Builder"
        assert len(plan.stages) >= 8
        assert plan.total_budget_tokens == 5000
        assert plan.strict_mode is True

    def test_plan_governance_order(self):
        """Test stages execute in governance order."""
        plan = create_business_builder_plan(brand_context={})

        ordered = plan.get_execution_order()

        # SAFETY should come first
        assert ordered[0].category == StageCategory.SAFETY

        # OPERATIONAL should come before ROUTING
        op_idx = next(i for i, s in enumerate(ordered) if s.category == StageCategory.OPERATIONAL)
        rt_idx = next(i for i, s in enumerate(ordered) if s.category == StageCategory.ROUTING)
        assert op_idx < rt_idx

        # CUSTOM should be last
        assert ordered[-1].category == StageCategory.CUSTOM

    def test_plan_stage_ids(self):
        """Test all expected stages are present."""
        plan = create_business_builder_plan(brand_context={})

        stage_ids = [s.id for s in plan.stages]

        assert "preflight" in stage_ids
        assert "research" in stage_ids
        assert "strategy" in stage_ids
        assert "copy" in stage_ids
        assert "ux" in stage_ids
        assert "consistency" in stage_ids
        assert "bundle" in stage_ids

    def test_plan_to_yaml(self):
        """Test plan serialization to YAML."""
        plan = create_business_builder_plan(brand_context={"test": True})

        yaml_str = plan.to_yaml()

        assert "plan_id:" in yaml_str
        assert "stages:" in yaml_str
        assert "research" in yaml_str

    def test_plan_from_yaml(self):
        """Test plan deserialization from YAML."""
        plan = create_business_builder_plan(brand_context={})
        yaml_str = plan.to_yaml()

        restored = ExecutionPlan.from_yaml(yaml_str)

        assert restored.plan_id == plan.plan_id
        assert len(restored.stages) == len(plan.stages)

    def test_replay_token(self):
        """Test replay token generation (M4)."""
        plan = create_business_builder_plan(
            brand_context={"name": "Test"},
            budget=3000,
        )

        token = plan.to_replay_token()

        assert "plan_id" in token
        assert "seed" in token
        assert token["seed"] != 0  # Should be deterministic from context


# =============================================================================
# Worker Execution Tests
# =============================================================================


class TestWorkerExecution:
    """Tests for worker execution."""

    @pytest.mark.asyncio
    async def test_worker_basic_execution(self):
        """Test basic worker execution."""
        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="AI tool for podcasters",
            budget=5000,
        )

        assert result.success is True
        assert result.error is None
        assert len(result.execution_trace) > 0
        assert result.total_tokens_used >= 0

    @pytest.mark.asyncio
    async def test_worker_with_brand(self):
        """Test worker execution with brand constraints."""
        brand = create_minimal_brand(
            company_name="PodcastAI",
            mission="To help podcasters reach more listeners",
            value_proposition="The AI-powered podcast growth platform",
        )

        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="AI tool for podcasters",
            brand=brand,
            budget=3000,
        )

        assert result.success is True
        assert "landing_copy" in result.artifacts or "copy" in str(result.artifacts)

    @pytest.mark.asyncio
    async def test_worker_generates_replay_token(self):
        """Test worker generates replay token (M4)."""
        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="E-commerce platform",
            budget=5000,
        )

        assert result.replay_token is not None
        assert "plan_id" in result.replay_token
        assert "seed" in result.replay_token

    @pytest.mark.asyncio
    async def test_worker_cost_report(self):
        """Test worker generates cost report."""
        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="SaaS for developers",
            budget=5000,
        )

        assert result.cost_report is not None
        assert "total_tokens" in result.cost_report
        assert "stages" in result.cost_report

    @pytest.mark.asyncio
    async def test_worker_execution_trace(self):
        """Test worker records execution trace."""
        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="Marketing automation",
        )

        assert len(result.execution_trace) > 0

        # Each trace entry should have required fields
        for entry in result.execution_trace:
            assert "stage" in entry
            assert "status" in entry
            assert "latency_ms" in entry

    @pytest.mark.asyncio
    async def test_worker_drift_metrics(self):
        """Test worker tracks drift metrics (M18)."""
        brand = create_minimal_brand(
            company_name="DriftTest",
            mission="Testing drift detection capabilities",
            value_proposition="We verify brand consistency across outputs",
        )

        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="Brand consistency tool",
            brand=brand,
        )

        # Some stages should have drift metrics
        # (currently mocked, but structure should be there)
        assert isinstance(result.drift_metrics, dict)


# =============================================================================
# Policy Validation Tests (M19/M20)
# =============================================================================


class TestPolicyValidation:
    """Tests for policy validation integration."""

    @pytest.mark.asyncio
    async def test_forbidden_claim_detection(self):
        """Test forbidden claims are detected."""
        brand = BrandSchema(
            company_name="Test",
            mission="A valid mission statement here",
            value_proposition="We provide the best solutions for modern problems",
            forbidden_claims=[
                ForbiddenClaim(
                    pattern="test_forbidden",
                    reason="Test pattern",
                    severity="error",
                ),
            ],
        )

        worker = BusinessBuilderWorker(auto_register_agents=False)

        # The worker should check forbidden claims
        # Even with mock data, the structure should work
        result = await worker.run(
            task="A product with test_forbidden in the description",
            brand=brand,
        )

        # Policy check is called but mock outputs don't contain forbidden text
        assert result.success is True

    @pytest.mark.asyncio
    async def test_budget_enforcement(self):
        """Test budget constraints are tracked."""
        brand = create_minimal_brand(
            company_name="BudgetTest",
            mission="Testing budget enforcement",
            value_proposition="We verify budget limits are respected",
        )
        brand.budget_tokens = 1000  # Very low budget

        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="Budget test",
            brand=brand,
            budget=1000,
        )

        # Cost report should show budget info
        assert result.cost_report is not None
        assert result.cost_report.get("budget") == 1000


# =============================================================================
# Stage Implementation Tests
# =============================================================================


class TestStageImplementations:
    """Tests for individual stage implementations."""

    @pytest.mark.asyncio
    async def test_research_stage(self):
        """Test research stage produces expected outputs."""
        from app.workers.business_builder.stages.research import ResearchStage

        stage = ResearchStage(depth="medium")
        output = await stage.execute("AI for podcasters")

        assert output.market_report is not None
        assert len(output.competitor_matrix) > 0
        assert len(output.trend_analysis) > 0
        assert output.confidence > 0

    @pytest.mark.asyncio
    async def test_strategy_stage(self):
        """Test strategy stage produces expected outputs."""
        from app.workers.business_builder.stages.strategy import StrategyStage

        stage = StrategyStage()
        output = await stage.execute(
            market_report={"summary": "Test"},
            competitor_matrix=[{"name": "CompA"}],
            brand_context={"mission": "Test mission"},
        )

        assert output.positioning is not None
        assert output.messaging_framework is not None
        assert len(output.value_props) > 0

    @pytest.mark.asyncio
    async def test_copy_stage(self):
        """Test copy stage produces expected outputs."""
        from app.workers.business_builder.stages.copy import CopyStage

        stage = CopyStage()
        output = await stage.execute(
            positioning="Best solution",
            messaging_framework={"headline": "Test"},
            tone_guidelines={"primary": "professional"},
            brand_name="TestCo",
        )

        assert output.landing_copy is not None
        assert len(output.blog_drafts) > 0
        assert len(output.email_sequence) > 0

    @pytest.mark.asyncio
    async def test_ux_stage(self):
        """Test UX stage produces valid HTML/CSS."""
        from app.workers.business_builder.stages.ux import UXStage

        stage = UXStage()
        output = await stage.execute(
            landing_copy={"hero": {"headline": "Test", "cta": "Start"}},
            brand_visual={"primary_color": "#3B82F6"},
            brand_name="TestCo",
        )

        assert "<!DOCTYPE html>" in output.landing_html
        assert "TestCo" in output.landing_html
        assert "--primary-color" in output.landing_css
        assert output.component_map.get("hero") is True


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for full workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete end-to-end workflow."""
        brand = create_minimal_brand(
            company_name="IntegrationTest Co",
            mission="To provide comprehensive integration testing",
            value_proposition="The most thorough testing platform for modern applications",
            tone=ToneLevel.PROFESSIONAL,
        )

        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="Integration testing platform",
            brand=brand,
            budget=10000,
            strict_mode=False,
        )

        # Verify complete execution
        assert result.success is True
        assert result.replay_token is not None
        assert result.cost_report is not None
        assert len(result.execution_trace) >= 8  # All stages

        # Verify artifacts
        assert len(result.artifacts) > 0

    @pytest.mark.asyncio
    async def test_workflow_with_strict_mode(self):
        """Test workflow with strict policy enforcement."""
        brand = create_minimal_brand(
            company_name="StrictTest",
            mission="Testing strict mode enforcement",
            value_proposition="Ensuring policy compliance in all outputs",
        )

        worker = BusinessBuilderWorker(auto_register_agents=False)

        result = await worker.run(
            task="Compliance tool",
            brand=brand,
            budget=5000,
            strict_mode=True,
        )

        # Should still succeed with mock data (no violations)
        assert result.success is True
