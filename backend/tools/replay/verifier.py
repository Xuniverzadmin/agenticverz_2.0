# M11 Replay Verifier
# Compare workflow executions for determinism

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .audit import AuditStore, OpRecord, compute_hash

logger = logging.getLogger("m11.verifier")


@dataclass
class DiffEntry:
    """Single difference between original and replay."""
    op_index: int
    op_type: str
    field: str
    original_value: Any
    replay_value: Any
    severity: str  # "critical", "warning", "info"


@dataclass
class VerificationResult:
    """Result of verification comparison."""
    verified: bool
    total_ops: int
    matched_ops: int
    mismatched_ops: int
    skipped_ops: int
    diffs: List[DiffEntry]
    summary: str


class ReplayVerifier:
    """
    Compare recorded and replayed workflow executions.

    Provides:
    - Structural comparison (status, error codes)
    - Hash comparison (exact result match)
    - Field-level diff generation
    """

    def __init__(self, audit_store: Optional[AuditStore] = None):
        self.audit_store = audit_store or AuditStore()

    def compare_ops(
        self,
        original: OpRecord,
        replay_result: Dict[str, Any],
        strict: bool = False,
    ) -> List[DiffEntry]:
        """
        Compare original operation with replay result.

        Args:
            original: Recorded operation
            replay_result: Result from replay execution
            strict: If True, require exact hash match

        Returns:
            List of differences found
        """
        diffs = []

        if original.result is None:
            return diffs  # Nothing to compare

        # Extract statuses
        original_status = original.result.get("status") or original.result.get("result", {}).get("status")
        replay_status = replay_result.get("status") or replay_result.get("result", {}).get("status")

        # Normalize stubbed/ok/completed as equivalent
        def normalize_status(s):
            if s in ("ok", "completed", "stubbed"):
                return "success"
            return s

        orig_norm = normalize_status(original_status)
        replay_norm = normalize_status(replay_status)

        if orig_norm != replay_norm:
            diffs.append(DiffEntry(
                op_index=original.op_index,
                op_type=original.op_type,
                field="status",
                original_value=original_status,
                replay_value=replay_status,
                severity="critical",
            ))

        # Check error codes if both failed
        if orig_norm != "success" and replay_norm != "success":
            orig_error = original.result.get("error") or original.result.get("result", {}).get("error")
            replay_error = replay_result.get("error") or replay_result.get("result", {}).get("error")

            if orig_error != replay_error:
                diffs.append(DiffEntry(
                    op_index=original.op_index,
                    op_type=original.op_type,
                    field="error_code",
                    original_value=orig_error,
                    replay_value=replay_error,
                    severity="warning",
                ))

        # Strict mode - compare full result hash
        if strict:
            original_hash = compute_hash(original.result)
            replay_hash = compute_hash(replay_result)

            if original_hash != replay_hash:
                diffs.append(DiffEntry(
                    op_index=original.op_index,
                    op_type=original.op_type,
                    field="result_hash",
                    original_value=original_hash,
                    replay_value=replay_hash,
                    severity="warning",
                ))

        # Check skill-specific fields
        if original.op_type == "voyage_embed":
            # For embeddings, check dimensions match
            orig_dims = original.result.get("result", {}).get("dimensions")
            replay_dims = replay_result.get("result", {}).get("dimensions")
            if orig_dims != replay_dims:
                diffs.append(DiffEntry(
                    op_index=original.op_index,
                    op_type=original.op_type,
                    field="dimensions",
                    original_value=orig_dims,
                    replay_value=replay_dims,
                    severity="critical",
                ))

        elif original.op_type == "kv_store":
            # For KV, check operation type matches
            orig_op = original.result.get("operation")
            replay_op = replay_result.get("operation")
            if orig_op != replay_op:
                diffs.append(DiffEntry(
                    op_index=original.op_index,
                    op_type=original.op_type,
                    field="operation",
                    original_value=orig_op,
                    replay_value=replay_op,
                    severity="critical",
                ))

        return diffs

    def verify_workflow(
        self,
        workflow_run_id: str,
        replay_results: List[Dict[str, Any]],
        strict: bool = False,
    ) -> VerificationResult:
        """
        Verify replayed workflow against recorded execution.

        Args:
            workflow_run_id: Original workflow run ID
            replay_results: List of replay results in op_index order
            strict: If True, require exact hash match

        Returns:
            VerificationResult with comparison details
        """
        # Get recorded operations
        recorded_ops = self.audit_store.get_ops(workflow_run_id)

        if len(recorded_ops) != len(replay_results):
            return VerificationResult(
                verified=False,
                total_ops=len(recorded_ops),
                matched_ops=0,
                mismatched_ops=0,
                skipped_ops=0,
                diffs=[DiffEntry(
                    op_index=0,
                    op_type="workflow",
                    field="op_count",
                    original_value=len(recorded_ops),
                    replay_value=len(replay_results),
                    severity="critical",
                )],
                summary=f"Operation count mismatch: {len(recorded_ops)} vs {len(replay_results)}",
            )

        all_diffs = []
        matched = 0
        mismatched = 0
        skipped = 0

        for op, replay_result in zip(recorded_ops, replay_results):
            if op.transient:
                skipped += 1
                continue

            diffs = self.compare_ops(op, replay_result, strict)

            if not diffs:
                matched += 1
            else:
                mismatched += 1
                all_diffs.extend(diffs)

        verified = mismatched == 0
        summary = f"{matched} matched, {mismatched} mismatched, {skipped} skipped"

        if not verified:
            critical_count = sum(1 for d in all_diffs if d.severity == "critical")
            summary += f" ({critical_count} critical differences)"

        return VerificationResult(
            verified=verified,
            total_ops=len(recorded_ops),
            matched_ops=matched,
            mismatched_ops=mismatched,
            skipped_ops=skipped,
            diffs=all_diffs,
            summary=summary,
        )

    def generate_diff_report(self, result: VerificationResult) -> str:
        """Generate human-readable diff report."""
        lines = [
            "=" * 60,
            "REPLAY VERIFICATION REPORT",
            "=" * 60,
            f"Status: {'PASSED' if result.verified else 'FAILED'}",
            f"Total Operations: {result.total_ops}",
            f"Matched: {result.matched_ops}",
            f"Mismatched: {result.mismatched_ops}",
            f"Skipped: {result.skipped_ops}",
            "",
        ]

        if result.diffs:
            lines.append("DIFFERENCES:")
            lines.append("-" * 40)

            for diff in result.diffs:
                lines.append(f"  [{diff.severity.upper()}] op_index={diff.op_index} {diff.op_type}")
                lines.append(f"    Field: {diff.field}")
                lines.append(f"    Original: {diff.original_value}")
                lines.append(f"    Replay:   {diff.replay_value}")
                lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)


# Convenience function
def verify_replay(
    workflow_run_id: str,
    replay_results: List[Dict[str, Any]],
    strict: bool = False,
) -> VerificationResult:
    """Verify replayed workflow against recorded execution."""
    verifier = ReplayVerifier()
    return verifier.verify_workflow(workflow_run_id, replay_results, strict)
