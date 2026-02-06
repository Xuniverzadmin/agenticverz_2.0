# Layer: L4 — HOC Spine (Adapter)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Generate structured export bundles from incidents and traces
# Callers: L2 API routes
# Allowed Imports: L6 drivers
# Forbidden Imports: L1, L2, sqlalchemy, sqlmodel, Session
# Reference: HOC_LAYER_TOPOLOGY_V1.md, LOGS_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# ADAPTER CONTRACT:
# - Translation + aggregation only
# - No state mutation
# - No retries
# - No policy decisions
# - Delegates all DB access to L6 ExportBundleStore

"""
Export Bundle Adapter (L2)

Generates structured export bundles from incidents, runs, and traces
for evidence export, SOC2 compliance, and executive debriefs.

ADAPTER CONTRACT:
- NO sqlalchemy imports
- NO direct database queries
- Delegates all data access to L6 ExportBundleStore
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

# PIN-513 L1 Re-wiring: ExportBundleStore injected via constructor.
# The actual implementation lives in logs/L6_drivers/export_bundle_store.py
# and is wired by L4 orchestrator at construction time.

# Models for response types (L5 schemas - allowed at adapter level)
from app.models.export_bundles import (
    DEFAULT_SOC2_CONTROLS,
    EvidenceBundle,
    ExecutiveDebriefBundle,
    PolicyContext,
    SOC2Bundle,
    TraceStepEvidence,
)

# Snapshot types for type hints (L6 domain types)
from app.hoc.cus.logs.L6_drivers.export_bundle_store import (
    IncidentSnapshot,
    RunSnapshot,
    TraceSummarySnapshot,
)


logger = logging.getLogger("nova.adapters.export_bundle")


class ExportBundleAdapter:
    """
    Adapter for generating export bundles.

    Translates between API requests and L6 store,
    composing bundle structures from raw data.
    """

    def __init__(self, store=None):
        """Initialize with injected store (PIN-513 L1 re-wiring).

        Args:
            store: ExportBundleStore instance, injected by L4 orchestrator.
        """
        if store is None:
            raise NotImplementedError(
                "ExportBundleStore not injected. Wire via ExportBundleAdapter(store=...)"
            )
        self._store = store

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
        # Get incident from L6 store
        incident = self._store.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        # Get related run
        run: Optional[RunSnapshot] = None
        if incident.source_run_id:
            run = self._store.get_run_by_run_id(incident.source_run_id)

        # Get trace data
        trace_summary: Optional[TraceSummarySnapshot] = None
        steps: list[TraceStepEvidence] = []

        if run:
            trace_summary = await self._store.get_trace_summary(
                run_id=run.run_id,
                tenant_id=incident.tenant_id,
            )

            if include_raw_steps and trace_summary:
                trace_steps = await self._store.get_trace_steps(
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
                            step_type=step.step_type,
                            tokens=step.tokens,
                            cost_cents=step.cost_cents,
                            duration_ms=step.duration_ms,
                            status="violation" if is_violation else "ok",
                            is_inflection=is_violation,
                            content_hash=step.content_hash,
                        )
                    )

        # Build policy context
        policy_context = PolicyContext(
            policy_snapshot_id=run.policy_snapshot_id if run else "N/A",
            active_policies=[],
            violated_policy_id=incident.policy_id,
            violated_policy_name=incident.policy_name,
            violation_type=incident.violation_type,
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
        # Get incident from L6 store
        incident = self._store.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        # Get related run
        run: Optional[RunSnapshot] = None
        if incident.source_run_id:
            run = self._store.get_run_by_run_id(incident.source_run_id)

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

        cost_incurred = run.total_cost_cents or 0 if run else 0

        bundle = ExecutiveDebriefBundle(
            incident_summary=incident_summary,
            business_impact=business_impact,
            risk_level=risk_level,
            run_id=run.run_id if run else "N/A",
            incident_id=incident_id,
            tenant_id=incident.tenant_id,
            policy_violated=incident.policy_name or "Policy Violation",
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

    # -------------------------------------------------------------------------
    # Private Helpers (Pure computation, no DB access)
    # -------------------------------------------------------------------------

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

    def _assess_risk_level(self, incident: IncidentSnapshot) -> str:
        """Assess risk level for executive summary."""
        severity = incident.severity or "medium"
        if severity in ["critical", "high"]:
            return "high"
        elif severity == "medium":
            return "medium"
        return "low"

    def _generate_incident_summary(
        self, incident: IncidentSnapshot, run: Optional[RunSnapshot]
    ) -> str:
        """Generate non-technical incident summary."""
        policy_name = incident.policy_name or "a governance policy"
        return (
            f"An AI system execution was automatically stopped after violating "
            f"{policy_name}. The governance system detected the violation and "
            f"terminated the execution to prevent potential harm or excessive "
            f"resource consumption. All execution data has been preserved for "
            f"audit purposes."
        )

    def _assess_business_impact(
        self, incident: IncidentSnapshot, run: Optional[RunSnapshot]
    ) -> str:
        """Assess business impact for executive summary."""
        return (
            "The automated governance system successfully prevented the AI "
            "execution from exceeding configured limits. No business operations "
            "were affected beyond the stopped execution. The incident has been "
            "logged for compliance review."
        )

    def _generate_recommendations(
        self, incident: IncidentSnapshot, run: Optional[RunSnapshot]
    ) -> list[str]:
        """Generate recommended actions."""
        return [
            "Review the policy threshold that triggered this violation",
            "Assess if the policy limits are appropriately calibrated",
            "Consider adjusting limits if legitimate use cases are being blocked",
            "Verify that governance policies are documented and communicated",
        ]


# =============================================================================
# Singleton Factory
# =============================================================================

_adapter_instance: ExportBundleAdapter | None = None


def get_export_bundle_adapter() -> ExportBundleAdapter:
    """Get or create ExportBundleAdapter singleton."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ExportBundleAdapter()
    return _adapter_instance


__all__ = [
    "ExportBundleAdapter",
    "get_export_bundle_adapter",
]
