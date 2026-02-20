# capability_id: CAP-012
# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Learning system database tables
# Callers: learning/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: C5 Learning

"""
C5 Learning Table Boundaries.

Learning MUST operate on metadata tables only.
It MUST NOT access runtime, coordination, or kill-switch tables.

Reference: CI-C5-3, PIN-232, C5_S1_CI_ENFORCEMENT.md
"""

# Tables that learning IS allowed to read/write
# These are metadata/historical tables only
LEARNING_ALLOWED_TABLES = frozenset(
    {
        # Learning's own tables
        "learning_suggestions",
        # Historical observation sources (read-only for learning)
        # C5-S1 specifically uses coordination_audit_records for rollback data
        # NOTE: In practice, we read from in-memory CoordinationManager.get_audit_trail()
        # until we persist audit records to a table
    }
)

# Tables that learning MUST NOT access
# These are runtime, coordination, and kill-switch tables
LEARNING_FORBIDDEN_TABLES = frozenset(
    {
        # Runtime tables (I-C5-3 violation)
        "runs",
        "steps",
        "traces",
        "workflow_state",
        "active_envelopes",
        "envelope_state",
        "current_baselines",
        "memory_entries",
        # Coordination tables (I-C5-3 violation)
        "coordination_decisions",
        "priority_overrides",
        # Kill-switch tables (I-C5-6 violation)
        "killswitch_state",
        "killswitch_history",
        # Core execution tables
        "agents",
        "goals",
        "tenants",
        "api_keys",
    }
)


def validate_table_access(table_name: str) -> bool:
    """
    Validate that learning can access a table.

    Args:
        table_name: Name of the table to check.

    Returns:
        True if access is allowed, False otherwise.

    Raises:
        LearningBoundaryViolation: If table is in forbidden list.
    """
    if table_name in LEARNING_FORBIDDEN_TABLES:
        raise LearningBoundaryViolation(f"Learning module cannot access forbidden table: {table_name}")

    if table_name in LEARNING_ALLOWED_TABLES:
        return True

    # Unknown table - log warning but don't block
    # This allows flexibility for new metadata tables
    import logging

    logger = logging.getLogger("nova.learning.tables")
    logger.warning(
        "unknown_table_access",
        extra={
            "table_name": table_name,
            "note": "Table not in allowed or forbidden list",
        },
    )
    return True


class LearningBoundaryViolation(Exception):
    """
    Raised when learning attempts to access forbidden resources.

    This exception indicates a CI-C5-3 or CI-C5-6 violation.
    """

    pass
