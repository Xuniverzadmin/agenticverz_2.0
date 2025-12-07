"""
Tests for Trace schema and serialization.
"""

import pytest
import json
import tempfile
from pathlib import Path

from aos_sdk import Trace, TraceStep, diff_traces, hash_data, RuntimeContext, create_trace_from_context


class TestTraceStep:
    """Tests for TraceStep class."""

    def test_create_step(self):
        """Create a basic trace step."""
        step = TraceStep(
            step_index=0,
            skill_id="transform",
            input_hash="abc123",
            output_hash="def456",
            rng_state_before="aabbcc",
            duration_ms=150,
            outcome="success"
        )

        assert step.step_index == 0
        assert step.skill_id == "transform"
        assert step.outcome == "success"

    def test_step_timestamp_auto(self):
        """Step gets automatic timestamp."""
        step = TraceStep(
            step_index=0,
            skill_id="test",
            input_hash="x",
            output_hash="y",
            rng_state_before="z",
            duration_ms=100,
            outcome="success"
        )

        assert step.timestamp is not None
        assert "T" in step.timestamp

    def test_step_to_dict(self):
        """Step serializes to dict."""
        step = TraceStep(
            step_index=1,
            skill_id="echo",
            input_hash="in",
            output_hash="out",
            rng_state_before="rng",
            duration_ms=50,
            outcome="failure",
            error_code="E001",
            timestamp="2025-01-01T00:00:00Z"
        )

        data = step.to_dict()

        assert data["step_index"] == 1
        assert data["skill_id"] == "echo"
        assert data["outcome"] == "failure"
        assert data["error_code"] == "E001"

    def test_step_from_dict(self):
        """Step deserializes from dict."""
        data = {
            "step_index": 2,
            "skill_id": "http",
            "input_hash": "req",
            "output_hash": "resp",
            "rng_state_before": "state",
            "duration_ms": 1000,
            "outcome": "success",
            "error_code": None,
            "timestamp": "2025-06-15T12:00:00Z"
        }

        step = TraceStep.from_dict(data)

        assert step.step_index == 2
        assert step.skill_id == "http"
        assert step.duration_ms == 1000


class TestTrace:
    """Tests for Trace class."""

    def test_create_trace(self):
        """Create a basic trace."""
        trace = Trace(
            seed=42,
            plan=[{"skill": "test"}]
        )

        assert trace.seed == 42
        assert trace.plan == [{"skill": "test"}]
        assert trace.version == "1.1.0"  # v1.1 for deterministic hashing
        assert trace.finalized is False

    def test_add_step(self):
        """Add steps to trace."""
        trace = Trace(seed=42, plan=[])

        step = trace.add_step(
            skill_id="transform",
            input_data={"x": 1},
            output_data={"y": 2},
            rng_state="abc",
            duration_ms=100,
            outcome="success"
        )

        assert len(trace.steps) == 1
        assert step.step_index == 0
        assert step.skill_id == "transform"

    def test_add_multiple_steps(self):
        """Add multiple steps with correct indices."""
        trace = Trace(seed=42, plan=[])

        trace.add_step("s1", {}, {}, "r1", 10, "success")
        trace.add_step("s2", {}, {}, "r2", 20, "success")
        trace.add_step("s3", {}, {}, "r3", 30, "failure", "E001")

        assert len(trace.steps) == 3
        assert trace.steps[0].step_index == 0
        assert trace.steps[1].step_index == 1
        assert trace.steps[2].step_index == 2

    def test_finalize(self):
        """Finalize computes root hash."""
        trace = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace.add_step("test", {}, {}, "rng", 100, "success")

        root = trace.finalize()

        assert trace.finalized is True
        assert trace.root_hash is not None
        assert len(trace.root_hash) == 64
        assert root == trace.root_hash

    def test_finalize_twice_raises(self):
        """Cannot finalize twice."""
        trace = Trace(seed=42, plan=[])
        trace.finalize()

        with pytest.raises(ValueError, match="already finalized"):
            trace.finalize()

    def test_add_step_after_finalize_raises(self):
        """Cannot add steps after finalize."""
        trace = Trace(seed=42, plan=[])
        trace.finalize()

        with pytest.raises(ValueError, match="finalized trace"):
            trace.add_step("test", {}, {}, "rng", 100, "success")

    def test_verify_valid(self):
        """Verify returns True for valid trace."""
        trace = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace.add_step("test", {}, {}, "rng", 100, "success")
        trace.finalize()

        assert trace.verify() is True

    def test_verify_tampered(self):
        """Verify returns False for tampered trace."""
        trace = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace.add_step("test", {}, {}, "rng", 100, "success")
        trace.finalize()

        # Tamper with the trace
        original_hash = trace.root_hash
        trace.root_hash = "0" * 64

        assert trace.verify() is False

        # Restore
        trace.root_hash = original_hash
        assert trace.verify() is True

    def test_to_dict(self):
        """Trace serializes to dict."""
        trace = Trace(
            seed=42,
            plan=[{"skill": "x"}],
            timestamp="2025-01-01T00:00:00Z",
            tenant_id="t1",
            metadata={"key": "value"}
        )
        trace.add_step("x", {"a": 1}, {"b": 2}, "rng", 50, "success")
        trace.finalize()

        data = trace.to_dict()

        assert data["version"] == "1.1.0"  # v1.1 for deterministic hashing
        assert data["seed"] == 42
        assert data["tenant_id"] == "t1"
        assert data["plan"] == [{"skill": "x"}]
        assert len(data["steps"]) == 1
        assert data["finalized"] is True
        assert data["root_hash"] is not None

    def test_to_json(self):
        """Trace serializes to canonical JSON."""
        trace = Trace(seed=42, plan=[])
        trace.finalize()

        json_str = trace.to_json()

        # Should be compact (no pretty printing)
        assert "\n" not in json_str
        assert "  " not in json_str

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["seed"] == 42

    def test_from_dict(self):
        """Trace deserializes from dict."""
        data = {
            "version": "1.0.0",
            "seed": 99,
            "timestamp": "2025-06-15T00:00:00Z",
            "tenant_id": "restored",
            "plan": [{"skill": "y"}],
            "steps": [
                {
                    "step_index": 0,
                    "skill_id": "y",
                    "input_hash": "i",
                    "output_hash": "o",
                    "rng_state_before": "r",
                    "duration_ms": 200,
                    "outcome": "success",
                    "error_code": None,
                    "timestamp": "2025-06-15T00:00:00Z"
                }
            ],
            "root_hash": "abcd1234",
            "finalized": True,
            "metadata": {}
        }

        trace = Trace.from_dict(data)

        assert trace.seed == 99
        assert trace.tenant_id == "restored"
        assert len(trace.steps) == 1
        assert trace.root_hash == "abcd1234"

    def test_roundtrip_serialization(self):
        """Trace survives dict roundtrip."""
        original = Trace(
            seed=42,
            plan=[{"skill": "roundtrip"}],
            timestamp="2025-01-01T00:00:00Z"
        )
        original.add_step("roundtrip", {"in": 1}, {"out": 2}, "rng", 100, "success")
        original.finalize()

        # Roundtrip through dict
        data = original.to_dict()
        restored = Trace.from_dict(data)

        assert restored.seed == original.seed
        assert restored.root_hash == original.root_hash
        assert len(restored.steps) == len(original.steps)
        assert restored.verify()

    def test_roundtrip_json(self):
        """Trace survives JSON roundtrip."""
        original = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        original.add_step("test", {}, {}, "rng", 50, "success")
        original.finalize()

        # Roundtrip through JSON
        json_str = original.to_json()
        restored = Trace.from_json(json_str)

        assert restored.root_hash == original.root_hash
        assert restored.verify()


