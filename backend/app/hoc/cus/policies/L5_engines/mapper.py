# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Map incidents to relevant SOC2 controls
# Callers: services/export_bundle_service.py, api/incidents.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-025 (SOC2 Control Mapping)

"""
Module: mapper
Purpose: Map incidents and evidence to SOC2 controls.

Provides intelligent mapping of incident categories and evidence
to the appropriate SOC2 Trust Service Criteria controls.

Exports:
    - SOC2ControlMapper: Maps incidents to controls
    - get_control_mappings_for_incident: Main entry point
"""

from datetime import datetime, timezone
from typing import Any, Optional

from app.hoc.cus.general.L5_engines.control_registry import (
    SOC2ComplianceStatus,
    SOC2Control,
    SOC2ControlMapping,
    SOC2ControlRegistry,
    get_control_registry,
)


def utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


# Mapping of incident categories to relevant control prefixes
CATEGORY_CONTROL_MAP: dict[str, list[str]] = {
    # Execution failures map to incident response and processing integrity
    "EXECUTION_FAILURE": ["CC7.1", "CC7.2", "CC7.3", "CC7.4", "PI1.1", "PI1.2"],
    # Budget exceeded maps to risk mitigation and incident response
    "BUDGET_EXCEEDED": ["CC7.1", "CC7.2", "CC7.3", "CC9.1", "CC9.2"],
    # Rate limits map to availability and incident response
    "RATE_LIMIT": ["CC7.1", "CC7.2", "CC7.3", "A1.1"],
    # Policy violations map to access controls and incident response
    "POLICY_VIOLATION": ["CC7.1", "CC7.2", "CC7.3", "CC7.4", "CC6.1"],
    # Resource exhaustion maps to availability
    "RESOURCE_EXHAUSTION": ["CC7.1", "CC7.2", "A1.1", "A1.2"],
    # Manual incidents map to incident management
    "MANUAL": ["CC7.1", "CC7.2", "CC7.3", "CC7.5"],
    # Hallucination (per INV-002: non-blocking but tracked)
    "HALLUCINATION": ["PI1.1", "PI1.4", "CC7.1"],
    # Success outcomes (PIN-407)
    "EXECUTION_SUCCESS": ["PI1.1", "PI1.2", "PI1.3"],
    # Default for unknown categories
    "DEFAULT": ["CC7.1", "CC7.2", "CC7.3"],
}

# Evidence descriptions for each control
EVIDENCE_TEMPLATES: dict[str, str] = {
    "CC7.1": "Policy violation detected at step {step_index} with severity {severity}.",
    "CC7.2": "Incident response initiated: run terminated at inflection point.",
    "CC7.3": "Incident managed: {incident_id} created with full trace evidence.",
    "CC7.4": "Complete execution trace available for root cause analysis.",
    "CC7.5": "Incident communication: escalation to {escalated_to}.",
    "CC6.1": "Access policy {policy_name} enforced during execution.",
    "CC8.1": "Policy change {policy_proposal_id} proposed based on incident.",
    "CC9.1": "Risk identified: {error_code} pattern detected.",
    "CC9.2": "Risk mitigation: prevention rule created for pattern.",
    "PI1.1": "Processing accuracy verified through execution trace.",
    "PI1.2": "Processing completeness verified: {total_steps} steps executed.",
    "PI1.3": "Processing timeliness: execution completed in {duration_ms}ms.",
    "PI1.4": "Output validation performed: {validation_status}.",
    "A1.1": "Capacity utilization tracked: {token_count} tokens used.",
    "A1.2": "Recovery procedures defined in incident response.",
    "CC2.1": "Policy constraints communicated to executing agent.",
}


