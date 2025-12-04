# PIN-024: M6 Feature Freeze & Observability Specification

**Serial:** PIN-024
**Title:** M6 v1 Feature Freeze & Observability + Determinism & Replay
**Category:** Milestone / Specification
**Status:** ❌ **NOT COMPLETE** - Requires rework per authoritative gate criteria
**Created:** 2025-12-04
**Last Updated:** 2025-12-04
**Reclassified:** 2025-12-04

---

## Critical Status Update

### Previous Claim: "M6 COMPLETE" - **REJECTED**

The previous session incorrectly claimed M6 was complete based on a reduced scope interpretation. This has been **rejected** against the authoritative M6 Completion Gate Criteria.

### Authoritative Gate Criteria Compliance

| Requirement | Status | Gap |
|-------------|--------|-----|
| **1. CostSim V2 Sandbox Path** | ❌ 0% | Not started |
| **2. Drift Detection & Alerts** | ❌ 5% | Only basic drift metric exists |
| **3. status_history API** | ❌ 0% | Not implemented |
| **4. Cost Divergence Reporting** | ❌ 0% | Not implemented |
| **5. Reference Dataset Validation** | ❌ 0% | No datasets exist |
| **6. M6a Packaging** | ⚠️ 10% | K8s manifests exist, no Helm |
| **7. M6b Isolation Prep** | ⚠️ 15% | Basic tenant filtering only |
| **8. M6 Exit Tests** | ❌ 20% | Only basic tests, no canary/drift tests |

**Overall M6 Compliance: ~6%**

---

## What Was Actually Delivered (Reclassified as "M6-Lite" or "M5.6")

The following work was completed but does NOT satisfy M6 gate criteria:

| Deliverable | Status | Proper Classification |
|-------------|--------|----------------------|
| `docs/v1_feature_freeze.md` | ✅ | M5 hardening |
| `docs/replay_scope.md` | ✅ | M5 documentation |
| Metrics wiring in runtime | ✅ | M5 observability |
| Replay REST endpoint | ✅ | M5.5 machine-native |
| Traces endpoints | ✅ | M5.5 machine-native |
| 17 determinism tests | ✅ | M5 validation |
| 15 metrics integration tests | ✅ | M5 validation |

**Reclassification:** This work should be labeled **M5.6 - Observability Groundwork**, not M6.

---

## M6 Authoritative Requirements (Full List)

### 0. Precondition: M5 Lock (Must Stay Frozen)

| Item | Status |
|------|--------|
| Pre-execution cost simulator (V1) | ✅ Frozen |
| SDK v1 (Python + TS) | ⚠️ Python only, TS not verified |
| Soft capability enforcement | ✅ Frozen |
| Capability denial structured errors | ✅ Frozen |
| Rate limits + scopes | ✅ Frozen |
| File-based webhook keys | ✅ Frozen |
| RBAC stub | ✅ Frozen |
| Simple PgBouncer auth | ✅ Frozen |
| Zero regressions vs M5 | ✅ 783 tests passing |

### 1. CostSim V2 Sandbox Path (Mandatory)

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| `costsim_v2_adapter` implemented | ❌ | Create adapter module |
| `COSTSIM_V2_SANDBOX` feature flag | ❌ | Add feature flag |
| Sandbox routing | ❌ | Implement routing logic |
| Provenance logging (input_hash, output_hash, etc.) | ❌ | Add comprehensive logging |
| Canary runner (daily) | ❌ | Create canary infrastructure |
| V2 vs V1 comparison | ❌ | Implement comparison logic |
| V2 vs golden datasets comparison | ❌ | Create comparison tooling |
| Isolation guarantee (zero prod writes) | ❌ | Implement isolation |

**Effort Estimate:** 3-4 weeks

### 2. Drift Detection & Alerts (Mandatory)

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| `costsim_runs_total` metric | ❌ | Add metric |
| `costsim_drift_score` metric | ❌ | Add metric |
| `costsim_output_p50` metric | ❌ | Add metric |
| `costsim_output_p90` metric | ❌ | Add metric |
| `costsim_runtime_ms` metric | ❌ | Add metric |
| `costsim_schema_errors_total` metric | ❌ | Add metric |
| P1 Alert: Auto-disable V2 on drift | ❌ | Create alert rule |
| P2 Alert: Slack on median shift | ❌ | Create alert rule |
| P3 Alert: Schema mismatch | ❌ | Create alert rule |
| Incident file creation | ❌ | Implement incident flow |
| Disabled routing state | ❌ | Implement state machine |
| Stored diff artifacts | ❌ | Implement artifact storage |

**Effort Estimate:** 1-2 weeks

### 3. status_history API (Mandatory)

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| `GET /status-history` endpoint | ❌ | Create endpoint |
| CSV export support | ❌ | Add formatter |
| JSONL export support | ❌ | Add formatter |
| Pagination | ❌ | Implement pagination |
| Tenant scoping | ❌ | Add tenant filter |
| Immutable table schema | ❌ | Create migration |
| Auditor role access | ❌ | Add role check (stub OK) |
| Signed URL for exports | ❌ | Implement signing |
| >100k row export performance | ❌ | Optimize + test |

