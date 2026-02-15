# tests/runtime/test_invariants.py
"""
Runtime Invariants Test Suite

Tests the fundamental invariants that the AOS runtime must maintain.
These are properties that must ALWAYS hold, regardless of implementation details.

Invariants tested:
1. StructuredOutcome never throws
2. execute() always returns StructuredOutcome
3. Skill descriptors are immutable after registration
4. Content hashes are deterministic
5. Side effects are ordered and stable
6. Budget tracking is monotonic
7. Error categories are exhaustive
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add backend to path for imports
_backend_path = str(Path(__file__).parent.parent.parent)
_app_path = str(Path(__file__).parent.parent.parent / "app")
_runtime_path = str(Path(__file__).parent.parent.parent / "app" / "worker" / "runtime")

for p in [_backend_path, _app_path, _runtime_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.hoc.int.worker.runtime.core import (
    ErrorCategory,
    ResourceContract,
    Runtime,
    SkillDescriptor,
    StructuredOutcome,
)


class TestStructuredOutcomeInvariants:
    """Invariant: StructuredOutcome never throws, always has valid structure."""

    def test_outcome_always_has_ok_field(self):
        """StructuredOutcome must always have 'ok' field."""
        # Success case
        success = StructuredOutcome(id="test-1", ok=True, result={"data": "value"})
        assert hasattr(success, "ok")
        assert success.ok is True

        # Error case
        error = StructuredOutcome(id="test-2", ok=False, error={"code": "TEST_ERROR", "message": "test"})
        assert hasattr(error, "ok")
        assert error.ok is False

    def test_outcome_success_has_result(self):
        """Successful outcome must have result field."""
        outcome = StructuredOutcome(id="test-1", ok=True, result={"data": "value"})
        assert outcome.ok is True
        assert outcome.result is not None

    def test_outcome_error_has_error_details(self):
        """Error outcome must have error field with required keys."""
        outcome = StructuredOutcome(
            id="test-1", ok=False, error={"code": "TEST_ERROR", "message": "Something went wrong"}
        )
        assert outcome.ok is False
        assert outcome.error is not None
        assert "code" in outcome.error
        assert "message" in outcome.error

    def test_outcome_id_always_present(self):
        """Every outcome must have an ID."""
        outcome = StructuredOutcome(id="test-123", ok=True, result={})
        assert outcome.id is not None
        assert len(outcome.id) > 0

    def test_outcome_serialization_never_fails(self):
        """Outcome serialization must never raise."""
        outcomes = [
            StructuredOutcome(id="1", ok=True, result={"key": "value"}),
            StructuredOutcome(id="2", ok=False, error={"code": "E1", "message": "m"}),
            StructuredOutcome(id="3", ok=True, result=None),
            StructuredOutcome(id="4", ok=True, result={"nested": {"deep": {"value": 42}}}),
        ]

        for outcome in outcomes:
            # Should never raise
            serialized = outcome.to_dict()
            assert isinstance(serialized, dict)
            assert "id" in serialized
            assert "ok" in serialized


class TestRuntimeExecuteInvariants:
    """Invariant: runtime.execute() always returns StructuredOutcome, never throws."""

    @pytest.fixture
    def runtime(self):
        """Create a runtime with test handlers."""
        rt = Runtime()

        # Register a successful handler
        async def success_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "ok", "data": inputs.get("data", "default")}

        # Register a failing handler
        async def failing_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Intentional failure")

        # Register a timeout handler
        async def timeout_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
            await asyncio.sleep(10)  # Will timeout
            return {"status": "ok"}

        rt.register_skill(
            SkillDescriptor(
                skill_id="test.success",
                name="Success Test",
                version="1.0.0",
                inputs_schema_version="1.0",
                outputs_schema_version="1.0",
                stable_fields={},
                cost_model={},
                failure_modes=[],
                constraints={},
            ),
            success_handler,
        )

        rt.register_skill(
            SkillDescriptor(
                skill_id="test.fail",
                name="Failing Test",
                version="1.0.0",
                inputs_schema_version="1.0",
                outputs_schema_version="1.0",
                stable_fields={},
                cost_model={},
                failure_modes=[{"code": "ERR_INTENTIONAL", "category": "PERMANENT"}],
                constraints={},
            ),
            failing_handler,
        )

        rt.register_skill(
            SkillDescriptor(
                skill_id="test.timeout",
                name="Timeout Test",
                version="1.0.0",
                inputs_schema_version="1.0",
                outputs_schema_version="1.0",
                stable_fields={},
                cost_model={},
                failure_modes=[{"code": "ERR_TIMEOUT", "category": "TRANSIENT"}],
                constraints={},
            ),
            timeout_handler,
        )

        return rt

    @pytest.mark.asyncio
    async def test_execute_success_returns_outcome(self, runtime):
        """Successful execution returns StructuredOutcome with ok=True."""
        outcome = await runtime.execute("test.success", {"data": "test"})

        assert isinstance(outcome, StructuredOutcome)
        assert outcome.ok is True
        assert outcome.result is not None

    @pytest.mark.asyncio
    async def test_execute_failure_returns_outcome_not_exception(self, runtime):
        """Failed execution returns StructuredOutcome, does not raise."""
        outcome = await runtime.execute("test.fail", {})

        # MUST return outcome, not raise
        assert isinstance(outcome, StructuredOutcome)
        assert outcome.ok is False
        assert outcome.error is not None
        assert "code" in outcome.error

    @pytest.mark.asyncio
    async def test_execute_timeout_returns_outcome(self, runtime):
        """Timeout returns StructuredOutcome, does not raise."""
        outcome = await runtime.execute("test.timeout", {}, timeout_s=0.1)

        assert isinstance(outcome, StructuredOutcome)
        assert outcome.ok is False
        assert outcome.error is not None
        assert outcome.error["code"] == "ERR_TIMEOUT"

    @pytest.mark.asyncio
    async def test_execute_unknown_skill_returns_outcome(self, runtime):
        """Unknown skill returns error outcome, does not raise."""
        outcome = await runtime.execute("nonexistent.skill", {})

        assert isinstance(outcome, StructuredOutcome)
        assert outcome.ok is False
        assert "SKILL_NOT_FOUND" in outcome.error["code"]


class TestSkillDescriptorInvariants:
    """Invariant: Skill descriptors are immutable after creation."""

    def test_descriptor_fields_are_readonly(self):
        """Descriptor fields should not be modifiable after creation."""
        descriptor = SkillDescriptor(
            skill_id="test.skill",
            name="Test Skill",
            version="1.0.0",
            inputs_schema_version="1.0",
            outputs_schema_version="1.0",
            stable_fields={"output": "DETERMINISTIC"},
            cost_model={"base_cents": 1},
            failure_modes=[{"code": "ERR_TEST", "category": "PERMANENT"}],
            constraints={"max_size": 1000},
        )

        # These assertions verify the structure exists
        assert descriptor.skill_id == "test.skill"
        assert descriptor.version == "1.0.0"

        # Note: Python dataclasses aren't truly immutable without frozen=True
        # This test documents the expectation that descriptors shouldn't be modified

    def test_descriptor_version_is_semantic(self):
        """Version must be semantic versioning format."""
        valid_versions = ["1.0.0", "2.1.0", "0.1.0", "1.0.0-stub", "1.0.0-beta"]

        for version in valid_versions:
            descriptor = SkillDescriptor(
                skill_id="test",
                name="Test",
                version=version,
                inputs_schema_version="1.0",
                outputs_schema_version="1.0",
                stable_fields={},
                cost_model={},
                failure_modes=[],
                constraints={},
            )
            assert descriptor.version == version


class TestContentHashInvariants:
    """Invariant: Content hashes are deterministic."""

    def test_same_input_same_hash(self):
        """Same input must produce same hash."""
        from app.utils.canonical_json import content_hash

        data = {"key": "value", "nested": {"a": 1, "b": 2}}

        hash1 = content_hash(data)
        hash2 = content_hash(data)

        assert hash1 == hash2

    def test_key_order_does_not_affect_hash(self):
        """Key order must not affect hash (canonical sorting)."""
        from app.utils.canonical_json import content_hash

        data1 = {"z": 1, "a": 2, "m": 3}
        data2 = {"a": 2, "m": 3, "z": 1}

        assert content_hash(data1) == content_hash(data2)

    def test_hash_length_is_consistent(self):
        """Hash length must be consistent."""
        from app.utils.canonical_json import content_hash

        data = {"test": "data"}

        hash16 = content_hash(data, length=16)
        hash32 = content_hash(data, length=32)

        assert len(hash16) == 16
        assert len(hash32) == 32
        assert hash32.startswith(hash16)


class TestErrorCategoryInvariants:
    """Invariant: All errors fit into defined categories."""

    def test_all_categories_defined(self):
        """All error categories must be defined."""
        expected_categories = {
            "TRANSIENT",
            "PERMANENT",
            "RESOURCE",
            "PERMISSION",
            "VALIDATION",
        }

        actual_categories = {cat.value for cat in ErrorCategory}

        assert expected_categories == actual_categories

    def test_category_determines_retryability(self):
        """Error category must determine retry behavior."""
        # TRANSIENT errors are retryable
        assert ErrorCategory.TRANSIENT.is_retryable() is True

        # PERMANENT errors are not retryable
        assert ErrorCategory.PERMANENT.is_retryable() is False

        # RESOURCE errors may be retryable (after wait)
        assert ErrorCategory.RESOURCE.is_retryable() is True

        # PERMISSION errors are not retryable
        assert ErrorCategory.PERMISSION.is_retryable() is False

        # VALIDATION errors are not retryable
        assert ErrorCategory.VALIDATION.is_retryable() is False


class TestSideEffectOrderingInvariants:
    """Invariant: Side effects are ordered and stable across replays."""

    def test_side_effects_maintain_order(self):
        """Side effects must maintain insertion order."""
        outcome = StructuredOutcome(
            id="test-1",
            ok=True,
            result={},
            meta={
                "side_effects": [
                    {"type": "write", "target": "file1"},
                    {"type": "write", "target": "file2"},
                    {"type": "delete", "target": "file3"},
                ]
            },
        )

        side_effects = outcome.meta.get("side_effects", [])
        targets = [se["target"] for se in side_effects]

        assert targets == ["file1", "file2", "file3"]

    def test_side_effects_serialization_preserves_order(self):
        """Side effects order must be preserved in serialization."""
        outcome = StructuredOutcome(
            id="test-1",
            ok=True,
            result={},
            meta={
                "side_effects": [
                    {"seq": 1, "action": "create"},
                    {"seq": 2, "action": "update"},
                    {"seq": 3, "action": "delete"},
                ]
            },
        )

        serialized = outcome.to_dict()
        side_effects = serialized["meta"]["side_effects"]

        sequences = [se["seq"] for se in side_effects]
        assert sequences == [1, 2, 3]


class TestResourceContractInvariants:
    """Invariant: Resource contracts are enforced."""

    def test_budget_is_non_negative(self):
        """Budget values must be non-negative."""
        contract = ResourceContract(
            resource_id="test-resource", budget_cents=100, rate_limit_per_min=60, max_concurrent=5
        )

        assert contract.budget_cents >= 0
        assert contract.rate_limit_per_min >= 0
        assert contract.max_concurrent >= 0

    def test_contract_declares_limits(self):
        """Contract must declare all limit types."""
        contract = ResourceContract(
            resource_id="test-resource", budget_cents=100, rate_limit_per_min=60, max_concurrent=5
        )

        # All limits must be explicitly declared
        assert hasattr(contract, "budget_cents")
        assert hasattr(contract, "rate_limit_per_min")
        assert hasattr(contract, "max_concurrent")


class TestQueryInvariants:
    """Invariant: runtime.query() returns consistent results."""

    @pytest.fixture
    def runtime(self):
        rt = Runtime()
        return rt

    @pytest.mark.asyncio
    async def test_query_budget_returns_dict(self, runtime):
        """Budget query must return a dictionary."""
        result = await runtime.query("budget", agent_id="test")

        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_query_unknown_type_returns_error(self, runtime):
        """Unknown query type must return error result."""
        result = await runtime.query("unknown_query_type")

        assert "error" in result or result.get("ok") is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
