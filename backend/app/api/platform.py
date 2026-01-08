# Layer: L2 — Product APIs
# Product: founder-console (fops.agenticverz.com)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Platform health and eligibility endpoints (Founder-only)
# Callers: Founder Console (frontend)
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
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
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

# L6 imports (allowed)
from app.db import get_session

router = APIRouter(prefix="/platform", tags=["platform"])


# =============================================================================
# NOTE: Lightweight Implementation
# =============================================================================
# All endpoints use direct SQL queries for performance with remote databases.
# The full PlatformHealthService (L4) is available for batch processing or
# more detailed health analysis but is too slow for real-time API calls
# due to the number of queries required (~90 queries for full system health).


# =============================================================================
# RESPONSE MODELS (for OpenAPI documentation)
# =============================================================================


# Using dict responses for simplicity - full Pydantic models can be added later


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/health", response_model=None)
def get_platform_health(
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Get platform system health (lightweight version).

    Returns basic governance status without iterating all capabilities.
    For full capability health, use /platform/capabilities.

    Audience: Founder only
    """
    from sqlalchemy import text

    now = datetime.now(timezone.utc)

    # Single query to get BLCA status
    blca_result = session.execute(
        text("""
            SELECT decision FROM governance_signals
            WHERE signal_type = 'BLCA_STATUS'
            AND scope = 'SYSTEM'
            AND superseded_at IS NULL
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
    ).fetchone()
    blca_status = blca_result[0] if blca_result else "UNKNOWN"

    # Single query to get lifecycle coherence
    lifecycle_result = session.execute(
        text("""
            SELECT decision FROM governance_signals
            WHERE signal_type = 'LIFECYCLE_QUALIFIER_COHERENCE'
            AND scope = 'SYSTEM'
            AND superseded_at IS NULL
            ORDER BY recorded_at DESC
            LIMIT 1
        """)
    ).fetchone()
    lifecycle_coherence = lifecycle_result[0] if lifecycle_result else "UNKNOWN"

    # Determine overall state
    state = "HEALTHY"
    if blca_status == "BLOCKED":
        state = "BLOCKED"
    elif blca_status == "WARN" or lifecycle_coherence == "INCOHERENT":
        state = "DEGRADED"

    return {
        "state": state,
        "blca_status": blca_status,
        "lifecycle_coherence": lifecycle_coherence,
        "last_checked": now.isoformat(),
        "note": "Lightweight health check. Use /platform/capabilities for full capability status.",
    }


