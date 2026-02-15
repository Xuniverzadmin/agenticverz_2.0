# PIN-550: Run Proof Test Plan v1 Execution + Neon Connection Purge

**Date:** 2026-02-09
**Status:** COMPLETE
**Author:** Claude Opus 4.6

---

## Summary

Two tasks completed in this session:

1. **Run Proof Test Plan v1** — Executed `docs/architecture/hoc/run_proof_test_plan_v1.md` end-to-end against local PostgreSQL. All 5 steps passed, all 4 acceptance criteria met.
2. **Neon Connection Purge** — Audited entire system for active Neon DB references and eliminated all executable paths that could accidentally wake Neon compute.

---

## Part 1: Run Proof Test Plan v1

**Report:** `docs/architecture/hoc/run_proof_test_plan_v1_implemented.md`

### Results

| Step | Status |
|------|--------|
| 1. Confirm trace data exists | PASS (seeded synthetic data) |
| 2. Confirm trace steps exist | PASS (3 steps) |
| 3. Coordinator production path | PASS (HASH_CHAIN / VERIFIED) |
| 4. Verify integrity result | PASS (all 4 checks) |
| 5. Coordinator pytest | PASS (10/10, 2.43s) |

### Issues Found and Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Empty DB (no trace data) | Fresh rebuild from alembic | Seeded synthetic run + trace + 3 steps |
| `runs` INSERT rejected by trigger | `origin_system_id DEFAULT 'legacy-migration'` + trigger blocking that value | Explicit `origin_system_id = 'run-proof-test-v1'` |
| `pg_store.py` ModuleNotFoundError | `redact.py` moved from L6_drivers to L5_engines, import never updated | Changed to `from app.traces.redact import redact_trace_data` |

### Coordinator Output

```
integrity_model: HASH_CHAIN
verification_status: VERIFIED
chain_length: 3
root_hash: 0ca74e198c14a378a33c2ecad49ac725c74f3c33cce6dc1512fb32b258654c32
trace_count: 1
step_count: 3
```

---

## Part 2: Neon Connection Purge

### Audit Scope

Checked all running processes, Docker containers, systemd timers, cron jobs, PgBouncer config, docker-compose files, environment files, network connections, and source code.

### Active Connections

**Zero.** All services confirmed on local PostgreSQL (`localhost:6432` via PgBouncer).

### Hardcoded Neon Defaults Fixed

| File | Risk Before | Fix |
|------|-------------|-----|
| `scripts/verification/truth_preflight.sh:33` | HIGH | Replaced Neon default with `localhost:6432/nova_aos` |
| `backend/tests/test_m12_agents.py:18` | MEDIUM | Replaced `setdefault` Neon URL with local |
| `backend/tests/test_m12_load.py:24` | MEDIUM | Replaced `setdefault` Neon URL with local |

### Remaining References (All Safe)

- `.env` lines 9-10: commented out
- `secrets/neon.env`: standalone file, not loaded by any service
- Detection/guard logic in `_db_guard.py`, `customer_sandbox.py`, `alembic/env.py`: reads URL string for classification, never connects
- `.github/workflows/ci.yml`: Neon ephemeral branches, gated behind secrets

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/hoc/cus/logs/L6_drivers/pg_store.py` | Fixed broken import: `.redact` -> `app.traces.redact` |
| `scripts/verification/truth_preflight.sh` | Replaced Neon default URL with local |
| `backend/tests/test_m12_agents.py` | Replaced Neon `setdefault` with local |
| `backend/tests/test_m12_load.py` | Replaced Neon `setdefault` with local |

## Files Created

| File | Purpose |
|------|---------|
| `docs/architecture/hoc/run_proof_test_plan_v1_implemented.md` | Execution report |

---

## Key Takeaways

1. **origin_system_id trap**: The `runs` table has a default that is immediately rejected by its own trigger — any INSERT omitting `origin_system_id` will fail.
2. **Duplicate redact.py**: Three identical copies exist (`app/traces/`, `L5_engines/`, formerly `L6_drivers/`). Should consolidate.
3. **Neon charge risk**: Hardcoded Neon defaults in scripts/tests are a silent cost risk. All executable paths are now patched.
