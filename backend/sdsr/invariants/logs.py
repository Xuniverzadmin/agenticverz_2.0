# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: SDSR validation
#   Execution: sync
# Role: L1 LOGS Domain Invariants - Verify Logs domain contracts
# Reference: LOGS_DOMAIN_V2_ARCHITECTURE.md, PIN-370

"""
L1 LOGS Domain Invariants

These invariants verify LOGS domain semantic truth:
- EvidenceMetadata present and valid
- Required metadata fields populated
- Source domain from valid enum
- Immutable flag set correctly

Per LOGS_DOMAIN_V2_ARCHITECTURE.md (lines 84-119):
All LOGS responses MUST include EvidenceMetadata.

Usage:
    from backend.sdsr.invariants.logs import LOGS_INVARIANTS

    for inv in LOGS_INVARIANTS:
        result = inv["assert"](response, context)
"""

from typing import Any, Dict, List

# Valid source domains per LOGS_DOMAIN_V2_ARCHITECTURE.md line 112
VALID_SOURCE_DOMAINS = frozenset({
    "ACTIVITY",
    "POLICY",
    "INCIDENTS",
    "LOGS",
    "SYSTEM",
})

# Valid origin types per LOGS_DOMAIN_V2_ARCHITECTURE.md line 114
VALID_ORIGINS = frozenset({
    "SYSTEM",
    "HUMAN",
    "AGENT",
    "MIGRATION",
    "REPLAY",
})

# Required EvidenceMetadata fields per LOGS_DOMAIN_V2_ARCHITECTURE.md lines 88-119
REQUIRED_METADATA_FIELDS = frozenset({
    "tenant_id",
    "occurred_at",
    "recorded_at",
    "source_domain",
})

# Optional but recommended fields
RECOMMENDED_METADATA_FIELDS = frozenset({
    "run_id",
    "trace_id",
    "source_component",
    "origin",
    "immutable",
})


def _get_items(response: Any) -> List[Dict[str, Any]]:
    """Extract items from response (handles both list and items envelope)."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        if "items" in response:
            return response.get("items", [])
        # Single item response - return as list
        return [response]
    return []


def _get_evidence_metadata(item: Dict[str, Any]) -> Dict[str, Any] | None:
    """Extract evidence_metadata from an item."""
    if not isinstance(item, dict):
        return None
    # Check multiple possible field names
    return (
        item.get("evidence_metadata")
        or item.get("metadata")
        or item.get("evidence")
    )


# =============================================================================
# LOGS DOMAIN INVARIANTS (L1)
# =============================================================================


def inv_evidence_metadata_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-001: evidence_metadata is present in response or all items."""
    # Check if metadata is at top level (single record endpoint)
    if isinstance(response, dict):
        if _get_evidence_metadata(response):
            return True, "evidence_metadata present at top level"

    items = _get_items(response)

    if not items:
        # For list endpoints, empty is allowed
        if context.get("allow_empty_response", True):
            return True, "No items in response (allowed)"
        return False, "No items in response"

    missing_count = 0
    for i, item in enumerate(items):
        if _get_evidence_metadata(item) is None:
            missing_count += 1

    if missing_count == 0:
        return True, f"evidence_metadata present in all {len(items)} items"
    return False, f"evidence_metadata missing in {missing_count}/{len(items)} items"


