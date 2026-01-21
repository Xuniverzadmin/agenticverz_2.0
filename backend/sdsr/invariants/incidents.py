# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: L1 INCIDENTS Domain Invariants - Verify Incidents domain contracts
# Reference: INCIDENTS_DOMAIN_MIGRATION_PLAN.md, PIN-370

"""
L1 INCIDENTS Domain Invariants

These invariants verify INCIDENTS domain semantic truth:
- Incident structure complete
- Severity from valid enum
- Status from valid enum
- Source run linkage present
- Topic-scoped response shape

Per INCIDENTS_DOMAIN_MIGRATION_PLAN.md:
- Topic-scoped endpoints: /incidents/active, /incidents/resolved, /incidents/historical
- Response shape: TopicScopedIncidentsResponse with items envelope

Usage:
    from backend.sdsr.invariants.incidents import INCIDENTS_INVARIANTS

    for inv in INCIDENTS_INVARIANTS:
        result = inv["assert"](response, context)
"""

from typing import Any, Dict, List

# Valid severity levels
VALID_SEVERITIES = frozenset({
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "INFO",
    "NONE",  # For success outcomes (PIN-407)
})

# Valid incident statuses
VALID_STATUSES = frozenset({
    "OPEN",
    "ACKNOWLEDGED",
    "INVESTIGATING",
    "CONTAINED",
    "RESOLVED",
    "CLOSED",
})

# Valid incident categories
VALID_CATEGORIES = frozenset({
    "EXECUTION_FAILURE",
    "EXECUTION_SUCCESS",  # PIN-407: Success as first-class data
    "POLICY_VIOLATION",
    "THRESHOLD_BREACH",
    "RATE_LIMIT",
    "BUDGET_EXCEEDED",
    "SYSTEM_ERROR",
    "TIMEOUT",
})

# Required fields for incident record
REQUIRED_INCIDENT_FIELDS = frozenset({
    "id",
    "severity",
    "status",
})

# Recommended fields
RECOMMENDED_INCIDENT_FIELDS = frozenset({
    "source_run_id",
    "tenant_id",
    "created_at",
    "category",
})