**Effort Estimate:** 1-2 weeks

### 4. Cost Divergence Reporting (Mandatory)

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| `GET /costsim/divergence-report` | ❌ | Create endpoint |
| Date range filter | ❌ | Add parameter |
| Version filter | ❌ | Add parameter |
| CSV output | ❌ | Add formatter |
| JSONL output | ❌ | Add formatter |
| Parquet output | ❌ | Add formatter |
| delta_p50 calculation | ❌ | Implement stats |
| delta_p90 calculation | ❌ | Implement stats |
| KL divergence calculation | ❌ | Implement stats |
| Outlier detection | ❌ | Implement algorithm |
| Fail ratio calculation | ❌ | Implement metric |
| Matching rate calculation | ❌ | Implement metric |
| Downloadable file generation | ❌ | Implement export |

**Effort Estimate:** 1-2 weeks

### 5. Reference Dataset Validation (Mandatory)

| Dataset | Status | Work Required |
|---------|--------|---------------|
| Low variance dataset | ❌ | Create dataset |
| High variance dataset | ❌ | Create dataset |
| Mixed city dataset | ❌ | Create dataset |
| Noise injected dataset | ❌ | Create dataset |
| Real historical (anonymized) | ❌ | Obtain + anonymize |
| mean error metric | ❌ | Implement |
| median error metric | ❌ | Implement |
| std deviation metric | ❌ | Implement |
| outlier % metric | ❌ | Implement |
| drift score metric | ❌ | Implement |
| Verdict generation | ❌ | Implement |
| Persisted validation reports | ❌ | Implement storage |

**Effort Estimate:** 2-3 weeks

### 6. M6a Packaging & Deployment Prep

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| Helm chart skeleton | ❌ | Create chart |
| K8s manifests with probes | ⚠️ Partial | Add health probes |
| Sandbox namespace for CostSim V2 | ❌ | Create namespace config |
| Tenant-aware configuration | ❌ | Add placeholders |

**Effort Estimate:** 1 week

### 7. M6b Isolation Preparation

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| Tenant context propagation check | ⚠️ Partial | Audit + fix gaps |
| Tenant-aware query patterns | ⚠️ Partial | Extend coverage |
| status_history tenant scoping | ❌ | Add with API |
| Cross-tenant leak fixes | ❓ Unknown | Audit required |

**Effort Estimate:** 1 week

### 8. M6 Exit Tests

| Requirement | Status | Work Required |
|-------------|--------|---------------|
| New endpoints test coverage | ❌ | Write tests |
| Canary logic tests | ❌ | Write tests |
| Drift metrics tests | ❌ | Write tests |
| status_history tests | ❌ | Write tests |
| Divergence report tests | ❌ | Write tests |
| Reference dataset tests | ❌ | Write tests |
| ≥90% coverage on new code | ❌ | Achieve coverage |
| 0 regressions vs M5 | ✅ | Maintain |
| Load test 500-1000 evals | ❌ | Run load test |

**Effort Estimate:** 1-2 weeks

---

## Total Effort Estimate for Genuine M6

| Phase | Effort |
|-------|--------|
| CostSim V2 Sandbox | 3-4 weeks |
| Drift Detection | 1-2 weeks |
| status_history API | 1-2 weeks |
| Divergence Reporting | 1-2 weeks |
| Reference Datasets | 2-3 weeks |
| Packaging | 1 week |
| Isolation Prep | 1 week |
| Exit Tests | 1-2 weeks |
| **TOTAL** | **11-18 weeks** |

---

## Acceptance Criteria (Non-Negotiable)

M6 is accepted ONLY if ALL of the following are true:

- [ ] All mandatory deliverables implemented
- [ ] No critical or high-severity bugs
- [ ] Canary for V2 stays green 3+ consecutive days
- [ ] Drift alerts fire correctly
- [ ] status_history works end-to-end
- [ ] Divergence reports match spec
- [ ] All 5 datasets validated
- [ ] No regressions to M5
- [ ] No security regressions
- [ ] Packaging & isolation groundwork done

---

## After M6 Acceptance → M5.9 Hardening Sprint

Deliver in 1 week:
- Real auth
- Vault
- PgBouncer secure auth
- Prometheus lifecycle
- Redis HA
- Golden replay full rebuild

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-04 | **RECLASSIFIED** - Previous "M6 COMPLETE" claim rejected |
| 2025-12-04 | Gap analysis performed against authoritative gate criteria |
| 2025-12-04 | Previous work reclassified as "M5.6 - Observability Groundwork" |
| 2025-12-04 | Genuine M6 requirements documented: 11-18 weeks of work |
| 2025-12-04 | Original M6 specification (now superseded) |
