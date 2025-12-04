# PIN-015: M4 Validation & Maturity Gates

**Serial:** PIN-015
**Title:** M4 Workflow Engine Validation & Maturity Gates
**Category:** Milestone / Validation
**Status:** IN PROGRESS (24h shadow run active)
**Created:** 2025-12-02
**Updated:** 2025-12-02

---

## Executive Summary

This PIN documents the comprehensive validation process for M4 Workflow Engine maturity. Following the P0 blockers identified in PIN-014, a multi-phase validation harness was executed to verify determinism, fault tolerance, and production readiness.

**Current Status:** 24-hour shadow simulation in progress (started 2025-12-02 13:12 CET)

---

## Validation Phases

### Phase A: Observability Infrastructure

**Objective:** Verify Prometheus/Grafana alerting pipeline is operational.

| Test | Result | Notes |
|------|--------|-------|
| Prometheus rules reload | PASS | Fixed permission issue (chmod 644) |
| 22 alert rules loaded | PASS | 6 rule groups active |
| Grafana dashboard import | PASS | Required JSON wrapper format |
| Synthetic alert verification | PASS | Alerts firing correctly |

**Issues Fixed:**
- `workflow-alerts.yml` had 600 permissions, Prometheus couldn't read
- Grafana API requires `{"dashboard": <json>, "overwrite": true}` wrapper

---

### Phase B: Multi-Worker Determinism Validation

**Objective:** Verify workflow execution is deterministic across workers.

| Metric | Value |
|--------|-------|
| Workers | 3 |
| Iterations per worker | 500 |
| Seeds per iteration | 5 |
| Workflow types | 3 (compute, io, llm) |
| **Total iterations** | **22,500** |
| **Mismatches** | **0** |
| **Duration** | 11.23 seconds |

**Test Script:** `/tmp/multi_worker_500.py`

**Key Verification:**
- Seed propagation via SHA256 derivation
- Step-level hash comparison
- Cross-worker determinism

---

### Phase C: Golden Archive/Resign/Verify E2E

**Objective:** Verify complete golden file lifecycle.

| Test | Result |
|------|--------|
| Generate golden file with HMAC | PASS |
| Sign with known key | PASS |
| Verify valid signature | PASS |
| Detect tampered content | PASS |
| Detect tampered signature | PASS |
| Archive to compressed format | PASS |
| Extract and verify | PASS |
| Resign with new key | PASS |
| Verify new signature | PASS |

**Tests Passed:** 9/9

**Test Script:** `/tmp/golden_lifecycle_test.py`

---

### Phase D: Fault Injection & CPU Stress

**Objective:** Verify error taxonomy and determinism under stress.

#### Fault Injection Results

| Fault Type | Injected | Classified | Status |
|------------|----------|------------|--------|
| TIMEOUT | Yes | TRANSIENT | PASS |
| DNS_FAILURE | Yes | TRANSIENT | PASS |
| CONNECTION_REFUSED | Yes | TRANSIENT | PASS |
| HTTP_500 | Yes | TRANSIENT | PASS |
| HTTP_503 | Yes | TRANSIENT | PASS |
| HTTP_400 | Yes | PERMANENT | PASS |
| HTTP_404 | Yes | PERMANENT | PASS |
| RATE_LIMITED | Yes | RESOURCE | PASS |
| BUDGET_EXCEEDED | Yes | RESOURCE | PASS |
| PERMISSION_DENIED | Yes | PERMISSION | PASS |
| INVALID_INPUT | Yes | VALIDATION | PASS |
| SCHEMA_ERROR | Yes | VALIDATION | PASS |

**Golden Corruption:** 0
**Error Taxonomy Compliance:** 100%

**Test Script:** `/tmp/fault_injection_test.py`

#### CPU Stress Replay Results

| Metric | Value |
|--------|-------|
| CPU Stress Workers | 4 |
| Replay Workers | 4 |
| Workflows | 100 |
| Replays | 100 |
| **Mismatches under load** | **0** |

**Test Script:** `/tmp/cpu_stress_replay.py`

---

### Phase E: Lifecycle & Shadow Run

#### Lifecycle Kill/Restore Test

**Objective:** Verify checkpoint save/load/resume functionality.

| Test | Result |
|------|--------|
| Save checkpoint mid-workflow | PASS |
| Load checkpoint state | PASS |
| Resume from checkpoint | PASS |
| Kill workflow simulation | PASS |
| Restore and continue | PASS |
| Verify resumed hash matches baseline | PASS |

**Tests Passed:** 6/6

**Test Script:** `/tmp/lifecycle_kill_restore.py`

#### 24-Hour Shadow Simulation

**Objective:** Continuous shadow replay verification over 24 hours.

