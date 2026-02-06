# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Role: Determinism level definitions (shared across L2 and L5)
# Callers: api/cus/policies/guard.py (L2), logs/L5_engines/replay_determinism.py (L5)
# Reference: PIN-504 (Cross-Domain Violation Resolution)
# artifact_class: CODE

"""
Determinism Types

Shared enum definitions for replay determinism levels.
Lives in L5_schemas so L2 can import without violating L2→L5 rules.
"""

from enum import Enum


class DeterminismLevel(str, Enum):
    """
    Determinism level for replay validation.

    STRICT: Byte-for-byte exact match
    LOGICAL: Policy decision equivalence (default for LLM)
    SEMANTIC: Meaning-equivalent match
    """

    STRICT = "strict"
    LOGICAL = "logical"
    SEMANTIC = "semantic"


__all__ = [
    "DeterminismLevel",
]
