# PIN-242: Layer Map Baseline Freeze

**Status:** FROZEN (BASELINE)
**Created:** 2025-12-30
**Category:** Architecture / Layer Governance
**Related:** PIN-240 (Seven-Layer Model), PIN-241 (Violation Triage)

---

## Declaration

> **This inventory is the baseline truth.**

As of 2025-12-30, the AOS codebase layer classification is frozen. All future changes must be measured against this baseline.

---

## Baseline Metrics

| Metric | Value |
|--------|-------|
| Total files scanned | ~1,042 |
| Files with layer tags | 13 |
| Files needing tags | ~990 |
| Violations found | 17 (all L2→L5) |
| Layer validator | Operational |

---

## Layer Distribution (Frozen)

| Layer | Files | % | Description |
|-------|-------|---|-------------|
| L1 — Product Experience | 138 | 13% | Frontend UI |
| L2 — Product APIs | ~35 | 3% | Console + Public APIs |
| L3 — Boundary Adapters | ~22 | 2% | Translation layer |
| L4 — Domain Engines | ~85 | 8% | Core truth & rules |
| L5 — Execution & Workers | ~45 | 4% | Background jobs |
| L6 — Platform Substrate | ~380 | 37% | Infrastructure |
| L7 — Ops & Deployment | ~95 | 9% | Operations |
| L8 — Catalyst / Meta | ~250 | 24% | Tests & CI |

---

## Structural Findings (Frozen)

### 1. System is structurally sound
- Product ownership is correct (L1-L3 only)
- L4-L8 are properly system-wide
- No systemic violations

### 2. One layer is underdeveloped
- **L3 (Boundary Adapters)** is bypassed in all 17 violations
- Fix: Design adapter responsibilities, not remove imports

### 3. One layer is overloaded
- **L6 (Platform Substrate)** mixes auth, db, utils, SDK
- Fix: Subdivide into L6a-L6e subdomains

### 4. Violations are localized
- All 17 are L2→L5 (API calling workers)
- Concentrated in: `runtime.py`, `policy.py`, `workers.py`
- Not systemic rot

---

## Files Already Tagged (13)

| File | Layer | Status |
|------|-------|--------|
| `app/api/guard.py` | L2a | VALID |
| `app/api/customer_visibility.py` | L2a | VALID |
| `app/api/v1_killswitch.py` | L2b | VALID |
| `app/services/evidence_report.py` | L3 | VALID |
| `app/services/certificate.py` | L3 | VALID |
| `app/services/prediction.py` | L3 | VALID |
| `app/services/policy_proposal.py` | L3 | VALID |
| `app/services/email_verification.py` | L3 | VALID |
| `app/services/cost_anomaly_detector.py` | L4 | VALID |
| `app/services/pattern_detection.py` | L4 | VALID |
| `app/services/recovery_matcher.py` | L4 | VALID |
| `app/services/recovery_rule_engine.py` | L4 | VALID |
| `app/services/event_emitter.py` | L6 | VALID |

---

## Violations (17 Total)

### Bucket A — Structural (HIGH RISK) — 8 violations
```
app/api/runtime.py:148 → L2 imports L5 (CostSimulator)
app/api/runtime.py:159 → L2 imports L5 (Runtime)
app/api/workers.py:39 → L2 imports L5 (calculate_llm_cost_cents)
app/api/workers.py:686 → L2 imports L5 (business_builder.schemas)
app/api/workers.py:753 → L2 imports L5 (BusinessBuilderWorker)
app/api/workers.py:1020 → L2 imports L5 (BusinessBuilderWorker)
app/api/workers.py:1078 → L2 imports L5 (replay)
app/api/workers.py:1420 → L2 imports L5 (BusinessBuilderWorker)
```

### Bucket B — Shortcut (MEDIUM RISK) — 9 violations
```
app/api/policy.py:58-118 → L2 imports L5 (workflow.metrics)
app/api/policy.py:373 → L2 imports L5 (CostSimulator)
app/api/policy.py:396 → L2 imports L5 (PolicyEnforcer)
```

---

## LOW-Confidence Files (Require Human Decision)

| File | Question |
|------|----------|
| `incident_aggregator.py` | L3 (translation) or L4 (logic)? |
| `orphan_recovery.py` | L4 (logic) or L5 (execution)? |
| `scoped_execution.py` | L4 (engine) or L5 (worker)? |
| `tenant_service.py` | L3 (adapter) or L6 (platform)? |
| `worker_registry_service.py` | L4 (engine) or L6 (platform)? |
| `llm_failure_service.py` | L4 (engine) or L6 (platform)? |
| `policy_violation_service.py` | L4 (engine) or L6 (platform)? |

---

## Mental Model (Compression)

```
┌─────────────── Products (Slices) ───────────────┐
│   AI Console     Ops Console    Product Builder  │
│   (L1-L3)        (L1-L3)         (L1-L3)         │
└───────────────┬──────────────────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │ L3 — Boundary Adapters (UNDERDEVELOPED)  │
        │   Currently bypassed in 17 violations    │
        └───────┬──────────────────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │ L4 — Domain Engines (CORRECT)            │
        │   policy, recovery, detection, routing   │
        └───────┬──────────────────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │ L5 — Execution & Workers                 │
        │   APIs reach here directly (VIOLATION)   │
        └───────┬──────────────────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │ L6 — Platform Substrate (OVERLOADED)     │
        │   Needs subdivision into L6a-L6e         │
        └───────┬──────────────────────────────────┘
                │
        ┌───────▼──────────────────────────────────┐
        │ L7/L8 — Ops & Catalyst (CLEAN)           │
        └──────────────────────────────────────────┘
```

---

## What This Freeze Enables

1. **No reclassification churn** — Map is fixed
2. **Violations are counted** — Progress is measurable
3. **Design before refactor** — Think, then act
4. **Human decisions preserved** — LOW-confidence stays for review

---

## Governance Rules

1. **New files** must declare layer in header
2. **Reclassifications** require PIN update
3. **Violations** must decrease monotonically
4. **L3 additions** are encouraged (fill the gap)

---

## Next Steps (Ordered)

1. Resolve 7 LOW-confidence files (human judgment)
2. Subdivide L6 on paper (no refactor)
3. Design L3 adapter contract
4. Then — and only then — consider fixing violations

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial freeze. Baseline established. |
