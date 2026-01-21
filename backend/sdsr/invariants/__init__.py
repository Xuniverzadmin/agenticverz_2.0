# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: SDSR Invariant Loader API - Unified interface for domain invariants
# Reference: PIN-370, SDSR Layered Architecture

"""
SDSR Invariant System - Domain-Owned Validation

This module provides a unified API for loading and executing SDSR invariants.

ARCHITECTURE (3-Layer Model):
    L0 — Transport (synth-owned)     → Endpoint reachable, auth works, response exists
    L1 — Domain (domain-owned)       → policy_context, EvidenceMetadata, etc.
    L2 — Capability (optional)       → Specific business rules

DOMAIN AUTHORITY:
    - Each domain owns its invariants
    - Synth ATTACHES invariants, does not INVENT them
    - Invariants are callable functions, not strings
    - Pydantic models for structure validation

Usage:
    from backend.sdsr.invariants import load_domain_invariants, get_invariant_by_id

    # Get all invariants for a domain
    invariants = load_domain_invariants("ACTIVITY")

    # Get a specific invariant by ID
    inv = get_invariant_by_id("INV-ACT-001")
    passed, message = inv["assert"](response, context)

    # Execute all invariants for a domain
    results = execute_invariants(response, "ACTIVITY", context)
"""

from typing import Any, Callable, Dict, List, Optional

# Import domain-specific invariants
from .transport import (
    TRANSPORT_INVARIANTS,
    get_transport_invariants,
    get_transport_invariant_ids,
)
from .activity import (
    ACTIVITY_INVARIANTS,
    get_activity_invariants,
    get_activity_invariant_ids,
    get_activity_default_params,
)
from .logs import (
    LOGS_INVARIANTS,
    get_logs_invariants,
    get_logs_invariant_ids,
    get_logs_default_params,
)
from .incidents import (
    INCIDENTS_INVARIANTS,
    get_incidents_invariants,
    get_incidents_invariant_ids,
    get_incidents_default_params,
)
from .policies import (
    POLICIES_INVARIANTS,
    get_policies_invariants,
    get_policies_invariant_ids,
    get_policies_default_params,
)

# Type alias for invariant assertion function
InvariantFn = Callable[[Any, Dict[str, Any]], tuple[bool, str]]


# =============================================================================
# DOMAIN REGISTRY
# =============================================================================

DOMAIN_INVARIANTS: Dict[str, List[Dict[str, Any]]] = {
    "TRANSPORT": TRANSPORT_INVARIANTS,  # L0
    "ACTIVITY": ACTIVITY_INVARIANTS,    # L1
    "LOGS": LOGS_INVARIANTS,            # L1
    "INCIDENTS": INCIDENTS_INVARIANTS,  # L1
    "POLICIES": POLICIES_INVARIANTS,    # L1
}

DOMAIN_GETTERS: Dict[str, Callable] = {
    "TRANSPORT": get_transport_invariants,
    "ACTIVITY": get_activity_invariants,
    "LOGS": get_logs_invariants,
    "INCIDENTS": get_incidents_invariants,
    "POLICIES": get_policies_invariants,
}

DOMAIN_DEFAULT_PARAMS: Dict[str, Callable] = {
    "ACTIVITY": get_activity_default_params,
    "LOGS": get_logs_default_params,
    "INCIDENTS": get_incidents_default_params,
    "POLICIES": get_policies_default_params,
}


# =============================================================================
# INVARIANT INDEX (For ID-based lookup)
# =============================================================================

_INVARIANT_INDEX: Dict[str, Dict[str, Any]] = {}


def _build_invariant_index() -> None:
    """Build global invariant index for ID-based lookup."""
    global _INVARIANT_INDEX
    _INVARIANT_INDEX = {}

    for domain, invariants in DOMAIN_INVARIANTS.items():
        for inv in invariants:
            inv_id = inv["id"]
            if inv_id in _INVARIANT_INDEX:
                raise ValueError(f"Duplicate invariant ID: {inv_id}")
            _INVARIANT_INDEX[inv_id] = inv


