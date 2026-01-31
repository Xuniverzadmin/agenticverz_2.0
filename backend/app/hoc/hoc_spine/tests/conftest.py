# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Pytest conftest for hoc_spine tests
# artifact_class: TEST
#
# WHY TESTS LIVE HERE (hoc_spine/tests/) INSTEAD OF hoc_spine/orchestrator/tests/:
#   orchestrator/__init__.py has broken cross-domain imports (ValidatorVerdict
#   relocated 2026-01-30, pending L1 re-wiring). Any file inside the orchestrator/
#   package triggers the __init__.py chain and crashes. Tests live one level up at
#   hoc_spine/tests/ to avoid the broken package import.
#
#   MOVE to hoc_spine/orchestrator/tests/ when __init__.py cross-domain imports are fixed.
