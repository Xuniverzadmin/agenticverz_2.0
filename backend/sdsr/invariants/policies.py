# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: L1 POLICIES Domain Invariants - Verify Policies domain contracts
# Reference: POLICY_DOMAIN_V2_ARCHITECTURE.md, PIN-370

"""
L1 POLICIES Domain Invariants

These invariants verify POLICIES domain semantic truth:
- Policy structure complete
- Status from valid enum
- Limit type from valid enum
- Scope from valid enum
- Governance subdomains (GOVERNANCE, LIMITS)

Usage:
    from backend.sdsr.invariants.policies import POLICIES_INVARIANTS

    for inv in POLICIES_INVARIANTS:
        result = inv["assert"](response, context)
"""

from typing import Any, Dict, List

# Valid policy statuses
VALID_POLICY_STATUSES = frozenset({
    "ACTIVE",
    "PENDING",
    "APPROVED",
    "REJECTED",
    "DEPRECATED",
    "DRAFT",
    "SUSPENDED",
})

# Valid proposal statuses
VALID_PROPOSAL_STATUSES = frozenset({
    "PENDING",
    "APPROVED",
    "REJECTED",
    "WITHDRAWN",
    "EXPIRED",
})

# Valid limit types
VALID_LIMIT_TYPES = frozenset({
    "COST_USD",
    "TOKENS_INPUT",
    "TOKENS_OUTPUT",
    "TOKENS_TOTAL",
    "RATE_RPM",
    "TIME_SECONDS",
    "CONCURRENT_RUNS",
})

# Valid policy scopes
VALID_POLICY_SCOPES = frozenset({
    "GLOBAL",
    "TENANT",
    "PROJECT",
    "AGENT",
    "PROVIDER",
    "MODEL",
})

# Valid violation outcomes
VALID_VIOLATION_OUTCOMES = frozenset({
    "BLOCKED",
    "WARNED",
    "LOGGED",
    "OVERRIDDEN",
})

# Required fields for policy rules
REQUIRED_POLICY_RULE_FIELDS = frozenset({
    "id",
    "status",
})

# Required fields for policy proposals
REQUIRED_PROPOSAL_FIELDS = frozenset({
    "id",
    "status",
})

# Required fields for limit violations
REQUIRED_VIOLATION_FIELDS = frozenset({
    "id",
    "limit_type",
})