def _get_items(response: Any) -> List[Dict[str, Any]]:
    """Extract items from response (handles TopicScopedIncidentsResponse)."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        # TopicScopedIncidentsResponse uses 'items'
        if "items" in response:
            return response.get("items", [])
        # Legacy format uses 'incidents'
        if "incidents" in response:
            return response.get("incidents", [])
        # Data wrapper
        if "data" in response:
            data = response["data"]
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("items", data.get("incidents", []))
        # Single item response
        return [response]
    return []


# =============================================================================
# INCIDENTS DOMAIN INVARIANTS (L1)
# =============================================================================


def inv_incident_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-001: Incidents have required fields (id, severity, status)."""
    items = _get_items(response)

    if not items:
        if context.get("allow_empty_response", True):
            return True, "No items in response (allowed)"
        return False, "No items in response"

    missing_fields = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        for field in REQUIRED_INCIDENT_FIELDS:
            if field not in item or item[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, f"All {len(items)} incidents have required fields"
    return False, f"Missing required fields: {missing_fields}"


def inv_severity_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-002: severity is from valid enum."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_severities = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        severity = item.get("severity")
        if severity is not None:
            # Normalize to uppercase for comparison
            severity_upper = severity.upper() if isinstance(severity, str) else str(severity)
            if severity_upper not in VALID_SEVERITIES:
                invalid_severities.append((i, severity))

    if not invalid_severities:
        return True, "All severities are valid"
    return False, f"Invalid severities: {invalid_severities}"


def inv_status_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-003: status is from valid enum."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_statuses = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status is not None:
            # Normalize to uppercase for comparison
            status_upper = status.upper() if isinstance(status, str) else str(status)
            if status_upper not in VALID_STATUSES:
                invalid_statuses.append((i, status))

    if not invalid_statuses:
        return True, "All statuses are valid"
    return False, f"Invalid statuses: {invalid_statuses}"


def inv_source_run_linkage(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-004: source_run_id is present (incident linked to causing run)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_linkage = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        # Check for source_run_id or run_id
        if not item.get("source_run_id") and not item.get("run_id"):
            missing_linkage.append(i)

    if not missing_linkage:
        return True, "All incidents have source run linkage"
    # This is a warning, not a failure - some incidents may be system-generated
    if len(missing_linkage) < len(items):
        return True, f"{len(items) - len(missing_linkage)}/{len(items)} incidents have source run linkage"
    return False, f"No incidents have source run linkage"


def inv_category_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-005: category is from valid enum (if present)."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_categories = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        if category is not None:
            category_upper = category.upper() if isinstance(category, str) else str(category)
            if category_upper not in VALID_CATEGORIES:
                invalid_categories.append((i, category))

    if not invalid_categories:
        return True, "All categories are valid"
    return False, f"Invalid categories: {invalid_categories}"


def inv_tenant_id_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-006: tenant_id is present."""
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
        return True, "All incidents have tenant_id"
    return False, f"Incidents missing tenant_id: {missing_tenant}"


def inv_created_at_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-007: created_at timestamp is present."""
    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_timestamp = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        if not item.get("created_at"):
            missing_timestamp.append(i)

    if not missing_timestamp:
        return True, "All incidents have created_at"
    return False, f"Incidents missing created_at: {missing_timestamp}"


def inv_items_envelope_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-008: Response uses items envelope (TopicScopedIncidentsResponse)."""
    if not isinstance(response, dict):
        return False, "Response is not a dict"

    # Check for items envelope (new format)
    if "items" in response:
        items = response["items"]
        if isinstance(items, list):
            return True, f"items envelope present with {len(items)} items"
        return False, "items is not a list"

    # Check for data.items (nested)
    if "data" in response and isinstance(response["data"], dict):
        if "items" in response["data"]:
            return True, "data.items envelope present"

    # Legacy format - still valid but deprecated
    if "incidents" in response:
        return True, "Legacy incidents envelope present (deprecated)"

    return False, "No items envelope found"


def inv_pagination_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-INC-009: Pagination metadata present in response."""
    if not isinstance(response, dict):
        return True, "Single item response, pagination not applicable"

    # Check for pagination fields
    has_total = "total" in response
    has_has_more = "has_more" in response
    has_pagination = "pagination" in response

    if has_total or has_has_more or has_pagination:
        return True, "Pagination metadata present"

    # Check nested in data
    if "data" in response and isinstance(response["data"], dict):
        data = response["data"]
        if "total" in data or "has_more" in data or "pagination" in data:
            return True, "Pagination metadata present in data"

    return False, "No pagination metadata found"


# =============================================================================
# INCIDENTS INVARIANT REGISTRY (L1)
# =============================================================================

INCIDENTS_INVARIANTS: List[Dict[str, Any]] = [
    {
        "id": "INV-INC-001",
        "name": "incident_required_fields",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "Incidents have required fields (id, severity, status)",
        "assert": inv_incident_required_fields,
        "required": True,
    },
    {
        "id": "INV-INC-002",
        "name": "severity_valid",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "severity is from valid enum",
        "assert": inv_severity_valid,
        "required": True,
    },
    {
        "id": "INV-INC-003",
        "name": "status_valid",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "status is from valid enum",
        "assert": inv_status_valid,
        "required": True,
    },
    {
        "id": "INV-INC-004",
        "name": "source_run_linkage",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "source_run_id present (incident linked to causing run)",
        "assert": inv_source_run_linkage,
        "required": False,  # Some system incidents may not have source run
    },
    {
        "id": "INV-INC-005",
        "name": "category_valid",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "category is from valid enum (if present)",
        "assert": inv_category_valid,
        "required": False,
    },
    {
        "id": "INV-INC-006",
        "name": "tenant_id_present",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "tenant_id is present",
        "assert": inv_tenant_id_present,
        "required": True,
    },
    {
        "id": "INV-INC-007",
        "name": "created_at_present",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "created_at timestamp is present",
        "assert": inv_created_at_present,
        "required": True,
    },
    {
        "id": "INV-INC-008",
        "name": "items_envelope_present",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "Response uses items envelope (TopicScopedIncidentsResponse)",
        "assert": inv_items_envelope_present,
        "required": True,
        "reference": "INCIDENTS_DOMAIN_MIGRATION_PLAN.md:99-102",
    },
    {
        "id": "INV-INC-009",
        "name": "pagination_present",
        "layer": "L1",
        "domain": "INCIDENTS",
        "description": "Pagination metadata present in response",
        "assert": inv_pagination_present,
        "required": False,
    },
]


# =============================================================================
# INCIDENTS DEFAULT QUERY PARAMS (Domain-Owned)
# =============================================================================

INCIDENTS_DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "EVENTS": {
        "ACTIVE": {"limit": 50},
        "RESOLVED": {"limit": 50},
        "HISTORICAL": {"window": "7d", "limit": 100},
    },
}


def get_incidents_invariants(required_only: bool = False) -> List[Dict[str, Any]]:
    """Get all L1 INCIDENTS domain invariants."""
    if required_only:
        return [inv for inv in INCIDENTS_INVARIANTS if inv.get("required", True)]
    return INCIDENTS_INVARIANTS


def get_incidents_invariant_ids() -> List[str]:
    """Get all L1 INCIDENTS domain invariant IDs."""
    return [inv["id"] for inv in INCIDENTS_INVARIANTS]


def get_incidents_default_params(subdomain: str, topic: str) -> Dict[str, Any]:
    """Get default query parameters for INCIDENTS subdomain/topic."""
    subdomain_params = INCIDENTS_DEFAULT_PARAMS.get(subdomain, {})
    return subdomain_params.get(topic, {})
