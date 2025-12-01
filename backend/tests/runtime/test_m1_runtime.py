# tests/runtime/test_m1_runtime.py
"""
M1 Runtime Interface Tests (Standalone)

Tests for the machine-native runtime interfaces.
This file avoids importing the full worker module to prevent sqlmodel dependency.
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

# Direct path to runtime module (avoid triggering pydantic-dependent imports)
_runtime_path = str(Path(__file__).parent.parent.parent / "app" / "worker" / "runtime")
if _runtime_path not in sys.path:
    sys.path.insert(0, _runtime_path)

from core import (
    Runtime,
    StructuredOutcome,
    SkillDescriptor,
    ResourceContract,
    ErrorCategory
)
from contracts import (
    ContractMetadata,
    SkillContract,
    FailureMode,
    CostModel,
    BudgetTracker
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def runtime():
    """Create a fresh runtime instance with echo skill registered."""
    rt = Runtime()

    async def echo_handler(inputs):
        """Deliberately deterministic echo handler."""
        return {"echo": inputs}

    descriptor = SkillDescriptor(
        skill_id="skill.echo",
        name="Echo",
        version="1.0.0",
        inputs_schema_version="1.0",
        outputs_schema_version="1.0",
        stable_fields={"echo": "DETERMINISTIC"},
        cost_model={"base_cents": 0}
    )
    rt.register_skill(descriptor, echo_handler)
    return rt


@pytest.fixture
def runtime_with_slow_skill(runtime):
    """Runtime with a slow skill for timeout testing."""
    async def slow_handler(inputs):
        await asyncio.sleep(0.1)
        return {"slow": True}

    descriptor = SkillDescriptor(
        skill_id="skill.slow",
        name="Slow Skill",
        version="1.0.0"
    )
    runtime.register_skill(descriptor, slow_handler)
    return runtime


@pytest.fixture
def runtime_with_failing_skill(runtime):
    """Runtime with a skill that raises exceptions."""
    async def failing_handler(inputs):
        raise ValueError("Intentional test failure")

    descriptor = SkillDescriptor(
        skill_id="skill.failing",
        name="Failing Skill",
        version="1.0.0"
    )
    runtime.register_skill(descriptor, failing_handler)
    return runtime


@pytest.fixture
def runtime_with_contract(runtime):
    """Runtime with a resource contract registered."""
    contract = ResourceContract(
        resource_id="test-resource",
        budget={"total_cents": 500, "remaining_cents": 500, "per_step_max_cents": 50},
        rate_limits={"skill.echo": {"remaining": 100, "resets_at": "2025-12-01T12:00:00Z"}},
        concurrency={"max_parallel_steps": 5, "current_running": 0},
        time={"max_run_duration_ms": 60000, "elapsed_ms": 0, "remaining_ms": 60000}
    )
    runtime.register_resource_contract(contract)
    return runtime


# ============================================================================
# Test: runtime.execute()
# ============================================================================

class TestRuntimeExecute:
    """Tests for runtime.execute() interface."""

    @pytest.mark.asyncio
    async def test_execute_success(self, runtime):
        """Execute should return StructuredOutcome with ok=True on success."""
        outcome = await runtime.execute("skill.echo", {"a": 1, "b": 2})

        assert isinstance(outcome, StructuredOutcome)
        assert outcome.ok is True
        assert outcome.result == {"echo": {"a": 1, "b": 2}}
        assert outcome.error is None
        assert "call_id" in outcome.meta
        assert "skill_id" in outcome.meta
        assert outcome.meta["skill_id"] == "skill.echo"

    @pytest.mark.asyncio
    async def test_execute_missing_skill(self, runtime):
        """Execute should return structured error for missing skill."""
        outcome = await runtime.execute("skill.nonexistent", {})

        assert outcome.ok is False
        assert outcome.error is not None
        assert outcome.error["code"] == "ERR_SKILL_NOT_FOUND"
        assert outcome.error["category"] == "PERMANENT"
        assert outcome.error["retryable"] is False

    @pytest.mark.asyncio
    async def test_execute_timeout(self, runtime_with_slow_skill):
        """Execute should return timeout error when skill exceeds timeout."""
        outcome = await runtime_with_slow_skill.execute(
            "skill.slow",
            {},
            timeout_s=0.01  # 10ms timeout, skill takes 100ms
        )

        assert outcome.ok is False
        assert outcome.error["code"] == "ERR_TIMEOUT"
        assert outcome.error["category"] == "TRANSIENT"
        assert outcome.error["retryable"] is True

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, runtime_with_failing_skill):
        """Execute should catch exceptions and return structured error."""
        outcome = await runtime_with_failing_skill.execute("skill.failing", {})

        assert outcome.ok is False
        assert outcome.error["code"] == "ERR_RUNTIME_EXCEPTION"
        assert "Intentional test failure" in outcome.error["message"]
        assert outcome.meta["exception_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_execute_never_throws(self, runtime_with_failing_skill):
        """Execute must NEVER throw an exception - core guarantee."""
        # This should not raise even with a failing skill
        outcome = await runtime_with_failing_skill.execute("skill.failing", {})
        assert isinstance(outcome, StructuredOutcome)

        # Missing skill should not raise
        outcome = await runtime_with_failing_skill.execute("skill.xxx", {})
        assert isinstance(outcome, StructuredOutcome)

    @pytest.mark.asyncio
    async def test_execute_records_meta_timing(self, runtime):
        """Execute should record timing metadata."""
        outcome = await runtime.execute("skill.echo", {"test": 1})

        assert "started_at" in outcome.meta
        assert "ended_at" in outcome.meta
        assert "duration_s" in outcome.meta
        assert outcome.meta["duration_s"] >= 0


# ============================================================================
# Test: runtime.describe_skill()
# ============================================================================

class TestDescribeSkill:
    """Tests for runtime.describe_skill() interface."""

    def test_describe_existing_skill(self, runtime):
        """describe_skill should return SkillDescriptor for registered skill."""
        desc = runtime.describe_skill("skill.echo")

        assert desc is not None
        assert isinstance(desc, SkillDescriptor)
        assert desc.skill_id == "skill.echo"
        assert desc.name == "Echo"
        assert desc.version == "1.0.0"

    def test_describe_missing_skill(self, runtime):
        """describe_skill should return None for unregistered skill."""
        desc = runtime.describe_skill("skill.nonexistent")
        assert desc is None

    def test_describe_returns_stable_fields(self, runtime):
        """describe_skill should include stable_fields mapping."""
        desc = runtime.describe_skill("skill.echo")

        assert desc is not None
        assert "echo" in desc.stable_fields
        assert desc.stable_fields["echo"] == "DETERMINISTIC"


# ============================================================================
# Test: runtime.query()
# ============================================================================

class TestRuntimeQuery:
    """Tests for runtime.query() interface."""

    @pytest.mark.asyncio
    async def test_query_remaining_budget(self, runtime):
        """query('remaining_budget_cents') should return budget info."""
        runtime.set_budget(total_cents=1000, spent_cents=250)

        result = await runtime.query("remaining_budget_cents")

        assert result["remaining_cents"] == 750
        assert result["spent_cents"] == 250
        assert result["total_cents"] == 1000

    @pytest.mark.asyncio
    async def test_query_allowed_skills(self, runtime):
        """query('allowed_skills') should return list of registered skills."""
        result = await runtime.query("allowed_skills")

        assert "skills" in result
        assert "skill.echo" in result["skills"]
        assert result["count"] == len(result["skills"])

    @pytest.mark.asyncio
    async def test_query_what_did_i_try_already(self, runtime):
        """query('what_did_i_try_already') should return execution history."""
        # Execute some skills first
        await runtime.execute("skill.echo", {"a": 1})
        await runtime.execute("skill.echo", {"b": 2})

        result = await runtime.query("what_did_i_try_already")

        assert "history" in result
        assert len(result["history"]) == 2
        assert result["history"][0]["skill_id"] == "skill.echo"

    @pytest.mark.asyncio
    async def test_query_last_step_outcome(self, runtime):
        """query('last_step_outcome') should return most recent execution."""
        await runtime.execute("skill.echo", {"last": True})

        result = await runtime.query("last_step_outcome")

        assert result["outcome"] is not None
        assert result["outcome"]["skill_id"] == "skill.echo"
        assert result["outcome"]["ok"] is True

    @pytest.mark.asyncio
    async def test_query_skills_for_goal_deterministic(self, runtime):
        """query('skills_available_for_goal') should be deterministic."""
        # Same goal should return same results
        r1 = await runtime.query("skills_available_for_goal", goal="test goal")
        r2 = await runtime.query("skills_available_for_goal", goal="test goal")

        assert r1 == r2
        assert "seed" in r1
        assert r1["seed"] == r2["seed"]

    @pytest.mark.asyncio
    async def test_query_unknown_type(self, runtime):
        """query() with unknown type should return error with supported list."""
        result = await runtime.query("unknown_query_type")

        assert "error" in result
        assert "supported" in result
        assert "remaining_budget_cents" in result["supported"]


# ============================================================================
# Test: runtime.get_resource_contract()
# ============================================================================

class TestGetResourceContract:
    """Tests for runtime.get_resource_contract() interface."""

    def test_get_existing_contract(self, runtime_with_contract):
        """get_resource_contract should return contract for registered resource."""
        contract = runtime_with_contract.get_resource_contract("test-resource")

        assert contract is not None
        assert isinstance(contract, ResourceContract)
        assert contract.resource_id == "test-resource"
        assert contract.budget["total_cents"] == 500

    def test_get_missing_contract(self, runtime):
        """get_resource_contract should return None for unregistered resource."""
        contract = runtime.get_resource_contract("nonexistent")
        assert contract is None


# ============================================================================
# Test: StructuredOutcome
# ============================================================================

class TestStructuredOutcome:
    """Tests for StructuredOutcome dataclass."""

    def test_success_factory(self):
        """StructuredOutcome.success() should create successful outcome."""
        outcome = StructuredOutcome.success(
            call_id="test-123",
            result={"data": "value"},
            meta={"timing": 100}
        )

        assert outcome.ok is True
        assert outcome.result == {"data": "value"}
        assert outcome.error is None
        assert outcome.meta["timing"] == 100

    def test_failure_factory(self):
        """StructuredOutcome.failure() should create failed outcome."""
        outcome = StructuredOutcome.failure(
            call_id="test-456",
            code="ERR_TEST",
            message="Test error",
            category=ErrorCategory.TRANSIENT,
            retryable=True
        )

        assert outcome.ok is False
        assert outcome.result is None
        assert outcome.error["code"] == "ERR_TEST"
        assert outcome.error["category"] == "TRANSIENT"
        assert outcome.error["retryable"] is True

    def test_to_dict_serialization(self):
        """StructuredOutcome.to_dict() should produce valid JSON."""
        outcome = StructuredOutcome.success("id-1", {"key": "value"})
        d = outcome.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(d)
        parsed = json.loads(json_str)

        assert parsed["id"] == "id-1"
        assert parsed["ok"] is True
        assert parsed["result"]["key"] == "value"


# ============================================================================
# Test: Contract Dataclasses
# ============================================================================

class TestContractDataclasses:
    """Tests for contract helper dataclasses."""

    def test_contract_metadata_now(self):
        """ContractMetadata.now() should create with current timestamp."""
        meta = ContractMetadata.now("1.0.0", "Initial version")

        assert meta.version == "1.0.0"
        assert meta.changelog == "Initial version"
        assert "Z" in meta.frozen_at  # ISO format with Z suffix

    def test_cost_model_estimate(self):
        """CostModel.estimate() should calculate cost correctly."""
        model = CostModel(
            base_cents=5,
            per_kb_cents=0.1,
            per_token_cents=0.001,
            max_cents=100
        )

        # Base only
        assert model.estimate() == 5

        # With KB
        assert model.estimate(input_size_kb=10) == 6  # 5 + 1

        # With tokens
        assert model.estimate(tokens=1000) == 6  # 5 + 1

        # Cap at max
        model_high = CostModel(base_cents=1000, max_cents=50)
        assert model_high.estimate() == 50

    def test_budget_tracker_spending(self):
        """BudgetTracker should track spending correctly."""
        tracker = BudgetTracker(total_cents=100, per_step_max_cents=30)

        assert tracker.remaining_cents == 100
        assert tracker.can_spend(30) is True
        assert tracker.can_spend(31) is False  # Over per-step max

        assert tracker.spend(25) is True
        assert tracker.remaining_cents == 75

        assert tracker.spend(30) is True
        assert tracker.remaining_cents == 45


# ============================================================================
# Test: Determinism
# ============================================================================

class TestDeterminism:
    """Tests to verify deterministic behavior for replay."""

    @pytest.mark.asyncio
    async def test_same_inputs_same_outcome_shape(self, runtime):
        """Same inputs should produce same outcome structure."""
        o1 = await runtime.execute("skill.echo", {"x": 1})
        runtime.clear_history()
        o2 = await runtime.execute("skill.echo", {"x": 1})

        # Results should match (deterministic skill)
        assert o1.result == o2.result
        assert o1.ok == o2.ok

    @pytest.mark.asyncio
    async def test_error_codes_are_deterministic(self, runtime):
        """Error codes should be deterministic for same error conditions."""
        o1 = await runtime.execute("skill.missing", {})
        o2 = await runtime.execute("skill.missing", {})

        assert o1.error["code"] == o2.error["code"]
        assert o1.error["category"] == o2.error["category"]


# ============================================================================
# Test: Registration
# ============================================================================

class TestRegistration:
    """Tests for skill and contract registration."""

    def test_register_skill_success(self):
        """register_skill should succeed for new skill."""
        rt = Runtime()

        async def handler(inputs):
            return inputs

        desc = SkillDescriptor(skill_id="new.skill", name="New")
        rt.register_skill(desc, handler)

        assert "new.skill" in rt.get_all_skills()

    def test_register_duplicate_skill_fails(self, runtime):
        """register_skill should fail for duplicate skill_id."""
        async def handler(inputs):
            return inputs

        desc = SkillDescriptor(skill_id="skill.echo", name="Duplicate")

        with pytest.raises(RuntimeError, match="skill_already_registered"):
            runtime.register_skill(desc, handler)
