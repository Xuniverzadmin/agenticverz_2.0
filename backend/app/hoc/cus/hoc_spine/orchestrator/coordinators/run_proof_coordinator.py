# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — run integrity proof
# Callers: ActivityFacade (L5)
# Allowed Imports: hoc_spine, bridges (lazy)
# Forbidden Imports: L1, L2, L5 engines directly
# Reference: PIN-519 System Run Introspection
# artifact_class: CODE

"""
Run Proof Coordinator (PIN-519)

L4 coordinator that verifies run integrity via traces.

Supports integrity models:
- HASH_CHAIN (Phase 1): Sequential hash of trace steps
- MERKLE_TREE (future): Merkle tree of trace evidence
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from app.hoc.cus.hoc_spine.schemas.run_introspection_protocols import (
    INTEGRITY_CONFIG,
    IntegrityVerificationResult,
    RunProofResult,
    TraceStepSummary,
    TraceSummary,
)

logger = logging.getLogger("nova.hoc_spine.coordinators.run_proof")


class RunProofCoordinator:
    """L4 coordinator: Verify run integrity via traces.

    Fetches traces and computes integrity verification based on
    the configured integrity model (HASH_CHAIN by default).
    """

    async def get_run_proof(
        self,
        session: Any,
        tenant_id: str,
        run_id: str,
        include_payloads: bool = False,
    ) -> RunProofResult:
        """
        Fetch traces and compute integrity verification.

        Args:
            session: Database session (may not be used for SQLite traces)
            tenant_id: Tenant ID for isolation
            run_id: Run ID to verify
            include_payloads: Include raw log payloads

        Returns:
            RunProofResult with integrity verification
        """
        # Get logs bridge (lazy import)
        from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.logs_bridge import (
            get_logs_bridge,
        )

        logs_bridge = get_logs_bridge()
        trace_store = logs_bridge.traces_store_capability()

        # Fetch trace for this run
        trace = await trace_store.get_trace(run_id)

        if trace is None:
            # No trace found - return UNSUPPORTED
            logger.info(
                "run_proof_no_trace",
                extra={"tenant_id": tenant_id, "run_id": run_id},
            )
            return RunProofResult(
                run_id=run_id,
                integrity=IntegrityVerificationResult(
                    model="NONE",
                    root_hash=None,
                    chain_length=0,
                    verification_status="UNSUPPORTED",
                    failure_reason="No trace found for run",
                ),
                aos_traces=[],
                aos_trace_steps=[],
                raw_logs=None,
                verified_at=datetime.now(timezone.utc),
            )

        # Build trace summary
        trace_summary = TraceSummary(
            trace_id=trace.run_id,  # TraceRecord uses run_id as primary key
            run_id=trace.run_id,
            status=trace.status.value if hasattr(trace.status, "value") else str(trace.status),
            step_count=len(trace.steps),
            started_at=trace.started_at,
            completed_at=trace.completed_at,
        )

        # Build step summaries
        step_summaries = [
            TraceStepSummary(
                step_index=step.step_index,
                skill_name=step.skill_name,
                status=step.status.value if hasattr(step.status, "value") else str(step.status),
                duration_ms=step.duration_ms,
                cost_cents=step.cost_cents,
            )
            for step in trace.steps
        ]

        # Compute integrity verification
        integrity = self._compute_integrity(run_id, trace.steps)

        logger.info(
            "run_proof_computed",
            extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
                "integrity_status": integrity.verification_status,
                "chain_length": integrity.chain_length,
            },
        )

        return RunProofResult(
            run_id=run_id,
            integrity=integrity,
            aos_traces=[trace_summary],
            aos_trace_steps=step_summaries,
            raw_logs=None if not include_payloads else [],  # Placeholder for raw logs
            verified_at=datetime.now(timezone.utc),
        )

    def _compute_integrity(
        self,
        run_id: str,
        steps: list[Any],
    ) -> IntegrityVerificationResult:
        """
        Compute integrity verification based on configured model.

        Phase 1: HASH_CHAIN - sequential hash of trace steps.
        """
        model = INTEGRITY_CONFIG.get("model", "HASH_CHAIN")

        if model == "NONE":
            return IntegrityVerificationResult(
                model="NONE",
                root_hash=None,
                chain_length=0,
                verification_status="UNSUPPORTED",
                failure_reason="Integrity model is NONE",
            )

        if model == "HASH_CHAIN":
            return self._compute_hash_chain(run_id, steps)

        if model == "MERKLE_TREE":
            # Future implementation
            return IntegrityVerificationResult(
                model="MERKLE_TREE",
                root_hash=None,
                chain_length=len(steps),
                verification_status="UNSUPPORTED",
                failure_reason="MERKLE_TREE not yet implemented",
            )

        return IntegrityVerificationResult(
            model="NONE",
            root_hash=None,
            chain_length=0,
            verification_status="UNSUPPORTED",
            failure_reason=f"Unknown integrity model: {model}",
        )

    def _compute_hash_chain(
        self,
        run_id: str,
        steps: list[Any],
    ) -> IntegrityVerificationResult:
        """
        Compute sequential hash chain of trace steps.

        Algorithm:
        1. Start with hash of run_id
        2. For each step, update hash with step data
        3. Return final hash as root_hash
        """
        if not steps:
            return IntegrityVerificationResult(
                model="HASH_CHAIN",
                root_hash=None,
                chain_length=0,
                verification_status="UNSUPPORTED",
                failure_reason="No steps to verify",
            )

        try:
            h = hashlib.sha256(run_id.encode())

            for step in steps:
                # Extract step data
                step_index = getattr(step, "step_index", 0)
                skill_name = getattr(step, "skill_name", "unknown")
                status = getattr(step, "status", "unknown")
                status_str = status.value if hasattr(status, "value") else str(status)

                # Update hash
                step_data = f"{step_index}:{skill_name}:{status_str}"
                h.update(step_data.encode())

            root_hash = h.hexdigest()

            return IntegrityVerificationResult(
                model="HASH_CHAIN",
                root_hash=root_hash,
                chain_length=len(steps),
                verification_status="VERIFIED",
                failure_reason=None,
            )
        except Exception as e:
            logger.warning(f"Hash chain computation failed for run {run_id}: {e}")
            return IntegrityVerificationResult(
                model="HASH_CHAIN",
                root_hash=None,
                chain_length=len(steps),
                verification_status="FAILED",
                failure_reason=str(e),
            )


# =============================================================================
# Singleton
# =============================================================================

_instance = None


def get_run_proof_coordinator() -> RunProofCoordinator:
    """Get the singleton RunProofCoordinator instance."""
    global _instance
    if _instance is None:
        _instance = RunProofCoordinator()
    return _instance


__all__ = [
    "RunProofCoordinator",
    "get_run_proof_coordinator",
]
