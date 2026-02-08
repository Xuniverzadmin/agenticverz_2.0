# PIN-532: Delete Legacy backend/app/api

**Status:** ✅ COMPLETE
**Created:** 2026-02-08
**Category:** HOC Governance

---

## Summary

Deleted legacy backend/app/api after rewiring all callers to app.hoc.api; proof gates t0/init hygiene/layer boundaries/cross-domain/purity/pairing all green.

---

## Details

### What Changed

- Canonical surface is now `backend/app/hoc/api/**` (`app.hoc.api.*` import paths).
- Legacy `backend/app/api/**` was deleted after rewiring all callers (tests, scripts, contracts, and capability registry pointers).
- Added canonical HOC replacement for the lifecycle middleware dependency:
  - `backend/app/hoc/api/int/general/lifecycle_gate.py`
- Normalized AURORA capability status values:
  - `status: ASSUMED` → `status: DECLARED` across the generated capability registry
  - `CAPABILITY_STATUS_MODEL.yaml` doc `status` aligned to allowed values (`TRUSTED`)
- Updated the intent-ledger sync generator defaults so future regeneration stays compliant:
  - `scripts/tools/sync_from_intent_ledger.py` now defaults to `DECLARED` (not `ASSUMED`)

### Mechanical Proof Gates (Post-Deletion)

- `cd backend && PYTHONPATH=. pytest tests/governance/t0 -q`
  - Result: `601 passed, 18 xfailed, 1 xpassed`
- `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
  - Result: `0 blocking violations`
- `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`
  - Result: `CLEAN`
- `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`
  - Result: `CLEAN`
- `PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --all-domains --advisory`
  - Result: `0 blocking, 0 advisory`
- `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py`
  - Result: `69 wired, 0 orphaned, 0 direct`
- `PYTHONPATH=. pytest tests/hoc_spine/test_hoc_spine_import_guard.py -q`
  - Result: `3 passed`

### Commits

- `8a8f833b`: Rewire legacy `app.api.*` references to HOC (`app.hoc.api.*`) + add `lifecycle_gate.py` + capability status normalization.
- `b9becb37`: Delete legacy `backend/app/api/**`.

### Canonical References

- `docs/memory-pins/PIN-526-hoc-api-wiring-migration.md`
- `backend/app/hoc/api/hoc_api_canonical_literature.md`
