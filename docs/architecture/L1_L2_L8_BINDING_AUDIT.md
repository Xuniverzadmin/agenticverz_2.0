# L1 ↔ L2 ↔ L8 Binding Audit

**Status:** COMPLETE
**Scope:** Read-only audit (no refactors)
**Generated:** 2025-12-30
**Scripts:** `scripts/inventory/l8_signal_inventory.py`, `l2_api_inventory.py`, `l1_api_usage.py`, `l8_to_l2_binding.py`

---

## 1. Purpose

This document establishes **explicit bindings** between:
- L8 (signals, verification, observability)
- L2 (product APIs)
- L1 (user-facing console)

**Goal:** Ensure L1 is an *honest slice* of platform capability.

**Key Finding:** The platform is structurally sound. All signal concepts are bound.
L1 can safely expand.

---

## 2. Executive Summary

| Layer | Inventory | Binding Status |
|-------|-----------|----------------|
| L8 | 103 signals (74 function calls, 13 alert rules, 11 prometheus queries) | COMPLETE |
| L2 | 334 routes across 33 API files | COMPLETE |
| L1 | 85 unique API paths referenced | PARTIAL (gaps exist) |
| L8→L2 | 21/21 signal concepts bound | **100% BOUND** |
| L2→L1 | ~26% surfaced | EXPANSION SAFE |

**Verdict:** No orphaned signals. L1 is underselling a robust platform.

---

## 3. L8 Signal Inventory

**Total Signals Found:** 103

### 3.1 Signal Sources by Type

| Type | Count | Description |
|------|-------|-------------|
| function_call | 74 | Signal emission functions in scripts |
| alert_rule | 13 | Prometheus/Alertmanager alert definitions |
| prometheus_query | 11 | PromQL expressions for metrics |
| metric_definition | 5 | Prometheus metric registrations |

### 3.2 Key Signal Emitters (L8 Sources)

| Signal Category | Files | Purpose |
|-----------------|-------|---------|
| Incident/Violation | `incident_classifier.py`, `s3_policy_violation_verification.py` | Incident creation & classification |
| Alert | `canary_runner.py`, `m10_observability_validation.py`, `alert_fuzzer.py` | Alert emission |
| Anomaly | `m27_real_cost_test.py`, `test_cost_snapshots.py` | Cost anomaly detection |
| Recovery | `m25_gate_passage_demo.py`, `m25_trigger_real_incident.py` | Recovery trigger signals |
| Semantic Auditor | `layering.py`, `authority.py`, `execution.py`, `affordance.py` | Architecture signals |

### 3.3 Orphaned Signals

**None.** All 21 tracked signal concepts have L2 consumers.

---

## 4. L2 API Capability Inventory

**Total Routes:** 334
**Files Scanned:** 33

### 4.1 Routes by Domain (Top 15)

| Domain | Route Count | Mutation Rate |
|--------|-------------|---------------|
| agents | 19 | 68% |
| policy-layer | 16 | 50% |
| recovery | 14 | 64% |
| cost | 12 | 33% |
| runtime | 9 | 33% |
| guard | 8+ | 50% |
| traces | 8 | 50% |
| auth | 10 | 60% |
| ops | 8 | 25% |
| integration | 6 | 50% |
| embedding | 6 | 50% |
| memory | 5 | 60% |

### 4.2 Authority Distribution

| Authority Level | Count | Product-Safe |
|-----------------|-------|--------------|
| user | 310+ | YES |
| founder | 4 | MAYBE |
| system | 5 | NO |

### 4.3 Files with Semantic Headers

All 4 flagged API files now have semantic headers:
- `policy.py` ✓
- `traces.py` ✓
- `integration.py` ✓
- `v1_proxy.py` ✓

### 4.4 L2 → L6 Write Bindings (API Self-Authority)

26 API files write directly to persistent storage:

