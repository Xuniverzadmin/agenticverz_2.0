# PIN-064: M13 Boundary Checklist

**Created:** 2025-12-13
**Status:** INPUTS READY — DO NOT START M13 YET
**Category:** Milestone / Boundary
**Milestone:** M13
**Parent PINs:** PIN-062 (M12), PIN-063 (M12.1)
**Author:** Claude Code + Human Review

---

## Purpose

This checklist documents the **required inputs** before starting M13 work.
M13 should NOT begin until M12.1 production enablement is complete.

---

## M13 Scope (Proposed)

Based on PIN-033 roadmap:
- UI Console / Metrics Dashboard
- Metrics Completion
- Blackboard Scale Testing
- Documentation Pass

---

## Required Inputs (Checklist)

### From M12.1

| Input | Status | Location | Notes |
|-------|--------|----------|-------|
| M12.1 validated | ✅ Ready | PIN-063 | Staging validation passed |
| Migration 025/026 applied | ✅ Ready | Neon production | Verified 2025-12-13 |
| Job cancellation working | ✅ Ready | job_service.py:cancel_job | With credit refunds |
| Invoke audit trail | ✅ Ready | invoke_audit_service.py | Logging all invokes |
| LISTEN/NOTIFY implemented | ✅ Ready | message_service.py | Sub-second latency |
| Load test passing | ✅ Ready | test_m12_load.py | 50 items × 10 workers |
| Simulation endpoint | ✅ Ready | /api/v1/jobs/simulate | Credit estimation |

### Metrics Gaps (For M13)

| Gap | Description | Priority |
|-----|-------------|----------|
| job_spawn_duration | Time to spawn job | P1 |
| job_completion_duration | Time from start to complete | P1 |
| blackboard_op_duration | Blackboard operation latency | P1 |
| credit_reservation_total | Total credits reserved | P1 |
| credit_refund_total | Total credits refunded | P1 |
| invoke_success_total | Successful invokes | P1 |
| invoke_failure_total | Failed invokes | P1 |
| m12_* Grafana dashboard | Visual dashboard | P1 |

### Blackboard Scale Concerns

| Concern | Description | Testing Needed |
|---------|-------------|----------------|
| SCAN performance | Degrades >10K keys | Test with 10K entries |
| Write rate races | Concurrent aggregators | Test 50 concurrent writes |
| TTL cleanup | Expired keys accumulation | Verify SCAN excludes expired |
| Key namespacing | Isolation between jobs | Implement job_id prefix |

### Documentation Available

| Document | Status | Location |
|----------|--------|----------|
| M12 PIN | ✅ Complete | PIN-062 |
| M12.1 PIN | ✅ Complete | PIN-063 |
| API endpoints | ✅ Documented | api/agents.py |
| Database schema | ✅ Documented | migration 025/026 |
| Credit costs | ✅ Documented | credit_service.py |

---

## Pre-M13 Validation

Before starting M13, confirm these are complete:

### Production Enablement (Owner: Human)

| Check | Status | Owner |
|-------|--------|-------|
| Check credits ledger after real traffic | ⏳ Pending | YOU |
| Test cancellation on live worker | ⏳ Pending | YOU |
| Validate NOTIFY performance under real load | ⏳ Pending | YOU |
| Validate audit trail entries | ⏳ Pending | YOU |
| Set up Grafana with m12_* metrics | ⏳ Pending | Infra |
| Run 10 parallel jobs on production | ⏳ Pending | YOU |

---

## M13 Should NOT Start Until

1. [ ] All 7 production enablement checks pass
2. [ ] M12.1 status updated to PRODUCTION-COMPLETE
3. [ ] PIN-033 roadmap updated with M13 scope
4. [ ] Product owner signs off on M12/M12.1

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-062 | M12 Multi-Agent (complete) |
| PIN-063 | M12.1 Stabilization (stabilized) |
| PIN-033 | M8-M14 Roadmap (parent) |
| PIN-005 | Machine-Native Architecture (vision) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-13 | Created boundary checklist for M13 |
| 2025-12-13 | Documented all M12.1 inputs as ready |
| 2025-12-13 | Listed production enablement blockers |
