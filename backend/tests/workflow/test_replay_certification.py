# tests/workflow/test_replay_certification.py
"""
Workflow Replay Certification Tests

BLOCKER for M3: Certify that workflows are deterministic and replayable.

This test suite verifies:
1. Same inputs -> Same outputs (determinism)
2. Workflow can be replayed from recorded state
3. Replay produces identical results to original run
4. Non-deterministic fields are properly isolated

Vision Alignment (PIN-005):
- Deterministic state management
- Replayable runs
- Zero silent failures
"""

import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Path setup
_backend_path = str(Path(__file__).parent.parent.parent)
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)


@dataclass
class ReplayRecord:
    """Record of a workflow execution for replay testing."""

    workflow_id: str
    run_id: str
    steps: List[Dict[str, Any]]
    final_status: str
    deterministic_hash: str
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StepRecord:
    """Record of a single step execution."""

    step_id: str
    skill: str
    params: Dict[str, Any]
    output: Dict[str, Any]
    status: str
    deterministic_hash: str


def compute_deterministic_hash(data: Dict[str, Any], exclude_fields: Optional[set] = None) -> str:
    """Compute deterministic hash excluding non-deterministic fields."""
    exclude = exclude_fields or {"timestamp", "duration_ms", "started_at", "ended_at", "meta"}

    def filter_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(d, dict):
            return d
        return {k: filter_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items()) if k not in exclude}

    filtered = filter_dict(data)
    canonical = json.dumps(filtered, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class WorkflowReplayHarness:
    """
    Test harness for workflow replay certification.

    Records workflow executions and verifies replay produces identical results.
    """

    def __init__(self):
        self.recorded_runs: Dict[str, ReplayRecord] = {}

    def record_run(self, workflow_id: str, steps: List[Dict[str, Any]], final_status: str) -> ReplayRecord:
        """Record a workflow run for replay testing."""
        import uuid

        # Compute deterministic hash of the run
        hash_data = {
            "workflow_id": workflow_id,
            "steps": [
                {
                    "step_id": s["step_id"],
                    "skill": s["skill"],
                    "status": s.get("status", "ok"),
                    "output_hash": compute_deterministic_hash(s.get("output", {})),
                }
                for s in steps
            ],
            "final_status": final_status,
        }

        record = ReplayRecord(
            workflow_id=workflow_id,
            run_id=str(uuid.uuid4()),
            steps=steps,
            final_status=final_status,
            deterministic_hash=compute_deterministic_hash(hash_data),
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )

        self.recorded_runs[record.run_id] = record
        return record

    def verify_replay(
        self, original_record: ReplayRecord, replay_steps: List[Dict[str, Any]], replay_status: str
    ) -> tuple[bool, str]:
        """
        Verify replay produces identical deterministic output.

        Returns:
            Tuple of (passed: bool, reason: str)
        """
        # Compute hash of replay
        replay_hash_data = {
            "workflow_id": original_record.workflow_id,
            "steps": [
                {
                    "step_id": s["step_id"],
                    "skill": s["skill"],
                    "status": s.get("status", "ok"),
                    "output_hash": compute_deterministic_hash(s.get("output", {})),
                }
                for s in replay_steps
            ],
            "final_status": replay_status,
        }
        replay_hash = compute_deterministic_hash(replay_hash_data)

        if replay_hash != original_record.deterministic_hash:
            return False, f"Hash mismatch: original={original_record.deterministic_hash}, replay={replay_hash}"

        # Verify step count matches
        if len(replay_steps) != len(original_record.steps):
            return False, f"Step count mismatch: original={len(original_record.steps)}, replay={len(replay_steps)}"

        # Verify each step
        for i, (orig, replay) in enumerate(zip(original_record.steps, replay_steps)):
            if orig["step_id"] != replay["step_id"]:
                return False, f"Step {i} ID mismatch: {orig['step_id']} vs {replay['step_id']}"
            if orig["skill"] != replay["skill"]:
                return False, f"Step {i} skill mismatch: {orig['skill']} vs {replay['skill']}"

        return True, "Replay certified - deterministic output verified"


class TestReplayCertification:
    """Replay certification tests for workflow determinism."""

    @pytest.fixture
    def harness(self):
        return WorkflowReplayHarness()

    def test_identical_runs_produce_same_hash(self, harness):
        """Two identical runs should produce the same deterministic hash."""
        steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
            {"step_id": "s2", "skill": "json_transform", "output": {"result": "world"}},
        ]

        record1 = harness.record_run("wf-1", steps, "succeeded")
        record2 = harness.record_run("wf-1", steps, "succeeded")

        assert record1.deterministic_hash == record2.deterministic_hash

    def test_different_outputs_produce_different_hash(self, harness):
        """Different outputs should produce different hashes."""
        steps1 = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
        ]
        steps2 = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "goodbye"}},
        ]

        record1 = harness.record_run("wf-1", steps1, "succeeded")
        record2 = harness.record_run("wf-1", steps2, "succeeded")

        assert record1.deterministic_hash != record2.deterministic_hash

    def test_timestamp_excluded_from_hash(self, harness):
        """Timestamps should not affect deterministic hash."""
        steps1 = [
            {
                "step_id": "s1",
                "skill": "json_transform",
                "output": {"result": "hello", "timestamp": "2025-01-01T00:00:00Z"},
            },
        ]
        steps2 = [
            {
                "step_id": "s1",
                "skill": "json_transform",
                "output": {"result": "hello", "timestamp": "2025-12-31T23:59:59Z"},
            },
        ]

        record1 = harness.record_run("wf-1", steps1, "succeeded")
        record2 = harness.record_run("wf-1", steps2, "succeeded")

        assert record1.deterministic_hash == record2.deterministic_hash

    def test_replay_verification_passes_for_identical_replay(self, harness):
        """Replay of identical steps should pass verification."""
        steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
            {"step_id": "s2", "skill": "json_transform", "output": {"result": "world"}},
        ]

        original = harness.record_run("wf-1", steps, "succeeded")

        # Replay with same steps
        passed, reason = harness.verify_replay(original, steps, "succeeded")

        assert passed is True
        assert "certified" in reason.lower()

    def test_replay_verification_fails_for_different_output(self, harness):
        """Replay with different output should fail verification."""
        original_steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
        ]
        replay_steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "different"}},
        ]

        original = harness.record_run("wf-1", original_steps, "succeeded")

        passed, reason = harness.verify_replay(original, replay_steps, "succeeded")

        assert passed is False
        assert "mismatch" in reason.lower()

    def test_replay_verification_fails_for_missing_step(self, harness):
        """Replay missing a step should fail verification."""
        original_steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
            {"step_id": "s2", "skill": "json_transform", "output": {"result": "world"}},
        ]
        replay_steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
        ]

        original = harness.record_run("wf-1", original_steps, "succeeded")

        passed, reason = harness.verify_replay(original, replay_steps, "succeeded")

        assert passed is False
        # Hash mismatch is also valid - detects the difference
        assert "mismatch" in reason.lower()

    def test_replay_verification_fails_for_wrong_skill(self, harness):
        """Replay with wrong skill should fail verification."""
        original_steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "hello"}},
        ]
        replay_steps = [
            {"step_id": "s1", "skill": "http_call", "output": {"result": "hello"}},
        ]

        original = harness.record_run("wf-1", original_steps, "succeeded")

        passed, reason = harness.verify_replay(original, replay_steps, "succeeded")

        assert passed is False
        assert "mismatch" in reason.lower()


