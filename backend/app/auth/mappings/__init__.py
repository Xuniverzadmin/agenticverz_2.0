# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: internal
#   Execution: sync
# Role: M7→M28 authority mapping package
# Reference: docs/invariants/AUTHZ_AUTHORITY.md

"""
M7→M28 Authority Mapping Package

This package contains the translation layer from legacy M7 (PolicyObject)
to the authoritative M28 (AuthorizationEngine).

INVARIANT: This is a ONE-WAY mapping. No M28→M7 reverse mapping allowed.
"""

from .m7_to_m28 import (
    M7ToM28Mapping,
    MappingResult,
    get_all_mappings,
    get_m28_equivalent,
    is_mapping_ambiguous,
)

__all__ = [
    "M7ToM28Mapping",
    "MappingResult",
    "get_all_mappings",
    "get_m28_equivalent",
    "is_mapping_ambiguous",
]
