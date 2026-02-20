# capability_id: CAP-012
# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Role: hoc_spine - schemas
# Reference: DIRECTORY_REORGANIZATION_PLAN.md
#
# SCHEMA ADMISSION RULE (PIN-510 Phase 0B):
# Files in this directory must satisfy ALL of:
#   1. >=2 domain consumers (cross-domain shared types only)
#   2. Facts/types only — no decisions, no behavior
#   3. Append-only evolution — existing fields never removed
#   4. Each file must document its consumers in header: # Consumers: domain1, domain2
# CI check 20 enforces rule 4.

"""
hoc_spine / schemas

Cross-domain shared types. Admission rule: >=2 consumers, facts only, append-only.
Each file must declare its consumers in the header.

Exports will be added as files are moved here.
"""

from .authority_decision import AuthorityDecision

__all__ = [
    "AuthorityDecision",
]
