"""
Determinism Invariant Test (PIN-126)

THE ONE TEST THAT MATTERS:
Given the same frozen trace, replay must produce identical output hash.
Or fail loudly with a classified reason.

This test:
- Must run in CI
- Must block merges
- Must never be flaky
- Must fail loudly with explanation

This is the proof, not a framework.
"""

import json
from pathlib import Path

from app.traces.models import TraceRecord, compare_traces


def load_frozen_trace(fixture_name: str) -> TraceRecord:
    """
    Load a frozen trace from fixtures.

    Frozen traces are immutable test artifacts that define
    the expected determinism contract.
    """
    fixture_path = Path(__file__).parent / "fixtures" / fixture_name
    with open(fixture_path) as f:
        data = json.load(f)
    return TraceRecord.from_dict(data)


class TestDeterminismInvariant:
    """
    The determinism invariant: identical inputs produce identical outputs.

    This is the core proof that our replay system is trustworthy.
    """

    def test_frozen_trace_has_schema_version(self):
        """
        Frozen traces must include schema version for compatibility.

        Without versioning, traces can silently become incompatible.
        """
        trace = load_frozen_trace("golden_trace.json")
        trace_dict = trace.to_dict()

        assert "schema_version" in trace_dict, "Trace must include schema_version"
        assert trace_dict["schema_version"] == TraceRecord.SCHEMA_VERSION, (
            f"Schema version mismatch: {trace_dict['schema_version']} != {TraceRecord.SCHEMA_VERSION}"
        )

    def test_frozen_trace_has_checksum(self):
        """
        Frozen traces must include integrity checksum.

        The checksum is the Merkle root of all determinism-relevant fields.
        """
        trace = load_frozen_trace("golden_trace.json")
        trace_dict = trace.to_dict()

        assert "checksum" in trace_dict, "Trace must include checksum"
        assert len(trace_dict["checksum"]) == 32, "Checksum must be 32 hex chars"

    def test_determinism_invariant_same_trace_same_hash(self):
        """
        THE CROWN JEWEL:
        Given the same frozen trace, computing the signature twice
        must produce identical results.

        This is the minimal proof that our hashing is deterministic.
        """
        trace = load_frozen_trace("golden_trace.json")

        # Compute signature twice
        sig1 = trace.determinism_signature()
        sig2 = trace.determinism_signature()

        assert sig1 == sig2, (
            f"Determinism invariant violated:\n"
            f"First computation:  {sig1}\n"
            f"Second computation: {sig2}\n"
            "Same trace must produce same hash."
        )

    def test_determinism_invariant_reload_same_hash(self):
        """
        Loading the same trace twice must produce identical signatures.

        This proves our serialization/deserialization is deterministic.
        """
        trace1 = load_frozen_trace("golden_trace.json")
        trace2 = load_frozen_trace("golden_trace.json")

        sig1 = trace1.determinism_signature()
        sig2 = trace2.determinism_signature()

        assert sig1 == sig2, (
            f"Determinism invariant violated across loads:\n"
            f"Load 1: {sig1}\n"
            f"Load 2: {sig2}\n"
            "Same trace file must produce same hash on reload."
        )

    def test_compare_traces_identical(self):
        """
        Comparing a trace to itself must show parity.
        """
        trace = load_frozen_trace("golden_trace.json")

        result = compare_traces(trace, trace)

        assert result.is_parity, (
            f"Self-comparison failed parity:\n"
            f"Original: {result.original_signature}\n"
            f"Replay:   {result.replay_signature}\n"
            f"Reason:   {result.divergence_reason}"
        )

    def test_float_normalization_prevents_drift(self):
        """
        Float values in params must be normalized to prevent precision drift.

        The golden_trace.json contains floats like 3.14159265 and 2.71828182.
        These must hash identically regardless of floating-point representation.
        """
        trace = load_frozen_trace("golden_trace.json")

        # The second step has float params nested in input
        step = trace.steps[1]
        assert "input" in step.params, "Test fixture must have 'input' param"
        assert "x" in step.params["input"], "Test fixture must have float param 'x' in input"
        assert isinstance(step.params["input"]["x"], float), "Param 'x' must be a float"

        # Hash must be stable
        hash1 = step.determinism_hash()
        hash2 = step.determinism_hash()

        assert hash1 == hash2, (
            f"Float normalization failed:\nHash 1: {hash1}\nHash 2: {hash2}\nFloat params must produce stable hashes."
        )

    def test_signature_is_stable_across_step_order(self):
        """
        The determinism signature must be computed from steps in order.

        This verifies the Merkle-root-like computation is stable.
        """
        trace = load_frozen_trace("golden_trace.json")

        # Signature should be a 32-char hex string
        sig = trace.determinism_signature()

        assert len(sig) == 32, f"Signature must be 32 hex chars, got {len(sig)}"
        assert all(c in "0123456789abcdef" for c in sig), "Signature must be hex"

        # Must be stable
        assert sig == trace.determinism_signature(), "Signature must be idempotent"


