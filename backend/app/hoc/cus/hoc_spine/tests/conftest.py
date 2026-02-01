# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Pytest conftest for hoc_spine tests
# artifact_class: TEST
#
# WHY TESTS LIVE HERE (hoc_spine/tests/) INSTEAD OF hoc_spine/orchestrator/tests/:
#   Historical: orchestrator/__init__.py had broken cross-domain imports.
#   PIN-513 replaced those with Protocol-based interfaces.
#   Tests may now be migrated to hoc_spine/orchestrator/tests/ if desired.