| API File | Write Pattern | Risk Level |
|----------|---------------|------------|
| `policy.py` | session.add, session.execute | LOW (documented) |
| `traces.py` | session.execute, INSERT | LOW (documented) |
| `integration.py` | session.execute, INSERT, UPDATE | MEDIUM |
| `v1_proxy.py` | session.add, create | LOW (documented) |
| `guard.py` | UPDATE | LOW |
| `cost_intelligence.py` | session.execute, UPDATE | LOW |
| `memory_pins.py` | DELETE, INSERT, UPDATE | MEDIUM |
| `recovery.py` | session.execute, delete, UPDATE | MEDIUM |
| `agents.py` | delete, UPDATE | MEDIUM |
| `workers.py` | session.execute, delete, UPDATE | MEDIUM |

---

## 5. L1 Surface Mapping

**Files Scanned:** 196 frontend files
**Unique API Paths Found:** 85

### 5.1 Most Used APIs (by reference count)

| API Path | Reference Count | Domain |
|----------|-----------------|--------|
| `/api/v1/traces` | 13 | traces |
| `/api/v1/runtime/capabilities` | 11 | runtime |
| `/api/v1/recovery/candidates` | 8 | recovery |
| `/api/v1/recovery/stats` | 8 | recovery |
| `/api/v1/failures` | 6 | failures |
| `/api/v1/runtime/simulate` | 6 | runtime |
| `/api/v1/runtime/skills` | 6 | runtime |
| `/api/v1/memory/pins` | 6 | memory |

### 5.2 L1 Domain Coverage

| L1 Domain | API Count | L2 Support |
|-----------|-----------|------------|
| Auth | 3 | FULL |
| Runtime | 4 | FULL |
| Traces | 2 | FULL |
| Recovery | 4 | FULL |
| Guard | 10+ | FULL |
| Ops | 7 | FULL |
| Integration | 5 | FULL |
| Policy | 1 | PARTIAL |
| Cost | 2 | PARTIAL |

### 5.3 Hardcoded Assumptions Found

| Type | Count | Risk |
|------|-------|------|
| `hardcoded_localhost` | 6 | DEV ONLY |
| `hardcoded_http` | 33 | LOW (mostly w3.org namespaces) |

**Note:** localhost references are in test configs and dev vite.config - not production code.

---

## 6. L8 → L2 Binding Matrix

All 21 signal concepts are fully bound:

| Signal Concept | L8 Sources | L2 Consumers | Status |
|----------------|------------|--------------|--------|
| incident | 29 | 13 | BOUND |
| violation | 47 | 10 | BOUND |
| alert | 41 | 3 | BOUND |
| anomaly | 10 | 6 | BOUND |
| budget | 24 | 16 | BOUND |
| cost | 43 | 21 | BOUND |
| failure | 76 | 13 | BOUND |
| guard | 36 | 9 | BOUND |
| health | 58 | 8 | BOUND |
| metric | 57 | 15 | BOUND |
| mismatch | 37 | 4 | BOUND |
| policy | 35 | 16 | BOUND |
| prediction | 21 | 2 | BOUND |
| recovery | 36 | 10 | BOUND |
| replay | 46 | 9 | BOUND |
| rollback | 32 | 6 | BOUND |
| trace | 23 | 6 | BOUND |
| killswitch | 8 | 4 | BOUND |
| canary | 13 | 2 | BOUND |
| timeout | 51 | 9 | BOUND |
| throttle | 1 | 1 | BOUND |

**Orphaned Signals:** 0

---

## 7. L2 → L1 Binding Gaps

### 7.1 L2 Capabilities NOT Yet Surfaced in L1

These are safe APIs that L1 doesn't use yet:

