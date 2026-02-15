# Ops — Domain Capability (DRAFT)

**Domain:** ops (fdr/ops)  
**Status:** DRAFT  
**Updated:** 2026-02-15  
**References:** PIN-564, PIN-565, PIN-566

---

## 1. Domain Purpose

Founder-facing operational control and visibility:
- system-level cost intelligence
- founder intervention actions (freeze/throttle/override + reversals)
- retrieval plane administration and evidence lookup
- UAT execution visibility route in founder console

## 2. Customer/Founder-Facing Operations

| Operation Surface | File | L4 Wired | Entry Point | Side Effects |
|------------------|------|----------|-------------|--------------|
| Cost Overview/Anomalies/Tenants/Customer Drilldown | `api/fdr/ops/cost_ops.py` | Yes | `ops.cost` | read-only |
| Founder Actions (freeze/throttle/override/reversal) | `api/fdr/ops/founder_actions.py` | Partial | direct + engine | db_write |
| Retrieval Plane Admin | `api/fdr/ops/retrieval_admin.py` | Yes | `knowledge.planes.*` | db_write |
| Founder UAT Console Route | `website/app-shell/src/routes/index.tsx` | N/A (frontend route) | `/prefops/uat`, `/fops/uat` | none |

## 3. Internal Capability Groups

### Decision / Engine Layer

| Functionality | Primary Files |
|---------------|---------------|
| Founder action write logic | `fdr/ops/engines/founder_action_write_engine.py` |
| Ops incident aggregation | `fdr/ops/engines/ops_incident_engine.py` |
| Founder review flow | `fdr/ops/engines/founder_review.py` |

### Persistence / Driver Layer

| Functionality | Primary Files |
|---------------|---------------|
| Founder action persistence | `fdr/ops/drivers/founder_action_write_driver.py` |
| Error store access | `fdr/ops/drivers/error_store.py` |
| Ops writes | `fdr/ops/drivers/ops_write_driver.py` |
| Ops event emission | `fdr/ops/drivers/event_emitter.py` |

### Founder Validation/Gating Surface

| Functionality | Primary Files |
|---------------|---------------|
| Unified UC/UAT validation gate | `backend/scripts/ops/hoc_uc_validation_uat_gate.sh` |
| UAT Playwright runtime | `website/app-shell/tests/uat/playwright.config.ts` |
| BIT Playwright runtime | `website/app-shell/tests/bit/playwright.config.ts` |
| UI hygiene guard | `website/app-shell/scripts/ui-hygiene-check.cjs` |

## 4. Explicit Non-Features (Current)

- No CUS `/ops/*` API surface is currently present in `backend/app/hoc/api/cus/ops/`.
- Ops literature remains draft until founder L2 boundaries are fully normalized to thin-route rules.
