# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Activity

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**L2.1 Surfaces:**
- `ACTIVITY.EXECUTIONS.ACTIVE_RUNS`
- `ACTIVITY.EXECUTIONS.COMPLETED_RUNS`
- `ACTIVITY.EXECUTIONS.RUN_DETAILS`

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-ACT-LIST (List Activities)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-ACT-LIST` | `customer_activity.py:56` |
| capability_name | List Activities | `GET /api/v1/customer/activity` |
| description | List activities for tenant with pagination and filters | `customer_activity.py:56-96` |
| mode | **READ** | No state mutation |
| scope | **BULK** | Paginated list |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Pagination (1-100 items) |
| latency_profile | **LOW** | L4 service query |
| execution_style | **SYNC** | `customer_activity.py:57` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerActivityAdapter` | `customer_activity_adapter.py:106` |
| operators | `CustomerActivityAdapter.list_activities()` → `CustomerActivityReadService.list_activities()` | `customer_activity_adapter.py:124-171` |
| input_contracts | `tenant_id (REQUIRED via X-Tenant-ID header)`, `limit (1-100)`, `offset`, `status`, `worker_id` | Route signature |
| output_contracts | `CustomerActivityListResponse {items[], total, limit, offset, has_more}` | `customer_activity_adapter.py:91-98` |
| side_effects | **NONE** | Pure read |
| failure_modes | 400 Missing tenant ID, 500 Internal error | `customer_activity.py:80-96` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `customer_activity.py:56-96`, `customer_activity_adapter.py:124-171` |
| risk_flags | None - clean architecture |

---

### Capability: CAP-ACT-DETAIL (Get Activity Detail)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-ACT-DETAIL` | `customer_activity.py:99` |
| capability_name | Get Activity Detail | `GET /api/v1/customer/activity/{run_id}` |
| description | Get detailed activity information for a run | `customer_activity.py:99-139` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single run |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L4 service query |
| execution_style | **SYNC** | `customer_activity.py:100` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerActivityAdapter` | `customer_activity_adapter.py:106` |
| operators | `CustomerActivityAdapter.get_activity()` → `CustomerActivityReadService.get_activity()` | `customer_activity_adapter.py:173-208` |
| input_contracts | `run_id (REQUIRED)`, `tenant_id (REQUIRED via X-Tenant-ID header)` | Route params |
| output_contracts | `CustomerActivityDetail {run_id, worker_name, task, status, success, error_summary, ...}` | `customer_activity_adapter.py:72-88` |
| side_effects | **NONE** | Pure read |
| failure_modes | 400 Missing tenant ID, 404 Activity not found, 500 Internal error | `customer_activity.py:118-137` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `customer_activity.py:99-139`, `customer_activity_adapter.py:173-208` |
| risk_flags | None - clean architecture |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | l2_1_surface | layer_route |
|------------|---------------|---------------|------------|--------------|--------------|-------------|
| CustomerActivityAdapter | list_activities() | CAP-ACT-LIST | sync | None | ACTIVITY.EXECUTIONS.ACTIVE_RUNS | L2_1 |
| CustomerActivityAdapter | list_activities() | CAP-ACT-LIST | sync | None | ACTIVITY.EXECUTIONS.COMPLETED_RUNS | L2_1 |
| CustomerActivityAdapter | get_activity() | CAP-ACT-DETAIL | sync | None | ACTIVITY.EXECUTIONS.RUN_DETAILS | L2_1 |
| CustomerActivityReadService | list_activities() | CAP-ACT-LIST | sync | None | - | L4 |
| CustomerActivityReadService | get_activity() | CAP-ACT-DETAIL | sync | None | - | L4 |

### Layer Architecture (CLEAN)

```
L2 (customer_activity.py) — API routes
      ↓
L3 (CustomerActivityAdapter) — Translation + tenant isolation
      ↓
L4 (CustomerActivityReadService) — Domain logic
      ↓
L6 (Database)
```

**Architectural Status:** CLEAN - proper L2→L3→L4 layering.

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### CAP-ACT-LIST

**Risk Flags:** NONE

**Notes:**
- Clean L2→L3→L4 architecture
- Tenant isolation enforced at L3
- Customer-safe schema (no cost_cents exposed)
- Pagination properly bounded (max 100)

**Confidence:** HIGH

---

### CAP-ACT-DETAIL

**Risk Flags:** NONE

**Notes:**
- Clean architecture
- Returns None if not found or wrong tenant (silent 404)
- Redacts internal fields: cost_cents, input_json, output_json, replay_token

**Confidence:** HIGH

---

## STOP CONDITIONS ENCOUNTERED

None - Activity domain is well-structured.

---

## L2.1 SURFACE MAPPING

| Capability ID | L2.1 Surface | Action ID (Seed) | Layer Route | Status |
|---------------|--------------|------------------|-------------|--------|
| CAP-ACT-LIST | `ACTIVITY.EXECUTIONS.ACTIVE_RUNS` | `ACT-ACTIVITY-ACTIVE-VIEW` | L2_1 | ✅ Aligned |
| CAP-ACT-LIST | `ACTIVITY.EXECUTIONS.COMPLETED_RUNS` | `ACT-ACTIVITY-COMPLETED-VIEW` | L2_1 | ✅ Aligned |
| CAP-ACT-LIST (export) | `ACTIVITY.EXECUTIONS.COMPLETED_RUNS` | `ACT-ACTIVITY-COMPLETED-DOWNLOAD` | L2_1 | **GAP: No export endpoint** |
| CAP-ACT-DETAIL | `ACTIVITY.EXECUTIONS.RUN_DETAILS` | `ACT-ACTIVITY-DETAIL-VIEW` | L2_1 | ✅ Aligned |
| CAP-ACT-DETAIL (export) | `ACTIVITY.EXECUTIONS.RUN_DETAILS` | `ACT-ACTIVITY-DETAIL-DOWNLOAD` | L2_1 | **GAP: No export endpoint** |

---

## ADDITIONAL CAPABILITIES IN SEED (Not Implemented)

| Seed Action ID | Action Name | Implementation Status |
|----------------|-------------|----------------------|
| `ACT-ACTIVITY-COMPLETED-DOWNLOAD` | Download Run History | **NOT IMPLEMENTED** |
| `ACT-ACTIVITY-DETAIL-DOWNLOAD` | Download Run Detail | **NOT IMPLEMENTED** |

**Gap:** Download/export actions are in L2.1 seed but not in backend code.

---

## ADDITIONAL API DISCOVERY

No additional Activity capabilities found beyond list and detail.

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities present in intelligence table | ✅ 2 capabilities documented |
| All adapters/operators cross-referenced | ✅ Clean L2→L3→L4 |
| All UNKNOWNs explicit | ✅ None |
| All risks surfaced | ✅ None - clean domain |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Activity domain)

**Overall Assessment:** Activity domain is well-architected with proper layer separation. Minor gap: download/export actions in seed but not implemented.

---

## References

- `backend/app/api/customer_activity.py` — L2 API routes
- `backend/app/adapters/customer_activity_adapter.py` — L3 adapter
- `backend/app/services/activity/customer_activity_read_service.py` — L4 service
