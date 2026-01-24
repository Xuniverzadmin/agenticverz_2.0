# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: SOC2 Trust Service Criteria control registry
# Callers: services/soc2/mapper.py, services/export_bundle_service.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: GAP-025 (SOC2 Control Mapping)

"""
Module: control_registry
Purpose: Registry of SOC2 Trust Service Criteria controls.

SOC2 Trust Service Categories:
    - CC (Common Criteria): Security-related controls
    - A (Availability): System availability controls
    - PI (Processing Integrity): Processing accuracy controls
    - C (Confidentiality): Data confidentiality controls
    - P (Privacy): Privacy-related controls

Key Controls for AI Agent Governance:
    - CC7.x: System Operations (Incident Response)
    - CC6.x: Logical and Physical Access Controls
    - CC8.x: Change Management
    - PI1.x: Processing Integrity
    - A1.x: Availability

Exports:
    - SOC2Category: Enum of trust service categories
    - SOC2ComplianceStatus: Enum of compliance states
    - SOC2Control: Control definition
    - SOC2ControlMapping: Mapping with evidence
    - SOC2ControlRegistry: Registry singleton
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SOC2Category(str, Enum):
    """SOC2 Trust Service Categories."""

    COMMON_CRITERIA = "CC"  # Security
    AVAILABILITY = "A"  # Availability
    PROCESSING_INTEGRITY = "PI"  # Processing Integrity
    CONFIDENTIALITY = "C"  # Confidentiality
    PRIVACY = "P"  # Privacy


class SOC2ComplianceStatus(str, Enum):
    """Compliance status for a control mapping."""

    DEMONSTRATED = "DEMONSTRATED"  # Control is fully demonstrated
    PARTIAL = "PARTIAL"  # Control is partially satisfied
    NOT_APPLICABLE = "NOT_APPLICABLE"  # Control doesn't apply
    NOT_DEMONSTRATED = "NOT_DEMONSTRATED"  # Control is not yet demonstrated
    PENDING_REVIEW = "PENDING_REVIEW"  # Awaiting auditor review


@dataclass
class SOC2Control:
    """
    SOC2 Trust Service Criteria control definition.

    Represents a single SOC2 control with its ID, name, description,
    and the category it belongs to.
    """

    control_id: str  # e.g., "CC7.2"
    control_name: str  # e.g., "Incident Response"
    control_description: str  # Full control description
    category: SOC2Category  # Trust service category
    subcategory: Optional[str] = None  # e.g., "System Operations"

    # Evidence requirements
    evidence_types: list[str] = field(default_factory=list)  # What evidence satisfies this
    verification_method: Optional[str] = None  # How to verify compliance

    def __post_init__(self):
        """Set default evidence types based on control category."""
        if not self.evidence_types:
            if self.control_id.startswith("CC7"):
                self.evidence_types = ["incident_record", "trace_evidence", "response_time"]
            elif self.control_id.startswith("CC6"):
                self.evidence_types = ["access_log", "policy_record"]
            elif self.control_id.startswith("PI1"):
                self.evidence_types = ["execution_trace", "validation_record"]


@dataclass
class SOC2ControlMapping:
    """
    Mapping of incident/evidence to a SOC2 control.

    Contains the control, the evidence provided, and compliance status.
    """

    control: SOC2Control
    evidence_provided: str  # Description of evidence
    compliance_status: SOC2ComplianceStatus = SOC2ComplianceStatus.DEMONSTRATED
    evidence_sources: list[str] = field(default_factory=list)  # Source references
    notes: Optional[str] = None  # Auditor notes
    verified_at: Optional[datetime] = None  # When verified
    verified_by: Optional[str] = None  # Who verified

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses (GAP-025)."""
        return {
            "control_id": self.control.control_id,
            "control_name": self.control.control_name,
            "control_description": self.control.control_description,
            "category": self.control.category.value,
            "subcategory": self.control.subcategory,
            "evidence_provided": self.evidence_provided,
            "compliance_status": self.compliance_status.value,
            "evidence_sources": self.evidence_sources,
            "evidence_types": self.control.evidence_types,
            "notes": self.notes,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verified_by": self.verified_by,
        }