# Build index on module load
_build_invariant_index()


# =============================================================================
# PUBLIC API
# =============================================================================


def load_domain_invariants(
    domain: str,
    required_only: bool = False,
    include_transport: bool = True,
) -> List[Dict[str, Any]]:
    """
    Load all invariants for a domain.

    Args:
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES)
        required_only: If True, return only required invariants
        include_transport: If True, include L0 transport invariants

    Returns:
        List of invariant definitions with callable 'assert' functions
    """
    domain_upper = domain.upper()

    if domain_upper not in DOMAIN_INVARIANTS:
        raise ValueError(f"Unknown domain: {domain}. Valid: {list(DOMAIN_INVARIANTS.keys())}")

    invariants = []

    # Add L0 transport invariants if requested
    if include_transport:
        invariants.extend(get_transport_invariants(required_only=required_only))

    # Add domain-specific invariants
    getter = DOMAIN_GETTERS.get(domain_upper)
    if getter:
        domain_invs = getter(required_only=required_only) if 'required_only' in getter.__code__.co_varnames else getter()
        invariants.extend(domain_invs)

    return invariants


def get_invariant_by_id(invariant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific invariant by its ID.

    Args:
        invariant_id: Invariant ID (e.g., "INV-ACT-001", "INV-L0-001")

    Returns:
        Invariant definition with callable 'assert' function, or None if not found
    """
    return _INVARIANT_INDEX.get(invariant_id)


def get_invariant_ids_for_domain(domain: str) -> List[str]:
    """
    Get all invariant IDs for a domain.

    Args:
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES, TRANSPORT)

    Returns:
        List of invariant IDs
    """
    domain_upper = domain.upper()

    if domain_upper == "TRANSPORT":
        return get_transport_invariant_ids()

    id_getters = {
        "ACTIVITY": get_activity_invariant_ids,
        "LOGS": get_logs_invariant_ids,
        "INCIDENTS": get_incidents_invariant_ids,
        "POLICIES": get_policies_invariant_ids,
    }

    getter = id_getters.get(domain_upper)
    if getter:
        return getter()

    raise ValueError(f"Unknown domain: {domain}")


def get_default_params(domain: str, subdomain: str = "", topic: str = "") -> Dict[str, Any]:
    """
    Get default query parameters for a domain endpoint.

    Args:
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES)
        subdomain: Subdomain name (e.g., "LLM_RUNS", "RECORDS", "EVENTS", "GOVERNANCE")
        topic: Topic name (e.g., "LIVE", "COMPLETED", "ACTIVE")

    Returns:
        Default query parameters dict
    """
    domain_upper = domain.upper()
    param_getter = DOMAIN_DEFAULT_PARAMS.get(domain_upper)

    if param_getter:
        return param_getter(subdomain, topic)

    return {}


# =============================================================================
# INVARIANT EXECUTION
# =============================================================================


def execute_invariant(
    invariant: Dict[str, Any],
    response: Any,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a single invariant against a response.

    Args:
        invariant: Invariant definition with 'assert' callable
        response: API response data
        context: Execution context (status_code, panel_class, etc.)

    Returns:
        Result dict with: id, name, passed, message, required
    """
    inv_id = invariant["id"]
    inv_name = invariant["name"]
    inv_fn = invariant["assert"]
    required = invariant.get("required", True)

    try:
        passed, message = inv_fn(response, context)
        return {
            "id": inv_id,
            "name": inv_name,
            "passed": passed,
            "message": message,
            "required": required,
            "error": None,
        }
    except Exception as e:
        return {
            "id": inv_id,
            "name": inv_name,
            "passed": False,
            "message": f"Invariant execution error: {e}",
            "required": required,
            "error": str(e),
        }


