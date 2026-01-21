# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Structured export bundle models for SOC2, evidence, and executive debrief
# Callers: services/export_bundle_service.py, services/pdf_renderer.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: BACKEND_REMEDIATION_PLAN.md GAP-008

"""
Export Bundle Models

Provides structured data models for exporting incident evidence,
SOC2 compliance reports, and executive debriefs.

Key Bundle Types:
1. EvidenceBundle - Generic evidence export with full trace data
2. SOC2Bundle - SOC2-compliant export with control objectives
3. ExecutiveDebriefBundle - Non-technical summary for leadership

Remediation: GAP-008 (Structured Export Bundles)
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def generate_bundle_id(prefix: str = "BND") -> str:
    """Generate unique bundle ID."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class TraceStepEvidence(BaseModel):
    """
    Single step in trace with evidence markers.

    Captures each execution step with status indicators
    for visualization in exports.
    """
    step_index: int
    timestamp: datetime
    step_type: str  # skill_name or action type
    tokens: int = 0
    cost_cents: float = 0.0
    duration_ms: float = 0.0
    status: str  # ok, warning, violation
    is_inflection: bool = False  # True if this is the violation step
    content_hash: Optional[str] = None  # For integrity verification

    class Config:
        from_attributes = True


class PolicyContext(BaseModel):
    """
    Policy information captured in evidence bundle.

    Records which policies were active and which was violated.
    """
    policy_snapshot_id: str
    active_policies: list[dict[str, Any]] = Field(default_factory=list)
    violated_policy_id: Optional[str] = None
    violated_policy_name: Optional[str] = None
    violation_type: Optional[str] = None  # token_limit, cost_limit, etc.
    threshold_value: Optional[str] = None
    actual_value: Optional[str] = None


class EvidenceBundle(BaseModel):
    """
    Generic evidence bundle for any export.

    Contains all data needed to reconstruct and verify
    what happened during a run, including the violation point.
    """
    bundle_id: str = Field(default_factory=lambda: generate_bundle_id("EVD"))
    bundle_type: str = "evidence"
    created_at: datetime = Field(default_factory=utc_now)

    # Source references (cross-domain linking)
    run_id: str
    incident_id: Optional[str] = None
    trace_id: str
    tenant_id: str
    agent_id: Optional[str] = None

    # Policy context
    policy_context: PolicyContext

    # Inflection point (GAP-003)
    violation_step_index: Optional[int] = None
    violation_timestamp: Optional[datetime] = None

    # Trace data
    steps: list[TraceStepEvidence] = Field(default_factory=list)
    total_steps: int = 0
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost_cents: float = 0.0

    # Run metadata
    run_goal: Optional[str] = None
    run_started_at: Optional[datetime] = None
    run_completed_at: Optional[datetime] = None
    termination_reason: Optional[str] = None  # RunTerminationReason value

    # Export metadata
    exported_by: str = "system"  # user_id or "system"
    export_reason: Optional[str] = None
    content_hash: Optional[str] = None  # SHA256 of bundle for integrity

    class Config:
        from_attributes = True


class SOC2ControlMapping(BaseModel):
    """
    SOC2 control objective mapping for compliance.

    Maps incident response to SOC2 Trust Service Criteria.
    """
    control_id: str  # e.g., "CC7.2"
    control_name: str  # e.g., "Incident Response"
    control_description: str
    evidence_provided: str  # How this bundle satisfies the control
    compliance_status: str = "DEMONSTRATED"  # DEMONSTRATED, PARTIAL, NOT_APPLICABLE


class SOC2Bundle(EvidenceBundle):
    """
    SOC2-specific export bundle.

    Extends EvidenceBundle with SOC2 compliance-specific fields
    for audit trails and attestation.
    """
    bundle_type: str = "soc2"
    bundle_id: str = Field(default_factory=lambda: generate_bundle_id("SOC2"))

    # SOC2 specific fields
    control_mappings: list[SOC2ControlMapping] = Field(default_factory=list)
    attestation_statement: str = ""
    compliance_period_start: Optional[datetime] = None
    compliance_period_end: Optional[datetime] = None

    # Audit trail
    auditor_notes: Optional[str] = None
    review_status: str = "PENDING"  # PENDING, REVIEWED, APPROVED
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # Trust Service Criteria coverage
    criteria_covered: list[str] = Field(
        default_factory=lambda: [
            "CC7.2",  # Incident Response
            "CC7.3",  # Incident Management
            "CC7.4",  # Analysis and Remediation
        ]
    )


class ExecutiveDebriefBundle(BaseModel):
    """
    Executive summary bundle (non-technical).

    Provides leadership-friendly summary without technical details.
    Focuses on business impact, risk, and recommended actions.
    """
    bundle_id: str = Field(default_factory=lambda: generate_bundle_id("EXEC"))
    bundle_type: str = "executive_debrief"
    created_at: datetime = Field(default_factory=utc_now)

    # Summary (non-technical, leadership-appropriate)
    incident_summary: str  # 2-3 sentence plain English summary
    business_impact: str  # Impact on business operations
    risk_level: str  # low, medium, high, critical

    # Key facts (minimal technical detail)
    run_id: str
    incident_id: str
    tenant_id: str
    policy_violated: str  # Policy name (not ID)
    violation_time: datetime
    detection_time: datetime

    # Resolution
    recommended_actions: list[str] = Field(default_factory=list)
    remediation_status: str = "pending"  # pending, in_progress, completed
    remediation_notes: Optional[str] = None

    # Metrics (business-relevant)
    time_to_detect_seconds: int = 0  # From violation to detection
    time_to_contain_seconds: Optional[int] = None  # From detection to containment
    cost_incurred_cents: int = 0  # Actual cost before stop
    cost_prevented_cents: Optional[int] = None  # Estimated prevented cost

    # Stakeholders
    prepared_for: Optional[str] = None  # Recipient name/role
    prepared_by: str = "system"
    classification: str = "INTERNAL"  # INTERNAL, CONFIDENTIAL, PUBLIC

    class Config:
        from_attributes = True


# Request/Response models for API

class ExportBundleRequest(BaseModel):
    """Request to create an export bundle."""
    incident_id: str
    bundle_type: str = "evidence"  # evidence, soc2, executive_debrief
    export_reason: Optional[str] = None
    include_raw_steps: bool = True
    prepared_for: Optional[str] = None  # For executive debrief


class ExportBundleResponse(BaseModel):
    """Response containing export bundle metadata."""
    bundle_id: str
    bundle_type: str
    created_at: datetime
    incident_id: Optional[str] = None
    run_id: str
    download_url: Optional[str] = None  # If async generation
    status: str = "ready"  # ready, generating, failed

    class Config:
        from_attributes = True


# Default SOC2 control mappings for incident response

DEFAULT_SOC2_CONTROLS = [
    SOC2ControlMapping(
        control_id="CC7.2",
        control_name="Incident Response",
        control_description="The entity responds to identified security incidents.",
        evidence_provided="Policy violation detected and run terminated at inflection point.",
        compliance_status="DEMONSTRATED",
    ),
    SOC2ControlMapping(
        control_id="CC7.3",
        control_name="Incident Management",
        control_description="The entity manages incidents to minimize impact.",
        evidence_provided="Incident automatically created with full trace evidence.",
        compliance_status="DEMONSTRATED",
    ),
    SOC2ControlMapping(
        control_id="CC7.4",
        control_name="Analysis and Remediation",
        control_description="The entity analyzes incidents and implements improvements.",
        evidence_provided="Complete execution trace available for root cause analysis.",
        compliance_status="DEMONSTRATED",
    ),
]
