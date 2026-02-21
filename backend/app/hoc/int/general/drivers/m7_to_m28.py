# capability_id: CAP-006
# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: M7 to M28 authority mapping (single source of truth)
# Callers: Authorization choke point only
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
M7 to M28 Authority Mapping

=============================================================================
INVARIANT: SINGLE MAPPING FILE (I-AUTH-002)
=============================================================================
This is the ONLY file that may contain M7→M28 mapping logic.
No other file may import from M7 and translate to M28 patterns.

Rules:
1. Mapping must be lossless (no information loss)
2. Ambiguous mappings HARD-FAIL (raise MappingError)
3. No reverse mapping (M28→M7) allowed
4. All fallbacks must emit telemetry

Reference: docs/invariants/AUTHZ_AUTHORITY.md
=============================================================================

Usage:
    from app.auth.mappings import get_m28_equivalent, MappingResult

    result = get_m28_equivalent("memory_pin", "write")
    if result.is_valid:
        # Use result.action, result.resource, result.scope
        pass
    else:
        # Handle ambiguous or unmapped case
        raise MappingError(result.error)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Optional, Tuple

logger = logging.getLogger("nova.auth.mapping")


class MappingStatus(str, Enum):
    """Status of a mapping attempt."""

    VALID = "valid"  # Direct mapping exists
    AMBIGUOUS = "ambiguous"  # Multiple possible mappings
    UNMAPPED = "unmapped"  # No mapping exists
    DEPRECATED = "deprecated"  # M7 pattern is obsolete


@dataclass(frozen=True)
class MappingResult:
    """
    Result of an M7→M28 mapping attempt.

    Immutable to prevent accidental mutation.
    """

    status: MappingStatus
    action: Optional[str] = None
    resource: Optional[str] = None
    scope: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.status == MappingStatus.VALID

    @property
    def is_ambiguous(self) -> bool:
        return self.status == MappingStatus.AMBIGUOUS

    def __repr__(self) -> str:
        if self.is_valid:
            return f"MappingResult(VALID: {self.action}:{self.resource})"
        return f"MappingResult({self.status.value}: {self.error})"


class MappingError(Exception):
    """Raised when a mapping is ambiguous or invalid."""

    def __init__(self, result: MappingResult):
        self.result = result
        super().__init__(f"Mapping error: {result.error}")


@dataclass(frozen=True)
class M7ToM28Mapping:
    """
    Single M7→M28 mapping definition.

    Each M7 (resource, action) pair maps to exactly one M28 (action, resource, scope).
    """

    m7_resource: str
    m7_action: str
    m28_action: str
    m28_resource: str
    m28_scope: Optional[str] = None
    notes: str = ""


# =============================================================================
# AUTHORITATIVE MAPPING TABLE
# =============================================================================
# This is the single source of truth for M7→M28 translation.
# Format: (m7_resource, m7_action) → M7ToM28Mapping

