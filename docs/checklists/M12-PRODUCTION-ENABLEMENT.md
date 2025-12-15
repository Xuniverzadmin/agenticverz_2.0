# M12 Production Enablement Checklist

**Created:** 2025-12-13
**Status:** 7 CHECKS REQUIRED BEFORE PRODUCTION
**Owner:** Product Owner (Human)

---

## Overview

This checklist contains **7 mandatory checks** that must pass before M12/M12.1 is considered production-ready.

Claude has completed all technical implementation. These checks require **human validation on production**.

---

## Pre-Flight (Claude Completed)

| Check | Status | Date |
|-------|--------|------|
| Apply migration 025 | ✅ Done | 2025-12-11 |
| Apply migration 026 | ✅ Done | 2025-12-13 |
| Staging validation script | ✅ Passed | 2025-12-13 |
| Load test (50×10) | ✅ Passed | 2025-12-13 |
| SKIP LOCKED verification | ✅ Passed | 2025-12-13 |

---

## Production Validation (Human Required)

### Check 1: Credit Ledger After Real Traffic
**Owner:** YOU
**Status:** ⏳ Pending

**Steps:**
1. Create a real job with 10+ items
2. Let workers process items
3. Query credit_ledger:
   ```sql
   SELECT * FROM agents.credit_ledger
   WHERE tenant_id = 'production'
   ORDER BY created_at DESC
   LIMIT 10;
   ```
4. Verify:
   - Reserve entry exists
   - Charge entries match completed items
   - Amounts are correct

**Pass Criteria:** Credit entries accurate for real traffic

---

### Check 2: Test Cancellation on Live Worker
**Owner:** YOU
**Status:** ⏳ Pending

**Steps:**
1. Create job with 50 items
2. Wait for ~10 items to complete
3. Call cancel endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/v1/jobs/{job_id}/cancel
   ```
4. Verify response includes:
   - `credits_refunded` > 0
   - `cancelled_items` count
5. Check job_cancellations table:
   ```sql
   SELECT * FROM agents.job_cancellations
   WHERE job_id = '{job_id}';
   ```

**Pass Criteria:** Cancellation works, refund recorded

---

### Check 3: Validate NOTIFY Performance Under Real Load
**Owner:** YOU
**Status:** ⏳ Pending

**Steps:**
1. Run 5 concurrent agent_invoke calls
2. Measure round-trip latency
3. Compare to polling baseline (~50-120s)
4. Target: <2s P95

**Test Command:**
```bash
# Run invoke latency test
PYTHONPATH=. python3 -c "
import time
from app.agents.skills.agent_invoke import AgentInvokeSkill, AgentInvokeInput
# Measure invoke latency under load
"
```

**Pass Criteria:** P95 latency < 2 seconds

---

### Check 4: Validate Audit Trail Entries
**Owner:** YOU
**Status:** ⏳ Pending

**Steps:**
1. Run several agent_invoke calls
2. Query invoke_audit:
   ```sql
   SELECT invoke_id, status, duration_ms, credits_charged
   FROM agents.invoke_audit
   ORDER BY started_at DESC
   LIMIT 10;
   ```
3. Verify:
   - All invokes have entries
   - Duration recorded
   - Credits recorded for success

**Pass Criteria:** All invokes audited

---

### Check 5: Set Up Grafana with m12_* Metrics
**Owner:** Infra
**Status:** ✅ Dashboard Created (needs import)

**Required Metrics:**
- `m12_jobs_started_total` (jobs created)
- `m12_jobs_completed_total`
- `m12_job_items_claimed_total` (items claimed)
- `m12_job_items_total` (items completed)
- `m12_credits_reserved_total`
- `m12_credits_spent_total`
- `m12_agent_invoke_latency_seconds` (invoke duration)
- `m12_message_latency_seconds`

**M18 Self-Optimization Metrics (also included):**
- `m18_reputation_score` - Agent reputation scores
- `m18_quarantine_state` - Quarantine state machine
- `m18_governor_state` - System stability state
- `m18_drift_signals_total` - Drift detection signals
- `m18_boundary_violations_total` - SBA violations
- `m18_feedback_loop_iterations_total` - Learning iterations

**Dashboard Location:**
```
monitoring/dashboards/m12_m18_multi_agent_self_optimization.json
```

**Steps:**
1. Import dashboard JSON:
   ```bash
   # Via Grafana UI: Dashboards > Import > Upload JSON
   # Or via API:
   curl -X POST http://localhost:3000/api/dashboards/db \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $GRAFANA_API_KEY" \
     -d @monitoring/dashboards/m12_m18_multi_agent_self_optimization.json
   ```
2. Verify all metrics visible
3. Set up alerts for:
   - Job failure rate > 5%
   - Credit depletion warning
   - Governor frozen state
   - High quarantine count

**Pass Criteria:** Dashboard visible, metrics flowing

---

### Check 6: Run 10 Parallel Jobs on Production
**Owner:** YOU
**Status:** ⏳ Pending

**Steps:**
1. Create 10 jobs concurrently, each with 20 items
2. Monitor completion
3. Verify:
   - All jobs complete
   - No duplicate claims
   - Credits accurate
   - No errors in logs

**Test Command:**
```bash
# Run concurrent job test
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -H "X-Tenant-ID: production" \
    -d '{
      "orchestrator_agent": "parallel_test",
      "worker_agent": "test_worker",
      "task": "Production validation '$i'",
      "items": [{"n": 1}, {"n": 2}, ...],
      "parallelism": 5
    }' &
done
wait
```

**Pass Criteria:** 200 items processed, 0 errors

---

### Check 7: Final Sign-Off
**Owner:** YOU
**Status:** ⏳ Pending

**Criteria:**
- [ ] All 6 checks above pass
- [ ] No blocking bugs discovered
- [ ] Performance acceptable
- [ ] Documentation reviewed
- [ ] Rollback plan confirmed

**Sign-off:**
```
Date: _______________
Signed: _______________
Notes: _______________
```

---

## After All Checks Pass

1. Update PIN-063 status to `PRODUCTION-COMPLETE`
2. Update PIN-062 status to `PRODUCTION`
3. Announce M12 release internally
4. Begin M13 planning

---

## Rollback Plan

If issues discovered:

1. **Immediate:** Disable agents API routes
2. **Migration rollback:**
   ```bash
   DATABASE_URL="$URL" PYTHONPATH=. alembic downgrade -2
   ```
3. **Verify schema:**
   ```sql
   SELECT * FROM alembic_version;
   ```
4. **Notify team:** Document issue in PIN

---

## Related Documents

- PIN-062: M12 Multi-Agent System
- PIN-063: M12.1 Stabilization
- PIN-064: M13 Boundary Checklist
- Release Notes: M12-M12.1