class TestTraceSaveLoad:
    """Tests for trace file operations."""

    def test_save_and_load(self):
        """Save and load trace from file."""
        trace = Trace(seed=42, plan=[{"skill": "file"}], timestamp="2025-01-01T00:00:00Z")
        trace.add_step("file", {"data": "test"}, {"result": "ok"}, "rng", 75, "success")
        trace.finalize()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.trace.json"

            trace.save(str(path))
            loaded = Trace.load(str(path))

            assert loaded.seed == trace.seed
            assert loaded.root_hash == trace.root_hash
            assert loaded.verify()


class TestDiffTraces:
    """Tests for trace diffing."""

    def test_identical_traces_match(self):
        """Identical traces report match - NO manual timestamp fixing needed."""
        # v1.1: root_hash excludes audit fields (timestamp, duration_ms)
        # Two traces with same deterministic fields should match regardless of step timestamps

        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.add_step("test", {"x": 1}, {"y": 2}, "rng", 100, "success")
        trace1.finalize()

        # Small delay doesn't matter - audit timestamps excluded from hash
        import time
        time.sleep(0.01)

        trace2 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace2.add_step("test", {"x": 1}, {"y": 2}, "rng", 200, "success")  # Different duration
        trace2.finalize()

        # Root hashes should be IDENTICAL because only deterministic fields are hashed
        assert trace1.root_hash == trace2.root_hash

        result = diff_traces(trace1, trace2)
        assert result["match"] is True
        assert len(result["differences"]) == 0

    def test_different_seed_detected(self):
        """Different seeds are detected."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.finalize()

        trace2 = Trace(seed=43, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace2.finalize()

        result = diff_traces(trace1, trace2)

        assert result["match"] is False
        assert any(d["field"] == "seed" for d in result["differences"])

    def test_different_timestamp_detected(self):
        """Different timestamps are detected."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.finalize()

        trace2 = Trace(seed=42, plan=[], timestamp="2025-01-02T00:00:00Z")
        trace2.finalize()

        result = diff_traces(trace1, trace2)

        assert result["match"] is False
        assert any(d["field"] == "timestamp" for d in result["differences"])

    def test_different_step_count_detected(self):
        """Different step counts are detected."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.add_step("a", {}, {}, "r", 10, "success")
        trace1.finalize()

        trace2 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace2.add_step("a", {}, {}, "r", 10, "success")
        trace2.add_step("b", {}, {}, "r", 10, "success")
        trace2.finalize()

        result = diff_traces(trace1, trace2)

        assert result["match"] is False
        assert any(d["field"] == "step_count" for d in result["differences"])

    def test_different_output_hash_detected(self):
        """Different output hashes are detected."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.add_step("test", {"x": 1}, {"y": 2}, "rng", 100, "success")
        trace1.finalize()

        trace2 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace2.add_step("test", {"x": 1}, {"y": 999}, "rng", 100, "success")  # Different output
        trace2.finalize()

        result = diff_traces(trace1, trace2)

        assert result["match"] is False
        assert any("output_hash" in d["field"] for d in result["differences"])

    def test_summary_message(self):
        """Diff provides human-readable summary."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace1.finalize()

        trace2 = Trace(seed=99, plan=[], timestamp="2025-01-01T00:00:00Z")
        trace2.finalize()

        result = diff_traces(trace1, trace2)

        assert "summary" in result
        assert "seed" in result["summary"].lower() or "differ" in result["summary"].lower()


class TestHashData:
    """Tests for hash_data utility."""

    def test_same_data_same_hash(self):
        """Identical data produces identical hash."""
        data1 = {"a": 1, "b": [1, 2, 3]}
        data2 = {"a": 1, "b": [1, 2, 3]}

        assert hash_data(data1) == hash_data(data2)

    def test_key_order_independent(self):
        """Key order doesn't affect hash."""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}

        assert hash_data(data1) == hash_data(data2)

    def test_different_data_different_hash(self):
        """Different data produces different hash."""
        data1 = {"value": 1}
        data2 = {"value": 2}

        assert hash_data(data1) != hash_data(data2)

    def test_hash_length(self):
        """Hash is 16 hex characters."""
        h = hash_data({"test": "data"})

        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)


