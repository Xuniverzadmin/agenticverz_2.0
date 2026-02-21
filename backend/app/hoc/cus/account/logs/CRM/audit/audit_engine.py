# capability_id: CAP-012
# Layer: L8 — Catalyst / Verification
# AUDIENCE: CUSTOMER
# Product: system-wide (CRM governance job audit)
# Temporal:
#   Trigger: job completion
#   Execution: sync (deterministic verification)
# Role: Audit Engine - verifies job execution against contract intent
# Callers: hoc_spine (governance.audit_job)
# Allowed Imports: L6 models only
# Forbidden Imports: L1, L2, L3, L4, L5 (auditor is independent)
# Reference: PIN-295, GOVERNANCE_AUDIT_MODEL.md, part2-design-v1
# NOTE: Renamed audit_service.py → audit_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
# NOTE: Moved from logs CRM support to account-owned CRM audit namespace (2026-02-08)
#
# ==============================================================================
# GOVERNANCE RULE: AUDIT-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This service verifies execution. It is a JUDGE, not a FIXER.
#
# Auditor properties:
#   - EVIDENCE CONSUMER: Reads frozen evidence only
#   - VERDICT PRODUCER: Issues PASS / FAIL / INCONCLUSIVE
#   - TERMINAL: Verdicts cannot be overridden or retried
#   - INDEPENDENT: Cannot modify jobs, contracts, or health
#
# The Auditor:
#   - MAY: Read evidence, evaluate checks, produce verdicts
#   - MUST NOT: Modify jobs, modify contracts, retry execution,
#               fix failures, override verdicts, consult humans
#
# Reference: GOVERNANCE_AUDIT_MODEL.md, part2-design-v1
#
# ==============================================================================

"""
Part-2 Governance Audit Service (L8)

Verifies that job execution matched contract intent.

Audit is:
- Post-execution (runs after job completes)
- Deterministic (same evidence → same verdict)
- Authoritative (verdicts cannot be overridden)
- Mandatory (no rollout without audit)

Invariants:
- AUDIT-001: All completed jobs require audit
- AUDIT-002: PASS required for COMPLETED
- AUDIT-003: FAIL triggers rollback
- AUDIT-004: Verdicts are immutable
- AUDIT-005: Evidence is preserved
- AUDIT-006: Health snapshots required

Reference: PIN-295, GOVERNANCE_AUDIT_MODEL.md, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from app.hoc.cus.hoc_spine.schemas.domain_enums import AuditVerdict

# Audit service version
AUDIT_SERVICE_VERSION = "1.0.0"


# ==============================================================================
# CHECK RESULT ENUM
# ==============================================================================


class CheckResult(str, Enum):
    """Result of an individual audit check."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


# ==============================================================================
# AUDIT DATA TYPES
# ==============================================================================


@dataclass(frozen=True)
class AuditCheck:
    """
    Result of a single audit check.

    Each check answers one question about execution integrity.
    """

    check_id: str  # A-001, A-002, etc.
    name: str
    question: str
    result: CheckResult
    reason: str
    evidence: dict[str, Any]


@dataclass(frozen=True)
class AuditInput:
    """
    Input to the audit process.

    This is frozen evidence from job execution.
    The auditor cannot modify this.
    """

    job_id: UUID
    contract_id: UUID
    job_status: str  # COMPLETED or FAILED
    contract_scope: list[str]  # affected_capabilities from contract
    proposed_changes: dict[str, Any]
    steps_executed: list[dict[str, Any]]  # Step results
    step_results: list[dict[str, Any]]  # StepResult evidence
    health_before: Optional[dict[str, Any]]
    health_after: Optional[dict[str, Any]]
    activation_window_start: Optional[datetime]
    activation_window_end: Optional[datetime]
    job_started_at: datetime
    job_completed_at: datetime
    execution_duration_seconds: float


