# PIN-575: CUS L2.1 Facade Package-Form Standardization

**Status:** ✅ COMPLETE
**Created:** 2026-02-16
**Category:** Architecture / Topology / Naming
**Depends on:** PIN-573

---

## Summary

Standardized all canonical CUS L2.1 facade entrypoints to package-form pathing:

- `backend/app/hoc/api/facades/cus/<domain>/<domain>_fac.py`

This removes mixed naming/path ambiguity and locks one diagnostic pattern for triage and rollout.

---

## Scope Completed

All 10 canonical CUS domains now use package-form facades:

- `overview/overview_fac.py`
- `activity/activity_fac.py`
- `incidents/incidents_fac.py`
- `policies/policies_fac.py`
- `controls/controls_fac.py`
- `logs/logs_fac.py`
- `analytics/analytics_fac.py`
- `integrations/integrations_fac.py`
- `api_keys/api_keys_fac.py`
- `account/account_fac.py`

---

## Invariants Locked

- Facade activation point remains `backend/app/hoc/api/facades/cus/__init__.py`.
- L2 domain boundary routes remain under `backend/app/hoc/api/cus/<domain>/`.
- L2.1 facade modules contain wiring only (no business logic).
- `*_public.py` modules are the designated L2 public-boundary entry scaffolds for incremental domain rollout.

---

## Verification

- `pytest -q backend/tests/hoc_spine/test_l21_facades_integrity.py` (passed during rollout)
- `PYTHONPATH=. python3 backend/scripts/ci/check_layer_boundaries.py` (clean during rollout)

---

## Topology Note

`docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md` now explicitly records package-form CUS facade examples as constitutional reference.