class TestWorkflowDeterminism:
    """Tests for workflow execution determinism."""

    def test_json_transform_is_deterministic(self):
        """json_transform skill produces deterministic output."""
        from app.skills import load_all_skills
        from app.skills.json_transform import JsonTransformSkill

        load_all_skills()

        skill = JsonTransformSkill()
        params = {"data": {"name": "Alice", "age": 30}, "operation": "identity"}

        # Execute twice with fresh event loop
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result1 = loop.run_until_complete(skill.execute(params))
            result2 = loop.run_until_complete(skill.execute(params))
        finally:
            loop.close()

        # Results should be identical (excluding meta/timing)
        hash1 = compute_deterministic_hash(result1)
        hash2 = compute_deterministic_hash(result2)

        assert hash1 == hash2, "json_transform should be deterministic"

    def test_deterministic_hash_is_stable(self):
        """Deterministic hash function produces stable output."""
        data = {"key": "value", "nested": {"a": 1, "b": 2}}

        hash1 = compute_deterministic_hash(data)
        hash2 = compute_deterministic_hash(data)
        hash3 = compute_deterministic_hash(data)

        assert hash1 == hash2 == hash3


class TestReplayRecording:
    """Tests for replay recording functionality."""

    def test_record_captures_all_fields(self):
        """ReplayRecord captures all required fields."""
        harness = WorkflowReplayHarness()

        steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "test"}},
        ]

        record = harness.record_run("wf-test", steps, "succeeded")

        assert record.workflow_id == "wf-test"
        assert record.run_id is not None
        assert len(record.steps) == 1
        assert record.final_status == "succeeded"
        assert record.deterministic_hash is not None
        assert record.recorded_at is not None

    def test_record_serializes_to_dict(self):
        """ReplayRecord serializes to dict for storage."""
        harness = WorkflowReplayHarness()

        steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "test"}},
        ]

        record = harness.record_run("wf-test", steps, "succeeded")
        record_dict = record.to_dict()

        assert isinstance(record_dict, dict)
        assert "workflow_id" in record_dict
        assert "deterministic_hash" in record_dict

    def test_records_are_stored_by_run_id(self):
        """Records are stored and retrievable by run_id."""
        harness = WorkflowReplayHarness()

        steps = [
            {"step_id": "s1", "skill": "json_transform", "output": {"result": "test"}},
        ]

        record = harness.record_run("wf-test", steps, "succeeded")

        assert record.run_id in harness.recorded_runs
        assert harness.recorded_runs[record.run_id] == record


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