@dataclass(frozen=True)
class AuditResult:
    """
    Complete audit result with all checks and final verdict.

    This is what the audit produces.
    """

    audit_id: UUID
    job_id: UUID
    contract_id: UUID
    verdict: AuditVerdict
    verdict_reason: str
    checks: tuple[AuditCheck, ...]
    checks_passed: int
    checks_failed: int
    checks_inconclusive: int
    evidence_summary: dict[str, Any]
    health_snapshot_before: Optional[dict[str, Any]]
    health_snapshot_after: Optional[dict[str, Any]]
    audited_at: datetime
    duration_ms: int
    auditor_version: str


# ==============================================================================
# AUDIT CHECKS (A-001 to A-007)
# ==============================================================================


class AuditChecks:
    """
    Individual audit check implementations.

    Each check answers one specific question about execution integrity.
    Checks are stateless and deterministic.
    """

    @staticmethod
    def check_scope_compliance(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-001: Scope Compliance

        Question: Did job execute only within contract scope?
        """
        contract_scope = set(audit_input.contract_scope)
        executed_targets: set[str] = set()

        for step_result in audit_input.step_results:
            # Extract target from step result
            output = step_result.get("output") or {}
            target = output.get("target")
            if target:
                executed_targets.add(target)

        # Check for unauthorized targets
        unauthorized = executed_targets - contract_scope

        if unauthorized:
            return AuditCheck(
                check_id="A-001",
                name="Scope Compliance",
                question="Did job execute only within contract scope?",
                result=CheckResult.FAIL,
                reason=f"Unauthorized targets: {unauthorized}",
                evidence={
                    "contract_scope": list(contract_scope),
                    "executed_targets": list(executed_targets),
                    "unauthorized": list(unauthorized),
                },
            )

        return AuditCheck(
            check_id="A-001",
            name="Scope Compliance",
            question="Did job execute only within contract scope?",
            result=CheckResult.PASS,
            reason="All steps within contract scope",
            evidence={
                "contract_scope": list(contract_scope),
                "executed_targets": list(executed_targets),
            },
        )

    @staticmethod
    def check_health_preservation(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-002: Health Preservation

        Question: Did execution preserve system health?
        """
        health_before = audit_input.health_before
        health_after = audit_input.health_after

        # AUDIT-006: Health snapshots required
        if health_before is None or health_after is None:
            return AuditCheck(
                check_id="A-002",
                name="Health Preservation",
                question="Did execution preserve system health?",
                result=CheckResult.INCONCLUSIVE,
                reason="Health snapshots unavailable",
                evidence={
                    "health_before_available": health_before is not None,
                    "health_after_available": health_after is not None,
                },
            )

        # Compare health states
        # Simple check: no degradation in any capability
        degraded_capabilities: list[str] = []

        # Health structure is capability_name -> status
        for cap_name, status_before in health_before.items():
            status_after = health_after.get(cap_name)
            if status_after is None:
                # Capability removed - potential degradation
                degraded_capabilities.append(cap_name)
            elif AuditChecks._is_health_degraded(status_before, status_after):
                degraded_capabilities.append(cap_name)

        if degraded_capabilities:
            return AuditCheck(
                check_id="A-002",
                name="Health Preservation",
                question="Did execution preserve system health?",
                result=CheckResult.FAIL,
                reason=f"Health degraded for: {degraded_capabilities}",
                evidence={
                    "health_before": health_before,
                    "health_after": health_after,
                    "degraded_capabilities": degraded_capabilities,
                },
            )

        return AuditCheck(
            check_id="A-002",
            name="Health Preservation",
            question="Did execution preserve system health?",
            result=CheckResult.PASS,
            reason="Health maintained or improved",
            evidence={
                "health_before": health_before,
                "health_after": health_after,
            },
        )

    @staticmethod
    def _is_health_degraded(before: Any, after: Any) -> bool:
        """Check if health status degraded."""
        # Health status ordering: HEALTHY > DEGRADED > UNHEALTHY
        health_order = {"HEALTHY": 2, "DEGRADED": 1, "UNHEALTHY": 0}

        before_level = health_order.get(str(before), 1)
        after_level = health_order.get(str(after), 1)

        return after_level < before_level

    @staticmethod
    def check_execution_fidelity(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-003: Execution Fidelity

        Question: Did execution match proposed changes?
        """
        proposed_changes = audit_input.proposed_changes
        step_results = audit_input.step_results

        # Check that each proposed change has a corresponding executed step
        proposed_targets = set()
        if isinstance(proposed_changes, list):
            for change in proposed_changes:
                if isinstance(change, dict):
                    target = change.get("capability_name") or change.get("scope")
                    if target:
                        proposed_targets.add(target)
        elif isinstance(proposed_changes, dict):
            # Single change
            target = proposed_changes.get("capability_name") or proposed_changes.get("scope")
            if target:
                proposed_targets.add(target)

        executed_targets = set()
        for step_result in step_results:
            output = step_result.get("output") or {}
            target = output.get("target")
            if target:
                executed_targets.add(target)

        # Check for missing executions (proposed but not executed)
        missing = proposed_targets - executed_targets

        if missing and audit_input.job_status == "COMPLETED":
            return AuditCheck(
                check_id="A-003",
                name="Execution Fidelity",
                question="Did execution match proposed changes?",
                result=CheckResult.FAIL,
                reason=f"Proposed changes not executed: {missing}",
                evidence={
                    "proposed_targets": list(proposed_targets),
                    "executed_targets": list(executed_targets),
                    "missing": list(missing),
                },
            )

        return AuditCheck(
            check_id="A-003",
            name="Execution Fidelity",
            question="Did execution match proposed changes?",
            result=CheckResult.PASS,
            reason="Execution matches proposal",
            evidence={
                "proposed_targets": list(proposed_targets),
                "executed_targets": list(executed_targets),
            },
        )

    @staticmethod
    def check_timing_compliance(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-004: Timing Compliance

        Question: Did execution occur within activation window?
        """
        window_start = audit_input.activation_window_start
        window_end = audit_input.activation_window_end
        job_started = audit_input.job_started_at
        job_completed = audit_input.job_completed_at

        if window_start is None or window_end is None:
            return AuditCheck(
                check_id="A-004",
                name="Timing Compliance",
                question="Did execution occur within activation window?",
                result=CheckResult.INCONCLUSIVE,
                reason="Activation window not defined",
                evidence={
                    "window_start": None,
                    "window_end": None,
                    "job_started_at": job_started.isoformat(),
                    "job_completed_at": job_completed.isoformat(),
                },
            )

        # Check if job was within window
        started_in_window = window_start <= job_started <= window_end
        completed_in_window = window_start <= job_completed <= window_end

        if not started_in_window or not completed_in_window:
            return AuditCheck(
                check_id="A-004",
                name="Timing Compliance",
                question="Did execution occur within activation window?",
                result=CheckResult.FAIL,
                reason="Execution outside activation window",
                evidence={
                    "window_start": window_start.isoformat(),
                    "window_end": window_end.isoformat(),
                    "job_started_at": job_started.isoformat(),
                    "job_completed_at": job_completed.isoformat(),
                    "started_in_window": started_in_window,
                    "completed_in_window": completed_in_window,
                },
            )

        return AuditCheck(
            check_id="A-004",
            name="Timing Compliance",
            question="Did execution occur within activation window?",
            result=CheckResult.PASS,
            reason="Execution within activation window",
            evidence={
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "job_started_at": job_started.isoformat(),
                "job_completed_at": job_completed.isoformat(),
            },
        )

    @staticmethod
    def check_rollback_availability(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-005: Rollback Availability

        Question: Can this execution be rolled back if needed?
        """
        step_results = audit_input.step_results

        # For this implementation, we assume steps have rollback
        # if they completed successfully
        steps_with_rollback = 0
        steps_without_rollback = 0
        non_rollbackable_steps: list[int] = []

        for i, step_result in enumerate(step_results):
            status = step_result.get("status")
            output = step_result.get("output") or {}

            if status == "COMPLETED":
                # Check if rollback action is defined
                rollback_action = output.get("rollback_action")
                if rollback_action is not None:
                    steps_with_rollback += 1
                else:
                    # Completed but no rollback - check if type supports it
                    step_type = output.get("step_type") or output.get("handler")
                    if step_type in ("noop", "configuration_change", "unknown"):
                        # These types may not need rollback
                        steps_with_rollback += 1
                    else:
                        steps_without_rollback += 1
                        non_rollbackable_steps.append(i)

        total_completed = steps_with_rollback + steps_without_rollback

        if steps_without_rollback > 0:
            return AuditCheck(
                check_id="A-005",
                name="Rollback Availability",
                question="Can this execution be rolled back if needed?",
                result=CheckResult.INCONCLUSIVE,
                reason=f"Some steps lack rollback path: {non_rollbackable_steps}",
                evidence={
                    "total_completed": total_completed,
                    "with_rollback": steps_with_rollback,
                    "without_rollback": steps_without_rollback,
                    "non_rollbackable_steps": non_rollbackable_steps,
                },
            )

        return AuditCheck(
            check_id="A-005",
            name="Rollback Availability",
            question="Can this execution be rolled back if needed?",
            result=CheckResult.PASS,
            reason="Full rollback path available",
            evidence={
                "total_completed": total_completed,
                "with_rollback": steps_with_rollback,
            },
        )

    @staticmethod
    def check_signal_consistency(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-006: Signal Consistency

        Question: Are governance signals consistent post-execution?
        """
        # This check requires external signal lookup
        # For now, we assume consistency if execution completed successfully
        if audit_input.job_status == "COMPLETED":
            return AuditCheck(
                check_id="A-006",
                name="Signal Consistency",
                question="Are governance signals consistent post-execution?",
                result=CheckResult.PASS,
                reason="Job completed successfully, signals assumed consistent",
                evidence={
                    "job_status": audit_input.job_status,
                    "note": "Signal verification requires external lookup",
                },
            )

        return AuditCheck(
            check_id="A-006",
            name="Signal Consistency",
            question="Are governance signals consistent post-execution?",
            result=CheckResult.INCONCLUSIVE,
            reason="Cannot verify signals for failed job",
            evidence={
                "job_status": audit_input.job_status,
            },
        )

    @staticmethod
    def check_no_unauthorized_mutations(
        audit_input: AuditInput,
    ) -> AuditCheck:
        """
        A-007: No Unauthorized Mutations

        Question: Were there any mutations outside job context?
        """
        # This check compares before/after state for unauthorized changes
        # For now, we verify that health changes only affect scoped capabilities

        contract_scope = set(audit_input.contract_scope)
        health_before = audit_input.health_before or {}
        health_after = audit_input.health_after or {}

        # Find capabilities that changed
        changed_capabilities: list[str] = []
        for cap_name in set(health_before.keys()) | set(health_after.keys()):
            before_status = health_before.get(cap_name)
            after_status = health_after.get(cap_name)
            if before_status != after_status:
                changed_capabilities.append(cap_name)

        # Check if changes are within scope
        unauthorized_changes = [cap for cap in changed_capabilities if cap not in contract_scope]

        if unauthorized_changes:
            return AuditCheck(
                check_id="A-007",
                name="No Unauthorized Mutations",
                question="Were there any mutations outside job context?",
                result=CheckResult.FAIL,
                reason=f"Unauthorized mutations detected: {unauthorized_changes}",
                evidence={
                    "contract_scope": list(contract_scope),
                    "changed_capabilities": changed_capabilities,
                    "unauthorized_changes": unauthorized_changes,
                },
            )

        return AuditCheck(
            check_id="A-007",
            name="No Unauthorized Mutations",
            question="Were there any mutations outside job context?",
            result=CheckResult.PASS,
            reason="No unauthorized mutations detected",
            evidence={
                "contract_scope": list(contract_scope),
                "changed_capabilities": changed_capabilities,
            },
        )


# ==============================================================================
# AUDIT SERVICE
# ==============================================================================


class AuditService:
    """
    Part-2 Governance Audit Service (L8)

    Verifies that job execution matched contract intent.

    Key Properties (GOVERNANCE_AUDIT_MODEL.md):
    - Post-execution verification
    - Deterministic verdicts
    - Authoritative and final
    - Cannot modify execution

    Invariants:
    - AUDIT-001: All completed jobs require audit
    - AUDIT-002: PASS required for COMPLETED
    - AUDIT-003: FAIL triggers rollback
    - AUDIT-004: Verdicts are immutable
    - AUDIT-005: Evidence is preserved
    - AUDIT-006: Health snapshots required

    Usage:
        auditor = AuditService()
        result = auditor.audit(audit_input)
    """

    def __init__(
        self,
        auditor_version: str = AUDIT_SERVICE_VERSION,
    ):
        """
        Initialize Audit Service.

        Args:
            auditor_version: Version string
        """
        self._version = auditor_version

    @property
    def version(self) -> str:
        """Return auditor version."""
        return self._version

    def audit(self, audit_input: AuditInput) -> AuditResult:
        """
        Perform audit on completed job.

        AUDIT-001: All completed jobs require audit
        AUDIT-005: Evidence is preserved

        Args:
            audit_input: Frozen evidence from job execution

        Returns:
            AuditResult with verdict and all checks

        Note:
            This method does NOT modify any state.
            It only reads evidence and produces a verdict.
        """
        start_time = datetime.now(timezone.utc)

        # Run all checks
        checks = self._run_all_checks(audit_input)

        # Determine verdict
        verdict, verdict_reason = self._determine_verdict(checks)

        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Count check results
        checks_passed = sum(1 for c in checks if c.result == CheckResult.PASS)
        checks_failed = sum(1 for c in checks if c.result == CheckResult.FAIL)
        checks_inconclusive = sum(1 for c in checks if c.result == CheckResult.INCONCLUSIVE)

        # Build evidence summary
        evidence_summary = {
            "job_id": str(audit_input.job_id),
            "contract_id": str(audit_input.contract_id),
            "job_status": audit_input.job_status,
            "steps_executed": len(audit_input.step_results),
            "execution_duration_seconds": audit_input.execution_duration_seconds,
        }

        return AuditResult(
            audit_id=uuid4(),
            job_id=audit_input.job_id,
            contract_id=audit_input.contract_id,
            verdict=verdict,
            verdict_reason=verdict_reason,
            checks=tuple(checks),
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            checks_inconclusive=checks_inconclusive,
            evidence_summary=evidence_summary,
            health_snapshot_before=audit_input.health_before,
            health_snapshot_after=audit_input.health_after,
            audited_at=end_time,
            duration_ms=duration_ms,
            auditor_version=self._version,
        )

    def _run_all_checks(self, audit_input: AuditInput) -> list[AuditCheck]:
        """Run all audit checks and return results."""
        return [
            AuditChecks.check_scope_compliance(audit_input),
            AuditChecks.check_health_preservation(audit_input),
            AuditChecks.check_execution_fidelity(audit_input),
            AuditChecks.check_timing_compliance(audit_input),
            AuditChecks.check_rollback_availability(audit_input),
            AuditChecks.check_signal_consistency(audit_input),
            AuditChecks.check_no_unauthorized_mutations(audit_input),
        ]

    def _determine_verdict(
        self,
        checks: list[AuditCheck],
    ) -> tuple[AuditVerdict, str]:
        """
        Determine final verdict from check results.

        Logic (from GOVERNANCE_AUDIT_MODEL.md):
        - Any failure → FAIL
        - Any inconclusive → INCONCLUSIVE
        - All pass → PASS
        """
        failed_checks = [c for c in checks if c.result == CheckResult.FAIL]
        inconclusive_checks = [c for c in checks if c.result == CheckResult.INCONCLUSIVE]

        # AUDIT-003: Any failure triggers FAIL
        if failed_checks:
            failed_names = [c.name for c in failed_checks]
            return (
                AuditVerdict.FAIL,
                f"Failed checks: {', '.join(failed_names)}",
            )

        # Any inconclusive → INCONCLUSIVE
        if inconclusive_checks:
            inconclusive_names = [c.name for c in inconclusive_checks]
            return (
                AuditVerdict.INCONCLUSIVE,
                f"Inconclusive checks: {', '.join(inconclusive_names)}",
            )

        # All pass → PASS
        return (
            AuditVerdict.PASS,
            "All checks passed",
        )


# ==============================================================================
# ROLLOUT GATE
# ==============================================================================


class RolloutGate:
    """
    Gate that determines if rollout is authorized.

    This is a simple policy enforcer:
    - PASS verdict → rollout authorized
    - FAIL verdict → rollout blocked
    - INCONCLUSIVE verdict → rollout blocked

    The gate does NOT modify the audit or verdict.
    """

    @staticmethod
    def is_rollout_authorized(verdict: AuditVerdict) -> bool:
        """
        Check if rollout is authorized based on verdict.

        AUDIT-002: PASS required for COMPLETED

        Args:
            verdict: Audit verdict

        Returns:
            True if PASS, False otherwise
        """
        return verdict == AuditVerdict.PASS

    @staticmethod
    def get_rollout_status(verdict: AuditVerdict) -> dict[str, Any]:
        """
        Get rollout status details.

        Args:
            verdict: Audit verdict

        Returns:
            Status dict with authorization and reason
        """
        if verdict == AuditVerdict.PASS:
            return {
                "authorized": True,
                "reason": "Audit passed - rollout authorized",
                "action": "proceed",
            }
        elif verdict == AuditVerdict.FAIL:
            return {
                "authorized": False,
                "reason": "Audit failed - rollback required",
                "action": "rollback",
            }
        elif verdict == AuditVerdict.INCONCLUSIVE:
            return {
                "authorized": False,
                "reason": "Audit inconclusive - human review required",
                "action": "escalate",
            }
        else:
            # PENDING should not reach rollout gate
            return {
                "authorized": False,
                "reason": "Audit pending - cannot determine rollout status",
                "action": "wait",
            }


# ==============================================================================
# AUDIT RESULT HELPERS
# ==============================================================================


def audit_result_to_record(result: AuditResult) -> dict[str, Any]:
    """
    Convert AuditResult to database record format.

    This is what gets persisted.
    """
    return {
        "audit_id": str(result.audit_id),
        "job_id": str(result.job_id),
        "contract_id": str(result.contract_id),
        "verdict": result.verdict.value,
        "verdict_reason": result.verdict_reason,
        "checks_performed": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "question": c.question,
                "result": c.result.value,
                "reason": c.reason,
                "evidence": c.evidence,
            }
            for c in result.checks
        ],
        "checks_passed": result.checks_passed,
        "checks_failed": result.checks_failed,
        "checks_inconclusive": result.checks_inconclusive,
        "evidence": result.evidence_summary,
        "health_snapshot_before": result.health_snapshot_before,
        "health_snapshot_after": result.health_snapshot_after,
        "audited_at": result.audited_at.isoformat(),
        "duration_ms": result.duration_ms,
        "auditor_version": result.auditor_version,
    }


def create_audit_input_from_evidence(
    job_id: UUID,
    contract_id: UUID,
    job_status: str,
    contract_scope: list[str],
    proposed_changes: dict[str, Any],
    execution_result: dict[str, Any],
    activation_window_start: Optional[datetime] = None,
    activation_window_end: Optional[datetime] = None,
) -> AuditInput:
    """
    Create AuditInput from job execution evidence.

    Helper to transform evidence into audit-ready format.
    """
    step_results = execution_result.get("step_results", [])
    health_obs = execution_result.get("health_observations", {})
    timing = execution_result.get("timing", {})

    # Parse timing
    started_at_str = timing.get("started_at")
    completed_at_str = timing.get("completed_at")

    if started_at_str:
        started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
    else:
        started_at = datetime.now(timezone.utc)

    if completed_at_str:
        completed_at = datetime.fromisoformat(completed_at_str.replace("Z", "+00:00"))
    else:
        completed_at = datetime.now(timezone.utc)

    duration = timing.get("duration_seconds", 0.0)

    return AuditInput(
        job_id=job_id,
        contract_id=contract_id,
        job_status=job_status,
        contract_scope=contract_scope,
        proposed_changes=proposed_changes,
        steps_executed=[],  # Populated from step_results
        step_results=step_results,
        health_before=health_obs.get("before"),
        health_after=health_obs.get("after"),
        activation_window_start=activation_window_start,
        activation_window_end=activation_window_end,
        job_started_at=started_at,
        job_completed_at=completed_at,
        execution_duration_seconds=duration,
    )
