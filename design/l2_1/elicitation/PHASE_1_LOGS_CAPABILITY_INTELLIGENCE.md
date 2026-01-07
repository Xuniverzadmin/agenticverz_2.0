# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Logs

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**L2.1 Surfaces:**
- `LOGS.AUDIT_LOGS.SYSTEM_AUDIT`
- `LOGS.AUDIT_LOGS.USER_AUDIT`
- `LOGS.EXECUTION_TRACES.TRACE_DETAILS`

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-LOG-LIST (List Logs)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-LOG-LIST` | `guard_logs.py:58` |
| capability_name | List Logs | `GET /guard/logs` |
| description | List execution logs with filters and pagination | `guard_logs.py:58-99` |
| mode | **READ** | No state mutation |
| scope | **BULK** | Paginated list |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Pagination (max 100 per page) |
| latency_profile | **MEDIUM** | Async L4 queries |
| execution_style | **ASYNC** | `guard_logs.py:59` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerLogsAdapter` | `customer_logs_adapter.py:113` |
| operators | `CustomerLogsAdapter.list_logs()` → `LogsReadService.search_traces()` | `customer_logs_adapter.py:137-209` |
| input_contracts | `tenant_id (REQUIRED)`, `agent_id`, `status`, `from_date`, `to_date`, `limit (max 100)`, `offset` | Route params |
| output_contracts | `CustomerLogListResponse {items[], total, page, page_size}` | `customer_logs_adapter.py:99-105` |
| side_effects | **NONE** | Pure read |
| failure_modes | 500 Internal error | `guard_logs.py:96-99` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `guard_logs.py:58-99`, `customer_logs_adapter.py:137-209` |
| risk_flags | None - clean architecture |

---

### Capability: CAP-LOG-DETAIL (Get Log Detail)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-LOG-DETAIL` | `guard_logs.py:169` |
| capability_name | Get Log Detail | `GET /guard/logs/{log_id}` |
| description | Get log detail with execution steps | `guard_logs.py:169-207` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single log |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | Single L4 query |
| execution_style | **ASYNC** | `guard_logs.py:170` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerLogsAdapter` | `customer_logs_adapter.py:113` |
| operators | `CustomerLogsAdapter.get_log()` → `LogsReadService.get_trace()` | `customer_logs_adapter.py:211-288` |
| input_contracts | `log_id (REQUIRED)`, `tenant_id (REQUIRED via query param)` | Route params |
| output_contracts | `CustomerLogDetail {log_id, run_id, correlation_id, steps[], total_steps, ...}` | `customer_logs_adapter.py:80-96` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Log not found, 500 Internal error | `guard_logs.py:196-207` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `guard_logs.py:169-207`, `customer_logs_adapter.py:211-288` |
| risk_flags | **Redacts internal fields:** cost_cents, hashes, replay_behavior |

---

### Capability: CAP-LOG-EXPORT (Export Logs)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-LOG-EXPORT` | `guard_logs.py:107` |
| capability_name | Export Logs | `GET /guard/logs/export` |
| description | Export logs as JSON or CSV | `guard_logs.py:107-161` |
| mode | **READ** | No state mutation (generates file) |
| scope | **BULK** | Up to 10000 records |
| mutates_state | **NO** | Read-only |
| bulk_support | **YES** | Max 10000 records |
| latency_profile | **MEDIUM-HIGH** | Depends on volume |
| execution_style | **ASYNC** | `guard_logs.py:108` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerLogsAdapter` | `customer_logs_adapter.py:113` |
| operators | `CustomerLogsAdapter.export_logs()` | `customer_logs_adapter.py:290-369` |
| input_contracts | `tenant_id (REQUIRED)`, `format (json/csv)`, `from_date`, `to_date`, `limit (max 10000)` | Route params |
| output_contracts | JSON dict OR CSV StreamingResponse | `guard_logs.py:138-157` |
| side_effects | **NONE** | Pure read |
| failure_modes | 500 Internal error | `guard_logs.py:159-161` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence |
| evidence_refs | `guard_logs.py:107-161`, `customer_logs_adapter.py:290-369` |
| risk_flags | **HIGH VOLUME** - can export up to 10000 records; **CSV injection risk** if user data contains formulas |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | l2_1_surface | layer_route |
|------------|---------------|---------------|------------|--------------|--------------|-------------|
| CustomerLogsAdapter | list_logs() | CAP-LOG-LIST | async | None | LOGS.EXECUTION_TRACES.TRACE_DETAILS | L2_1 |
| CustomerLogsAdapter | get_log() | CAP-LOG-DETAIL | async | None | LOGS.EXECUTION_TRACES.TRACE_DETAILS | L2_1 |
| CustomerLogsAdapter | export_logs() | CAP-LOG-EXPORT | async | None | LOGS.EXECUTION_TRACES.TRACE_DETAILS | L2_1 |
| LogsReadService | search_traces() | CAP-LOG-LIST | async | None | - | L4 |
| LogsReadService | get_trace() | CAP-LOG-DETAIL | async | None | - | L4 |
| LogsReadService | get_trace_count() | CAP-LOG-LIST | async | None | - | L4 |

### Layer Architecture (CLEAN)

```
L2 (guard_logs.py) — API routes + console auth
      ↓