**Status:** IN PROGRESS

| Parameter | Value |
|-----------|-------|
| Start Time | 2025-12-02 13:12:19 CET |
| Duration | 24 hours |
| Workers | 3 |
| Cycle Interval | 30 seconds |
| Workflows/Cycle | 10 |
| Expected Cycles | ~2,880 |
| Expected Workflows | ~25,920 |

**Monitoring:**
```bash
# Check status
/root/agenticverz2.0/scripts/stress/check_shadow_status.sh

# Watch logs
tail -f /var/lib/aos/shadow_24h_20251202_131219.log

# Webhook notifications
# https://webhook.site/91e10688-b9d4-4b48-ab2a-6f80f552c3d4
```

**Process:** PID 752320

**Early Results (first 12 minutes):**
- Cycles: 24
- Workflows: 216
- Replays: 216
- Mismatches: 0

---

## Bug Fixes During Validation

### BUG-001: Bash Arithmetic Exit Code

**File:** `/root/agenticverz2.0/scripts/stress/run_shadow_simulation.sh`

**Issue:** Under `set -e`, `((MISMATCHES += 0))` returns exit code 1, terminating script.

**Root Cause:** Bash arithmetic `(( ))` returns 1 when result is 0.

**Fix:** Added `|| true` to lines 497-499 and 511:
```bash
((TOTAL_WORKFLOWS += primary_total)) || true
((TOTAL_REPLAYS += replays)) || true
((MISMATCHES += mismatches)) || true
((CYCLES_COMPLETED++)) || true
```

### BUG-002: Prometheus Rules Permission

**File:** `/root/agenticverz2.0/monitoring/rules/workflow-alerts.yml`

**Issue:** File had 600 permissions, Prometheus couldn't read.

**Fix:** `chmod 644`

### BUG-003: Grafana Dashboard Import Format

**Issue:** Raw dashboard JSON rejected by API.

**Fix:** Wrapped in `{"dashboard": <json>, "overwrite": true, "folderId": 0}`

---

## Validation Scripts Created

| Script | Purpose | Location |
|--------|---------|----------|
| Multi-worker determinism | Phase B harness | `/tmp/multi_worker_500.py` |
| Golden lifecycle E2E | Phase C harness | `/tmp/golden_lifecycle_test.py` |
| Fault injection | Phase D harness | `/tmp/fault_injection_test.py` |
| CPU stress replay | Phase D harness | `/tmp/cpu_stress_replay.py` |
| Lifecycle kill/restore | Phase E harness | `/tmp/lifecycle_kill_restore.py` |
| 2-minute shadow test | Quick validation | `/tmp/shadow_2min_test.py` |
| Quick shadow test v2 | Quick validation | `/tmp/quick_shadow_test_v2.py` |
| Shadow status check | Monitoring | `/root/agenticverz2.0/scripts/stress/check_shadow_status.sh` |
| 24h shadow starter | Launch script | `/tmp/start_24h_shadow.sh` |

---

## Maturity Gate Checklist

| Gate | Status | Evidence |
|------|--------|----------|
| Prometheus alerts operational | PASS | 22 rules, 6 groups |
| Multi-worker determinism (500+ iterations) | PASS | 22,500 iterations, 0 diffs |
| Golden file lifecycle E2E | PASS | 9/9 tests |
| Fault injection (all 12 types) | PASS | 0 corruption |
| CPU stress determinism | PASS | 0 mismatches |
| Checkpoint save/load/resume | PASS | 6/6 tests |
| 24-hour shadow run | IN PROGRESS | 0 mismatches so far |
| Runbook tabletop exercise | PENDING | After shadow run |
| SRE sign-off | PENDING | After shadow run |

---

## Next Steps

1. **Monitor 24-hour shadow run** (ends 2025-12-03 ~13:12 CET)
2. **Verify final shadow run report** (0 mismatches required)
3. **Conduct runbook tabletop exercise**
4. **Complete self-sign certification** (see below)
5. **Update PIN-014 with resolution status**
6. **Proceed to M5: Failure Catalog v1**

---

## Self-Sign Runbook Checklist

**Instructions:** Execute each step in order. Record actual results. All steps must PASS for M4 sign-off.

### Pre-Flight Checks

| # | Check | Command | Expected | Actual | Status |
|---|-------|---------|----------|--------|--------|
| 1 | Backend health | `curl -s http://localhost:8000/health \| jq .status` | `"healthy"` | | |
| 2 | Worker running | `docker ps \| grep worker` | Container UP | | |
| 3 | Redis ping | `redis-cli ping` | `PONG` | | |
| 4 | PostgreSQL | `PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "SELECT 1"` | `1` | | |
| 5 | Prometheus up | `curl -s http://localhost:9090/-/healthy` | `Prometheus Server is Healthy` | | |

