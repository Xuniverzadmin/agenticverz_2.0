# M11 Replay End-to-End Tests
# Verify deterministic replay of workflows

import os
from datetime import datetime

import pytest

# Skip all tests if DATABASE_URL not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set - requires database for replay tests"
)

# Test fixtures
SAMPLE_WORKFLOW = {
    "steps": [
        {
            "id": "s1",
            "skill": "kv_store",
            "params": {"operation": "set", "namespace": "test_replay", "key": "status", "value": {"state": "started"}},
        },
        {
            "id": "s2",
            "skill": "voyage_embed",
            "params": {"input": "Test embedding for replay", "model": "voyage-3-lite"},
        },
        {
            "id": "s3",
            "skill": "slack_send",
            "params": {"text": "Workflow replay test", "idempotency_key": "replay_test_s3"},
        },
        {"id": "s4", "skill": "kv_store", "params": {"operation": "get", "namespace": "test_replay", "key": "status"}},
        {
            "id": "s5",
            "skill": "email_send",
            "params": {
                "to": "test@example.com",
                "subject": "Replay Test Complete",
                "body": "Done",
                "idempotency_key": "replay_test_s5",
            },
        },
    ]
}


class TestReplayEndToEnd:
    """End-to-end replay verification tests."""

    @pytest.fixture
    def workflow_run_id(self):
        """Generate unique workflow run ID."""
        return f"wf_replay_test_{int(datetime.now().timestamp())}"

    @pytest.mark.asyncio
    async def test_run_and_replay_verify(self, workflow_run_id):
        """
        Test full run → replay → verify cycle.

        This is the core determinism test:
        1. Run workflow with stubbed skills (recording ops)
        2. Replay workflow in verify mode
        3. Assert all operations match
        """
        from tools.replay.runner import WorkflowRunner

        # Configure all skills as stubbed for testing
        skill_config = {
            "kv_store": {"allow_external": False},
            "voyage_embed": {"allow_external": False},
            "slack_send": {"allow_external": False},
            "email_send": {"allow_external": False},
        }

        runner = WorkflowRunner()

        # Step 1: Run workflow (records to audit log)
        run_result = await runner.run(
            workflow_spec=SAMPLE_WORKFLOW,
            workflow_run_id=workflow_run_id,
            skill_config=skill_config,
        )

        print(f"\n=== RUN RESULT ===\n{run_result.output}")

        assert run_result.exit_code == 0, f"Run failed: {run_result.errors}"
        assert run_result.total_ops == 5
        assert run_result.completed_ops == 5

        # Step 2: Replay in verify mode
        replay_result = await runner.replay(
            workflow_run_id=workflow_run_id,
            mode="verify",
            skill_config=skill_config,
        )

        print(f"\n=== REPLAY RESULT ===\n{replay_result.output}")

        assert replay_result.exit_code == 0, f"Replay failed: {replay_result.mismatch_diff}"
        assert replay_result.ops_verified == 5
        assert replay_result.ops_failed == 0
        assert replay_result.first_mismatch_op_index is None

    @pytest.mark.asyncio
    async def test_replay_dry_run(self, workflow_run_id):
        """Test dry run mode shows what would happen."""
        from tools.replay.runner import WorkflowRunner

        skill_config = {
            "kv_store": {"allow_external": False},
            "voyage_embed": {"allow_external": False},
            "slack_send": {"allow_external": False},
            "email_send": {"allow_external": False},
        }

        runner = WorkflowRunner()

        # First run the workflow
        run_result = await runner.run(
            workflow_spec=SAMPLE_WORKFLOW,
            workflow_run_id=workflow_run_id,
            skill_config=skill_config,
        )
        assert run_result.exit_code == 0

        # Replay in dry run mode
        replay_result = await runner.replay(
            workflow_run_id=workflow_run_id,
            mode="dry_run",
            skill_config=skill_config,
        )

        print(f"\n=== DRY RUN RESULT ===\n{replay_result.output}")

        # Dry run should succeed without actual execution
        assert replay_result.exit_code == 0
        assert "[DRY]" in replay_result.output

    @pytest.mark.asyncio
    async def test_replay_detects_nonexistent_workflow(self):
        """Test replay fails for non-existent workflow."""
        from tools.replay.runner import WorkflowRunner

        runner = WorkflowRunner()

        replay_result = await runner.replay(
            workflow_run_id="nonexistent_workflow_123",
            mode="verify",
        )

        assert replay_result.exit_code == 1
        assert replay_result.ops_total == 0
        assert "No operations found" in replay_result.output

    @pytest.mark.asyncio
    async def test_audit_ops_recorded(self, workflow_run_id):
        """Test that ops are properly recorded in audit log."""
        from tools.replay.audit import AuditStore
        from tools.replay.runner import WorkflowRunner

        skill_config = {
            "kv_store": {"allow_external": False},
            "voyage_embed": {"allow_external": False},
            "slack_send": {"allow_external": False},
            "email_send": {"allow_external": False},
        }

        runner = WorkflowRunner()
        audit = AuditStore()

        # Run workflow
        run_result = await runner.run(
            workflow_spec=SAMPLE_WORKFLOW,
            workflow_run_id=workflow_run_id,
            skill_config=skill_config,
        )
        assert run_result.exit_code == 0

        # Verify ops in audit log
        ops = audit.get_ops(workflow_run_id)

        assert len(ops) == 5
        assert ops[0].op_index == 1
        assert ops[0].op_type == "kv_store"
        assert ops[0].status == "completed"

        assert ops[1].op_index == 2
        assert ops[1].op_type == "voyage_embed"

        assert ops[2].op_index == 3
        assert ops[2].op_type == "slack_send"

        # Verify op_index is monotonically increasing
        for i, op in enumerate(ops):
            assert op.op_index == i + 1

    @pytest.mark.asyncio
    async def test_transient_ops_skipped(self, workflow_run_id):
        """Test that transient operations are skipped during replay."""
        from tools.replay.runner import WorkflowRunner

        # Workflow with transient step
        workflow = {
            "steps": [
                {
                    "id": "s1",
                    "skill": "kv_store",
                    "params": {"operation": "set", "namespace": "test", "key": "k1", "value": "v1"},
                },
                {
                    "id": "s2_transient",
                    "skill": "kv_store",
                    "transient": True,  # This op should be skipped in replay
                    "params": {"operation": "set", "namespace": "test", "key": "temp", "value": "temp"},
                },
                {"id": "s3", "skill": "kv_store", "params": {"operation": "get", "namespace": "test", "key": "k1"}},
            ]
        }

        skill_config = {"kv_store": {"allow_external": False}}

        runner = WorkflowRunner()

        # Run
        run_result = await runner.run(
            workflow_spec=workflow,
            workflow_run_id=workflow_run_id,
            skill_config=skill_config,
        )
        assert run_result.exit_code == 0

        # Replay
        replay_result = await runner.replay(
            workflow_run_id=workflow_run_id,
            mode="verify",
            skill_config=skill_config,
        )

        print(f"\n=== TRANSIENT TEST ===\n{replay_result.output}")

        assert replay_result.exit_code == 0
        assert replay_result.ops_skipped == 1  # s2_transient skipped
        assert replay_result.ops_verified == 2