@router.get("/capabilities", response_model=None)
def get_capabilities_eligibility(
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Get capability eligibility list (lightweight version).

    Returns a batch summary of all capabilities using efficient queries.

    Audience: Founder only
    """
    from sqlalchemy import text

    now = datetime.now(timezone.utc)

    # All capabilities
    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    # Single query to get all blocked scopes
    blocked_result = session.execute(
        text("""
            SELECT DISTINCT scope FROM governance_signals
            WHERE decision = 'BLOCKED'
            AND superseded_at IS NULL
            AND (expires_at IS NULL OR expires_at > NOW())
        """)
    ).fetchall()

    blocked_scopes = {row[0] for row in blocked_result}
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

    return {
        "total": len(capabilities),
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "capabilities": capabilities,
        "checked_at": now.isoformat(),
    }


@router.get("/domains/{domain_name}", response_model=None)
def get_domain_health(
    domain_name: str,
    session: Session = Depends(get_session),
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
    from sqlalchemy import text

    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    domain = domain_name.upper()
    if domain not in DOMAIN_CAPABILITIES:
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain_name}' not found. Valid domains: {list(DOMAIN_CAPABILITIES.keys())}",
        )

    # Single query to get blocked scopes
    blocked_result = session.execute(
        text("""
            SELECT DISTINCT scope FROM governance_signals
            WHERE decision = 'BLOCKED'
            AND superseded_at IS NULL
            AND (expires_at IS NULL OR expires_at > NOW())
        """)
    ).fetchall()

    blocked_scopes = {row[0] for row in blocked_result}
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

    return {
        "domain": domain,
        "state": domain_state,
        "healthy_count": healthy_count,
        "blocked_count": blocked_count,
        "capabilities": capabilities,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/capabilities/{capability_name}", response_model=None)
def get_capability_health(
    capability_name: str,
    session: Session = Depends(get_session),
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
    from sqlalchemy import text

    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    all_capabilities = []
    cap_to_domain = {}
    for domain, caps in DOMAIN_CAPABILITIES.items():
        all_capabilities.extend(caps)
        for cap in caps:
            cap_to_domain[cap] = domain

    cap_name = capability_name.upper()
    if cap_name not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found. Valid capabilities: {sorted(all_capabilities)}",
        )

    # Get any blocking/warning signals for this capability
    signals_result = session.execute(
        text("""
            SELECT signal_type, decision, reason, recorded_by, recorded_at
            FROM governance_signals
            WHERE (scope = :cap_name OR scope = 'SYSTEM')
            AND decision IN ('BLOCKED', 'WARN')
            AND superseded_at IS NULL
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY recorded_at DESC
            LIMIT 5
        """),
        {"cap_name": cap_name},
    ).fetchall()

    reasons = []
    is_blocked = False
    is_degraded = False

    for row in signals_result:
        signal_type, decision, reason, recorded_by, recorded_at = row
        if decision == "BLOCKED":
            is_blocked = True
        elif decision == "WARN":
            is_degraded = True
        reasons.append(
            {
                "signal_type": signal_type,
                "decision": decision,
                "reason": reason or f"Signal from {recorded_by}",
                "recorded_at": recorded_at.isoformat() if recorded_at else None,
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

    return {
        "capability": cap_name,
        "domain": cap_to_domain[cap_name],
        "state": state,
        "is_eligible": not is_blocked,
        "reasons": reasons,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/eligibility/{capability_name}")
def check_capability_eligibility(
    capability_name: str,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Quick eligibility check for a capability (lightweight version).

    Uses direct SQL to check for blocking signals in a single query.

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
    from sqlalchemy import text

    # Valid capabilities
    DOMAIN_CAPABILITIES = {
        "LOGS": ["LOGS_LIST", "LOGS_DETAIL", "LOGS_EXPORT"],
        "INCIDENTS": ["INCIDENTS_LIST", "INCIDENTS_DETAIL", "INCIDENT_ACKNOWLEDGE", "INCIDENT_RESOLVE"],
        "KEYS": ["KEYS_LIST", "KEYS_FREEZE", "KEYS_UNFREEZE"],
        "POLICY": ["POLICY_CONSTRAINTS", "GUARDRAIL_DETAIL"],
        "KILLSWITCH": ["KILLSWITCH_STATUS", "KILLSWITCH_ACTIVATE", "KILLSWITCH_DEACTIVATE"],
        "ACTIVITY": ["ACTIVITY_LIST", "ACTIVITY_DETAIL"],
    }

    all_capabilities = []
    for caps in DOMAIN_CAPABILITIES.values():
        all_capabilities.extend(caps)

    cap_name = capability_name.upper()
    if cap_name not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found",
        )

    # Single query to check for blocking signals
    blocked_result = session.execute(
        text("""
            SELECT COUNT(*) FROM governance_signals
            WHERE (scope = :cap_name OR scope = 'SYSTEM')
            AND decision = 'BLOCKED'
            AND superseded_at IS NULL
            AND (expires_at IS NULL OR expires_at > NOW())
        """),
        {"cap_name": cap_name},
    ).scalar()

    is_blocked = (blocked_result or 0) > 0

    # Check for hardcoded disqualified (KILLSWITCH_STATUS per CAPABILITY_LIFECYCLE.yaml)
    if cap_name == "KILLSWITCH_STATUS":
        is_blocked = True

    # Determine state
    state = "BLOCKED" if is_blocked else "HEALTHY"

    return {
        "capability": cap_name,
        "is_eligible": not is_blocked,
        "state": state,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