### Shadow Run Verification

| # | Check | Command | Expected | Actual | Status |
|---|-------|---------|----------|--------|--------|
| 6 | Shadow completed | `grep "Shadow simulation complete" /var/lib/aos/shadow_24h_*.log` | Found | | |
| 7 | Total cycles | `grep -c "Running cycle" /var/lib/aos/shadow_24h_*.log` | ≥2500 | | |
| 8 | Total mismatches | `grep ", 0 mismatches" /var/lib/aos/shadow_24h_*.log \| wc -l` | = cycles | | |
| 9 | No errors | `grep -E "[1-9][0-9]* mismatches" /var/lib/aos/shadow_24h_*.log \| grep -v ", 0 mismatches" \| wc -l` | `0` | | |
| 10 | Golden files created | `ls /tmp/shadow_simulation_*/golden/*.json \| wc -l` | >20000 | | |

### Runbook Operations

| # | Check | Command | Expected | Actual | Status |
|---|-------|---------|----------|--------|--------|
| 11 | Quick shadow test | `./scripts/stress/run_shadow_simulation.sh --quick` | 0 mismatches | | |
| 12 | Sanity check | `./scripts/stress/shadow_sanity_check.sh` | All sections OK | | |
| 13 | Emergency stop enable | `./scripts/ops/disable-workflows.sh enable` | Flag created | | |
| 14 | Emergency stop status | `./scripts/ops/disable-workflows.sh status` | ENABLED | | |
| 15 | Emergency stop disable | `./scripts/ops/disable-workflows.sh disable` | Flag removed | | |
| 16 | Golden diff (dry) | `python3 scripts/stress/golden_diff_debug.py --summary-dir /tmp/shadow_simulation_*/golden 2>&1 \| head -5` | Summary output | | |

### Alerting Verification

| # | Check | Command | Expected | Actual | Status |
|---|-------|---------|----------|--------|--------|
| 17 | Prometheus alerts | `curl -s http://localhost:9090/api/v1/rules \| jq '.data.groups \| length'` | ≥6 | | |
| 18 | Active alerts | `curl -s http://localhost:9090/api/v1/alerts \| jq '.data.alerts \| length'` | Number | | |
| 19 | Alertmanager health | `curl -s http://localhost:9093/-/healthy` | OK | | |

### Database/Checkpoint

| # | Check | Command | Expected | Actual | Status |
|---|-------|---------|----------|--------|--------|
| 20 | Checkpoint table exists | `PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "SELECT COUNT(*) FROM checkpoints" 2>/dev/null \|\| echo "Table check"` | Count or N/A | | |

---

## Sign-Off Section

### Certification Statement

I hereby certify that:

1. The 24-hour shadow simulation completed with **0 mismatches**
2. All 20 checklist items above have been executed and verified
3. The incident playbook has been reviewed and is understood
4. Emergency stop procedures have been tested and work correctly
5. Monitoring infrastructure (daemon + cron) is operational

### Signature Block

```
═══════════════════════════════════════════════════════════════
M4 WORKFLOW ENGINE MATURITY CERTIFICATION

Owner:          ________________________________
Date:           ________________________________
Shadow Run ID:  shadow_24h_20251202_131219
Total Cycles:   ________________________________
Total Workflows:________________________________
Mismatches:     0

Evidence Locations:
- Shadow Log:   /var/lib/aos/shadow_24h_20251202_131219.log
- Monitor Log:  /var/lib/aos/shadow_monitor.log
- Golden Dir:   /tmp/shadow_simulation_20251202_131219/golden/

Checklist Results: ___/20 PASS

CERTIFIED: [ ] YES  [ ] NO (if NO, attach remediation plan)

Signature: ________________________________
═══════════════════════════════════════════════════════════════
```

---

## Incident Playbook Reference

For any issues during validation, refer to:
- **Incident Playbook:** `docs/runbooks/m4-incident-playbook.md`

Key scenarios covered:
1. Mismatch detected (P0)
2. Shadow process died (P1)
3. Disk full (P1)
4. Stale logs (P2)
5. Webhook failures (P3)

---

## Related Documents

- [PIN-013](PIN-013-m4-workflow-engine-completion.md) - M4 Completion Report
- [PIN-014](PIN-014-m4-technical-review.md) - M4 Technical Review (P0 blockers)
- [PIN-008](PIN-008-v1-milestone-plan-full.md) - v1 Milestone Plan

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-02 | Added self-sign runbook checklist (20 items) and signature block |
| 2025-12-02 | Added incident playbook reference |
| 2025-12-02 | Initial creation, 24h shadow run started |
