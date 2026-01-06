# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Authorization status endpoint for ops visibility
# Callers: Ops console, monitoring
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
Authorization Status API

Provides visibility into the M28/M7 authorization system state.

Endpoints:
    GET /internal/authz/status - Current authorization configuration
    GET /internal/authz/mappings - All M7→M28 mappings
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.auth.authorization_choke import (
    M7_LEGACY_RESOURCES,
    M28_NATIVE_RESOURCES,
    get_authz_phase,
    is_strict_mode,
)
from app.auth.authorization_metrics import (
    PROMETHEUS_AVAILABLE,
    get_alert_rules,
    get_dashboard_queries,
)
from app.auth.mappings import get_all_mappings

router = APIRouter(prefix="/internal/authz", tags=["Internal - Authorization"])


@router.get("/status")
async def get_authz_status() -> Dict[str, Any]:
    """
    Get current authorization system status.

    Returns phase, strict mode, and resource counts.
    """
    phase = get_authz_phase()
    strict = is_strict_mode()
    mappings = get_all_mappings()

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "phase": {
            "current": phase.value,
            "description": _get_phase_description(phase.value),
        },
        "strict_mode": {
            "enabled": strict,
            "description": "Hard-fail on any M7 fallback" if strict else "Allow M7 fallback with telemetry",
        },
        "resources": {
            "m28_native_count": len(M28_NATIVE_RESOURCES),
            "m28_native": sorted(M28_NATIVE_RESOURCES),
            "m7_legacy_count": len(M7_LEGACY_RESOURCES),
            "m7_legacy": sorted(M7_LEGACY_RESOURCES),
        },
        "mappings": {
            "total_count": len(mappings),
            "coverage": _calculate_coverage(mappings),
        },
        "environment": {
            "AUTHZ_PHASE": phase.value,
            "AUTHZ_STRICT_MODE": str(strict).lower(),
        },
    }


@router.get("/mappings")
async def get_authz_mappings() -> Dict[str, Any]:
    """
    Get all M7→M28 mappings for inspection.

    Returns the complete mapping table.
    """
    mappings = get_all_mappings()

    mapping_list = []
    for (m7_resource, m7_action), mapping in sorted(mappings.items()):
        mapping_list.append(
            {
                "m7_resource": mapping.m7_resource,
                "m7_action": mapping.m7_action,
                "m28_resource": mapping.m28_resource,
                "m28_action": mapping.m28_action,
                "m28_scope": mapping.m28_scope,
                "notes": mapping.notes,
            }
        )

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "count": len(mapping_list),
        "mappings": mapping_list,
    }


@router.get("/phase-info")
async def get_phase_info() -> Dict[str, Any]:
    """
    Get detailed information about authorization phases.

    Returns descriptions and migration guidance for each phase.
    """
    return {
        "phases": {
            "A": {
                "name": "Phase A - Read-Only Enforcement",
                "description": "M28 enforced on reads, M7 writes logged but allowed",
                "strict_mode_effect": "Hard-fail on any M7 usage",
                "migration_status": "Safe for gradual rollout",
            },
            "B": {
                "name": "Phase B - Write Path Enforcement",
                "description": "M28 enforced on reads and writes, unmapped M7 writes blocked",
                "strict_mode_effect": "Hard-fail on any M7 usage",
                "migration_status": "Requires all M7 patterns to be mapped",
            },
            "C": {
                "name": "Phase C - Full M28 Enforcement",
                "description": "All M7 usage blocked, M28 only",
                "strict_mode_effect": "Same as Phase C (M7 disabled)",
                "migration_status": "Final state before M7 removal",
            },
        },
        "current_phase": get_authz_phase().value,
        "strict_mode": is_strict_mode(),
        "transition_guidance": {
            "A_to_B": "Ensure all M7 write patterns are mapped before transitioning",
            "B_to_C": "Run with strict_mode=true to validate before final transition",
            "C_to_removal": "Remove M7 code after Phase C is stable",
        },
    }


@router.get("/metrics-info")
async def get_metrics_info() -> Dict[str, Any]:
    """
    Get metrics information for authorization monitoring.

    Returns dashboard queries and alert rules.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "metrics": {
            "authz_m7_fallback_total": {
                "type": "counter",
                "description": "Count of M7 to M28 authorization fallbacks",
                "labels": ["resource", "action", "decision", "phase"],
            },
            "authz_decision_total": {
                "type": "counter",
                "description": "Count of all authorization decisions",
                "labels": ["source", "resource", "action", "allowed", "phase"],
            },
            "authz_latency_seconds": {
                "type": "histogram",
                "description": "Authorization decision latency in seconds",
                "labels": ["source"],
            },
            "authz_phase_info": {
                "type": "gauge",
                "description": "Current authorization enforcement phase",
                "labels": ["phase"],
            },
            "authz_strict_mode": {
                "type": "gauge",
                "description": "Whether strict mode is enabled",
                "labels": [],
            },
        },
        "dashboard_queries": get_dashboard_queries(),
    }


@router.get("/alert-rules")
async def get_alert_rules_endpoint() -> Dict[str, Any]:
    """
    Get Prometheus alert rules for authorization monitoring.

    Returns YAML alert rule templates.
    """
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "format": "prometheus-alerting-rules",
        "rules": get_alert_rules(),
    }


def _get_phase_description(phase: str) -> str:
    """Get description for a phase."""
    descriptions = {
        "A": "Read-only enforcement: M28 on reads, log M7 writes",
        "B": "Write path enforcement: M28 on reads+writes, block unmapped M7",
        "C": "Full enforcement: M28 only, all M7 blocked",
    }
    return descriptions.get(phase, "Unknown phase")


def _calculate_coverage(mappings: dict) -> Dict[str, Any]:
    """Calculate mapping coverage statistics."""
    resources_mapped = set()
    actions_mapped = set()

    for (resource, action), _ in mappings.items():
        resources_mapped.add(resource)
        actions_mapped.add(action)

    return {
        "resources_mapped": len(resources_mapped),
        "unique_actions": len(actions_mapped),
        "resources": sorted(resources_mapped),
        "actions": sorted(actions_mapped),
    }
