# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: L1 ACTIVITY Domain Invariants - Verify Activity domain contracts
# Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md, PIN-370

"""
L1 ACTIVITY Domain Invariants

These invariants verify ACTIVITY domain semantic truth:
- policy_context present and valid
- evaluation_outcome from valid enum
- threshold fields populated
- run state consistency

Per ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md (lines 62-104):
Every Activity response that returns runs or signals MUST include policy_context.

Usage:
    from backend.sdsr.invariants.activity import ACTIVITY_INVARIANTS

    for inv in ACTIVITY_INVARIANTS:
        result = inv["assert"](response, context)
"""

from typing import Any, Dict, List

# Valid evaluation outcomes per ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md line 97-103
VALID_EVALUATION_OUTCOMES = frozenset({
    "OK",              # Run within all limits
    "NEAR_THRESHOLD",  # Run at 80%+ of limit
    "BREACH",          # Run exceeded limit
    "OVERRIDDEN",      # Human override applied
    "ADVISORY",        # System default, informational only
})

# Valid policy scopes
VALID_POLICY_SCOPES = frozenset({
    "TENANT",
    "PROJECT",
    "AGENT",
    "PROVIDER",
    "GLOBAL",
})

# Valid limit types
VALID_LIMIT_TYPES = frozenset({
    "COST_USD",
    "TOKENS_INPUT",
    "TOKENS_OUTPUT",
    "TOKENS_TOTAL",
    "RATE_RPM",
    "TIME_SECONDS",
})

# Valid threshold sources
VALID_THRESHOLD_SOURCES = frozenset({
    "TENANT_OVERRIDE",
    "PROJECT_OVERRIDE",
    "AGENT_OVERRIDE",
    "SYSTEM_DEFAULT",
})


def _get_items(response: Any) -> List[Dict[str, Any]]:
    """Extract items from response (handles both list and items envelope)."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        if "items" in response:
            return response.get("items", [])
        # Single item response
        return [response]
    return []


def _get_policy_context(item: Dict[str, Any]) -> Dict[str, Any] | None:
    """Extract policy_context from an item."""
    if not isinstance(item, dict):
        return None
    return item.get("policy_context")


# =============================================================================
# ACTIVITY DOMAIN INVARIANTS (L1)
# =============================================================================


def inv_policy_context_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-001: policy_context is present in response or all items."""
    items = _get_items(response)

    if not items:
        # No items - this may be valid for empty responses
        if context.get("allow_empty_response", True):
            return True, "No items in response (allowed)"
        return False, "No items in response"

    missing_count = 0
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            missing_count += 1

    if missing_count == 0:
        return True, f"policy_context present in all {len(items)} items"
    return False, f"policy_context missing in {missing_count}/{len(items)} items"


def inv_evaluation_outcome_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-002: evaluation_outcome is from valid enum."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_outcomes = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue  # Covered by INV-ACT-001

        outcome = pc.get("evaluation_outcome")
        if outcome is None:
            invalid_outcomes.append((i, "missing"))
        elif outcome not in VALID_EVALUATION_OUTCOMES:
            invalid_outcomes.append((i, outcome))

    if not invalid_outcomes:
        return True, "All evaluation_outcomes are valid"
    return False, f"Invalid evaluation_outcomes: {invalid_outcomes}"