class TestCreateTraceFromContext:
    """Tests for trace creation from RuntimeContext."""

    def test_create_from_context(self):
        """Create trace from RuntimeContext."""
        ctx = RuntimeContext(
            seed=42,
            now="2025-01-01T00:00:00Z",
            tenant_id="test-tenant"
        )

        plan = [{"skill": "x"}, {"skill": "y"}]
        trace = create_trace_from_context(ctx, plan)

        assert trace.seed == 42
        assert trace.tenant_id == "test-tenant"
        assert trace.plan == plan
        assert "2025-01-01" in trace.timestamp


class TestTraceDeterminism:
    """End-to-end determinism tests."""

    def test_full_determinism_workflow(self):
        """Complete workflow produces identical traces - NO manual timestamp fixing."""
        # v1.1: Audit fields excluded from hash, so this test works naturally

        # First run
        ctx1 = RuntimeContext(seed=42, now="2025-01-01T00:00:00Z")
        trace1 = Trace(seed=ctx1.seed, plan=[{"skill": "det"}], timestamp=ctx1.timestamp())

        # Simulate using context
        random_val_1 = ctx1.randint(0, 1000)
        trace1.add_step(
            skill_id="det",
            input_data={"seed": 42},
            output_data={"random": random_val_1},
            rng_state=ctx1.rng_state,
            duration_ms=100,
            outcome="success"
        )
        trace1.finalize()

        # Second run with same seed/time - different duration doesn't matter
        ctx2 = RuntimeContext(seed=42, now="2025-01-01T00:00:00Z")
        trace2 = Trace(seed=ctx2.seed, plan=[{"skill": "det"}], timestamp=ctx2.timestamp())

        random_val_2 = ctx2.randint(0, 1000)
        trace2.add_step(
            skill_id="det",
            input_data={"seed": 42},
            output_data={"random": random_val_2},
            rng_state=ctx2.rng_state,
            duration_ms=250,  # Different duration - doesn't affect hash
            outcome="success"
        )
        trace2.finalize()

        # Verify identical - random values and root hashes must match
        assert random_val_1 == random_val_2
        assert trace1.root_hash == trace2.root_hash

        result = diff_traces(trace1, trace2)
        assert result["match"] is True

    def test_audit_fields_preserved_but_excluded_from_hash(self):
        """Audit fields (timestamp, duration_ms) are stored but don't affect root_hash."""
        trace1 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        step1 = trace1.add_step("test", {"x": 1}, {"y": 2}, "rng", 100, "success")
        trace1.finalize()

        trace2 = Trace(seed=42, plan=[], timestamp="2025-01-01T00:00:00Z")
        step2 = trace2.add_step("test", {"x": 1}, {"y": 2}, "rng", 999, "success")  # Very different duration
        trace2.finalize()

        # Audit fields are different
        assert step1.duration_ms != step2.duration_ms
        assert step1.timestamp != step2.timestamp  # Auto-generated, will differ

        # But root hashes are identical
        assert trace1.root_hash == trace2.root_hash

        # And audit fields are preserved in serialization
        data1 = trace1.to_dict()
        assert data1["steps"][0]["duration_ms"] == 100
        assert data1["steps"][0]["timestamp"] is not None
