# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: L0 Transport Invariants - Verify API reachability and basic response shape
# Reference: PIN-370, SDSR Layered Architecture

"""
L0 Transport Invariants (Synth-Owned)

These invariants verify transport-level correctness:
- Endpoint reachable
- Auth enforced
- Response exists and has basic structure
- Provenance envelope present (for interpretation panels)

These are DOMAIN-AGNOSTIC. They apply to ALL endpoints.

Usage:
    from backend.sdsr.invariants.transport import TRANSPORT_INVARIANTS

    for inv in TRANSPORT_INVARIANTS:
        result = inv["assert"](response, context)
"""

from typing import Any, Dict, List, Optional, Callable

# Type alias for invariant assertion function
# Takes (response_data, context) and returns (passed: bool, message: str)
InvariantFn = Callable[[Any, Dict[str, Any]], tuple[bool, str]]


def inv_response_exists(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-001: Response exists and is not empty."""
    if response is None:
        return False, "Response is None"
    if isinstance(response, dict) and len(response) == 0:
        return False, "Response is empty dict"
    if isinstance(response, list) and len(response) == 0:
        # Empty list may be valid (no items) - check context
        if context.get("allow_empty_list", True):
            return True, "Response is empty list (allowed)"
        return False, "Response is empty list"
    return True, "Response exists"


def inv_response_is_dict_or_list(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-002: Response is dict or list (valid JSON structure)."""
    if isinstance(response, (dict, list)):
        return True, f"Response is {type(response).__name__}"
    return False, f"Response is {type(response).__name__}, expected dict or list"


def inv_status_code_success(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-003: HTTP status code is 2xx."""
    status_code = context.get("status_code")
    if status_code is None:
        return False, "No status_code in context"
    if 200 <= status_code < 300:
        return True, f"Status code {status_code} is success"
    return False, f"Status code {status_code} is not success"


def inv_auth_not_rejected(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-004: Request was not rejected for auth reasons (401/403)."""
    status_code = context.get("status_code")
    if status_code is None:
        return False, "No status_code in context"
    if status_code == 401:
        return False, "401 Unauthorized - authentication failed"
    if status_code == 403:
        return False, "403 Forbidden - authorization failed"
    return True, "Auth not rejected"


def inv_no_server_error(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-005: No server error (5xx)."""
    status_code = context.get("status_code")
    if status_code is None:
        return False, "No status_code in context"
    if 500 <= status_code < 600:
        return False, f"Server error {status_code}"
    return True, "No server error"


def inv_response_time_acceptable(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-006: Response time is within acceptable bounds."""
    response_time_ms = context.get("response_time_ms")
    max_response_time_ms = context.get("max_response_time_ms", 30000)  # 30s default

    if response_time_ms is None:
        return True, "Response time not measured (skipped)"

    if response_time_ms <= max_response_time_ms:
        return True, f"Response time {response_time_ms}ms <= {max_response_time_ms}ms"
    return False, f"Response time {response_time_ms}ms > {max_response_time_ms}ms"


def inv_provenance_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-007: Provenance envelope present (for interpretation panels only)."""
    panel_class = context.get("panel_class")

    # Only required for interpretation panels
    if panel_class != "interpretation":
        return True, "Not an interpretation panel (provenance not required)"

    if not isinstance(response, dict):
        return False, "Response is not a dict, cannot check provenance"

    if "provenance" in response:
        provenance = response["provenance"]
        if isinstance(provenance, dict):
            return True, "Provenance envelope present"
        return False, "Provenance is not a dict"

    return False, "Provenance envelope missing (required for interpretation panels)"


def inv_items_envelope_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-L0-008: List endpoints use items envelope (if expected)."""
    expects_items = context.get("expects_items_envelope", False)

    if not expects_items:
        return True, "Items envelope not expected"

    if not isinstance(response, dict):
        return False, "Response is not a dict, cannot check items envelope"

    if "items" in response:
        if isinstance(response["items"], list):
            return True, f"Items envelope present with {len(response['items'])} items"
        return False, "Items is not a list"

    return False, "Items envelope missing (expected for this endpoint)"


# =============================================================================
# TRANSPORT INVARIANT REGISTRY (L0)
# =============================================================================

TRANSPORT_INVARIANTS: List[Dict[str, Any]] = [
    {
        "id": "INV-L0-001",
        "name": "response_exists",
        "layer": "L0",
        "description": "Response exists and is not empty",
        "assert": inv_response_exists,
        "required": True,
    },
    {
        "id": "INV-L0-002",
        "name": "response_is_dict_or_list",
        "layer": "L0",
        "description": "Response is valid JSON structure (dict or list)",
        "assert": inv_response_is_dict_or_list,
        "required": True,
    },
    {
        "id": "INV-L0-003",
        "name": "status_code_success",
        "layer": "L0",
        "description": "HTTP status code is 2xx",
        "assert": inv_status_code_success,
        "required": True,
    },
    {
        "id": "INV-L0-004",
        "name": "auth_not_rejected",
        "layer": "L0",
        "description": "Request not rejected for auth (401/403)",
        "assert": inv_auth_not_rejected,
        "required": True,
    },
    {
        "id": "INV-L0-005",
        "name": "no_server_error",
        "layer": "L0",
        "description": "No server error (5xx)",
        "assert": inv_no_server_error,
        "required": True,
    },
    {
        "id": "INV-L0-006",
        "name": "response_time_acceptable",
        "layer": "L0",
        "description": "Response time within bounds",
        "assert": inv_response_time_acceptable,
        "required": False,  # Optional - may not always be measured
    },
    {
        "id": "INV-L0-007",
        "name": "provenance_present",
        "layer": "L0",
        "description": "Provenance envelope present (interpretation panels)",
        "assert": inv_provenance_present,
        "required": False,  # Only for interpretation panels
    },
    {
        "id": "INV-L0-008",
        "name": "items_envelope_present",
        "layer": "L0",
        "description": "Items envelope present for list endpoints",
        "assert": inv_items_envelope_present,
        "required": False,  # Only for list endpoints
    },
]


def get_transport_invariants(required_only: bool = False) -> List[Dict[str, Any]]:
    """Get all L0 transport invariants."""
    if required_only:
        return [inv for inv in TRANSPORT_INVARIANTS if inv.get("required", True)]
    return TRANSPORT_INVARIANTS


def get_transport_invariant_ids() -> List[str]:
    """Get all L0 transport invariant IDs."""
    return [inv["id"] for inv in TRANSPORT_INVARIANTS]