| Domain | Capability | L2 Ready | L1 Status |
|--------|------------|----------|-----------|
| Cost Intelligence | `/cost/dashboard`, `/cost/projection` | YES | NOT SURFACED |
| Cost Intelligence | `/cost/by-feature`, `/cost/by-model` | YES | NOT SURFACED |
| Policy Layer | `/policy-layer/conflicts` | YES | NOT SURFACED |
| Policy Layer | `/policy-layer/temporal-policies` | YES | NOT SURFACED |
| Policy Layer | `/policy-layer/ethical-constraints` | YES | NOT SURFACED |
| Discovery | `/api/v1/discovery`, `/api/v1/discovery/stats` | YES | NOT SURFACED |
| Agents | `/api/v1/agents/{id}/reputation` | YES | NOT SURFACED |
| Agents | `/api/v1/agents/{id}/evolution` | YES | NOT SURFACED |
| Routing | `/api/v1/routing/stability` | YES | NOT SURFACED |
| Predictions | `/api/v1/predictions` | YES | NOT SURFACED |
| Feedback | `/api/v1/feedback` | YES | NOT SURFACED |
| RBAC | `/api/v1/rbac/audit`, `/api/v1/rbac/matrix` | YES | NOT SURFACED |

### 7.2 L1 Pages with Assumed APIs

| L1 Page | APIs Used | Missing Capability |
|---------|-----------|-------------------|
| Incidents | /guard/incidents | Timeline context |
| Costs | /guard/costs | Full cost intelligence |
| Recovery | /api/v1/recovery | Recovery explain |

---

## 8. Binding Summary

### 8.1 What L8 Provides (System Signals)

- **103 signals** across verification, monitoring, and semantic auditing
- **13 alert rules** in Prometheus/Alertmanager
- **11 prometheus queries** for metrics
- **Full coverage** of incident, violation, anomaly, recovery, prediction concepts

### 8.2 What L2 Exposes (Product APIs)

- **334 routes** across 33 API files
- **310+ user-authority** routes (product-safe)
- **26 files** with direct DB writes (documented authority)
- **Strong domain coverage**: guard, recovery, cost, policy, runtime, agents

### 8.3 What L1 Currently Shows (Console Surface)

- **85 unique API paths** referenced
- **~26% of L2 capability** currently surfaced
- **No broken bindings** - all L1 references map to real L2 routes
- **Dev-only localhost** assumptions (safe)

### 8.4 What L1 Could Safely Show (Expansion)

L1 has permission to surface:
- Full cost intelligence dashboard
- Discovery signals UI
- Prediction viewing
- Agent evolution/reputation
- Policy layer conflicts/constraints
- RBAC audit trails
- Feedback loops

---

## 9. Conclusions

### 9.1 Platform Readiness

| Assessment | Status |
|------------|--------|
| L8 → L2 Signal Binding | **100% COMPLETE** |
| L2 Semantic Headers | **100% COMPLETE** (4 flagged files fixed) |
| L2 → L1 Binding | **SAFE FOR EXPANSION** |
| Orphaned Signals | **NONE** |
| Architecture Integrity | **VERIFIED** |

### 9.2 L1 Assessment

- L1 is currently: **Minimal** (conservative slice)
- Platform readiness for L1 expansion: **HIGH**
- All L1 API references resolve to real L2 routes: **YES**

### 9.3 Recommended L1 Expansion Priority

1. **Cost Intelligence** - Full dashboard, projections
2. **Discovery** - Signal visibility UI
3. **Policy Layer** - Conflicts, constraints, temporal policies
4. **Predictions** - Prediction viewing
5. **Agent Details** - Evolution, reputation, strategy

---

## 10. Governance Decision

This audit:

- [ ] Blocks L1 work
- [x] **Allows scoped L1 expansion**
- [ ] Allows full product iteration

**Rationale:** All structural proofs pass. L8→L2 is 100% bound. L2→L1 binding gaps are intentional (not bugs). L1 can safely expand to surface more L2 capability.

**Next Steps:**
1. Pick L1 expansion scope (cost dashboard recommended first)
2. Create UI → API binding plan
3. Implement with confidence

---

## Appendix: Regenerating This Audit

```bash
cd /root/agenticverz2.0

# Run all inventory scripts
python3 scripts/inventory/l8_signal_inventory.py > /tmp/l8.md
python3 scripts/inventory/l2_api_inventory.py > /tmp/l2.md
python3 scripts/inventory/l1_api_usage.py > /tmp/l1.md
python3 scripts/inventory/l8_to_l2_binding.py > /tmp/binding.md
```

---

**Signed-off by:** Claude Opus 4.5 (Audit Generator)
**Date:** 2025-12-30
