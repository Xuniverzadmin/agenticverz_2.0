# SCENARIO VIOLATIONS TABLE

**Version:** 1.0
**Status:** AUTHORITATIVE
**Last Updated:** 2026-01-12
**Reference:** docs/ops/SESSION_LIFECYCLE_SCENARIOS.md

---

## Purpose

This document tracks violations detected during scenario execution.
An empty table indicates all scenarios conform to the lifecycle matrix.

---

## Violation Table

| Scenario | Run | Timestamp | Violation Type | Description | Status |
|----------|-----|-----------|----------------|-------------|--------|
| - | - | - | - | - | - |

**Status:** EMPTY TABLE = ALL SCENARIOS PASSED

---

## Critical Scenario Execution Log

The following critical failure-resilience scenarios have been verified:

### S14: RECONCILE_INTERRUPTED

| Property | Value |
|----------|-------|
| Run ID | SCENARIO-S14-RUN-1 |
| Timestamp | 2026-01-12T12:49:54Z |
| Result | PASSED |
| Violations | 0 |
| Exit Verdict Verified | EXIT_BLOCKED |
| Artifact | artifacts/scenario_runs/SCENARIO-S14-RUN-1.yaml |

**Verification:**
- Exit gate correctly blocked exit on interrupted reconciliation
- SR artifact correctly recorded as incomplete (no verdict)
- System correctly requires reconciliation restart

---

### S17: FORCED_EXIT_ATTEMPT

| Property | Value |
|----------|-------|
| Run ID | SCENARIO-S17-RUN-3 |
| Timestamp | 2026-01-12T12:50:55Z |
| Result | PASSED |
| Violations | 0 |
| Exit Verdict Verified | EXIT_BLOCKED |
| Artifact | artifacts/scenario_runs/SCENARIO-S17-RUN-3.yaml |

**Verification:**
- Exit gate correctly blocked exit on dirty state (tests failed)
- BLOCKED status correctly reported in output
- Blocking reasons correctly explained
- Session state correctly shows tests status = failed

---

### S19: SERVICES_UNHEALTHY_POST_HK

| Property | Value |
|----------|-------|
| Run ID | SCENARIO-S19-RUN-1 |
| Timestamp | 2026-01-12T12:51:06Z |
| Result | PASSED |
| Violations | 0 |
| Exit Verdict Verified | EXIT_BLOCKED |
| Artifact | artifacts/scenario_runs/SCENARIO-S19-RUN-1.yaml |

**Verification:**
- HK artifact correctly reports services_protected = false
- HK artifact correctly reports success = false
- Post-check correctly records unhealthy service status
- System correctly detects service degradation after cleanup

---

## Multi-Agent Authorization Status

Per CLAUDE_AUTHORITY.md Section 11:

> Until at least one clean execution exists for S14, S17, and S19,
> multi-agent concurrency is NOT allowed.

**Current Status:**

| Scenario | Clean Execution | Authorization |
|----------|-----------------|---------------|
| S14 | YES | GRANTED |
| S17 | YES | GRANTED |
| S19 | YES | GRANTED |

**MULTI-AGENT CONCURRENCY:** AUTHORIZED

---

## Invariant Verification Summary

| Invariant | Verified By | Status |
|-----------|-------------|--------|
| V01: Pipeline Order | S14 (interrupted mid-pipeline) | VERIFIED |
| V02: Block New Work | S17 (dirty state blocked) | VERIFIED |
| V03: Exit Gate | S14, S17 (both blocked correctly) | VERIFIED |
| V04: Domain Separation | S19 (HK-only, no SR cross) | VERIFIED |
| V05: Session State Protection | All (no unauthorized writes) | VERIFIED |

---

## Audit Trail

| Date | Action | Scenarios | Result |
|------|--------|-----------|--------|
| 2026-01-12 | Initial execution | S14, S17, S19 | ALL PASSED |

---

## Notes

- S17-RUN-1 and S17-RUN-2 failed due to `python` vs `python3` command issue
- Fixed in scenario_executor.py, S17-RUN-3 passed cleanly
- All three critical scenarios now verified
- System is failure-resilient as designed