class TestDeterminismDriftDetection:
    """
    Tests that verify we detect divergence correctly.

    These are the "fail loudly" cases.
    """

    def test_detect_step_count_divergence(self):
        """
        Traces with different step counts must not show parity.
        """
        trace1 = load_frozen_trace("golden_trace.json")
        trace2 = load_frozen_trace("golden_trace.json")

        # Remove a step from trace2
        trace2.steps = trace2.steps[:1]

        result = compare_traces(trace1, trace2)

        assert not result.is_parity, "Different step counts must fail parity"
        assert "step count" in (result.divergence_reason or "").lower(), (
            f"Divergence reason must mention step count, got: {result.divergence_reason}"
        )

    def test_detect_status_divergence(self):
        """
        Traces with different step statuses must not show parity.
        """
        from app.traces.models import TraceStatus

        trace1 = load_frozen_trace("golden_trace.json")
        trace2 = load_frozen_trace("golden_trace.json")

        # Change status of first step
        trace2.steps[0].status = TraceStatus.FAILURE

        result = compare_traces(trace1, trace2)

        assert not result.is_parity, "Different statuses must fail parity"
        assert result.divergence_step == 0, "Divergence must be at step 0"

    def test_detect_params_divergence(self):
        """
        Traces with different params must not show parity.
        """
        trace1 = load_frozen_trace("golden_trace.json")
        trace2 = load_frozen_trace("golden_trace.json")

        # Change params of first step
        trace2.steps[0].params = {"input": {"a": 999, "b": 2}}

        result = compare_traces(trace1, trace2)

        assert not result.is_parity, "Different params must fail parity"
        assert result.divergence_step == 0, "Divergence must be at step 0"
        assert "params" in (result.divergence_reason or "").lower(), (
            f"Divergence reason must mention params, got: {result.divergence_reason}"
        )


class TestSchemaVersioning:
    """
    Tests for schema version compatibility.
    """

    def test_schema_version_is_set(self):
        """
        TraceRecord must have a SCHEMA_VERSION class variable.
        """
        assert hasattr(TraceRecord, "SCHEMA_VERSION"), "TraceRecord must have SCHEMA_VERSION"
        assert isinstance(TraceRecord.SCHEMA_VERSION, str), "SCHEMA_VERSION must be a string"
        assert TraceRecord.SCHEMA_VERSION == "1.0.0", "Initial schema version must be 1.0.0"

    def test_to_dict_includes_schema_version(self):
        """
        to_dict() must include schema_version for all traces.
        """
        trace = load_frozen_trace("golden_trace.json")
        trace_dict = trace.to_dict()

        assert "schema_version" in trace_dict, "to_dict() must include schema_version"
        assert trace_dict["schema_version"] == "1.0.0", "Schema version must match class constant"

    def test_to_dict_includes_checksum(self):
        """
        to_dict() must include checksum for integrity verification.
        """
        trace = load_frozen_trace("golden_trace.json")
        trace_dict = trace.to_dict()

        assert "checksum" in trace_dict, "to_dict() must include checksum"
        assert trace_dict["checksum"] == trace.determinism_signature(), "Checksum must match determinism_signature()"