class TestVerifier:
    """Test the verifier directly."""

    def test_compare_matching_ops(self):
        """Test verifier identifies matching operations."""
        from tools.replay.audit import OpRecord
        from tools.replay.verifier import ReplayVerifier

        verifier = ReplayVerifier()

        original = OpRecord(
            op_id="op_1",
            workflow_run_id="wf_1",
            op_index=1,
            op_type="kv_store",
            args={"operation": "set", "key": "test"},
            args_hash="abc123",
            result={"status": "ok", "operation": "set"},
        )

        replay_result = {"status": "ok", "operation": "set"}

        diffs = verifier.compare_ops(original, replay_result)
        assert len(diffs) == 0

    def test_compare_status_mismatch(self):
        """Test verifier detects status mismatch."""
        from tools.replay.audit import OpRecord
        from tools.replay.verifier import ReplayVerifier

        verifier = ReplayVerifier()

        original = OpRecord(
            op_id="op_1",
            workflow_run_id="wf_1",
            op_index=1,
            op_type="kv_store",
            args={"operation": "set", "key": "test"},
            args_hash="abc123",
            result={"status": "ok"},
        )

        replay_result = {"status": "error", "error": "timeout"}

        diffs = verifier.compare_ops(original, replay_result)
        assert len(diffs) >= 1
        assert any(d.field == "status" and d.severity == "critical" for d in diffs)

    def test_generate_diff_report(self):
        """Test diff report generation."""
        from tools.replay.verifier import DiffEntry, ReplayVerifier, VerificationResult

        verifier = ReplayVerifier()

        result = VerificationResult(
            verified=False,
            total_ops=5,
            matched_ops=3,
            mismatched_ops=2,
            skipped_ops=0,
            diffs=[
                DiffEntry(
                    op_index=2,
                    op_type="slack_send",
                    field="status",
                    original_value="ok",
                    replay_value="error",
                    severity="critical",
                ),
            ],
            summary="3 matched, 2 mismatched",
        )

        report = verifier.generate_diff_report(result)

        assert "FAILED" in report
        assert "op_index=2" in report
        assert "slack_send" in report
        assert "CRITICAL" in report.upper()


class TestAuditStore:
    """Test audit store operations."""

    @pytest.fixture
    def workflow_run_id(self):
        return f"wf_audit_test_{int(datetime.now().timestamp())}"

    def test_append_and_get_ops(self, workflow_run_id):
        """Test appending and retrieving operations."""
        from tools.replay.audit import AuditStore

        audit = AuditStore()

        # Append operations
        op1 = audit.append_op(
            workflow_run_id=workflow_run_id,
            op_type="kv_store",
            args={"operation": "set", "key": "test"},
        )
        assert op1.op_index == 1

        op2 = audit.append_op(
            workflow_run_id=workflow_run_id,
            op_type="slack_send",
            args={"text": "Hello"},
        )
        assert op2.op_index == 2

        # Retrieve operations
        ops = audit.get_ops(workflow_run_id)
        assert len(ops) == 2
        assert ops[0].op_index == 1
        assert ops[1].op_index == 2

    def test_update_result(self, workflow_run_id):
        """Test updating operation result."""
        from tools.replay.audit import AuditStore

        audit = AuditStore()

        # Append operation
        op = audit.append_op(
            workflow_run_id=workflow_run_id,
            op_type="kv_store",
            args={"operation": "get", "key": "test"},
        )

        # Update result
        audit.update_result(
            op_id=op.op_id,
            result={"status": "ok", "value": "test_value"},
            status="completed",
            duration_ms=50,
        )

        # Verify update
        updated_op = audit.get_op(op.op_id)
        assert updated_op.status == "completed"
        assert updated_op.result["status"] == "ok"
        assert updated_op.duration_ms == 50
