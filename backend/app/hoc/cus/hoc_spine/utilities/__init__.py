# capability_id: CAP-012
# Layer: L4 — HOC Spine (Utilities)
# AUDIENCE: SHARED
# Role: Pure decision utilities — cross-domain policy functions (no side effects)
# Reference: PIN-507 (Law 1 + Law 6 remediation)
# artifact_class: CODE

"""
HOC Spine Utilities — Pure Decision Functions

BOUNDARY CONTRACT (PIN-507 Law 1, Law 6):
    Utilities are pure decision logic shared across domains.
    They express POLICY, not types (schemas) or data access (drivers).

NEGATIVE CONSTRAINTS (mechanically enforced by CI — check_init_hygiene.py):
    - MUST NOT import from L6_drivers (any domain)
    - MUST NOT import from L5_engines (any domain)
    - MUST NOT import from app.db or app.models
    - MAY import from hoc_spine/schemas, L5_schemas, stdlib

SCOPE:
    Cross-domain pure decision utilities live here (spine-only).
    Domain-specific pure decision logic lives in that domain's
    L5_schemas/ under files named *_policy.py.
    See PIN-507 Law 1/6 remediation.

DOMAIN-LEVEL CONVENTION:
    Domains must NOT create their own utilities/ directories.
    Domain-specific pure logic belongs in L5_schemas/*_policy.py files.
    Only cross-domain shared logic belongs here in hoc_spine/utilities/.
"""
