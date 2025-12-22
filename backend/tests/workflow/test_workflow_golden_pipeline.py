# Golden-File Pipeline Tests (M4)
"""
Tests for golden-file recording and verification.

Tests:
1. Recording run events
2. HMAC signing and verification
3. Golden file comparison
4. Tamper detection
"""

import json
import os
import tempfile

import pytest

from app.workflow.engine import StepDescriptor, StepResult, WorkflowSpec
from app.workflow.golden import (
    GoldenEvent,
    GoldenRecorder,
    InMemoryGoldenRecorder,
    _canonical_json,
)


@pytest.fixture
def golden_dir():
    """Create temporary directory for golden files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def recorder(golden_dir):
    """Create golden recorder with temp directory."""
    return GoldenRecorder(golden_dir, secret="test-secret")


@pytest.fixture
def spec():
    """Create test workflow spec."""
    return WorkflowSpec(
        id="golden-test-spec",
        name="Golden Test Spec",
        version="1.0.0",
        steps=[
            StepDescriptor(id="step1", skill_id="noop", inputs={"x": 1}),
            StepDescriptor(id="step2", skill_id="echo", inputs={"y": 2}),
        ],
    )


@pytest.fixture
def step_result():
    """Create test step result."""
    return StepResult(
        step_id="step1",
        success=True,
        output={"value": 42},
        cost_cents=10,
    )


class TestGoldenRecorder:
    """Tests for GoldenRecorder."""

    @pytest.mark.asyncio
    async def test_record_run_start(self, recorder, golden_dir, spec):
        """Record run start event."""
        await recorder.record_run_start(
            run_id="test-run",
            spec=spec,
            seed=12345,
            replay=False,
        )

        filepath = os.path.join(golden_dir, "test-run.steps.jsonl")
        assert os.path.exists(filepath)

        with open(filepath) as f:
            line = f.readline()
            event = json.loads(line)

        assert event["event_type"] == "run_start"
        assert event["run_id"] == "test-run"
        assert event["data"]["spec_id"] == "golden-test-spec"
        assert event["data"]["seed"] == 12345
        assert event["data"]["replay"] is False

    @pytest.mark.asyncio
    async def test_record_step(self, recorder, golden_dir, spec, step_result):
        """Record step execution event."""
        await recorder.record_run_start("test-run", spec, 12345, False)
        await recorder.record_step(
            run_id="test-run",
            step_index=0,
            step=spec.steps[0],
            result=step_result,
            seed=99999,
        )

        filepath = os.path.join(golden_dir, "test-run.steps.jsonl")
        with open(filepath) as f:
            lines = f.readlines()

        assert len(lines) == 2
        event = json.loads(lines[1])

        assert event["event_type"] == "step"
        assert event["data"]["index"] == 0
        assert event["data"]["step_id"] == "step1"
        assert event["data"]["seed"] == 99999
        assert event["data"]["output"]["success"] is True

    @pytest.mark.asyncio
    async def test_record_run_end(self, recorder, golden_dir, spec, step_result):
        """Record run end and sign file."""
        await recorder.record_run_start("test-run", spec, 12345, False)
        await recorder.record_step("test-run", 0, spec.steps[0], step_result, 99999)
        await recorder.record_run_end("test-run", "completed")

        filepath = os.path.join(golden_dir, "test-run.steps.jsonl")
        sig_filepath = filepath + ".sig"

        assert os.path.exists(filepath)
        assert os.path.exists(sig_filepath)

        with open(filepath) as f:
            lines = f.readlines()
        assert len(lines) == 3

        event = json.loads(lines[2])
        assert event["event_type"] == "run_end"
        assert event["data"]["status"] == "completed"

    def test_sign_golden(self, recorder, golden_dir):
        """Sign golden file with HMAC."""
        filepath = os.path.join(golden_dir, "test.jsonl")
        with open(filepath, "w") as f:
            f.write('{"test": "data"}\n')

        sig = recorder.sign_golden(filepath)

        assert sig is not None
        assert len(sig) == 64  # SHA256 hex

        assert os.path.exists(filepath + ".sig")
        with open(filepath + ".sig") as f:
            stored_sig = f.read().strip()
        assert stored_sig == sig

    def test_verify_golden_valid(self, recorder, golden_dir):
        """Verify valid signature."""
        filepath = os.path.join(golden_dir, "valid.jsonl")
        with open(filepath, "w") as f:
            f.write('{"test": "data"}\n')

        recorder.sign_golden(filepath)
        assert recorder.verify_golden(filepath) is True

    def test_verify_golden_tampered(self, recorder, golden_dir):
        """Detect tampered file."""
        filepath = os.path.join(golden_dir, "tampered.jsonl")
        with open(filepath, "w") as f:
            f.write('{"test": "data"}\n')

        recorder.sign_golden(filepath)

        # Tamper with file
        with open(filepath, "a") as f:
            f.write('{"tampered": true}\n')

        assert recorder.verify_golden(filepath) is False

    def test_verify_golden_no_signature(self, recorder, golden_dir):
        """Reject file with no signature."""
        filepath = os.path.join(golden_dir, "unsigned.jsonl")
        with open(filepath, "w") as f:
            f.write('{"test": "data"}\n')

        assert recorder.verify_golden(filepath) is False

    def test_load_golden(self, recorder, golden_dir):
        """Load golden file events."""
        filepath = os.path.join(golden_dir, "load.jsonl")
        events_data = [
            {"event_type": "run_start", "run_id": "r1", "timestamp": "2025-01-01T00:00:00Z", "data": {"seed": 1}},
            {"event_type": "step", "run_id": "r1", "timestamp": "2025-01-01T00:00:01Z", "data": {"index": 0}},
            {"event_type": "run_end", "run_id": "r1", "timestamp": "2025-01-01T00:00:02Z", "data": {"status": "done"}},
        ]

        with open(filepath, "w") as f:
            for e in events_data:
                f.write(json.dumps(e, sort_keys=True) + "\n")

        events = recorder.load_golden(filepath)

        assert len(events) == 3
        assert events[0].event_type == "run_start"
        assert events[1].event_type == "step"
        assert events[2].event_type == "run_end"


class TestGoldenComparison:
    """Tests for golden file comparison."""

    def test_compare_identical(self, recorder, golden_dir):
        """Compare identical golden files."""
        file1 = os.path.join(golden_dir, "file1.jsonl")
        file2 = os.path.join(golden_dir, "file2.jsonl")

        events = [
            {"event_type": "run_start", "run_id": "r1", "timestamp": "T1", "data": {"seed": 1}},
            {"event_type": "run_end", "run_id": "r1", "timestamp": "T2", "data": {"status": "done"}},
        ]

        for filepath in [file1, file2]:
            with open(filepath, "w") as f:
                for e in events:
                    f.write(_canonical_json(e) + "\n")

        result = recorder.compare_golden(file1, file2)

        assert result["match"] is True
        assert len(result["diffs"]) == 0

    def test_compare_different_timestamps_ignored(self, recorder, golden_dir):
        """Ignore timestamp differences when flag set."""
        file1 = os.path.join(golden_dir, "file1.jsonl")
        file2 = os.path.join(golden_dir, "file2.jsonl")

        with open(file1, "w") as f:
            f.write(
                _canonical_json(
                    {
                        "event_type": "run_start",
                        "run_id": "r1",
                        "timestamp": "2025-01-01T00:00:00Z",
                        "data": {"seed": 1},
                    }
                )
                + "\n"
            )

        with open(file2, "w") as f:
            f.write(
                _canonical_json(
                    {
                        "event_type": "run_start",
                        "run_id": "r1",
                        "timestamp": "2025-01-02T00:00:00Z",  # Different timestamp
                        "data": {"seed": 1},
                    }
                )
                + "\n"
            )

        result = recorder.compare_golden(file1, file2, ignore_timestamps=True)
        assert result["match"] is True

    def test_compare_different_data(self, recorder, golden_dir):
        """Detect different data in events."""
        file1 = os.path.join(golden_dir, "file1.jsonl")
        file2 = os.path.join(golden_dir, "file2.jsonl")

        with open(file1, "w") as f:
            f.write(
                _canonical_json({"event_type": "run_start", "run_id": "r1", "timestamp": "T1", "data": {"seed": 1}})
                + "\n"
            )

        with open(file2, "w") as f:
            f.write(
                _canonical_json(
                    {
                        "event_type": "run_start",
                        "run_id": "r1",
                        "timestamp": "T1",
                        "data": {"seed": 999},  # Different seed
                    }
                )
                + "\n"
            )

        result = recorder.compare_golden(file1, file2)

        assert result["match"] is False
        assert len(result["diffs"]) == 1
        assert result["diffs"][0]["type"] == "event_mismatch"

    def test_compare_different_event_count(self, recorder, golden_dir):
        """Detect different number of events."""
        file1 = os.path.join(golden_dir, "file1.jsonl")
        file2 = os.path.join(golden_dir, "file2.jsonl")

        with open(file1, "w") as f:
            f.write(_canonical_json({"event_type": "run_start", "run_id": "r1", "timestamp": "T1", "data": {}}) + "\n")
            f.write(_canonical_json({"event_type": "run_end", "run_id": "r1", "timestamp": "T2", "data": {}}) + "\n")

        with open(file2, "w") as f:
            f.write(_canonical_json({"event_type": "run_start", "run_id": "r1", "timestamp": "T1", "data": {}}) + "\n")

        result = recorder.compare_golden(file1, file2)

        assert result["match"] is False
        assert any(d["type"] == "event_count_mismatch" for d in result["diffs"])


class TestInMemoryGoldenRecorder:
    """Tests for InMemoryGoldenRecorder."""

    @pytest.mark.asyncio
    async def test_records_events(self, spec, step_result):
        """In-memory recorder captures events."""
        recorder = InMemoryGoldenRecorder()

        await recorder.record_run_start("test-run", spec, 12345, False)
        await recorder.record_step("test-run", 0, spec.steps[0], step_result, 99999)
        await recorder.record_run_end("test-run", "completed")

        events = recorder.get_events("test-run")

        assert len(events) == 3
        assert events[0].event_type == "run_start"
        assert events[1].event_type == "step"
        assert events[2].event_type == "run_end"

    @pytest.mark.asyncio
    async def test_clear(self, spec):
        """Clear removes all events."""
        recorder = InMemoryGoldenRecorder()

        await recorder.record_run_start("run1", spec, 1, False)
        await recorder.record_run_start("run2", spec, 2, False)

        recorder.clear()

        assert len(recorder.get_events("run1")) == 0
        assert len(recorder.get_events("run2")) == 0


class TestGoldenEvent:
    """Tests for GoldenEvent dataclass."""

    def test_to_dict(self):
        """Event serializes to dict."""
        event = GoldenEvent(
            event_type="step",
            run_id="r1",
            timestamp="2025-01-01T00:00:00Z",
            data={"index": 0, "output": {"value": 42}},
        )

        d = event.to_dict()

        assert d["event_type"] == "step"
        assert d["run_id"] == "r1"
        assert d["timestamp"] == "2025-01-01T00:00:00Z"
        assert d["data"]["index"] == 0

    def test_to_deterministic_dict(self):
        """Deterministic dict excludes timestamp."""
        event = GoldenEvent(
            event_type="step",
            run_id="r1",
            timestamp="2025-01-01T00:00:00Z",
            data={"index": 0},
        )

        d = event.to_deterministic_dict()

        assert "timestamp" not in d
        assert d["event_type"] == "step"
        assert d["run_id"] == "r1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