class SOC2ControlMapper:
    """
    Maps incidents to relevant SOC2 controls.

    Provides intelligent mapping based on incident category,
    severity, and available evidence.

    GAP-025: Complete SOC2 control objective mapping.
    """

    def __init__(self, registry: Optional[SOC2ControlRegistry] = None):
        """Initialize mapper with control registry."""
        self._registry = registry or get_control_registry()

    def map_incident_to_controls(
        self,
        incident_category: str,
        incident_data: dict[str, Any],
    ) -> list[SOC2ControlMapping]:
        """
        Map an incident to relevant SOC2 controls.

        Args:
            incident_category: Category of the incident (e.g., EXECUTION_FAILURE)
            incident_data: Incident data including:
                - incident_id: Incident ID
                - severity: Incident severity
                - error_code: Error code
                - step_index: Inflection point step index
                - total_steps: Total steps in trace
                - duration_ms: Execution duration
                - token_count: Total tokens used
                - policy_name: Violated policy name (if any)
                - escalated_to: Escalation target (if any)
                - policy_proposal_id: Proposed policy ID (if any)

        Returns:
            List of SOC2ControlMapping objects
        """
        # Get control IDs for this category
        control_ids = CATEGORY_CONTROL_MAP.get(
            incident_category,
            CATEGORY_CONTROL_MAP["DEFAULT"]
        )

        mappings = []
        for control_id in control_ids:
            control = self._registry.get_control(control_id)
            if control:
                mapping = self._create_mapping(control, incident_data)
                mappings.append(mapping)

        return mappings

    def _create_mapping(
        self,
        control: SOC2Control,
        incident_data: dict[str, Any],
    ) -> SOC2ControlMapping:
        """Create a mapping with evidence for a control."""
        # Get template and format with incident data
        template = EVIDENCE_TEMPLATES.get(
            control.control_id,
            f"Evidence provided for {control.control_name}."
        )

        # Safe format with defaults
        format_data = {
            "incident_id": incident_data.get("incident_id", "unknown"),
            "severity": incident_data.get("severity", "MEDIUM"),
            "error_code": incident_data.get("error_code", "UNKNOWN"),
            "step_index": incident_data.get("step_index", "N/A"),
            "total_steps": incident_data.get("total_steps", 0),
            "duration_ms": incident_data.get("duration_ms", 0),
            "token_count": incident_data.get("token_count", 0),
            "policy_name": incident_data.get("policy_name", "default"),
            "escalated_to": incident_data.get("escalated_to", "N/A"),
            "policy_proposal_id": incident_data.get("policy_proposal_id", "N/A"),
            "validation_status": incident_data.get("validation_status", "passed"),
        }

        try:
            evidence = template.format(**format_data)
        except KeyError:
            evidence = f"Evidence provided for {control.control_name}."

        # Determine compliance status
        compliance_status = self._determine_compliance_status(
            control, incident_data
        )

        # Build evidence sources
        evidence_sources = []
        if incident_data.get("incident_id"):
            evidence_sources.append(f"incident:{incident_data['incident_id']}")
        if incident_data.get("trace_id"):
            evidence_sources.append(f"trace:{incident_data['trace_id']}")
        if incident_data.get("run_id"):
            evidence_sources.append(f"run:{incident_data['run_id']}")

        return SOC2ControlMapping(
            control=control,
            evidence_provided=evidence,
            compliance_status=compliance_status,
            evidence_sources=evidence_sources,
            verified_at=utc_now(),
            verified_by="system",
        )

    def _determine_compliance_status(
        self,
        control: SOC2Control,
        incident_data: dict[str, Any],
    ) -> SOC2ComplianceStatus:
        """Determine compliance status based on control and evidence."""
        # Check if we have all required evidence types
        has_incident = bool(incident_data.get("incident_id"))
        has_trace = bool(incident_data.get("trace_id"))
        has_run = bool(incident_data.get("run_id"))

        # Incident response controls require incident and trace
        if control.control_id.startswith("CC7"):
            if has_incident and has_trace:
                return SOC2ComplianceStatus.DEMONSTRATED
            elif has_incident or has_trace:
                return SOC2ComplianceStatus.PARTIAL
            return SOC2ComplianceStatus.PENDING_REVIEW

        # Processing integrity requires trace
        if control.control_id.startswith("PI1"):
            if has_trace and has_run:
                return SOC2ComplianceStatus.DEMONSTRATED
            elif has_trace or has_run:
                return SOC2ComplianceStatus.PARTIAL
            return SOC2ComplianceStatus.PENDING_REVIEW

        # Availability requires capacity data
        if control.control_id.startswith("A1"):
            if incident_data.get("token_count") or incident_data.get("duration_ms"):
                return SOC2ComplianceStatus.DEMONSTRATED
            return SOC2ComplianceStatus.PARTIAL

        # Default to demonstrated if we have basic evidence
        if has_incident:
            return SOC2ComplianceStatus.DEMONSTRATED

        return SOC2ComplianceStatus.PENDING_REVIEW

    def get_all_applicable_controls(
        self,
        incident_category: str,
    ) -> list[SOC2Control]:
        """Get all controls applicable to an incident category."""
        control_ids = CATEGORY_CONTROL_MAP.get(
            incident_category,
            CATEGORY_CONTROL_MAP["DEFAULT"]
        )

        controls = []
        for control_id in control_ids:
            control = self._registry.get_control(control_id)
            if control:
                controls.append(control)

        return controls


def get_control_mappings_for_incident(
    incident_category: str,
    incident_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Get SOC2 control mappings for an incident (GAP-025 main entry point).

    This is the primary function for obtaining SOC2 control mappings
    for incident exports and compliance reporting.

    Args:
        incident_category: Category of the incident
        incident_data: Incident data dict

    Returns:
        List of control mapping dicts suitable for API responses
    """
    mapper = SOC2ControlMapper()
    mappings = mapper.map_incident_to_controls(incident_category, incident_data)
    return [m.to_dict() for m in mappings]