L3 (CustomerLogsAdapter) — Translation + tenant isolation + redaction
      ↓
L4 (LogsReadService) — Domain logic
      ↓
L6 (Database)
```

**Architectural Status:** CLEAN - proper L2→L3→L4 layering.

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### CAP-LOG-LIST

**Risk Flags:** NONE

**Notes:**
- Clean L2→L3→L4 architecture
- Tenant isolation enforced at L3
- Cost_cents intentionally omitted from customer view
- Pagination bounded at 100

**Confidence:** HIGH

---

### CAP-LOG-DETAIL

**Risk Flags:**

1. **INTENTIONAL REDACTION**
   - Removes: cost_cents, hashes, replay_behavior
   - Removes: plan, root_hash, seed, internal metadata
   - This is governance-correct per PIN-281

**Confidence:** HIGH

---

### CAP-LOG-EXPORT

**Risk Flags:**

1. **HIGH VOLUME EXPORT**
   - Can export up to 10,000 records
   - May cause performance issues
   - **Recommendation:** Add rate limiting

2. **CSV INJECTION RISK**
   - User data (agent_id, status) written to CSV
   - If data contains `=`, `+`, `-`, `@` could execute formulas
   - **Recommendation:** Sanitize CSV output

**Confidence:** MEDIUM (due to CSV injection risk)

---

## STOP CONDITIONS ENCOUNTERED

None - Logs domain is well-structured.

---

## L2.1 SURFACE MAPPING

| Capability ID | L2.1 Surface | Action ID (Seed) | Layer Route | Status |
|---------------|--------------|------------------|-------------|--------|
| CAP-LOG-LIST | `LOGS.AUDIT_LOGS.SYSTEM_AUDIT` | `ACT-LOGS-SYSTEM-VIEW` | L2_1 | **PARTIAL** - API returns traces, not system audit |
| CAP-LOG-EXPORT | `LOGS.AUDIT_LOGS.SYSTEM_AUDIT` | `ACT-LOGS-SYSTEM-DOWNLOAD` | L2_1 | **PARTIAL** |
| CAP-LOG-LIST | `LOGS.AUDIT_LOGS.USER_AUDIT` | `ACT-LOGS-USER-VIEW` | L2_1 | **PARTIAL** - API returns traces, not user audit |
| CAP-LOG-EXPORT | `LOGS.AUDIT_LOGS.USER_AUDIT` | `ACT-LOGS-USER-DOWNLOAD` | L2_1 | **PARTIAL** |
| CAP-LOG-LIST | `LOGS.EXECUTION_TRACES.TRACE_DETAILS` | `ACT-LOGS-TRACE-VIEW` | L2_1 | ✅ Aligned |
| CAP-LOG-DETAIL | `LOGS.EXECUTION_TRACES.TRACE_DETAILS` | `ACT-LOGS-TRACE-VIEW` | L2_1 | ✅ Aligned |
| CAP-LOG-EXPORT | `LOGS.EXECUTION_TRACES.TRACE_DETAILS` | `ACT-LOGS-TRACE-DOWNLOAD` | L2_1 | ✅ Aligned |

---

## SURFACE ALIGNMENT ANALYSIS

### Execution Traces (Well Aligned)
- `LOGS.EXECUTION_TRACES.TRACE_DETAILS` — FULLY IMPLEMENTED
  - List: `GET /guard/logs`
  - Detail: `GET /guard/logs/{log_id}`
  - Download: `GET /guard/logs/export`

### Audit Logs (Semantic Mismatch)

| L2.1 Surface | Expected Semantics | Actual API Behavior |
|--------------|-------------------|---------------------|
| `LOGS.AUDIT_LOGS.SYSTEM_AUDIT` | System-level audit trail | Returns execution traces |
| `LOGS.AUDIT_LOGS.USER_AUDIT` | User action audit trail | Returns execution traces |

**Finding:** The L2.1 seed defines separate surfaces for system audit and user audit, but the API returns **execution traces** for both. True audit logs (user actions, policy changes) are NOT exposed.

---

## ADDITIONAL CAPABILITIES DISCOVERED

None beyond what's documented. The `/guard/logs` endpoints cover list, detail, and export.

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities present in intelligence table | ✅ 3 capabilities documented |
| All adapters/operators cross-referenced | ✅ Clean L2→L3→L4 |
| All UNKNOWNs explicit | ✅ None |
| All risks surfaced | ✅ CSV injection, semantic mismatch |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Logs domain)

**Overall Assessment:**
- Execution traces well-implemented
- AUDIT_LOGS surfaces semantically mismatched to actual API
- Export has CSV injection risk
- Clean architecture

---

## References

- `backend/app/api/guard_logs.py` — L2 API routes
- `backend/app/adapters/customer_logs_adapter.py` — L3 adapter
- `backend/app/services/logs_read_service.py` — L4 service
- PIN-280, PIN-281 — L2 Promotion Governance
