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

# L3 imports (allowed)
from app.adapters.platform_eligibility_adapter import (
    PlatformEligibilityAdapter,
    get_platform_eligibility_adapter,
)

# L6 imports (allowed)
from app.db import get_session

# L4 imports (allowed)
from app.services.platform.platform_health_service import (
    PlatformHealthService,
    get_platform_health_service,
)

router = APIRouter(prefix="/platform", tags=["platform"])


# =============================================================================
# DEPENDENCIES
# =============================================================================


def get_health_service(session: Session = Depends(get_session)) -> PlatformHealthService:
    """Get PlatformHealthService instance with session."""
    return get_platform_health_service(session)


def get_adapter() -> PlatformEligibilityAdapter:
    """Get PlatformEligibilityAdapter instance."""
    return get_platform_eligibility_adapter()


# =============================================================================
# RESPONSE MODELS (for OpenAPI documentation)
# =============================================================================


# Using dict responses for simplicity - full Pydantic models can be added later


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/health", response_model=None)
async def get_platform_health(
    health_service: PlatformHealthService = Depends(get_health_service),
    adapter: PlatformEligibilityAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get platform system health.

    Returns:
        SystemHealthView with:
        - Overall system state (HEALTHY, DEGRADED, BLOCKED)
        - BLCA status
        - Lifecycle coherence
        - Per-domain health summaries
        - Aggregate capability stats

    Audience: Founder only
    """
    system_health = health_service.get_system_health()
    view = adapter.system_to_view(system_health)

    # Convert dataclass to dict for JSON response
    return _dataclass_to_dict(view)


@router.get("/capabilities", response_model=None)
async def get_capabilities_eligibility(
    health_service: PlatformHealthService = Depends(get_health_service),
    adapter: PlatformEligibilityAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get capability eligibility list.

    Returns:
        PlatformEligibilityResponse with:
        - Total capability count
        - Eligible count
        - Blocked count
        - Per-capability eligibility status

    Audience: Founder only
    """
    response = adapter.to_eligibility_response(health_service)

    return _dataclass_to_dict(response)


@router.get("/domains/{domain_name}", response_model=None)
async def get_domain_health(
    domain_name: str,
    health_service: PlatformHealthService = Depends(get_health_service),
    adapter: PlatformEligibilityAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get health for a specific domain.

    Args:
        domain_name: Domain name (LOGS, INCIDENTS, KEYS, POLICY, KILLSWITCH, ACTIVITY)

    Returns:
        DomainHealthView with:
        - Domain state
        - Per-capability health
        - Healthy/degraded/blocked counts

    Raises:
        404: Domain not found
    """
    # Validate domain name
    valid_domains = ["LOGS", "INCIDENTS", "KEYS", "POLICY", "KILLSWITCH", "ACTIVITY"]
    if domain_name.upper() not in valid_domains:
        raise HTTPException(
            status_code=404,
            detail=f"Domain '{domain_name}' not found. Valid domains: {valid_domains}",
        )

    domain_health = health_service.get_domain_health(domain_name.upper())
    view = adapter.domain_to_view(domain_health)

    return _dataclass_to_dict(view)


@router.get("/capabilities/{capability_name}", response_model=None)
async def get_capability_health(
    capability_name: str,
    health_service: PlatformHealthService = Depends(get_health_service),
    adapter: PlatformEligibilityAdapter = Depends(get_adapter),
) -> Dict[str, Any]:
    """
    Get health for a specific capability.

    Args:
        capability_name: Capability name (e.g., LOGS_LIST, INCIDENTS_DETAIL)

    Returns:
        CapabilityHealthView with:
        - Capability state
        - Eligibility status
        - Qualifier and lifecycle status
        - Health reasons

    Raises:
        404: Capability not found
    """
    # Get all valid capabilities
    all_capabilities = []
    for caps in health_service.DOMAIN_CAPABILITIES.values():
        all_capabilities.extend(caps)

    if capability_name.upper() not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found. Valid capabilities: {sorted(all_capabilities)}",
        )

    cap_health = health_service.get_capability_health(capability_name.upper())
    view = adapter.capability_to_view(cap_health)

    return _dataclass_to_dict(view)


@router.get("/eligibility/{capability_name}")
async def check_capability_eligibility(
    capability_name: str,
    health_service: PlatformHealthService = Depends(get_health_service),
) -> Dict[str, Any]:
    """
    Quick eligibility check for a capability.

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
    # Get all valid capabilities
    all_capabilities = []
    for caps in health_service.DOMAIN_CAPABILITIES.values():
        all_capabilities.extend(caps)

    if capability_name.upper() not in all_capabilities:
        raise HTTPException(
            status_code=404,
            detail=f"Capability '{capability_name}' not found",
        )

    cap_health = health_service.get_capability_health(capability_name.upper())

    return {
        "capability": capability_name.upper(),
        "is_eligible": cap_health.is_eligible(),
        "state": cap_health.state.value,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert a dataclass to a dictionary, handling nested dataclasses.

    This is a simple recursive conversion for JSON serialization.
    """
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = _dataclass_to_dict(value)
        return result
    elif isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _dataclass_to_dict(value) for key, value in obj.items()}
    else:
        return obj