def inv_policy_context_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-003: policy_context has required fields."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    required_fields = ["policy_id", "threshold_value", "evaluation_outcome"]
    missing_fields = []

    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue  # Covered by INV-ACT-001

        for field in required_fields:
            if field not in pc or pc[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, "All policy_context have required fields"
    return False, f"Missing required fields: {missing_fields}"


def inv_policy_scope_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-004: policy_scope is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_scopes = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue

        scope = pc.get("policy_scope")
        if scope is not None and scope not in VALID_POLICY_SCOPES:
            invalid_scopes.append((i, scope))

    if not invalid_scopes:
        return True, "All policy_scopes are valid"
    return False, f"Invalid policy_scopes: {invalid_scopes}"


def inv_limit_type_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-005: limit_type is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_types = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue

        limit_type = pc.get("limit_type")
        if limit_type is not None and limit_type not in VALID_LIMIT_TYPES:
            invalid_types.append((i, limit_type))

    if not invalid_types:
        return True, "All limit_types are valid"
    return False, f"Invalid limit_types: {invalid_types}"


def inv_threshold_source_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-006: threshold_source is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_sources = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue

        source = pc.get("threshold_source")
        if source is not None and source not in VALID_THRESHOLD_SOURCES:
            invalid_sources.append((i, source))

    if not invalid_sources:
        return True, "All threshold_sources are valid"
    return False, f"Invalid threshold_sources: {invalid_sources}"


def inv_actual_value_numeric(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-007: actual_value is numeric when present."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    non_numeric = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue

        actual = pc.get("actual_value")
        if actual is not None and not isinstance(actual, (int, float)):
            non_numeric.append((i, type(actual).__name__))

    if not non_numeric:
        return True, "All actual_values are numeric"
    return False, f"Non-numeric actual_values: {non_numeric}"


def inv_threshold_value_numeric(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-008: threshold_value is numeric when present."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    non_numeric = []
    for i, item in enumerate(items):
        pc = _get_policy_context(item)
        if pc is None:
            continue

        threshold = pc.get("threshold_value")
        if threshold is not None and not isinstance(threshold, (int, float)):
            non_numeric.append((i, type(threshold).__name__))

    if not non_numeric:
        return True, "All threshold_values are numeric"
    return False, f"Non-numeric threshold_values: {non_numeric}"


def inv_run_id_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-009: Run items have id field."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_id = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if "id" not in item and "run_id" not in item:
            missing_id.append(i)

    if not missing_id:
        return True, "All items have id"
    return False, f"Items missing id: {missing_id}"


def inv_run_status_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-ACT-010: Run items have status field."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_status = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if "status" not in item:
            missing_status.append(i)

    if not missing_status:
        return True, "All items have status"
    return False, f"Items missing status: {missing_status}"


# =============================================================================
# ACTIVITY INVARIANT REGISTRY (L1)
# =============================================================================

ACTIVITY_INVARIANTS: List[Dict[str, Any]] = [
    {
        "id": "INV-ACT-001",
        "name": "policy_context_present",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "policy_context is present in response or all items",
        "assert": inv_policy_context_present,
        "required": True,
        "reference": "ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md:62-82",
    },
    {
        "id": "INV-ACT-002",
        "name": "evaluation_outcome_valid",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "evaluation_outcome is from valid enum",
        "assert": inv_evaluation_outcome_valid,
        "required": True,
        "reference": "ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md:97-103",
    },
    {
        "id": "INV-ACT-003",
        "name": "policy_context_required_fields",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "policy_context has required fields (policy_id, threshold_value, evaluation_outcome)",
        "assert": inv_policy_context_required_fields,
        "required": True,
        "reference": "ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md:68-81",
    },
    {
        "id": "INV-ACT-004",
        "name": "policy_scope_valid",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "policy_scope is from valid enum",
        "assert": inv_policy_scope_valid,
        "required": False,
    },
    {
        "id": "INV-ACT-005",
        "name": "limit_type_valid",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "limit_type is from valid enum",
        "assert": inv_limit_type_valid,
        "required": False,
    },
    {
        "id": "INV-ACT-006",
        "name": "threshold_source_valid",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "threshold_source is from valid enum",
        "assert": inv_threshold_source_valid,
        "required": False,
    },
    {
        "id": "INV-ACT-007",
        "name": "actual_value_numeric",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "actual_value is numeric when present",
        "assert": inv_actual_value_numeric,
        "required": False,
    },
    {
        "id": "INV-ACT-008",
        "name": "threshold_value_numeric",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "threshold_value is numeric when present",
        "assert": inv_threshold_value_numeric,
        "required": False,
    },
    {
        "id": "INV-ACT-009",
        "name": "run_id_present",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "Run items have id field",
        "assert": inv_run_id_present,
        "required": True,
    },
    {
        "id": "INV-ACT-010",
        "name": "run_status_present",
        "layer": "L1",
        "domain": "ACTIVITY",
        "description": "Run items have status field",
        "assert": inv_run_status_present,
        "required": True,
    },
]


# =============================================================================
# ACTIVITY DEFAULT QUERY PARAMS (Domain-Owned)
# =============================================================================

ACTIVITY_DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "LLM_RUNS": {
        "LIVE": {"limit": 50},
        "COMPLETED": {"limit": 50},
        "SIGNALS": {"window": "24h"},
    },
}


def get_activity_invariants(required_only: bool = False) -> List[Dict[str, Any]]:
    """Get all L1 ACTIVITY domain invariants."""
    if required_only:
        return [inv for inv in ACTIVITY_INVARIANTS if inv.get("required", True)]
    return ACTIVITY_INVARIANTS


def get_activity_invariant_ids() -> List[str]:
    """Get all L1 ACTIVITY domain invariant IDs."""
    return [inv["id"] for inv in ACTIVITY_INVARIANTS]


def get_activity_default_params(subdomain: str, topic: str) -> Dict[str, Any]:
    """Get default query parameters for ACTIVITY subdomain/topic."""
    subdomain_params = ACTIVITY_DEFAULT_PARAMS.get(subdomain, {})
    return subdomain_params.get(topic, {})