class SOC2ControlRegistry:
    """
    Registry of SOC2 Trust Service Criteria controls.

    Provides lookup and management of SOC2 controls relevant to
    AI agent governance and incident response.

    GAP-025: Complete SOC2 control objective mapping.
    """

    def __init__(self):
        """Initialize registry with all controls."""
        self._controls: dict[str, SOC2Control] = {}
        self._register_all_controls()

    def _register_all_controls(self) -> None:
        """Register all SOC2 controls relevant to AI governance."""
        # CC7.x - System Operations: Incident Response
        self._register_incident_response_controls()

        # CC6.x - Logical and Physical Access Controls
        self._register_access_controls()

        # CC8.x - Change Management
        self._register_change_management_controls()

        # PI1.x - Processing Integrity
        self._register_processing_integrity_controls()

        # A1.x - Availability
        self._register_availability_controls()

        # CC2.x - Communication and Information
        self._register_communication_controls()

        # CC9.x - Risk Mitigation
        self._register_risk_controls()

    def _register_incident_response_controls(self) -> None:
        """Register CC7.x Incident Response controls."""
        controls = [
            SOC2Control(
                control_id="CC7.1",
                control_name="Incident Detection",
                control_description=(
                    "The entity has procedures to detect and identify "
                    "potential security incidents in a timely manner."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="System Operations",
                evidence_types=["policy_violation_record", "monitoring_log", "alert_record"],
                verification_method="Review incident detection logs and response times",
            ),
            SOC2Control(
                control_id="CC7.2",
                control_name="Incident Response",
                control_description=(
                    "The entity responds to identified security incidents "
                    "by executing a defined incident response program."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="System Operations",
                evidence_types=["incident_record", "trace_evidence", "response_action"],
                verification_method="Review incident response actions and timelines",
            ),
            SOC2Control(
                control_id="CC7.3",
                control_name="Incident Management",
                control_description=(
                    "The entity manages incidents to minimize impact "
                    "and restore normal operations."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="System Operations",
                evidence_types=["incident_record", "containment_action", "resolution_record"],
                verification_method="Review incident containment and resolution procedures",
            ),
            SOC2Control(
                control_id="CC7.4",
                control_name="Analysis and Remediation",
                control_description=(
                    "The entity analyzes incidents, determines root causes, "
                    "and implements improvements."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="System Operations",
                evidence_types=["root_cause_analysis", "execution_trace", "policy_proposal"],
                verification_method="Review post-incident analysis and remediation actions",
            ),
            SOC2Control(
                control_id="CC7.5",
                control_name="Incident Communication",
                control_description=(
                    "The entity communicates incident information to "
                    "relevant parties in a timely manner."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="System Operations",
                evidence_types=["notification_record", "escalation_log", "stakeholder_notice"],
                verification_method="Review incident communication logs and escalation procedures",
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_access_controls(self) -> None:
        """Register CC6.x Access Controls."""
        controls = [
            SOC2Control(
                control_id="CC6.1",
                control_name="Logical Access Security",
                control_description=(
                    "The entity implements logical access security software, "
                    "infrastructure, and architectures over protected information assets."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Logical and Physical Access",
                evidence_types=["access_policy", "authentication_log", "authorization_record"],
            ),
            SOC2Control(
                control_id="CC6.2",
                control_name="Access Registration",
                control_description=(
                    "Prior to issuing system credentials, the entity registers "
                    "and authorizes new users."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Logical and Physical Access",
                evidence_types=["user_registration", "credential_issuance", "authorization_record"],
            ),
            SOC2Control(
                control_id="CC6.3",
                control_name="Access Removal",
                control_description=(
                    "The entity removes credentials and access when no longer needed."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Logical and Physical Access",
                evidence_types=["deprovisioning_record", "access_revocation"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_change_management_controls(self) -> None:
        """Register CC8.x Change Management controls."""
        controls = [
            SOC2Control(
                control_id="CC8.1",
                control_name="Change Authorization",
                control_description=(
                    "The entity authorizes, designs, develops, configures, "
                    "and implements changes to infrastructure and software."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Change Management",
                evidence_types=["policy_change_record", "approval_record", "deployment_log"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_processing_integrity_controls(self) -> None:
        """Register PI1.x Processing Integrity controls."""
        controls = [
            SOC2Control(
                control_id="PI1.1",
                control_name="Processing Accuracy",
                control_description=(
                    "The entity implements policies and procedures to ensure "
                    "processing integrity and accuracy."
                ),
                category=SOC2Category.PROCESSING_INTEGRITY,
                subcategory="Processing Integrity",
                evidence_types=["execution_trace", "validation_record", "accuracy_check"],
            ),
            SOC2Control(
                control_id="PI1.2",
                control_name="Processing Completeness",
                control_description=(
                    "The entity implements policies and procedures to ensure "
                    "processing is complete."
                ),
                category=SOC2Category.PROCESSING_INTEGRITY,
                subcategory="Processing Integrity",
                evidence_types=["completion_record", "trace_evidence"],
            ),
            SOC2Control(
                control_id="PI1.3",
                control_name="Processing Timeliness",
                control_description=(
                    "The entity implements policies and procedures to ensure "
                    "processing is timely."
                ),
                category=SOC2Category.PROCESSING_INTEGRITY,
                subcategory="Processing Integrity",
                evidence_types=["timing_record", "sla_compliance"],
            ),
            SOC2Control(
                control_id="PI1.4",
                control_name="Output Validation",
                control_description=(
                    "The entity implements policies and procedures to verify "
                    "that processing outputs are accurate and complete."
                ),
                category=SOC2Category.PROCESSING_INTEGRITY,
                subcategory="Processing Integrity",
                evidence_types=["output_validation", "hallucination_check", "accuracy_score"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_availability_controls(self) -> None:
        """Register A1.x Availability controls."""
        controls = [
            SOC2Control(
                control_id="A1.1",
                control_name="Capacity Planning",
                control_description=(
                    "The entity maintains, monitors, and evaluates current "
                    "processing capacity and availability."
                ),
                category=SOC2Category.AVAILABILITY,
                subcategory="Availability",
                evidence_types=["capacity_report", "utilization_metrics"],
            ),
            SOC2Control(
                control_id="A1.2",
                control_name="Recovery Planning",
                control_description=(
                    "The entity authorizes, designs, and implements "
                    "recovery plans to support system availability."
                ),
                category=SOC2Category.AVAILABILITY,
                subcategory="Availability",
                evidence_types=["recovery_plan", "backup_record"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_communication_controls(self) -> None:
        """Register CC2.x Communication controls."""
        controls = [
            SOC2Control(
                control_id="CC2.1",
                control_name="Policy Communication",
                control_description=(
                    "The entity communicates quality, security, and processing "
                    "commitments to authorized users."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Communication and Information",
                evidence_types=["policy_document", "user_notification"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def _register_risk_controls(self) -> None:
        """Register CC9.x Risk controls."""
        controls = [
            SOC2Control(
                control_id="CC9.1",
                control_name="Risk Identification",
                control_description=(
                    "The entity identifies, analyzes, and manages risks "
                    "that could impact the achievement of objectives."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Risk Mitigation",
                evidence_types=["risk_assessment", "threat_analysis"],
            ),
            SOC2Control(
                control_id="CC9.2",
                control_name="Risk Mitigation",
                control_description=(
                    "The entity implements risk mitigation strategies "
                    "to reduce identified risks to acceptable levels."
                ),
                category=SOC2Category.COMMON_CRITERIA,
                subcategory="Risk Mitigation",
                evidence_types=["mitigation_action", "policy_rule", "prevention_record"],
            ),
        ]
        for control in controls:
            self._controls[control.control_id] = control

    def get_control(self, control_id: str) -> Optional[SOC2Control]:
        """Get a control by ID."""
        return self._controls.get(control_id)

    def get_controls_by_category(self, category: SOC2Category) -> list[SOC2Control]:
        """Get all controls in a category."""
        return [c for c in self._controls.values() if c.category == category]

    def get_controls_by_prefix(self, prefix: str) -> list[SOC2Control]:
        """Get all controls with a given prefix (e.g., 'CC7')."""
        return [c for c in self._controls.values() if c.control_id.startswith(prefix)]

    def get_all_controls(self) -> list[SOC2Control]:
        """Get all registered controls."""
        return list(self._controls.values())

    def get_incident_response_controls(self) -> list[SOC2Control]:
        """Get all incident response controls (CC7.x)."""
        return self.get_controls_by_prefix("CC7")


# Singleton instance
_registry: Optional[SOC2ControlRegistry] = None


def get_control_registry() -> SOC2ControlRegistry:
    """Get or create the singleton control registry."""
    global _registry
    if _registry is None:
        _registry = SOC2ControlRegistry()
    return _registry