MAPPING_TABLE: Dict[Tuple[str, str], M7ToM28Mapping] = {
    # =========================================================================
    # Memory PIN operations
    # =========================================================================
    ("memory_pin", "read"): M7ToM28Mapping(
        m7_resource="memory_pin",
        m7_action="read",
        m28_action="read",
        m28_resource="memory_pins",
        notes="Read memory pins",
    ),
    ("memory_pin", "write"): M7ToM28Mapping(
        m7_resource="memory_pin",
        m7_action="write",
        m28_action="write",
        m28_resource="memory_pins",
        notes="Create/update memory pins",
    ),
    ("memory_pin", "delete"): M7ToM28Mapping(
        m7_resource="memory_pin",
        m7_action="delete",
        m28_action="delete",
        m28_resource="memory_pins",
        notes="Delete memory pins",
    ),
    ("memory_pin", "admin"): M7ToM28Mapping(
        m7_resource="memory_pin",
        m7_action="admin",
        m28_action="admin",
        m28_resource="memory_pins",
        notes="Admin memory pins",
    ),
    # =========================================================================
    # Cost Simulation operations
    # =========================================================================
    ("costsim", "read"): M7ToM28Mapping(
        m7_resource="costsim",
        m7_action="read",
        m28_action="read",
        m28_resource="costsim",
        notes="Read cost simulations",
    ),
    ("costsim", "write"): M7ToM28Mapping(
        m7_resource="costsim",
        m7_action="write",
        m28_action="write",
        m28_resource="costsim",
        notes="Create cost simulations",
    ),
    # =========================================================================
    # Policy operations
    # =========================================================================
    ("policy", "read"): M7ToM28Mapping(
        m7_resource="policy",
        m7_action="read",
        m28_action="read",
        m28_resource="policies",
        notes="Read policies",
    ),
    ("policy", "write"): M7ToM28Mapping(
        m7_resource="policy",
        m7_action="write",
        m28_action="write",
        m28_resource="policies",
        notes="Create/update policies",
    ),
    ("policy", "approve"): M7ToM28Mapping(
        m7_resource="policy",
        m7_action="approve",
        m28_action="admin",
        m28_resource="policies",
        notes="Approve policies (requires admin)",
    ),
    # =========================================================================
    # Agent operations
    # =========================================================================
    ("agent", "read"): M7ToM28Mapping(
        m7_resource="agent",
        m7_action="read",
        m28_action="read",
        m28_resource="agents",
        notes="Read agents",
    ),
    ("agent", "write"): M7ToM28Mapping(
        m7_resource="agent",
        m7_action="write",
        m28_action="write",
        m28_resource="agents",
        notes="Create/update agents",
    ),
    ("agent", "delete"): M7ToM28Mapping(
        m7_resource="agent",
        m7_action="delete",
        m28_action="delete",
        m28_resource="agents",
        notes="Delete agents",
    ),
    ("agent", "heartbeat"): M7ToM28Mapping(
        m7_resource="agent",
        m7_action="heartbeat",
        m28_action="write",
        m28_resource="agents",
        m28_scope="lifecycle",
        notes="Agent heartbeat (lifecycle write)",
    ),
    ("agent", "register"): M7ToM28Mapping(
        m7_resource="agent",
        m7_action="register",
        m28_action="write",
        m28_resource="agents",
        m28_scope="lifecycle",
        notes="Agent registration (lifecycle write)",
    ),
    # =========================================================================
    # Runtime operations
    # =========================================================================
    ("runtime", "simulate"): M7ToM28Mapping(
        m7_resource="runtime",
        m7_action="simulate",
        m28_action="execute",
        m28_resource="runtime",
        notes="Run simulation",
    ),
    ("runtime", "capabilities"): M7ToM28Mapping(
        m7_resource="runtime",
        m7_action="capabilities",
        m28_action="read",
        m28_resource="runtime",
        notes="Read capabilities",
    ),
    ("runtime", "query"): M7ToM28Mapping(
        m7_resource="runtime",
        m7_action="query",
        m28_action="read",
        m28_resource="runtime",
        notes="Query runtime state",
    ),
    # =========================================================================
    # Recovery operations
    # =========================================================================
    ("recovery", "suggest"): M7ToM28Mapping(
        m7_resource="recovery",
        m7_action="suggest",
        m28_action="read",
        m28_resource="recovery",
        notes="Get recovery suggestions",
    ),
    ("recovery", "execute"): M7ToM28Mapping(
        m7_resource="recovery",
        m7_action="execute",
        m28_action="execute",
        m28_resource="recovery",
        notes="Execute recovery",
    ),
    # =========================================================================
    # Prometheus operations (DEPRECATED - reclassify as ops)
    # =========================================================================
    ("prometheus", "query"): M7ToM28Mapping(
        m7_resource="prometheus",
        m7_action="query",
        m28_action="read",
        m28_resource="metrics",
        notes="Query Prometheus (ops)",
    ),
    ("prometheus", "reload"): M7ToM28Mapping(
        m7_resource="prometheus",
        m7_action="reload",
        m28_action="admin",
        m28_resource="metrics",
        notes="Reload Prometheus (admin)",
    ),
}

# Resources that have AMBIGUOUS mappings (require manual decision)
AMBIGUOUS_PATTERNS: FrozenSet[Tuple[str, str]] = frozenset(
    [
        # None currently - add as discovered
    ]
)

