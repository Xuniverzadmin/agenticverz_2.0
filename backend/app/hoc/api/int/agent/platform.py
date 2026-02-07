# Layer: L2 — Product APIs
# AUDIENCE: INTERNAL
# Product: founder-console (fops.agenticverz.com)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Platform health and eligibility endpoints (Founder-only)
# Callers: Founder Console (frontend)
# Allowed Imports: L4
# Forbidden Imports: L1, L5, L6
# Reference: PIN-284 (Platform Monitoring System)

"""
Platform Health API (L2)

Provides Founder-only endpoints for platform health monitoring.

Endpoints:
  GET /platform/health          - System health overview
  GET /platform/capabilities    - Capability eligibility list
  GET /platform/domains/{name}  - Domain health detail
  GET /platform/capabilities/{name} - Capability health detail

Audience: FOUNDER ONLY (Ops Console)
Security: Requires Founder authentication

PIN-284 Rule: Governance > Observability > UI

Refactored: DB execution moved to L6 driver (platform_driver.py)
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

# L4-provided registry dispatch for platform health queries (no direct L6 imports in L2)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_operation_registry,
    OperationContext,
)
from app.schemas.response import wrap_dict

router = APIRouter(prefix="/platform", tags=["platform"])


# =============================================================================
# NOTE: Lightweight Implementation
# =============================================================================
# All endpoints use efficient SQL queries via L6 driver for performance with
# remote databases. The full PlatformHealthService (L4) is available for batch
# processing or more detailed health analysis but is too slow for real-time
# API calls due to the number of queries required (~90 queries for full system
# health).


# =============================================================================
# RESPONSE MODELS (for OpenAPI documentation)
# =============================================================================


# Using dict responses for simplicity - full Pydantic models can be added later


# =============================================================================
# DOMAIN CAPABILITIES CONSTANT
# =============================================================================

DOMAIN_CAPABILITIES = {
    "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
    "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
    "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
    "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
    "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
    "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
}


def _get_all_capabilities() -> tuple[list[str], dict[str, str]]:
    """Build list of all capabilities and capability-to-domain mapping."""
    all_caps = []
    cap_to_domain = {}
    for domain, caps in DOMAIN_CAPABILITIES.items():
        all_caps.extend(caps)
        for cap in caps:
            cap_to_domain[cap] = domain
    return all_caps, cap_to_domain


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/health", response_model=None)
async def get_platform_health() -> Dict[str, Any]:
    """
    Get platform system health (lightweight version).

    Returns basic governance status without iterating all capabilities.
    For full capability health, use /platform/capabilities.

    Audience: Founder only
    """
    now = datetime.now(timezone.utc)
    registry = get_operation_registry()

    # Query BLCA status via registry dispatch
    blca_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={"method": "get_blca_status"},
    ))
    if not blca_result.success:
        raise HTTPException(status_code=500, detail=blca_result.error)
    blca_status = blca_result.data.get("status") or "UNKNOWN"

    # Query lifecycle coherence via registry dispatch
    coherence_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={"method": "get_lifecycle_coherence"},
    ))
    if not coherence_result.success:
        raise HTTPException(status_code=500, detail=coherence_result.error)
    lifecycle_coherence = coherence_result.data.get("coherence") or "UNKNOWN"

    # Determine overall state
    state = "HEALTHY"
    if blca_status == "BLOCKED":
        state = "BLOCKED"
    elif blca_status == "WARN" or lifecycle_coherence == "INCOHERENT":
        state = "DEGRADED"

    return wrap_dict({
        "state": state,
        "blca_status": blca_status,
        "lifecycle_coherence": lifecycle_coherence,
        "last_checked": now.isoformat(),
        "note": "Lightweight health check. Use /platform/capabilities for full capability status.",
    })


@router.get("/capabilities", response_model=None)
async def get_capabilities_eligibility() -> Dict[str, Any]:
    """
    Get capability eligibility list (lightweight version).

    Returns a batch summary of all capabilities using efficient queries.

    Audience: Founder only
    """
    now = datetime.now(timezone.utc)
    registry = get_operation_registry()

    # Query all blocked scopes via registry dispatch
    scopes_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={"method": "get_blocked_scopes"},
    ))
    if not scopes_result.success:
        raise HTTPException(status_code=500, detail=scopes_result.error)
    blocked_scopes = set(scopes_result.data.get("scopes", []))
    system_blocked = "SYSTEM" in blocked_scopes

    # Build capability list
    capabilities = []
    eligible_count = 0
    blocked_count = 0

    for domain, caps in DOMAIN_CAPABILITIES.items():
        for cap_name in caps:
            # Blocked if: system-wide block, capability-specific block, or KILLSWITCH_STATUS
            is_blocked = system_blocked or cap_name in blocked_scopes or cap_name == "KILLSWITCH_STATUS"

            capabilities.append(
                {
                    "name": cap_name,
                    "domain": domain,
                    "is_eligible": not is_blocked,
                    "state": "BLOCKED" if is_blocked else "HEALTHY",
                }
            )

            if is_blocked:
                blocked_count += 1
            else:
                eligible_count += 1

    return wrap_dict({
        "total": len(capabilities),
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "capabilities": capabilities,
        "checked_at": now.isoformat(),
    })


@router.get("/domains/{domain_name}", response_model=None)
async def get_domain_health(
    domain_name: str,
) -> Dict[str, Any]:
    """
    Get health for a specific domain (lightweight version).

    Args:
        domain_name: Domain name (LOGS, INCIDENTS, KEYS, POLICY, KILLSWITCH, ACTIVITY)

    Returns:
        Domain state with per-capability health summary

    Raises:
        404: Domain not found
    """
    domain = domain_name.upper()
    if domain not in DOMAIN_CAPABILITIES:
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain_name}' not found. Valid domains: {list(DOMAIN_CAPABILITIES.keys())}",
        )

    registry = get_operation_registry()

    # Query blocked scopes via registry dispatch
    scopes_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={"method": "get_blocked_scopes"},
    ))
    if not scopes_result.success:
        raise HTTPException(status_code=500, detail=scopes_result.error)
    blocked_scopes = set(scopes_result.data.get("scopes", []))
    system_blocked = "SYSTEM" in blocked_scopes

    # Build capability list for this domain
    capabilities = []
    healthy_count = 0
    blocked_count = 0

    for cap_name in DOMAIN_CAPABILITIES[domain]:
        is_blocked = system_blocked or cap_name in blocked_scopes or cap_name == "KILLSWITCH_STATUS"

        capabilities.append(
            {
                "name": cap_name,
                "is_eligible": not is_blocked,
                "state": "BLOCKED" if is_blocked else "HEALTHY",
            }
        )

        if is_blocked:
            blocked_count += 1
        else:
            healthy_count += 1

    # Domain state: BLOCKED if all caps blocked, DEGRADED if any blocked, else HEALTHY
    if blocked_count == len(capabilities):
        domain_state = "BLOCKED"
    elif blocked_count > 0:
        domain_state = "DEGRADED"
    else:
        domain_state = "HEALTHY"

    return wrap_dict({
        "domain": domain,
        "state": domain_state,
        "healthy_count": healthy_count,
        "blocked_count": blocked_count,
        "capabilities": capabilities,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/capabilities/{capability_name}", response_model=None)
async def get_capability_health(
    capability_name: str,
) -> Dict[str, Any]:
    """
    Get health for a specific capability (lightweight version).

    Args:
        capability_name: Capability name (e.g., LOGS_LIST, INCIDENTS_DETAIL)

    Returns:
        Capability state with eligibility and any blocking reasons

    Raises:
        404: Capability not found
    """
    all_capabilities, cap_to_domain = _get_all_capabilities()

    cap_name = capability_name.upper()
    if cap_name not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found. Valid capabilities: {sorted(all_capabilities)}",
        )

    registry = get_operation_registry()

    # Get blocking/warning signals via registry dispatch
    signals_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_capability_signals",
            "capability_name": cap_name,
            "limit": 5,
        },
    ))
    if not signals_result.success:
        raise HTTPException(status_code=500, detail=signals_result.error)
    signals = signals_result.data.get("signals", [])

    reasons = []
    is_blocked = False
    is_degraded = False

    for signal in signals:
        decision = signal["decision"]
        if decision == "BLOCKED":
            is_blocked = True
        elif decision == "WARN":
            is_degraded = True
        reasons.append(
            {
                "signal_type": signal["signal_type"],
                "decision": decision,
                "reason": signal["reason"] or f"Signal from {signal['recorded_by']}",
                "recorded_at": signal["recorded_at"].isoformat() if signal["recorded_at"] else None,
            }
        )

    # Check hardcoded disqualified
    if cap_name == "KILLSWITCH_STATUS":
        is_blocked = True
        reasons.append(
            {
                "signal_type": "QUALIFIER_STATUS",
                "decision": "DISQUALIFIED",
                "reason": "Hardcoded disqualification per CAPABILITY_LIFECYCLE.yaml",
                "recorded_at": None,
            }
        )

    # Determine state
    if is_blocked:
        state = "BLOCKED"
    elif is_degraded:
        state = "DEGRADED"
    else:
        state = "HEALTHY"

    return wrap_dict({
        "capability": cap_name,
        "domain": cap_to_domain[cap_name],
        "state": state,
        "is_eligible": not is_blocked,
        "reasons": reasons,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/eligibility/{capability_name}")
async def check_capability_eligibility(
    capability_name: str,
) -> Dict[str, Any]:
    """
    Quick eligibility check for a capability (lightweight version).

    Uses registry dispatch to check for blocking signals in a single query.

    Args:
        capability_name: Capability name

    Returns:
        {
            "capability": name,
            "is_eligible": bool,
            "state": "HEALTHY|DEGRADED|BLOCKED"
        }

    Raises:
        404: Capability not found
    """
    all_capabilities, _ = _get_all_capabilities()

    cap_name = capability_name.upper()
    if cap_name not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found",
        )

    registry = get_operation_registry()

    # Check for blocking signals via registry dispatch
    count_result = await registry.execute("platform.health", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "count_blocked_for_capability",
            "capability_name": cap_name,
        },
    ))
    if not count_result.success:
        raise HTTPException(status_code=500, detail=count_result.error)
    blocked_count = count_result.data.get("count", 0)
    is_blocked = blocked_count > 0

    # Check for hardcoded disqualified (KILLSWITCH_STATUS per CAPABILITY_LIFECYCLE.yaml)
    if cap_name == "KILLSWITCH_STATUS":
        is_blocked = True

    # Determine state
    state = "BLOCKED" if is_blocked else "HEALTHY"

    return wrap_dict({
        "capability": cap_name,
        "is_eligible": not is_blocked,
        "state": state,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    })