def execute_invariants(
    response: Any,
    domain: str,
    context: Dict[str, Any],
    required_only: bool = False,
    include_transport: bool = True,
) -> Dict[str, Any]:
    """
    Execute all invariants for a domain against a response.

    Args:
        response: API response data
        domain: Domain name (ACTIVITY, LOGS, INCIDENTS, POLICIES)
        context: Execution context (status_code, panel_class, endpoint, etc.)
        required_only: If True, only execute required invariants
        include_transport: If True, include L0 transport invariants

    Returns:
        Results dict with:
        - domain: Domain name
        - total: Total invariants executed
        - passed: Number passed
        - failed: Number failed
        - required_passed: Number of required invariants that passed
        - required_failed: Number of required invariants that failed
        - all_required_pass: True if all required invariants passed
        - results: List of individual invariant results
    """
    invariants = load_domain_invariants(
        domain,
        required_only=required_only,
        include_transport=include_transport,
    )

    results = []
    passed_count = 0
    failed_count = 0
    required_passed = 0
    required_failed = 0

    for inv in invariants:
        result = execute_invariant(inv, response, context)
        results.append(result)

        if result["passed"]:
            passed_count += 1
            if result["required"]:
                required_passed += 1
        else:
            failed_count += 1
            if result["required"]:
                required_failed += 1

    return {
        "domain": domain,
        "total": len(invariants),
        "passed": passed_count,
        "failed": failed_count,
        "required_passed": required_passed,
        "required_failed": required_failed,
        "all_required_pass": required_failed == 0,
        "results": results,
    }


def check_observed_promotion_eligible(
    response: Any,
    domain: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Check if a capability is eligible for OBSERVED promotion.

    PROMOTION RULE (MANDATORY):
    A capability may NOT move to OBSERVED unless:
    - All L0 (transport) invariants pass
    - At least ONE L1 (domain) invariant passes

    Args:
        response: API response data
        domain: Domain name
        context: Execution context

    Returns:
        Eligibility result with:
        - eligible: True if promotion is allowed
        - l0_pass: All L0 invariants passed
        - l1_pass_count: Number of L1 invariants that passed
        - reason: Human-readable explanation
    """
    # Execute L0 transport invariants
    l0_invariants = get_transport_invariants(required_only=True)
    l0_results = []
    l0_all_pass = True

    for inv in l0_invariants:
        result = execute_invariant(inv, response, context)
        l0_results.append(result)
        if not result["passed"]:
            l0_all_pass = False

    # Execute L1 domain invariants (required only)
    domain_invariants = load_domain_invariants(domain, required_only=True, include_transport=False)
    l1_results = []
    l1_pass_count = 0

    for inv in domain_invariants:
        result = execute_invariant(inv, response, context)
        l1_results.append(result)
        if result["passed"]:
            l1_pass_count += 1

    # Determine eligibility
    l1_at_least_one = l1_pass_count >= 1
    eligible = l0_all_pass and l1_at_least_one

    # Build reason
    if eligible:
        reason = f"Eligible: L0 PASS, L1 {l1_pass_count} invariants passed"
    elif not l0_all_pass:
        failed_l0 = [r["id"] for r in l0_results if not r["passed"]]
        reason = f"Not eligible: L0 FAILED ({failed_l0})"
    else:
        reason = f"Not eligible: No L1 invariants passed (need ≥1)"

    return {
        "eligible": eligible,
        "l0_pass": l0_all_pass,
        "l1_pass_count": l1_pass_count,
        "l1_total": len(domain_invariants),
        "reason": reason,
        "l0_results": l0_results,
        "l1_results": l1_results,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main API
    "load_domain_invariants",
    "get_invariant_by_id",
    "get_invariant_ids_for_domain",
    "get_default_params",
    "execute_invariant",
    "execute_invariants",
    "check_observed_promotion_eligible",
    # Domain registries (for direct access)
    "DOMAIN_INVARIANTS",
    "TRANSPORT_INVARIANTS",
    "ACTIVITY_INVARIANTS",
    "LOGS_INVARIANTS",
    "INCIDENTS_INVARIANTS",
    "POLICIES_INVARIANTS",
]
