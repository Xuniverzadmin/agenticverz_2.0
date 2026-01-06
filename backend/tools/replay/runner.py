# M11 Workflow Runner
# Execute workflows with audit logging for deterministic replay

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .audit import AuditStore, compute_hash

logger = logging.getLogger("m11.runner")


@dataclass
class RunResult:
    """Result of workflow run."""

    workflow_run_id: str
    exit_code: int
    total_ops: int
    completed_ops: int
    failed_ops: int
    duration_ms: int
    output: str
    errors: List[str]


@dataclass
class ReplayResult:
    """Result of workflow replay verification."""

    replay_id: str
    workflow_run_id: str
    exit_code: int
    mode: str
    ops_total: int
    ops_verified: int
    ops_failed: int
    ops_skipped: int
    first_mismatch_op_index: Optional[int]
    mismatch_diff: Optional[Dict]
    output: str


class WorkflowRunner:
    """
    Execute workflows with audit logging.

    Provides:
    - run(): Execute workflow and record all operations to audit log
    - replay(): Re-execute workflow and verify against recorded operations
    """

    def __init__(self, audit_store: Optional[AuditStore] = None):
        self.audit_store = audit_store or AuditStore()
        self._skill_registry = {}

    def _load_skills(self):
        """Load skill registry."""
        if not self._skill_registry:
            from app.skills import load_all_skills

            load_all_skills()
            self._skill_registry = {
                "kv_store": "KVStoreSkill",
                "slack_send": "SlackSendSkill",
                "webhook_send": "WebhookSendSkill",
                "voyage_embed": "VoyageEmbedSkill",
                "email_send": "EmailSendSkill",
                "http_call": "HttpCallSkill",
                "llm_invoke": "LLMInvokeSkill",
                "json_transform": "JsonTransformSkill",
                "postgres_query": "PostgresQuerySkill",
            }

    def _get_skill_instance(self, skill_name: str, config: Optional[Dict] = None):
        """Get skill instance by name."""
        self._load_skills()
        from app.skills import load_skill

        skill_class_name = self._skill_registry.get(skill_name)
        if not skill_class_name:
            raise ValueError(f"Unknown skill: {skill_name}")

        skill_class = load_skill(skill_class_name)
        config = config or {}
        return skill_class(**config)

    async def run(
        self,
        workflow_spec: Dict[str, Any],
        workflow_run_id: Optional[str] = None,
        tenant_id: str = "default",
        skill_config: Optional[Dict[str, Dict]] = None,
    ) -> RunResult:
        """
        Execute workflow and record operations to audit log.

        Args:
            workflow_spec: Workflow specification with 'steps' list
            workflow_run_id: Optional run ID (generated if not provided)
            tenant_id: Tenant identifier
            skill_config: Per-skill configuration overrides

        Returns:
            RunResult with execution summary
        """
        workflow_run_id = workflow_run_id or f"wf_{uuid.uuid4().hex[:16]}"
        skill_config = skill_config or {}
        start_time = time.time()
        errors = []
        completed_ops = 0
        failed_ops = 0

        steps = workflow_spec.get("steps", [])

        logger.info(f"Starting workflow {workflow_run_id} with {len(steps)} steps")

        for step in steps:
            step_id = step.get("id", f"step_{completed_ops + failed_ops + 1}")
            skill_name = step.get("skill")
            params = step.get("params", {})
            transient = step.get("transient", False)
            idempotency_key = params.get("idempotency_key")

            if not skill_name:
                errors.append(f"Step {step_id}: missing 'skill' field")
                failed_ops += 1
                continue

            # Record operation start
            op_record = self.audit_store.append_op(
                workflow_run_id=workflow_run_id,
                op_type=skill_name,
                args=params,
                idempotency_key=idempotency_key,
                tenant_id=tenant_id,
                transient=transient,
            )

            logger.info(f"Executing step {step_id} ({skill_name}) op_index={op_record.op_index}")

            # Execute skill
            try:
                config = skill_config.get(skill_name, {})
                skill = self._get_skill_instance(skill_name, config)

                op_start = time.time()
                result = await skill.execute(params)
                duration_ms = int((time.time() - op_start) * 1000)

                # Determine status from result
                result_status = result.get("status") or result.get("result", {}).get("status", "unknown")
                if result_status in ("ok", "stubbed", "completed"):
                    status = "completed"
                    completed_ops += 1
                else:
                    status = "failed"
                    failed_ops += 1
                    error_code = result.get("error") or result.get("result", {}).get("error")
                    error_msg = result.get("message") or result.get("result", {}).get("message")
                    errors.append(f"Step {step_id}: {error_code} - {error_msg}")

                # Update audit record
                self.audit_store.update_result(
                    op_id=op_record.op_id,
                    result=result,
                    status=status,
                    error_code=result.get("error") or result.get("result", {}).get("error"),
                    error_message=result.get("message") or result.get("result", {}).get("message"),
                    duration_ms=duration_ms,
                )

            except Exception as e:
                failed_ops += 1
                error_msg = str(e)[:500]
                errors.append(f"Step {step_id}: Exception - {error_msg}")

                self.audit_store.update_result(
                    op_id=op_record.op_id,
                    result={"error": "exception", "message": error_msg},
                    status="failed",
                    error_code="exception",
                    error_message=error_msg,
                    duration_ms=0,
                )

        total_duration = int((time.time() - start_time) * 1000)
        exit_code = 0 if failed_ops == 0 else 1

        output = f"Workflow {workflow_run_id}: {completed_ops}/{len(steps)} completed"
        if errors:
            output += "\nErrors:\n" + "\n".join(f"  - {e}" for e in errors)

        logger.info(f"Workflow {workflow_run_id} completed: exit_code={exit_code}")

        return RunResult(
            workflow_run_id=workflow_run_id,
            exit_code=exit_code,
            total_ops=len(steps),
            completed_ops=completed_ops,
            failed_ops=failed_ops,
            duration_ms=total_duration,
            output=output,
            errors=errors,
        )

    async def replay(
        self,
        workflow_run_id: str,
        mode: str = "verify",
        skill_config: Optional[Dict[str, Dict]] = None,
    ) -> ReplayResult:
        """
        Replay workflow and verify against recorded operations.

        Modes:
        - 'verify': Compare results without side effects (stubbed execution)
        - 'rehydrate': Re-execute and compare (with side effects)
        - 'dry_run': Show what would happen without execution

        Args:
            workflow_run_id: ID of workflow to replay
            mode: Replay mode
            skill_config: Per-skill configuration overrides

        Returns:
            ReplayResult with verification summary
        """
        replay_id = f"replay_{uuid.uuid4().hex[:16]}"
        skill_config = skill_config or {}

        # Get recorded operations
        recorded_ops = self.audit_store.get_ops(workflow_run_id)

        if not recorded_ops:
            return ReplayResult(
                replay_id=replay_id,
                workflow_run_id=workflow_run_id,
                exit_code=1,
                mode=mode,
                ops_total=0,
                ops_verified=0,
                ops_failed=0,
                ops_skipped=0,
                first_mismatch_op_index=None,
                mismatch_diff=None,
                output=f"No operations found for workflow {workflow_run_id}",
            )

        # Record replay start
        self.audit_store.record_replay_run(
            replay_id=replay_id,
            workflow_run_id=workflow_run_id,
            mode=mode,
            ops_total=len(recorded_ops),
        )

        logger.info(f"Starting replay {replay_id} for {workflow_run_id} with {len(recorded_ops)} ops (mode={mode})")

        ops_verified = 0
        ops_failed = 0
        ops_skipped = 0
        first_mismatch_op_index = None
        mismatch_diff = None
        output_lines = []

        for op in recorded_ops:
            # Skip transient operations
            if op.transient:
                ops_skipped += 1
                output_lines.append(f"[SKIP] op_index={op.op_index} {op.op_type} (transient)")
                continue

            # Dry run mode - just show what would happen
            if mode == "dry_run":
                output_lines.append(f"[DRY] op_index={op.op_index} {op.op_type}")
                ops_verified += 1
                continue

            # Verify mode - use stubbed execution
            if mode == "verify":
                config = skill_config.get(op.op_type, {})
                config["allow_external"] = False  # Force stubbed mode
            else:
                config = skill_config.get(op.op_type, {})

            try:
                skill = self._get_skill_instance(op.op_type, config)
                replay_result = await skill.execute(op.args)

                # Compare results
                if op.result is None:
                    # Original had no result recorded - treat as skip
                    ops_skipped += 1
                    output_lines.append(f"[SKIP] op_index={op.op_index} {op.op_type} (no recorded result)")
                    continue

                # For stubbed mode, compare structure rather than exact values
                if mode == "verify":
                    # Check status matches
                    original_status = op.result.get("status") or op.result.get("result", {}).get("status")
                    replay_status = replay_result.get("status") or replay_result.get("result", {}).get("status")

                    if original_status in ("ok", "completed", "stubbed") and replay_status in (
                        "ok",
                        "completed",
                        "stubbed",
                    ):
                        # Both succeeded - consider verified
                        ops_verified += 1
                        output_lines.append(f"[OK] op_index={op.op_index} {op.op_type}")
                    elif original_status == replay_status:
                        # Same status
                        ops_verified += 1
                        output_lines.append(f"[OK] op_index={op.op_index} {op.op_type} (status={original_status})")
                    else:
                        # Status mismatch
                        ops_failed += 1
                        if first_mismatch_op_index is None:
                            first_mismatch_op_index = op.op_index
                            mismatch_diff = {
                                "op_index": op.op_index,
                                "op_type": op.op_type,
                                "original_status": original_status,
                                "replay_status": replay_status,
                                "original_result": op.result,
                                "replay_result": replay_result,
                            }
                        output_lines.append(
                            f"[FAIL] op_index={op.op_index} {op.op_type} "
                            f"(expected={original_status}, got={replay_status})"
                        )
                else:
                    # Rehydrate mode - compare full results
                    original_hash = compute_hash(op.result)
                    replay_hash = compute_hash(replay_result)

                    if original_hash == replay_hash:
                        ops_verified += 1
                        output_lines.append(f"[OK] op_index={op.op_index} {op.op_type}")
                    else:
                        ops_failed += 1
                        if first_mismatch_op_index is None:
                            first_mismatch_op_index = op.op_index
                            mismatch_diff = {
                                "op_index": op.op_index,
                                "op_type": op.op_type,
                                "original_hash": original_hash,
                                "replay_hash": replay_hash,
                                "original_result": op.result,
                                "replay_result": replay_result,
                            }
                        output_lines.append(f"[FAIL] op_index={op.op_index} {op.op_type} (hash mismatch)")

            except Exception as e:
                ops_failed += 1
                error_msg = str(e)[:200]
                output_lines.append(f"[ERROR] op_index={op.op_index} {op.op_type}: {error_msg}")
                if first_mismatch_op_index is None:
                    first_mismatch_op_index = op.op_index
                    mismatch_diff = {
                        "op_index": op.op_index,
                        "op_type": op.op_type,
                        "error": error_msg,
                    }

        # Determine overall status
        if ops_failed > 0:
            status = "failed"
            exit_code = 1
        else:
            status = "verified"
            exit_code = 0

        # Record replay completion
        self.audit_store.complete_replay_run(
            replay_id=replay_id,
            status=status,
            ops_verified=ops_verified,
            ops_failed=ops_failed,
            ops_skipped=ops_skipped,
            first_mismatch_op_index=first_mismatch_op_index,
            mismatch_diff=mismatch_diff,
        )

        output = f"Replay {replay_id} ({mode}): {ops_verified} verified, {ops_failed} failed, {ops_skipped} skipped\n"
        output += "\n".join(output_lines)

        logger.info(f"Replay {replay_id} completed: exit_code={exit_code}")

        return ReplayResult(
            replay_id=replay_id,
            workflow_run_id=workflow_run_id,
            exit_code=exit_code,
            mode=mode,
            ops_total=len(recorded_ops),
            ops_verified=ops_verified,
            ops_failed=ops_failed,
            ops_skipped=ops_skipped,
            first_mismatch_op_index=first_mismatch_op_index,
            mismatch_diff=mismatch_diff,
            output=output,
        )


# Convenience functions
async def run_workflow(
    workflow_spec: Dict[str, Any],
    workflow_run_id: Optional[str] = None,
    tenant_id: str = "default",
    skill_config: Optional[Dict[str, Dict]] = None,
) -> RunResult:
    """Run a workflow and record to audit log."""
    runner = WorkflowRunner()
    return await runner.run(workflow_spec, workflow_run_id, tenant_id, skill_config)


async def replay_workflow(
    workflow_run_id: str,
    mode: str = "verify",
    skill_config: Optional[Dict[str, Dict]] = None,
) -> ReplayResult:
    """Replay a workflow and verify determinism."""
    runner = WorkflowRunner()
    return await runner.replay(workflow_run_id, mode, skill_config)
