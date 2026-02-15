# Ops — Domain Summary (DRAFT)

**Domain:** ops  
**Status:** DRAFT  
**Total files (ops folder):** 4 docs

---

## Documentation Inventory

| File | Purpose |
|------|---------|
| `SOFTWARE_BIBLE.md` | Domain-level architecture and operational reality |
| `OPS_CANONICAL_SOFTWARE_LITERATURE.md` | Canonical file/route map with current gaps |
| `DOMAIN_CAPABILITY.md` | Capability-oriented operation inventory |
| `_summary.md` | Domain documentation index |

## Runtime Inventory (Code Anchors)

| Layer/Surface | Paths |
|---------------|-------|
| L2 APIs | `backend/app/hoc/api/fdr/ops/cost_ops.py`, `backend/app/hoc/api/fdr/ops/founder_actions.py`, `backend/app/hoc/api/fdr/ops/retrieval_admin.py` |
| L2.1 Facades | `backend/app/hoc/fdr/ops/facades/ops_facade.py`, `backend/app/hoc/fdr/ops/facades/founder_review_adapter.py` |
| L5 Engines | `backend/app/hoc/fdr/ops/engines/founder_action_write_engine.py`, `backend/app/hoc/fdr/ops/engines/founder_review.py`, `backend/app/hoc/fdr/ops/engines/ops_incident_engine.py` |
| L6 Drivers | `backend/app/hoc/fdr/ops/drivers/error_store.py`, `backend/app/hoc/fdr/ops/drivers/event_emitter.py`, `backend/app/hoc/fdr/ops/drivers/founder_action_write_driver.py`, `backend/app/hoc/fdr/ops/drivers/ops_write_driver.py` |
| Founder UAT UI | `website/app-shell/src/features/uat/`, route `/prefops/uat` + `/fops/uat` |
| Ops Validation Gates | `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`, `website/app-shell/scripts/ui-hygiene-check.cjs` |

## Current Disposition

- Draft but synchronized to current repo reality as of 2026-02-15.
- Remaining canonicalization work: strict L2 boundary cleanup for founder ops routes.
