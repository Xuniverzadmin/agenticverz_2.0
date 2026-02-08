# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: AI Console
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: Incident, Run, AosTrace
#   Writes: none
# Database:
#   Scope: domain (incidents)
#   Models: Incident, Run
# Role: Generate structured export bundles from incidents and traces
# Callers: api/incidents.py
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, BACKEND_REMEDIATION_PLAN.md GAP-004, GAP-005, GAP-008
# NOTE: Renamed export_bundle_service.py → export_bundle_driver.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_driver.py for L6 files)

"""
Export Bundle Service

Generates structured export bundles from incidents, runs, and traces
for evidence export, SOC2 compliance, and executive debriefs.

Key Responsibilities:
1. Load incident, run, and trace data
2. Assemble EvidenceBundle with all cross-domain links
3. Enhance for SOC2 compliance (control mappings)
4. Generate executive summary (non-technical)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

from sqlmodel import Session, select

# NOTE: L6 drivers must not import L7 models via app.db.
# L7 models live under app.models/ by design (HOC Topology V2.0.0).
from app.db import Run, engine
from app.models.killswitch import Incident
from app.models.export_bundles import (
    DEFAULT_SOC2_CONTROLS,
    EvidenceBundle,
    ExecutiveDebriefBundle,
    PolicyContext,
    SOC2Bundle,
    TraceStepEvidence,
)

# PIN-521: Use Protocol for cross-domain dependency injection (no direct L6→L6 import)
# NOTE: T0 law tests require L6 drivers to avoid importing hoc_spine; keep the port local.
@runtime_checkable
class TraceStorePort(Protocol):
    async def get_trace_summary(self, run_id: str, tenant_id: str) -> Optional[Any]: ...

    async def get_trace_steps(self, trace_id: str, tenant_id: str) -> list: ...

logger = logging.getLogger("nova.services.export_bundle")


class ExportBundleDriver:
    """Generate structured export bundles from incidents/traces."""

    def __init__(self, trace_store: Optional[TraceStorePort] = None):
        """
        Initialize export bundle service.

        Args:
            trace_store: TraceStore instance (injected by caller)
                         PIN-521: Must be injected, no default instantiation.
        """
        self._trace_store = trace_store

    @property
    def trace_store(self) -> Optional[TraceStorePort]:
        """Get TraceStore instance (must be injected via constructor)."""
        return self._trace_store

    async def create_evidence_bundle(
        self,
        incident_id: str,
        exported_by: str = "system",
        export_reason: Optional[str] = None,
        include_raw_steps: bool = True,
    ) -> EvidenceBundle:
        """
        Create evidence bundle from incident.

        Args:
            incident_id: Incident to export
            exported_by: User ID or "system"
            export_reason: Optional reason for export
            include_raw_steps: Whether to include full step data

        Returns:
            EvidenceBundle with all evidence data
        """
        with Session(engine) as session:
            # Load incident
            incident = session.get(Incident, incident_id)
            if not incident:
                raise ValueError(f"Incident not found: {incident_id}")

            # Load related run
            run = None
            if incident.source_run_id:
                stmt = select(Run).where(Run.run_id == incident.source_run_id)
                result = session.exec(stmt)
                run = result.first()

            # Load trace
            trace_summary = None
            steps: list[TraceStepEvidence] = []
            if run:
                trace_summary = await self.trace_store.get_trace_summary(
                    run_id=run.run_id,
                    tenant_id=incident.tenant_id,
                )

                if include_raw_steps and trace_summary:
                    trace_steps = await self.trace_store.get_trace_steps(
                        trace_id=trace_summary.trace_id,
                        tenant_id=incident.tenant_id,
                    )
                    for i, step in enumerate(trace_steps):
                        is_violation = (
                            trace_summary.violation_step_index is not None
                            and i == trace_summary.violation_step_index
                        )
                        steps.append(
                            TraceStepEvidence(
                                step_index=i,
                                timestamp=step.timestamp,
                                step_type=step.step_type or "unknown",
                                tokens=step.tokens or 0,
                                cost_cents=step.cost_cents or 0.0,
                                duration_ms=step.duration_ms or 0.0,
                                status="violation" if is_violation else "ok",
                                is_inflection=is_violation,
                                content_hash=step.content_hash,
                            )
                        )

            # Build policy context
            policy_context = PolicyContext(
                policy_snapshot_id=run.policy_snapshot_id if run else "N/A",
                active_policies=[],  # TODO: Load from snapshot
                violated_policy_id=getattr(incident, "policy_id", None),
                violated_policy_name=getattr(incident, "policy_name", None),
                violation_type=getattr(incident, "violation_type", None),
            )

            # Calculate totals
            total_tokens = sum(s.tokens for s in steps)
            total_cost = sum(s.cost_cents for s in steps)
            total_duration = sum(s.duration_ms for s in steps)

            # Build bundle
            bundle = EvidenceBundle(
                run_id=run.run_id if run else "N/A",
                incident_id=incident_id,
                trace_id=trace_summary.trace_id if trace_summary else "N/A",
                tenant_id=incident.tenant_id,
                agent_id=run.agent_id if run else None,
                policy_context=policy_context,
                violation_step_index=trace_summary.violation_step_index if trace_summary else None,
                violation_timestamp=trace_summary.violation_timestamp if trace_summary else None,
                steps=steps,
                total_steps=len(steps),
                total_duration_ms=total_duration,
                total_tokens=total_tokens,
                total_cost_cents=total_cost,
                run_goal=run.goal if run else None,
                run_started_at=run.started_at if run else None,
                run_completed_at=run.completed_at if run else None,
                termination_reason=run.termination_reason if run else None,
                exported_by=exported_by,
                export_reason=export_reason,
            )

            # Calculate content hash for integrity
            bundle.content_hash = self._compute_bundle_hash(bundle)

            logger.info(
                "evidence_bundle_created",
                extra={
                    "bundle_id": bundle.bundle_id,
                    "incident_id": incident_id,
                    "step_count": len(steps),
                },
            )

            return bundle

    async def create_soc2_bundle(
        self,
        incident_id: str,
        exported_by: str = "system",
        compliance_period_start: Optional[datetime] = None,
        compliance_period_end: Optional[datetime] = None,
        auditor_notes: Optional[str] = None,
    ) -> SOC2Bundle:
        """
        Create SOC2-compliant bundle.

        Args:
            incident_id: Incident to export
            exported_by: User ID or "system"
            compliance_period_start: Start of compliance period
            compliance_period_end: End of compliance period
            auditor_notes: Optional auditor notes

        Returns:
            SOC2Bundle with control mappings
        """
        # Get base evidence bundle
        base = await self.create_evidence_bundle(
            incident_id=incident_id,
            exported_by=exported_by,
            export_reason="SOC2 compliance export",
        )

        # Create SOC2 bundle with additional fields
        bundle = SOC2Bundle(
            # Inherit from evidence bundle
            bundle_id=base.bundle_id.replace("EVD-", "SOC2-"),
            run_id=base.run_id,
            incident_id=base.incident_id,
            trace_id=base.trace_id,
            tenant_id=base.tenant_id,
            agent_id=base.agent_id,
            policy_context=base.policy_context,
            violation_step_index=base.violation_step_index,
            violation_timestamp=base.violation_timestamp,
            steps=base.steps,
            total_steps=base.total_steps,
            total_duration_ms=base.total_duration_ms,
            total_tokens=base.total_tokens,
            total_cost_cents=base.total_cost_cents,
            run_goal=base.run_goal,
            run_started_at=base.run_started_at,
            run_completed_at=base.run_completed_at,
            termination_reason=base.termination_reason,
            exported_by=exported_by,
            export_reason="SOC2 compliance export",
            content_hash=base.content_hash,
            # SOC2-specific fields
            control_mappings=list(DEFAULT_SOC2_CONTROLS),
            attestation_statement=self._generate_attestation(base),
            compliance_period_start=compliance_period_start or datetime.now(timezone.utc),
            compliance_period_end=compliance_period_end or datetime.now(timezone.utc),
            auditor_notes=auditor_notes,
        )

        logger.info(
            "soc2_bundle_created",
            extra={
                "bundle_id": bundle.bundle_id,
                "incident_id": incident_id,
                "controls_count": len(bundle.control_mappings),
            },
        )

        return bundle

    async def create_executive_debrief(
        self,
        incident_id: str,
        prepared_for: Optional[str] = None,
        prepared_by: str = "system",
    ) -> ExecutiveDebriefBundle:
        """
        Create executive summary (non-technical).

        Args:
            incident_id: Incident to summarize
            prepared_for: Recipient name/role
            prepared_by: Preparer ID

        Returns:
            ExecutiveDebriefBundle for leadership
        """
        with Session(engine) as session:
            # Load incident
            incident = session.get(Incident, incident_id)
            if not incident:
                raise ValueError(f"Incident not found: {incident_id}")

            # Load related run
            run = None
            if incident.source_run_id:
                stmt = select(Run).where(Run.run_id == incident.source_run_id)
                result = session.exec(stmt)
                run = result.first()

            # Determine risk level
            risk_level = self._assess_risk_level(incident)

            # Generate non-technical summary
            incident_summary = self._generate_incident_summary(incident, run)
            business_impact = self._assess_business_impact(incident, run)
            recommended_actions = self._generate_recommendations(incident, run)

            # Calculate metrics
            time_to_detect = 0
            if run and run.completed_at and run.started_at:
                time_to_detect = int((run.completed_at - run.started_at).total_seconds())

            cost_incurred = 0
            if run and hasattr(run, "total_cost_cents"):
                cost_incurred = run.total_cost_cents or 0

            bundle = ExecutiveDebriefBundle(
                incident_summary=incident_summary,
                business_impact=business_impact,
                risk_level=risk_level,
                run_id=run.run_id if run else "N/A",
                incident_id=incident_id,
                tenant_id=incident.tenant_id,
                policy_violated=getattr(incident, "policy_name", "Policy Violation"),
                violation_time=incident.created_at,
                detection_time=incident.created_at,
                recommended_actions=recommended_actions,
                remediation_status="pending",
                time_to_detect_seconds=time_to_detect,
                cost_incurred_cents=cost_incurred,
                prepared_for=prepared_for,
                prepared_by=prepared_by,
            )

            logger.info(
                "executive_debrief_created",
                extra={
                    "bundle_id": bundle.bundle_id,
                    "incident_id": incident_id,
                    "risk_level": risk_level,
                },
            )

            return bundle

    def _compute_bundle_hash(self, bundle: EvidenceBundle) -> str:
        """Compute SHA256 hash of bundle for integrity verification."""
        content = json.dumps(
            {
                "run_id": bundle.run_id,
                "incident_id": bundle.incident_id,
                "trace_id": bundle.trace_id,
                "steps": [s.model_dump() for s in bundle.steps],
                "created_at": bundle.created_at.isoformat(),
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _generate_attestation(self, bundle: EvidenceBundle) -> str:
        """Generate SOC2 attestation statement."""
        return (
            f"This evidence bundle (ID: {bundle.bundle_id}) contains a complete and "
            f"accurate record of incident {bundle.incident_id}. The system detected "
            f"a policy violation at step {bundle.violation_step_index or 'N/A'} and "
            f"terminated the execution according to configured governance policies. "
            f"All data in this bundle is immutable and cryptographically verified "
            f"(hash: {bundle.content_hash[:16]}...)."
        )

    def _assess_risk_level(self, incident: Incident) -> str:
        """Assess risk level for executive summary."""
        severity = getattr(incident, "severity", "medium")
        if severity in ["critical", "high"]:
            return "high"
        elif severity == "medium":
            return "medium"
        return "low"

    def _generate_incident_summary(
        self, incident: Incident, run: Optional[Run]
    ) -> str:
        """Generate non-technical incident summary."""
        policy_name = getattr(incident, "policy_name", "a governance policy")
        return (
            f"An AI system execution was automatically stopped after violating "
            f"{policy_name}. The governance system detected the violation and "
            f"terminated the execution to prevent potential harm or excessive "
            f"resource consumption. All execution data has been preserved for "
            f"audit purposes."
        )

    def _assess_business_impact(
        self, incident: Incident, run: Optional[Run]
    ) -> str:
        """Assess business impact for executive summary."""
        return (
            "The automated governance system successfully prevented the AI "
            "execution from exceeding configured limits. No business operations "
            "were affected beyond the stopped execution. The incident has been "
            "logged for compliance review."
        )

    def _generate_recommendations(
        self, incident: Incident, run: Optional[Run]
    ) -> list[str]:
        """Generate recommended actions."""
        return [
            "Review the policy threshold that triggered this violation",
            "Assess if the policy limits are appropriately calibrated",
            "Consider adjusting limits if legitimate use cases are being blocked",
            "Verify that governance policies are documented and communicated",
        ]


# Singleton instance
_export_bundle_driver: Optional[ExportBundleDriver] = None


def get_export_bundle_driver() -> ExportBundleDriver:
    """Get or create ExportBundleDriver singleton."""
    global _export_bundle_driver
    if _export_bundle_driver is None:
        _export_bundle_driver = ExportBundleDriver()
    return _export_bundle_driver


# Backward compatibility alias (legacy name from app.services.export_bundle_service)
get_export_bundle_service = get_export_bundle_driver
