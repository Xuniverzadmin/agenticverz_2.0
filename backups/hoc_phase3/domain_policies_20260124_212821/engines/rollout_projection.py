# Layer: L4 — Domain Engine (Projection)
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: query-time
#   Execution: sync (read-only projection)
# Role: Rollout Projection - read-only projection of audited truth
# Callers: L2 (founder console, customer console)
# Allowed Imports: L6 models only
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-296, GOVERNANCE_AUDIT_MODEL.md, part2-design-v1
#
# ==============================================================================
# GOVERNANCE RULE: PROJECTION-AUTHORITY (Non-Negotiable)
# ==============================================================================
#
# This service PROJECTS truth. It is a LENS, not a LEVER.
#
# Projection properties:
#   - READ-ONLY: Never modifies anything
#   - DERIVED: All data computed from existing sources
#   - NO EXECUTION: Cannot trigger execution
#   - NO APPROVAL: Cannot approve anything
#   - NO MUTATION: Cannot change state
#
# The Projection:
#   - MAY: Read contracts, read audits, compute views, derive stages
#   - MUST NOT: Modify contracts, modify audits, trigger execution,
#               approve changes, override verdicts, auto-advance stages
#
# Reference: part2-design-v1, PIN-296
#
# ==============================================================================

"""
Part-2 Rollout Projection Service (L4 - Projection)

Read-only projection layer that derives rollout state from audited truth.

This is the FINAL layer of Part-2 governance workflow.

Key Properties:
- Read-only and derived
- No execution authority
- No approval authority
- No mutation authority
- A lens, not a lever

Components:
- FounderRolloutView: Full lineage projection for founders
- GovernanceCompletionReport: Machine-generated completion artifact
- RolloutStage: State machine for exposure
- BlastRadius: Projection attribute for impact scope
- StabilizationWindow: Gate for stage advancement

Invariants:
- ROLLOUT-001: Projection is read-only
- ROLLOUT-002: Stage advancement requires audit PASS
- ROLLOUT-003: Stage advancement requires stabilization
- ROLLOUT-004: No health degradation during rollout
- ROLLOUT-005: Stages are monotonic (no regression without new contract)
- ROLLOUT-006: Customer sees only current stage facts

Reference: PIN-296, part2-design-v1
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

# Projection service version
PROJECTION_VERSION = "1.0.0"


# ==============================================================================
# ROLLOUT STAGE ENUM (Monotonic Progression)
# ==============================================================================


class RolloutStage(str, Enum):
    """
    Rollout stages for controlled exposure.

    IMPORTANT: Stages are monotonic. Regression requires new contract.
    """

    NOT_VISIBLE = "NOT_VISIBLE"  # Audit pending or failed
    PLANNED = "PLANNED"  # Audit passed, not yet released
    INTERNAL = "INTERNAL"  # Internal testing only
    LIMITED = "LIMITED"  # Beta/limited customers
    GENERAL = "GENERAL"  # Full availability


# Stage ordering for monotonic advancement
STAGE_ORDER = {
    RolloutStage.NOT_VISIBLE: 0,
    RolloutStage.PLANNED: 1,
    RolloutStage.INTERNAL: 2,
    RolloutStage.LIMITED: 3,
    RolloutStage.GENERAL: 4,
}


# ==============================================================================
# ROLLOUT DATA TYPES
# ==============================================================================


@dataclass(frozen=True)
class BlastRadius:
    """
    Blast radius projection attribute.

    This describes impact scope, not system behavior.
    Rollout Projection DECLARES blast radius.
    Execution does NOT change blast radius.
    """

    tenant_count: int
    customer_segment: str  # e.g., "all", "beta", "enterprise"
    region: str  # e.g., "all", "us-east", "eu-west"
    estimated_users: int


@dataclass(frozen=True)
class StabilizationWindow:
    """
    Stabilization window for stage advancement.

    Stage advancement requires stabilization window elapsed.
    """

    started_at: datetime
    duration_hours: int
    elapsed_hours: float
    is_satisfied: bool
    remaining_hours: float


@dataclass(frozen=True)
class ContractSummary:
    """Summary of contract for rollout view."""

    contract_id: UUID
    issue_id: UUID
    title: str
    eligibility_verdict: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    affected_capabilities: list[str]


@dataclass(frozen=True)
class ExecutionSummary:
    """Summary of execution for rollout view."""

    job_id: UUID
    status: str
    started_at: datetime
    completed_at: datetime
    steps_executed: int
    steps_succeeded: int


@dataclass(frozen=True)
class AuditSummary:
    """Summary of audit for rollout view."""

    audit_id: UUID
    verdict: str
    checks_passed: list[str]
    checks_failed: list[str]
    audited_at: datetime


@dataclass(frozen=True)
class RolloutPlan:
    """Rollout plan showing progression."""

    current_stage: RolloutStage
    planned_stages: tuple[RolloutStage, ...]
    blast_radius: BlastRadius
    stabilization: Optional[StabilizationWindow]


@dataclass(frozen=True)
class FounderRolloutView:
    """
    Complete rollout projection for founders.

    This is DERIVED, not stored. It shows the full lineage:
    Issue -> Contract -> Approval -> Execution -> Audit -> Rollout

    Founders see everything. Customers see only current stage facts.
    """

    contract: ContractSummary
    execution: Optional[ExecutionSummary]
    audit: Optional[AuditSummary]
    rollout: RolloutPlan
    lineage_complete: bool
    lineage_gaps: list[str]
    projected_at: datetime


@dataclass(frozen=True)
class GovernanceCompletionReport:
    """
    Machine-generated governance completion artifact.

    Generated ONLY if audit.verdict == PASS.

    This is immutable, append-only, and not human-editable.
    It is the document that says:
    "The system asserts this task completed truthfully."
    """

    report_id: UUID
    contract_id: UUID
    audit_verdict: str
    execution_summary: dict[str, Any]
    health_delta: dict[str, Any]
    evidence_refs: list[str]
    generated_at: datetime
    report_version: str


@dataclass(frozen=True)
class CustomerRolloutView:
    """
    Customer-facing rollout view.

    Customers see FACTS ONLY, never intent.
    - Only features at current rollout stage
    - No audit details
    - No job visibility
    - No "coming soon" claims
    """

    capability_name: str
    is_available: bool
    stage: RolloutStage
    availability_reason: str


# ==============================================================================
# ROLLOUT PROJECTION SERVICE
# ==============================================================================


class RolloutProjectionService:
    """
    Part-2 Rollout Projection Service (Read-Only)

    Projects rollout state from audited truth.

    Key Properties:
    - Read-only: Never modifies anything
    - Derived: All data computed from existing sources
    - No execution: Cannot trigger execution
    - No approval: Cannot approve anything

    Invariants:
    - ROLLOUT-001: Projection is read-only
    - ROLLOUT-002: Stage advancement requires audit PASS
    - ROLLOUT-003: Stage advancement requires stabilization
    - ROLLOUT-004: No health degradation during rollout
    - ROLLOUT-005: Stages are monotonic
    - ROLLOUT-006: Customer sees only current stage facts

    Usage:
        service = RolloutProjectionService()
        view = service.project_founder_view(contract, execution, audit)
    """

    def __init__(
        self,
        default_stabilization_hours: int = 24,
        projection_version: str = PROJECTION_VERSION,
    ):
        """
        Initialize Rollout Projection Service.

        Args:
            default_stabilization_hours: Default stabilization window
            projection_version: Version string
        """
        self._stabilization_hours = default_stabilization_hours
        self._version = projection_version

    @property
    def version(self) -> str:
        """Return projection version."""
        return self._version

    # ==========================================================================
    # FOUNDER PROJECTION
    # ==========================================================================

    def project_founder_view(
        self,
        contract: ContractSummary,
        execution: Optional[ExecutionSummary],
        audit: Optional[AuditSummary],
        current_stage: Optional[RolloutStage] = None,
        stabilization_started_at: Optional[datetime] = None,
    ) -> FounderRolloutView:
        """
        Project complete rollout view for founders.

        Shows full lineage: Issue -> Contract -> Approval -> Execution -> Audit -> Rollout

        Args:
            contract: Contract summary
            execution: Execution summary (optional)
            audit: Audit summary (optional)
            current_stage: Current rollout stage (optional, derived if not provided)
            stabilization_started_at: When stabilization started (optional)

        Returns:
            FounderRolloutView with complete lineage
        """
        # Check lineage completeness
        lineage_gaps = self._check_lineage_gaps(contract, execution, audit)
        lineage_complete = len(lineage_gaps) == 0

        # Derive current stage if not provided
        if current_stage is None:
            current_stage = self._derive_stage(audit)

        # Calculate stabilization
        stabilization = None
        if stabilization_started_at and current_stage != RolloutStage.NOT_VISIBLE:
            stabilization = self._calculate_stabilization(stabilization_started_at)

        # Build rollout plan
        rollout = RolloutPlan(
            current_stage=current_stage,
            planned_stages=self._get_planned_stages(current_stage),
            blast_radius=self._default_blast_radius(current_stage),
            stabilization=stabilization,
        )

        return FounderRolloutView(
            contract=contract,
            execution=execution,
            audit=audit,
            rollout=rollout,
            lineage_complete=lineage_complete,
            lineage_gaps=lineage_gaps,
            projected_at=datetime.now(timezone.utc),
        )

    def _check_lineage_gaps(
        self,
        contract: ContractSummary,
        execution: Optional[ExecutionSummary],
        audit: Optional[AuditSummary],
    ) -> list[str]:
        """Check for gaps in the lineage chain."""
        gaps = []

        # Contract must have approval for rollout
        if contract.approved_by is None:
            gaps.append("Contract not approved")

        # Execution required
        if execution is None:
            gaps.append("No execution record")

        # Audit required
        if audit is None:
            gaps.append("No audit record")
        elif audit.verdict != "PASS":
            gaps.append(f"Audit verdict is {audit.verdict}, not PASS")

        return gaps

    def _derive_stage(self, audit: Optional[AuditSummary]) -> RolloutStage:
        """Derive rollout stage from audit verdict."""
        if audit is None:
            return RolloutStage.NOT_VISIBLE

        if audit.verdict == "PASS":
            return RolloutStage.PLANNED

        # FAIL or INCONCLUSIVE
        return RolloutStage.NOT_VISIBLE

    def _get_planned_stages(self, current: RolloutStage) -> tuple[RolloutStage, ...]:
        """Get remaining planned stages after current."""
        all_stages = [
            RolloutStage.NOT_VISIBLE,
            RolloutStage.PLANNED,
            RolloutStage.INTERNAL,
            RolloutStage.LIMITED,
            RolloutStage.GENERAL,
        ]

        current_idx = all_stages.index(current)
        return tuple(all_stages[current_idx + 1 :])

    def _default_blast_radius(self, stage: RolloutStage) -> BlastRadius:
        """Get default blast radius for stage."""
        if stage == RolloutStage.NOT_VISIBLE:
            return BlastRadius(
                tenant_count=0,
                customer_segment="none",
                region="none",
                estimated_users=0,
            )
        elif stage == RolloutStage.PLANNED:
            return BlastRadius(
                tenant_count=0,
                customer_segment="none",
                region="none",
                estimated_users=0,
            )
        elif stage == RolloutStage.INTERNAL:
            return BlastRadius(
                tenant_count=1,
                customer_segment="internal",
                region="all",
                estimated_users=10,
            )
        elif stage == RolloutStage.LIMITED:
            return BlastRadius(
                tenant_count=10,
                customer_segment="beta",
                region="us-east",
                estimated_users=100,
            )
        else:  # GENERAL
            return BlastRadius(
                tenant_count=0,  # All
                customer_segment="all",
                region="all",
                estimated_users=0,  # All
            )

    def _calculate_stabilization(self, started_at: datetime) -> StabilizationWindow:
        """Calculate stabilization window status."""
        now = datetime.now(timezone.utc)
        elapsed = now - started_at
        elapsed_hours = elapsed.total_seconds() / 3600

        is_satisfied = elapsed_hours >= self._stabilization_hours
        remaining = max(0, self._stabilization_hours - elapsed_hours)

        return StabilizationWindow(
            started_at=started_at,
            duration_hours=self._stabilization_hours,
            elapsed_hours=round(elapsed_hours, 2),
            is_satisfied=is_satisfied,
            remaining_hours=round(remaining, 2),
        )

    # ==========================================================================
    # GOVERNANCE COMPLETION REPORT
    # ==========================================================================

    def generate_completion_report(
        self,
        report_id: UUID,
        contract_id: UUID,
        audit_verdict: str,
        execution_summary: dict[str, Any],
        health_before: Optional[dict[str, Any]],
        health_after: Optional[dict[str, Any]],
        evidence_refs: list[str],
    ) -> Optional[GovernanceCompletionReport]:
        """
        Generate governance completion report.

        ONLY generated if audit_verdict == PASS.
        This is machine-generated, immutable, not human-editable.

        Args:
            report_id: Unique report ID
            contract_id: Contract this report is for
            audit_verdict: Must be PASS
            execution_summary: Summary of execution
            health_before: Health state before
            health_after: Health state after
            evidence_refs: References to supporting evidence

        Returns:
            GovernanceCompletionReport if verdict is PASS, None otherwise
        """
        # ROLLOUT-002: Only generate report if audit PASS
        if audit_verdict != "PASS":
            return None

        # Calculate health delta
        health_delta = self._calculate_health_delta(health_before, health_after)

        return GovernanceCompletionReport(
            report_id=report_id,
            contract_id=contract_id,
            audit_verdict=audit_verdict,
            execution_summary=execution_summary,
            health_delta=health_delta,
            evidence_refs=evidence_refs,
            generated_at=datetime.now(timezone.utc),
            report_version=self._version,
        )

    def _calculate_health_delta(
        self,
        before: Optional[dict[str, Any]],
        after: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate health delta between before and after."""
        if before is None or after is None:
            return {"status": "unknown", "changes": []}

        changes = []
        all_caps = set(before.keys()) | set(after.keys())

        for cap in all_caps:
            before_status = before.get(cap)
            after_status = after.get(cap)
            if before_status != after_status:
                changes.append(
                    {
                        "capability": cap,
                        "before": before_status,
                        "after": after_status,
                    }
                )

        return {
            "status": "improved" if not changes else "changed",
            "changes": changes,
        }

    # ==========================================================================
    # CUSTOMER PROJECTION
    # ==========================================================================

    def project_customer_view(
        self,
        capability_name: str,
        current_stage: RolloutStage,
    ) -> CustomerRolloutView:
        """
        Project customer-facing rollout view.

        Customers see FACTS ONLY:
        - Only features at current rollout stage
        - No audit details
        - No job visibility
        - No "coming soon" claims

        Args:
            capability_name: Capability being queried
            current_stage: Current rollout stage

        Returns:
            CustomerRolloutView with facts only
        """
        # Determine availability based on stage
        is_available = current_stage == RolloutStage.GENERAL

        # Generate factual reason
        if is_available:
            reason = "Available"
        elif current_stage == RolloutStage.LIMITED:
            reason = "Available to select customers"
        elif current_stage == RolloutStage.INTERNAL:
            reason = "In testing"
        else:
            reason = "Not available"

        return CustomerRolloutView(
            capability_name=capability_name,
            is_available=is_available,
            stage=current_stage,
            availability_reason=reason,
        )

    # ==========================================================================
    # STAGE ADVANCEMENT (Read-Only Check)
    # ==========================================================================

    def can_advance_stage(
        self,
        current_stage: RolloutStage,
        target_stage: RolloutStage,
        audit_verdict: str,
        stabilization: Optional[StabilizationWindow],
        health_degraded: bool,
    ) -> tuple[bool, str]:
        """
        Check if stage advancement is allowed.

        This is a READ-ONLY check. It does NOT advance the stage.
        Stage advancement must be done through proper governance.

        ROLLOUT-002: Stage advancement requires audit PASS
        ROLLOUT-003: Stage advancement requires stabilization
        ROLLOUT-004: No health degradation during rollout
        ROLLOUT-005: Stages are monotonic

        Args:
            current_stage: Current rollout stage
            target_stage: Target stage
            audit_verdict: Current audit verdict
            stabilization: Stabilization window status
            health_degraded: Whether health has degraded

        Returns:
            Tuple of (can_advance, reason)
        """
        # ROLLOUT-005: Stages are monotonic
        current_order = STAGE_ORDER.get(current_stage, 0)
        target_order = STAGE_ORDER.get(target_stage, 0)

        if target_order <= current_order:
            return (False, "Stage regression not allowed without new contract")

        if target_order > current_order + 1:
            return (False, "Cannot skip stages")

        # ROLLOUT-002: Audit PASS required
        if audit_verdict != "PASS":
            return (False, f"Audit verdict is {audit_verdict}, not PASS")

        # ROLLOUT-004: No health degradation
        if health_degraded:
            return (False, "Health degradation detected")

        # ROLLOUT-003: Stabilization required
        if stabilization is not None and not stabilization.is_satisfied:
            return (
                False,
                f"Stabilization not complete ({stabilization.remaining_hours}h remaining)",
            )

        return (True, "Stage advancement allowed")


