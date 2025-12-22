# PIN-019: AOS Brainstorm and Revised Milestones

**Serial:** PIN-019
**Title:** AOS Milestone Plan Review & Corrections
**Category:** Planning / Strategic Review
**Status:** ACTIVE
**Created:** 2025-12-02
**Author:** Claude Code Review Session

---

## Executive Summary

This document captures the comprehensive review of the M0-M7 milestone roadmap against the actual AOS codebase state. The review identified factual inaccuracies in completion claims and missing critical dependencies.

**Overall Assessment: MOSTLY SOUND with CRITICAL CORRECTIONS NEEDED**

---

## 1. Codebase Validation Results

### What Was Verified

| Component | Status | Evidence |
|-----------|--------|----------|
| StructuredOutcome model | ✅ Implemented | `backend/app/worker/runtime/core.py` |
| Error taxonomy | ✅ 42+ codes | `backend/app/specs/error_taxonomy.md` |
| Registry v2 | ✅ Working | `backend/app/skills/registry_v2.py` (21K LOC) |
| Core skills | ✅ 5 skills | HTTP, LLM, JSON, Calendar, Postgres |
| Workflow engine | ✅ Functional | `backend/app/workflow/engine.py` (28K LOC) |
| Checkpointing | ✅ Implemented | `backend/app/workflow/checkpoint.py` (24K LOC) |
| Golden file replay | ✅ Infrastructure exists | HMAC signing, determinism validation |
| Test coverage | ✅ 599 passing | 761 collected, 40 test files |
| Multi-worker validation | ✅ 22,500 iterations | 0 diffs in determinism stress test |

### Technology Stack Confirmed
- **Backend:** FastAPI 0.109.0 + Python 3.11 + SQLModel
- **Database:** PostgreSQL 15 + Redis 5.0.1
- **LLM:** Anthropic Claude (claude-sonnet-4-20250514)
- **Observability:** Prometheus + Grafana + Alertmanager
- **Deployment:** Docker Compose (7 containers)

---

## 2. Critical Corrections Required

### M4: NOT Complete — Should Be CONDITIONAL PASS

PIN-014 documents **5 P0 production blockers** that remain unfixed:

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| P0-1 | Checkpoint methods block event loop | `checkpoint.py:151-365` | Async bottleneck under load |
| P0-2 | No backoff/jitter in retry logic | `engine.py:553-621` | Cascade failures |
| P0-3 | Duration fields leak into golden hash | `engine.py:446`, `golden.py:188` | Replay comparison failures |
| P0-4 | Inconsistent metric labels | `engine.py:507` | Alert grouping breaks |
| P0-5 | Golden file TOCTOU vulnerability | `golden.py:237-246` | Data corruption risk |

**Plus 7 P1 issues** including:
- P1-1: Optimistic locking not used by engine
- P1-2: Budget dict per-instance (multi-worker bypass)
- P1-6: Status field mismatch between code and migration

### M5: Definition Mismatch

**Plan defines M5 as:** "Runtime Hardening & Developer Experience" (4-6 weeks)
- Capability Enforcement Layer
- Pre-execution Cost Simulator
- SDK V1
- Security Hardening

**Actual M5-SPEC.md defines M5 as:** "Failure Catalog v1" (1 week)
- 50+ error codes
- Recovery modes
- Matching rules

**This is a scope conflict requiring resolution.**

### SDK Status: BROKEN

```
ERROR sdk/python/tests/test_python_sdk.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

The SDK needs ground-up implementation, not "finalization."

---

## 3. Revised Milestone Structure

### Insert M4.1 Before M5

```
M4.1: P0 Hardening Sprint
Duration: 1-2 weeks
Deliverables:
  - Fix P0-1: Convert CheckpointStore to async SQLAlchemy
  - Fix P0-2: Implement exponential backoff with seeded jitter
  - Fix P0-3: Exclude duration from golden output hash
  - Fix P0-4: Ensure consistent metric labels (never "unknown")
  - Fix P0-5: Atomic golden file write with signature
Exit Criteria:
  - Golden replay 100x passes
  - Nightly CI green for 1 week
  - All P0 tests added and passing
```

### Rename Existing M5 to M4.5

```
M4.5: Failure Catalog Integration
Duration: 3-5 days (most already exists in error taxonomy)
Deliverables:
  - FailureCatalog class with lookup/match
  - Recovery mode taxonomy
  - Integration with workflow engine
