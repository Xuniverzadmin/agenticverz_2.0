# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-025 (SOC2 Control Mapping)
"""
SOC2 Control Mapping Service (GAP-025)

Provides complete SOC2 Trust Service Criteria mapping for
incident response, evidence export, and compliance reporting.

This module provides:
    - SOC2ControlRegistry: Registry of all SOC2 controls
    - SOC2ControlMapper: Maps incidents to relevant controls
    - SOC2ComplianceStatus: Enum for compliance states
    - get_control_mappings_for_incident: Main entry point
"""

from app.services.soc2.control_registry import (
    SOC2Category,
    SOC2ComplianceStatus,
    SOC2Control,
    SOC2ControlMapping,
    SOC2ControlRegistry,
    get_control_registry,
)
from app.services.soc2.mapper import (
    SOC2ControlMapper,
    get_control_mappings_for_incident,
)

__all__ = [
    "SOC2Category",
    "SOC2ComplianceStatus",
    "SOC2Control",
    "SOC2ControlMapping",
    "SOC2ControlRegistry",
    "SOC2ControlMapper",
    "get_control_registry",
    "get_control_mappings_for_incident",
]