# ==============================================================================
# PROJECTION HELPERS
# ==============================================================================


def founder_view_to_dict(view: FounderRolloutView) -> dict[str, Any]:
    """Convert FounderRolloutView to dictionary for API response."""
    return {
        "contract": {
            "contract_id": str(view.contract.contract_id),
            "issue_id": str(view.contract.issue_id),
            "title": view.contract.title,
            "eligibility_verdict": view.contract.eligibility_verdict,
            "approved_by": view.contract.approved_by,
            "approved_at": view.contract.approved_at.isoformat() if view.contract.approved_at else None,
            "affected_capabilities": view.contract.affected_capabilities,
        },
        "execution": {
            "job_id": str(view.execution.job_id),
            "status": view.execution.status,
            "started_at": view.execution.started_at.isoformat(),
            "completed_at": view.execution.completed_at.isoformat(),
            "steps_executed": view.execution.steps_executed,
            "steps_succeeded": view.execution.steps_succeeded,
        }
        if view.execution
        else None,
        "audit": {
            "audit_id": str(view.audit.audit_id),
            "verdict": view.audit.verdict,
            "checks_passed": view.audit.checks_passed,
            "checks_failed": view.audit.checks_failed,
            "audited_at": view.audit.audited_at.isoformat(),
        }
        if view.audit
        else None,
        "rollout": {
            "current_stage": view.rollout.current_stage.value,
            "planned_stages": [s.value for s in view.rollout.planned_stages],
            "blast_radius": {
                "tenant_count": view.rollout.blast_radius.tenant_count,
                "customer_segment": view.rollout.blast_radius.customer_segment,
                "region": view.rollout.blast_radius.region,
                "estimated_users": view.rollout.blast_radius.estimated_users,
            },
            "stabilization": {
                "started_at": view.rollout.stabilization.started_at.isoformat(),
                "duration_hours": view.rollout.stabilization.duration_hours,
                "elapsed_hours": view.rollout.stabilization.elapsed_hours,
                "is_satisfied": view.rollout.stabilization.is_satisfied,
                "remaining_hours": view.rollout.stabilization.remaining_hours,
            }
            if view.rollout.stabilization
            else None,
        },
        "lineage_complete": view.lineage_complete,
        "lineage_gaps": view.lineage_gaps,
        "projected_at": view.projected_at.isoformat(),
    }


def completion_report_to_dict(report: GovernanceCompletionReport) -> dict[str, Any]:
    """Convert GovernanceCompletionReport to dictionary for storage."""
    return {
        "report_id": str(report.report_id),
        "contract_id": str(report.contract_id),
        "audit_verdict": report.audit_verdict,
        "execution_summary": report.execution_summary,
        "health_delta": report.health_delta,
        "evidence_refs": report.evidence_refs,
        "generated_at": report.generated_at.isoformat(),
        "report_version": report.report_version,
    }
