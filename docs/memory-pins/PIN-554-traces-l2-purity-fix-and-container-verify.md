# PIN-554: Traces L2 Purity Fix + Container Verification

**Status:** ✅ COMPLETE  
**Created:** 2026-02-10  
**Category:** HOC Governance / Logs Domain / Validation

---

## Summary

Eliminated L2→L6 import violations in `backend/app/hoc/api/cus/logs/traces.py` by routing trace endpoints through L4 `logs.traces_api` and new L5 engine `trace_api_engine`. Updated logs domain literature (canonical, software bible, domain capability, summary). Rebuilt `nova_agent_manager` container and verified source, tests, imports, and CI hygiene.

---

## Changes Implemented

### Code

- **New L5 engine:** `backend/app/hoc/cus/logs/L5_engines/trace_api_engine.py`
  - Orchestrates trace store operations (list/get/store/compare/delete/cleanup/idempotency)
  - Performs redaction via L6 `redact_trace_data`
- **New L4 handler:** `logs.traces_api` in `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py`
- **L2 traces API rewired:** `backend/app/hoc/api/cus/logs/traces.py` now calls L4 `logs.traces_api` (no direct L6 imports)

### Documentation

- `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/logs/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/logs/DOMAIN_CAPABILITY.md`
- `literature/hoc_domain/logs/_summary.md`
- Added `literature/hoc_domain/logs/L5_engines/hoc_cus_logs_L5_engines_trace_api_engine.md`

---

## Container Verification (post-rebuild)

Container rebuilt (`docker compose up -d --build backend`). Verified inside `nova_agent_manager`:

1. **Source verification (RunProofCoordinator):**
   - `tenant_id=tenant_id` in `get_trace`: **True**
   - `TypeError` fallback: **True**
2. **Pytest:**  
   `tests/test_run_introspection_coordinators.py` → **12 passed**
3. **Import sanity:**  
   `RunProofCoordinator` + `PostgresTraceStore` import OK  
   `PostgresTraceStore.get_trace` params: `['self', 'trace_id', 'tenant_id']`
4. **CI init hygiene:**  
   `scripts/ci/check_init_hygiene.py --ci` → **0 blocking violations**

---

## Notes / Pitfalls

- Prior container build was out-of-sync (missing `L6_drivers/redact.py` and updated RunProofCoordinator). Rebuild fixed.
- Codex process had intermittent DB connectivity failures (psycopg2 OperationalError) despite healthy DB; root cause suspected IPv6/localhost resolution + PgBouncer behavior. `.env` updated by user to use `127.0.0.1` with `connect_timeout=5&sslmode=disable`.

---

## Files

**Code:**
- `backend/app/hoc/cus/logs/L5_engines/trace_api_engine.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py`
- `backend/app/hoc/api/cus/logs/traces.py`

**Docs:**
- `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md`
- `literature/hoc_domain/logs/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/logs/DOMAIN_CAPABILITY.md`
- `literature/hoc_domain/logs/_summary.md`
- `literature/hoc_domain/logs/L5_engines/hoc_cus_logs_L5_engines_trace_api_engine.md`