```

### Split M6 Into Sub-Milestones

```
M6a: Packaging (3-4 weeks)
  - Helm Chart + K8s deployment
  - CLI setup tool (aos init)
  - Network policy templates

M6b: Multi-Tenant Isolation (4-6 weeks)
  - JWT → tenant context
  - RLS or scoped queries
  - Tenant context propagation audit
  - Cross-tenant leak tests

M6c: Enterprise Licensing (2-3 weeks)
  - License validation
  - Self-host key model
```

---

## 4. Revised Timeline Assessment

| Milestone | Original Plan | Realistic Estimate | Delta |
|-----------|---------------|-------------------|-------|
| M4.1 (NEW) | - | 1-2 weeks | +2 weeks |
| M4.5 (renamed) | - | 0.5-1 week | +1 week |
| M5 | 4-6 weeks | 5-7 weeks | +1-2 weeks |
| M6 | 6-10 weeks | 10-14 weeks | +4 weeks |
| M7 | 10-14 weeks | 8-12 weeks | -2 weeks (if M6 scoped) |

**Total M5-M7:**
- Original plan: ~20-30 weeks
- Realistic: **25-35 weeks** with proper scoping

---

## 5. Missing Acceptance Tests

### M5 Needs
- [ ] SDK collection passes with 0 errors
- [ ] Rate limiting blocks after N requests
- [ ] Capability denial returns `CAPABILITY_DENIED` error code

### M6 Needs
- [ ] Cross-tenant data leak test passes (not just "cannot see")
- [ ] Database migration from single-tenant works
- [ ] Tenant isolation in `list_running` endpoint

### M7 Needs
- [ ] API versioning strategy documented
- [ ] Migration guide for existing integrations

---

## 6. API Breaking Changes Warning

M7 proposes new introspection endpoints:
```
GET /inspect
GET /workflow/{id}/timeline
GET /task/{id}
GET /agent/{id}/state
```

Current API structure:
```
GET /agents/{id}/runs
GET /agents/{id}/runs/{run_id}
GET /agents/{id}/provenance
```

**Action Required:** Define API versioning strategy before M7.

---

## 7. Gaps in Current Implementation

### Multi-Tenancy
- PIN-014 P2-6: "No tenant isolation in `list_running`"
- Code has `tenant_hash="unknown"` fallback
- No RLS implemented

### Kubernetes
- No existing Kubernetes manifests
- Starting from zero for Helm

### SDK
- Python SDK broken (collection errors)
- TypeScript SDK does not exist
- OpenAPI spec needs validation

---

## 8. Recommendations Summary

1. **Insert M4.1** — Fix P0 blockers before any new features
2. **Split M6** — Three tracks (Packaging, Multi-tenant, Enterprise) are too different
3. **Add SDK repair time** — 2 extra weeks minimum
4. **Address API versioning** — M7 breaks existing contracts
5. **De-risk SDK** — Consider CLI-only for M5, defer SDK to M7

---

## 9. Scoring

| Aspect | Score | Notes |
|--------|-------|-------|
| Strategic coherence | 9/10 | Roadmap makes sense |
| Technical accuracy | 6/10 | M4 P0s incorrectly marked complete |
| Scope realism | 7/10 | M6 overloaded |
| Dependency sequencing | 6/10 | Missing M4.1 prerequisite |
| Exit criteria clarity | 8/10 | Generally good |

---

## 10. Key Files Referenced

| File | Purpose |
|------|---------|
| `docs/memory-pins/PIN-014-m4-technical-review.md` | M4 P0/P1 issues |
| `docs/milestones/M5-SPEC.md` | Original M5 definition |
| `backend/app/workflow/engine.py` | Workflow engine (28K LOC) |
| `backend/app/workflow/checkpoint.py` | Checkpointing (24K LOC) |
| `backend/app/workflow/golden.py` | Golden file replay (18K LOC) |
| `backend/app/skills/registry_v2.py` | Skill registry (21K LOC) |

---

## 11. Next Actions

1. [ ] Create M4.1 sprint plan with P0 fix tickets
2. [ ] Resolve M5 scope conflict (plan vs spec)
3. [ ] Audit SDK and create repair plan
4. [ ] Split M6 into M6a/M6b/M6c sub-milestones
5. [ ] Define API versioning strategy for M7

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-02 | Initial review completed |