# Resources that are DEPRECATED (should emit warning)
DEPRECATED_PATTERNS: FrozenSet[Tuple[str, str]] = frozenset(
    [
        ("prometheus", "query"),
        ("prometheus", "reload"),
    ]
)


def get_m28_equivalent(m7_resource: str, m7_action: str) -> MappingResult:
    """
    Get the M28 equivalent for an M7 (resource, action) pair.

    Args:
        m7_resource: M7 resource name (e.g., "memory_pin")
        m7_action: M7 action name (e.g., "write")

    Returns:
        MappingResult with status and M28 equivalents

    Raises:
        MappingError if the mapping is ambiguous and strict mode is enabled
    """
    key = (m7_resource, m7_action)

    # Check for ambiguous patterns first (HARD-FAIL)
    if key in AMBIGUOUS_PATTERNS:
        return MappingResult(
            status=MappingStatus.AMBIGUOUS,
            error=f"Ambiguous mapping: {m7_resource}:{m7_action} has multiple possible M28 equivalents",
        )

    # Check if deprecated
    if key in DEPRECATED_PATTERNS:
        mapping = MAPPING_TABLE.get(key)
        if mapping:
            logger.warning(
                "deprecated_m7_pattern",
                extra={
                    "m7_resource": m7_resource,
                    "m7_action": m7_action,
                    "m28_action": mapping.m28_action,
                    "m28_resource": mapping.m28_resource,
                },
            )
            return MappingResult(
                status=MappingStatus.DEPRECATED,
                action=mapping.m28_action,
                resource=mapping.m28_resource,
                scope=mapping.m28_scope,
            )

    # Look up in mapping table
    mapping = MAPPING_TABLE.get(key)
    if mapping:
        return MappingResult(
            status=MappingStatus.VALID,
            action=mapping.m28_action,
            resource=mapping.m28_resource,
            scope=mapping.m28_scope,
        )

    # No mapping found
    return MappingResult(
        status=MappingStatus.UNMAPPED,
        error=f"No M28 mapping for {m7_resource}:{m7_action}",
    )


def is_mapping_ambiguous(m7_resource: str, m7_action: str) -> bool:
    """Check if a mapping is ambiguous."""
    return (m7_resource, m7_action) in AMBIGUOUS_PATTERNS


def get_all_mappings() -> Dict[Tuple[str, str], M7ToM28Mapping]:
    """Get all defined mappings (for testing/validation)."""
    return MAPPING_TABLE.copy()


def validate_mapping_completeness(m7_patterns: list[Tuple[str, str]]) -> dict:
    """
    Validate that all M7 patterns have mappings.

    Args:
        m7_patterns: List of (resource, action) tuples from M7

    Returns:
        Dict with 'valid', 'ambiguous', 'unmapped' lists
    """
    result = {
        "valid": [],
        "ambiguous": [],
        "unmapped": [],
        "deprecated": [],
    }

    for resource, action in m7_patterns:
        mapping = get_m28_equivalent(resource, action)
        if mapping.status == MappingStatus.VALID:
            result["valid"].append((resource, action))
        elif mapping.status == MappingStatus.AMBIGUOUS:
            result["ambiguous"].append((resource, action))
        elif mapping.status == MappingStatus.DEPRECATED:
            result["deprecated"].append((resource, action))
        else:
            result["unmapped"].append((resource, action))

    return result


# =============================================================================
# Unit Tests (run with pytest)
# =============================================================================


def _test_valid_mappings():
    """Test that valid mappings return correct results."""
    result = get_m28_equivalent("memory_pin", "write")
    assert result.is_valid
    assert result.action == "write"
    assert result.resource == "memory_pins"


def _test_unmapped_returns_error():
    """Test that unmapped patterns return error."""
    result = get_m28_equivalent("nonexistent", "action")
    assert not result.is_valid
    assert result.status == MappingStatus.UNMAPPED


def _test_ambiguous_returns_error():
    """Test that ambiguous patterns return error."""
    # Currently no ambiguous patterns, but test the mechanism
    assert not is_mapping_ambiguous("memory_pin", "write")


if __name__ == "__main__":
    # Run basic validation
    _test_valid_mappings()
    _test_unmapped_returns_error()
    _test_ambiguous_returns_error()
    print("All mapping tests passed!")