def _get_items(response: Any) -> List[Dict[str, Any]]:
    """Extract items from response."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        if "items" in response:
            return response.get("items", [])
        if "rules" in response:
            return response.get("rules", [])
        if "proposals" in response:
            return response.get("proposals", [])
        if "violations" in response:
            return response.get("violations", [])
        if "policies" in response:
            return response.get("policies", [])
        if "data" in response:
            data = response["data"]
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return (
                    data.get("items", [])
                    or data.get("rules", [])
                    or data.get("proposals", [])
                    or data.get("violations", [])
                )
        # Single item response
        return [response]
    return []


# =============================================================================
# POLICIES DOMAIN INVARIANTS (L1) - GOVERNANCE
# =============================================================================


def inv_policy_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-001: Policies/rules have required fields (id, status)."""
    items = _get_items(response)

    if not items:
        if context.get("allow_empty_response", True):
            return True, "No items in response (allowed)"
        return False, "No items in response"

    missing_fields = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        for field in REQUIRED_POLICY_RULE_FIELDS:
            if field not in item or item[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, f"All {len(items)} policies have required fields"
    return False, f"Missing required fields: {missing_fields}"


def inv_policy_status_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-002: status is from valid enum."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_statuses = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status is not None:
            status_upper = status.upper() if isinstance(status, str) else str(status)
            # Allow both policy and proposal statuses
            all_valid = VALID_POLICY_STATUSES | VALID_PROPOSAL_STATUSES
            if status_upper not in all_valid:
                invalid_statuses.append((i, status))

    if not invalid_statuses:
        return True, "All statuses are valid"
    return False, f"Invalid statuses: {invalid_statuses}"


def inv_policy_scope_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-003: scope is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_scopes = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        scope = item.get("scope") or item.get("policy_scope")
        if scope is not None:
            scope_upper = scope.upper() if isinstance(scope, str) else str(scope)
            if scope_upper not in VALID_POLICY_SCOPES:
                invalid_scopes.append((i, scope))

    if not invalid_scopes:
        return True, "All scopes are valid"
    return False, f"Invalid scopes: {invalid_scopes}"


def inv_limit_type_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-004: limit_type is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_types = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        limit_type = item.get("limit_type")
        if limit_type is not None:
            limit_upper = limit_type.upper() if isinstance(limit_type, str) else str(limit_type)
            if limit_upper not in VALID_LIMIT_TYPES:
                invalid_types.append((i, limit_type))

    if not invalid_types:
        return True, "All limit_types are valid"
    return False, f"Invalid limit_types: {invalid_types}"


def inv_tenant_id_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-005: tenant_id is present."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_tenant = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if not item.get("tenant_id"):
            missing_tenant.append(i)

    if not missing_tenant:
        return True, "All items have tenant_id"
    # For GLOBAL policies, tenant_id may be optional
    if len(missing_tenant) < len(items):
        return True, f"{len(items) - len(missing_tenant)}/{len(items)} items have tenant_id"
    return False, f"Items missing tenant_id: {missing_tenant}"


def inv_proposal_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-006: Proposals have required fields (id, status)."""
    # Check if this is a proposals endpoint
    subdomain = context.get("subdomain", "")
    if "GOVERNANCE" not in subdomain and "proposal" not in str(context.get("endpoint", "")).lower():
        return True, "Not a proposals endpoint"

    items = _get_items(response)

    if not items:
        if context.get("allow_empty_response", True):
            return True, "No proposals in response (allowed)"
        return False, "No proposals in response"

    missing_fields = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        for field in REQUIRED_PROPOSAL_FIELDS:
            if field not in item or item[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, f"All {len(items)} proposals have required fields"
    return False, f"Missing required fields: {missing_fields}"


def inv_proposal_status_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-007: Proposal status is from valid enum."""
    # Check if this is a proposals endpoint
    if "proposal" not in str(context.get("endpoint", "")).lower():
        return True, "Not a proposals endpoint"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_statuses = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status is not None:
            status_upper = status.upper() if isinstance(status, str) else str(status)
            if status_upper not in VALID_PROPOSAL_STATUSES:
                invalid_statuses.append((i, status))

    if not invalid_statuses:
        return True, "All proposal statuses are valid"
    return False, f"Invalid proposal statuses: {invalid_statuses}"


# =============================================================================
# POLICIES DOMAIN INVARIANTS (L1) - LIMITS/VIOLATIONS
# =============================================================================


def inv_violation_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-008: Violations have required fields (id, limit_type)."""
    # Check if this is a violations endpoint
    if "violation" not in str(context.get("endpoint", "")).lower():
        return True, "Not a violations endpoint"

    items = _get_items(response)

    if not items:
        if context.get("allow_empty_response", True):
            return True, "No violations in response (allowed)"
        return False, "No violations in response"

    missing_fields = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        for field in REQUIRED_VIOLATION_FIELDS:
            if field not in item or item[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, f"All {len(items)} violations have required fields"
    return False, f"Missing required fields: {missing_fields}"


def inv_violation_outcome_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-009: Violation outcome is from valid enum (if present)."""
    # Check if this is a violations endpoint
    if "violation" not in str(context.get("endpoint", "")).lower():
        return True, "Not a violations endpoint"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_outcomes = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        outcome = item.get("outcome")
        if outcome is not None:
            outcome_upper = outcome.upper() if isinstance(outcome, str) else str(outcome)
            if outcome_upper not in VALID_VIOLATION_OUTCOMES:
                invalid_outcomes.append((i, outcome))

    if not invalid_outcomes:
        return True, "All violation outcomes are valid"
    return False, f"Invalid violation outcomes: {invalid_outcomes}"


def inv_threshold_values_numeric(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-010: Threshold values are numeric."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    non_numeric = []
    threshold_fields = ["threshold_value", "max_value", "limit_value", "current_value"]

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        for field in threshold_fields:
            value = item.get(field)
            if value is not None and not isinstance(value, (int, float)):
                non_numeric.append((i, field, type(value).__name__))

    if not non_numeric:
        return True, "All threshold values are numeric"
    return False, f"Non-numeric threshold values: {non_numeric}"


def inv_items_envelope_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-POL-011: Response uses items/rules/proposals envelope."""
    if not isinstance(response, dict):
        return False, "Response is not a dict"

    # Check for various envelope types
    envelope_fields = ["items", "rules", "proposals", "violations", "policies"]
    for field in envelope_fields:
        if field in response:
            items = response[field]
            if isinstance(items, list):
                return True, f"{field} envelope present with {len(items)} items"

    # Check nested in data
    if "data" in response and isinstance(response["data"], dict):
        for field in envelope_fields:
            if field in response["data"]:
                return True, f"data.{field} envelope present"

    return False, "No items envelope found"


# =============================================================================
# POLICIES INVARIANT REGISTRY (L1)
# =============================================================================

POLICIES_INVARIANTS: List[Dict[str, Any]] = [
    # GOVERNANCE invariants
    {
        "id": "INV-POL-001",
        "name": "policy_required_fields",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "GOVERNANCE",
        "description": "Policies/rules have required fields (id, status)",
        "assert": inv_policy_required_fields,
        "required": True,
    },
    {
        "id": "INV-POL-002",
        "name": "policy_status_valid",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "GOVERNANCE",
        "description": "status is from valid enum",
        "assert": inv_policy_status_valid,
        "required": True,
    },
    {
        "id": "INV-POL-003",
        "name": "policy_scope_valid",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "GOVERNANCE",
        "description": "scope is from valid enum (if present)",
        "assert": inv_policy_scope_valid,
        "required": False,
    },
    {
        "id": "INV-POL-004",
        "name": "limit_type_valid",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "LIMITS",
        "description": "limit_type is from valid enum (if present)",
        "assert": inv_limit_type_valid,
        "required": False,
    },
    {
        "id": "INV-POL-005",
        "name": "tenant_id_present",
        "layer": "L1",
        "domain": "POLICIES",
        "description": "tenant_id is present",
        "assert": inv_tenant_id_present,
        "required": False,  # GLOBAL policies may not have tenant_id
    },
    {
        "id": "INV-POL-006",
        "name": "proposal_required_fields",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "GOVERNANCE",
        "description": "Proposals have required fields (id, status)",
        "assert": inv_proposal_required_fields,
        "required": True,
    },
    {
        "id": "INV-POL-007",
        "name": "proposal_status_valid",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "GOVERNANCE",
        "description": "Proposal status is from valid enum",
        "assert": inv_proposal_status_valid,
        "required": True,
    },
    # LIMITS invariants
    {
        "id": "INV-POL-008",
        "name": "violation_required_fields",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "LIMITS",
        "description": "Violations have required fields (id, limit_type)",
        "assert": inv_violation_required_fields,
        "required": True,
    },
    {
        "id": "INV-POL-009",
        "name": "violation_outcome_valid",
        "layer": "L1",
        "domain": "POLICIES",
        "subdomain": "LIMITS",
        "description": "Violation outcome is from valid enum (if present)",
        "assert": inv_violation_outcome_valid,
        "required": False,
    },
    {
        "id": "INV-POL-010",
        "name": "threshold_values_numeric",
        "layer": "L1",
        "domain": "POLICIES",
        "description": "Threshold values are numeric",
        "assert": inv_threshold_values_numeric,
        "required": True,
    },
    {
        "id": "INV-POL-011",
        "name": "items_envelope_present",
        "layer": "L1",
        "domain": "POLICIES",
        "description": "Response uses items/rules/proposals envelope",
        "assert": inv_items_envelope_present,
        "required": True,
    },
]


# =============================================================================
# POLICIES DEFAULT QUERY PARAMS (Domain-Owned)
# =============================================================================

POLICIES_DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "GOVERNANCE": {
        "ACTIVE": {"status": "ACTIVE"},
        "DRAFTS": {"status": "DRAFT"},
        "PROPOSALS": {"limit": 50},
        "LIBRARY": {"limit": 100},
        "LESSONS": {"limit": 50},
    },
    "LIMITS": {
        "THRESHOLDS": {"limit": 100},
        "VIOLATIONS": {"limit": 50, "window": "24h"},
    },
}


def get_policies_invariants(required_only: bool = False, subdomain: str = None) -> List[Dict[str, Any]]:
    """Get L1 POLICIES domain invariants, optionally filtered by subdomain."""
    invariants = POLICIES_INVARIANTS

    if subdomain:
        invariants = [
            inv for inv in invariants
            if inv.get("subdomain") is None or inv.get("subdomain") == subdomain
        ]

    if required_only:
        invariants = [inv for inv in invariants if inv.get("required", True)]

    return invariants


def get_policies_invariant_ids() -> List[str]:
    """Get all L1 POLICIES domain invariant IDs."""
    return [inv["id"] for inv in POLICIES_INVARIANTS]


def get_policies_default_params(subdomain: str, topic: str) -> Dict[str, Any]:
    """Get default query parameters for POLICIES subdomain/topic."""
    subdomain_params = POLICIES_DEFAULT_PARAMS.get(subdomain, {})
    return subdomain_params.get(topic, {})