def inv_evidence_metadata_required_fields(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-002: evidence_metadata has required fields."""
    # Check top-level metadata first
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            missing = [f for f in REQUIRED_METADATA_FIELDS if f not in metadata]
            if missing:
                return False, f"Missing required fields at top level: {missing}"
            return True, "All required fields present at top level"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_fields = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue  # Covered by INV-LOG-001

        for field in REQUIRED_METADATA_FIELDS:
            if field not in metadata or metadata[field] is None:
                missing_fields.append((i, field))

    if not missing_fields:
        return True, "All required evidence_metadata fields present"
    return False, f"Missing required fields: {missing_fields}"


def inv_source_domain_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-003: source_domain is from valid enum."""
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            source = metadata.get("source_domain")
            if source is not None and source not in VALID_SOURCE_DOMAINS:
                return False, f"Invalid source_domain at top level: {source}"
            if source is not None:
                return True, f"source_domain '{source}' is valid"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_sources = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        source = metadata.get("source_domain")
        if source is not None and source not in VALID_SOURCE_DOMAINS:
            invalid_sources.append((i, source))

    if not invalid_sources:
        return True, "All source_domains are valid"
    return False, f"Invalid source_domains: {invalid_sources}"


def inv_origin_valid(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-004: origin is from valid enum (if present)."""
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            origin = metadata.get("origin")
            if origin is not None and origin not in VALID_ORIGINS:
                return False, f"Invalid origin at top level: {origin}"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    invalid_origins = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        origin = metadata.get("origin")
        if origin is not None and origin not in VALID_ORIGINS:
            invalid_origins.append((i, origin))

    if not invalid_origins:
        return True, "All origins are valid"
    return False, f"Invalid origins: {invalid_origins}"


def inv_immutable_flag_true(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-005: immutable flag is True (logs are immutable)."""
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            immutable = metadata.get("immutable")
            if immutable is False:
                return False, "immutable=False at top level (should be True)"
            if immutable is True:
                return True, "immutable=True at top level"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    non_immutable = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        immutable = metadata.get("immutable")
        if immutable is False:
            non_immutable.append(i)

    if not non_immutable:
        return True, "All items have immutable=True (or unset)"
    return False, f"Items with immutable=False: {non_immutable}"


def inv_tenant_id_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-006: tenant_id is present and non-empty."""
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            tenant_id = metadata.get("tenant_id")
            if not tenant_id:
                return False, "tenant_id missing or empty at top level"
            return True, f"tenant_id present: {tenant_id}"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_tenant = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        tenant_id = metadata.get("tenant_id")
        if not tenant_id:
            missing_tenant.append(i)

    if not missing_tenant:
        return True, "All items have tenant_id"
    return False, f"Items missing tenant_id: {missing_tenant}"


def inv_timestamps_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-007: occurred_at and recorded_at timestamps are present."""
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            occurred = metadata.get("occurred_at")
            recorded = metadata.get("recorded_at")
            if not occurred:
                return False, "occurred_at missing at top level"
            if not recorded:
                return False, "recorded_at missing at top level"
            return True, "Both timestamps present at top level"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    missing_timestamps = []
    for i, item in enumerate(items):
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        if not metadata.get("occurred_at"):
            missing_timestamps.append((i, "occurred_at"))
        if not metadata.get("recorded_at"):
            missing_timestamps.append((i, "recorded_at"))

    if not missing_timestamps:
        return True, "All items have required timestamps"
    return False, f"Missing timestamps: {missing_timestamps}"


def inv_correlation_spine_present(response: Any, context: Dict[str, Any]) -> tuple[bool, str]:
    """INV-LOG-008: Correlation spine fields present (trace_id, policy_ids, incident_ids)."""
    # This is a softer check - correlation spine should be present but may have empty values
    # Check top-level metadata
    if isinstance(response, dict):
        metadata = _get_evidence_metadata(response)
        if metadata:
            has_trace = "trace_id" in metadata
            has_policies = "policy_ids" in metadata
            has_incidents = "incident_ids" in metadata
            if has_trace or has_policies or has_incidents:
                return True, "Correlation spine fields present at top level"

    items = _get_items(response)

    if not items:
        return True, "No items to validate"

    # At least one correlation field should be present
    items_with_correlation = 0
    for item in items:
        metadata = _get_evidence_metadata(item)
        if metadata is None:
            continue

        has_trace = "trace_id" in metadata
        has_policies = "policy_ids" in metadata
        has_incidents = "incident_ids" in metadata
        if has_trace or has_policies or has_incidents:
            items_with_correlation += 1

    if items_with_correlation > 0:
        return True, f"{items_with_correlation}/{len(items)} items have correlation spine"
    return False, "No items have correlation spine fields"


# =============================================================================
# LOGS INVARIANT REGISTRY (L1)
# =============================================================================

LOGS_INVARIANTS: List[Dict[str, Any]] = [
    {
        "id": "INV-LOG-001",
        "name": "evidence_metadata_present",
        "layer": "L1",
        "domain": "LOGS",
        "description": "evidence_metadata is present in response or all items",
        "assert": inv_evidence_metadata_present,
        "required": True,
        "reference": "LOGS_DOMAIN_V2_ARCHITECTURE.md:84-119",
    },
    {
        "id": "INV-LOG-002",
        "name": "evidence_metadata_required_fields",
        "layer": "L1",
        "domain": "LOGS",
        "description": "evidence_metadata has required fields (tenant_id, occurred_at, recorded_at, source_domain)",
        "assert": inv_evidence_metadata_required_fields,
        "required": True,
        "reference": "LOGS_DOMAIN_V2_ARCHITECTURE.md:88-119",
    },
    {
        "id": "INV-LOG-003",
        "name": "source_domain_valid",
        "layer": "L1",
        "domain": "LOGS",
        "description": "source_domain is from valid enum",
        "assert": inv_source_domain_valid,
        "required": True,
        "reference": "LOGS_DOMAIN_V2_ARCHITECTURE.md:112",
    },
    {
        "id": "INV-LOG-004",
        "name": "origin_valid",
        "layer": "L1",
        "domain": "LOGS",
        "description": "origin is from valid enum (if present)",
        "assert": inv_origin_valid,
        "required": False,
    },
    {
        "id": "INV-LOG-005",
        "name": "immutable_flag_true",
        "layer": "L1",
        "domain": "LOGS",
        "description": "immutable flag is True (logs are immutable)",
        "assert": inv_immutable_flag_true,
        "required": True,
        "reference": "LOGS_DOMAIN_V2_ARCHITECTURE.md:118",
    },
    {
        "id": "INV-LOG-006",
        "name": "tenant_id_present",
        "layer": "L1",
        "domain": "LOGS",
        "description": "tenant_id is present and non-empty",
        "assert": inv_tenant_id_present,
        "required": True,
    },
    {
        "id": "INV-LOG-007",
        "name": "timestamps_present",
        "layer": "L1",
        "domain": "LOGS",
        "description": "occurred_at and recorded_at timestamps are present",
        "assert": inv_timestamps_present,
        "required": True,
    },
    {
        "id": "INV-LOG-008",
        "name": "correlation_spine_present",
        "layer": "L1",
        "domain": "LOGS",
        "description": "Correlation spine fields present (trace_id, policy_ids, incident_ids)",
        "assert": inv_correlation_spine_present,
        "required": False,
    },
]


# =============================================================================
# LOGS DEFAULT QUERY PARAMS (Domain-Owned)
# =============================================================================

LOGS_DEFAULT_PARAMS: Dict[str, Dict[str, Any]] = {
    "RECORDS": {
        "LLM": {"limit": 100},
        "AUDIT": {"limit": 100},
        "SYSTEM": {"limit": 100},
    },
}


def get_logs_invariants(required_only: bool = False) -> List[Dict[str, Any]]:
    """Get all L1 LOGS domain invariants."""
    if required_only:
        return [inv for inv in LOGS_INVARIANTS if inv.get("required", True)]
    return LOGS_INVARIANTS


def get_logs_invariant_ids() -> List[str]:
    """Get all L1 LOGS domain invariant IDs."""
    return [inv["id"] for inv in LOGS_INVARIANTS]


def get_logs_default_params(subdomain: str, topic: str) -> Dict[str, Any]:
    """Get default query parameters for LOGS subdomain/topic."""
    subdomain_params = LOGS_DEFAULT_PARAMS.get(subdomain, {})
    return subdomain_params.get(topic, {})
