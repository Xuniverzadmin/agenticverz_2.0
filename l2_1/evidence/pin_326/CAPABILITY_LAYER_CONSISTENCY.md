# PIN-326 Phase 3.1: Capability-Layer Consistency Check

**Generated:** 2026-01-06
**Status:** ELICITATION ONLY
**Purpose:** Verify layer assignments and cross-layer invocations

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Registered Capabilities (CAP-XXX) | 18 | Baseline |
| Latent Capabilities Discovered (LCAP-XXX) | 103 | **92% SHADOW** |
| Routes in allowed_routes | ~45 | Governed |
| Routes in LCAP (total) | ~365 | **88% UNMAPPED** |
| Layer Violations Detected | 2 | Flagged |
| Cross-Layer Authority Gaps | 14 | Flagged |

---

## Section 1: Capability Registry Coverage

### 1.1 Registered Capabilities (CAP-001 to CAP-018)

| CAP-ID | Name | State | Layer | Routes in allowed_routes |
|--------|------|-------|-------|--------------------------|
| CAP-001 | Replay | CLOSED | L2 | 15 routes |
| CAP-002 | Cost Simulation | CLOSED | L2 | 8 routes |
| CAP-003 | Policy Proposals | READ_ONLY | L2 | 4 routes |
| CAP-004 | Prediction Plane | READ_ONLY | L2 | 4 routes |
| CAP-005 | Founder Console | CLOSED | L2 | 5 wildcards |
| CAP-006 | Authentication | CLOSED | L3 | 0 (delegated) |
| CAP-007 | Authorization | CLOSED | L4 | 0 (internal) |
| CAP-008 | Multi-Agent | CLOSED | L2/L4 | 0 (SDK-only) |
| CAP-009 | Policy Engine | CLOSED | L2 | 4 routes |
| CAP-010 | CARE-L Routing | CLOSED | L4 | 0 (internal) |
| CAP-011 | Governance | CLOSED | L2 | 4 routes |
| CAP-012 | Workflow Engine | CLOSED | L4/L5 | 0 (internal) |
| CAP-013 | Learning Pipeline | CLOSED | L4 | 0 (internal) |
| CAP-014 | Memory System | CLOSED | L2 | 2 wildcards |
| CAP-015 | Optimization | CLOSED | L4 | 0 (internal) |
| CAP-016 | Skill System | CLOSED | L2/L4 | 0 (SDK-only) |
| CAP-017 | Cross-Project | PLANNED | - | 0 (not implemented) |
| CAP-018 | Integration | CLOSED | L2 | 5 routes |

**Total explicit routes in registry:** ~45-50

### 1.2 Latent Capability Distribution by Layer

| Layer | LCAP Count | Routes | Status |
|-------|------------|--------|--------|
| L1 (SDK) | 31 | ~40 methods | SHADOW |
| L2 (API) | 59 | ~365 routes | 92% SHADOW |
| L5 (Worker) | 3 | 9 workers | SHADOW |
| L7 (CLI) | 10 | 31 commands | SHADOW |
| **Total** | **103** | **~445** | **88% UNMAPPED** |

---

## Section 2: Layer Violation Analysis

### 2.1 Expected Layer Dependencies

```
L1 (SDK) ──────────► L2 (API)
                         │
                         ▼
                    L3 (Adapters) ──► L6 (Platform)
                         │
                         ▼
                    L4 (Engines)
                         │
                         ▼
                    L5 (Workers) ──► L6 (Platform)
```

### 2.2 Detected Layer Violations

| Violation | Source | Target | Severity | Evidence |
|-----------|--------|--------|----------|----------|
| LV-001 | L2 (integration.py) | L6 (DB direct) | CRITICAL | 13 SQL statements |
| LV-002 | L2 (cost_intelligence.py) | L6 (DB direct) | CRITICAL | 8 SQL statements |

**Note:** L5→L6 violations in workers are EXPECTED BY DESIGN per PIN-257.

### 2.3 Cross-Layer Authority Gaps

| Gap | Capability | Issue |
|-----|------------|-------|
| AG-001 | LCAP-001 to 010 (Agents) | All 45 routes missing from CAP-008 allowed_routes |
| AG-002 | LCAP-011 to 015 (Cost) | 24 routes, only 8 in CAP-002 allowed_routes |
| AG-003 | LCAP-016 to 019 (Policy) | 32 routes, only 4 in CAP-009 allowed_routes |
| AG-004 | LCAP-028 to 032 (Recovery) | 14 routes, only 5 in CAP-018 allowed_routes |
| AG-005 | LCAP-041 to 045 (Runtime) | 9 routes, none in any allowed_routes |
| AG-006 | LCAP-046 to 048 (Runs) | 7 routes, none in any allowed_routes |
| AG-007 | LCAP-CLI-001 to 010 | 31 commands, no CLI capability exists |
| AG-008 | LCAP-SDK-PY-001 to 015 | 15 methods, no SDK capability governance |
| AG-009 | LCAP-SDK-JS-001 to 016 | 16 methods, no SDK capability governance |
| AG-010 | LCAP-WKR-001 to 003 | 3 worker clusters, no worker capability exists |
| AG-011 | LCAP-033 to 035 (Founder Actions) | 7 routes in wildcard but not explicit |
| AG-012 | LCAP-036 to 040 (Ops) | 10 routes in wildcard but not explicit |
| AG-013 | LCAP-049 to 051 (Guard) | 6 routes partially covered |
| AG-014 | LCAP-052 to 055 (Predictions/Memory) | 6 routes partially covered |

---

## Section 3: Consistency Matrix

### 3.1 LCAP → CAP Mapping Status

| LCAP Range | Domain | Mapped CAP | Coverage |
|------------|--------|------------|----------|
| LCAP-001 to 010 | Agent Autonomy | CAP-008 | **0%** (no allowed_routes) |
| LCAP-011 to 015 | Cost Intelligence | CAP-002 | 33% (8/24 routes) |
| LCAP-016 to 019 | Policy Governance | CAP-009 | 12.5% (4/32 routes) |
| LCAP-020 to 023 | Incidents | CAP-001 | 50% (partial) |
| LCAP-024 to 027 | Trace/Replay | CAP-001 | 60% (partial) |
| LCAP-028 to 032 | Recovery | CAP-018 | 36% (5/14 routes) |
| LCAP-033 to 035 | Founder Actions | CAP-005 | Wildcard only |
| LCAP-036 to 040 | Ops Console | CAP-005 | Wildcard only |
| LCAP-041 to 045 | Runtime API | CAP-016 | **0%** (no allowed_routes) |
| LCAP-046 to 048 | Run Management | None | **SHADOW** |
| LCAP-049 to 051 | Guard System | CAP-001 | 50% |
| LCAP-052 to 053 | Predictions | CAP-004 | 100% |
| LCAP-054 to 055 | Memory | CAP-014 | Wildcard only |
| LCAP-056 to 057 | Integrations | CAP-018 | 60% |
| LCAP-058 | Failures | CAP-001 | 100% |
| LCAP-059 | Governance Review | CAP-011 | 100% |
| LCAP-CLI-* | CLI Commands | None | **NO CAP EXISTS** |
| LCAP-SDK-* | SDK Methods | None | **NO CAP EXISTS** |
| LCAP-WKR-* | Workers | None | **NO CAP EXISTS** |

### 3.2 Coverage Statistics

| Category | Total | Mapped | Shadow | Coverage % |
|----------|-------|--------|--------|------------|
| HTTP Routes (L2) | 365 | ~45 | ~320 | **12%** |
| CLI Commands (L7) | 31 | 0 | 31 | **0%** |
| SDK Methods (L1) | 31 | 0 | 31 | **0%** |
| Workers (L5) | 9 | 0 | 9 | **0%** |
| **Total** | **436** | **~45** | **~391** | **10%** |

---

## Section 4: Layer-Capability Consistency Rules

### 4.1 Rules Applied

| Rule | Description | Violations |
|------|-------------|------------|
| LC-001 | Every HTTP route must map to exactly one CAP | 320+ violations |
| LC-002 | L2 routes must not directly access L6 | 2 violations |
| LC-003 | CLI commands should map to L7 capability | No L7 CAP exists |
| LC-004 | SDK methods should map to L1 capability | No L1 CAP exists |
| LC-005 | Workers should map to L5 capability | No L5 CAP exists |
| LC-006 | Wildcards must have explicit route enumeration | Multiple gaps |

### 4.2 Consistency Verdict

```
┌─────────────────────────────────────────────────────────────────────┐
│                 CAPABILITY-LAYER CONSISTENCY                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  VERDICT: INCONSISTENT                                               │
│                                                                      │
│  Reasons:                                                            │
│  1. 90% of executable paths are unmapped to any capability           │
│  2. No capabilities exist for CLI (L7), SDK (L1), or Workers (L5)    │
│  3. Wildcard routes hide actual route enumeration                    │
│  4. 2 layer violations (L2→L6 direct)                                │
│                                                                      │
│  Layer Coverage:                                                     │
│  ├── L1 (SDK): 0% governed                                           │
│  ├── L2 (API): 12% governed                                          │
│  ├── L5 (Worker): 0% governed                                        │
│  └── L7 (CLI): 0% governed                                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Section 5: Required Actions (NOT IMPLEMENTED - Human Decision)

### 5.1 Option A: Expand Existing Capabilities

Add all discovered routes to existing CAP-XXX allowed_routes:
- CAP-002: Add 16 more cost routes
- CAP-008: Add 45 agent routes
- CAP-009: Add 28 more policy routes
- CAP-016: Add 9 runtime routes
- CAP-018: Add 9 more integration routes

### 5.2 Option B: Create New Capabilities

Create new capabilities for unserved layers:
- CAP-019: CLI Capability (L7) - 31 commands
- CAP-020: SDK Capability (L1) - 31 methods
- CAP-021: Worker Capability (L5) - 9 workers
- CAP-022: Run Management (L2) - 7 routes

### 5.3 Option C: Declare Shadow as FORBIDDEN

Mark all shadow routes as FORBIDDEN and require explicit opt-in.

### 5.4 Option D: Hybrid

Combination of above based on risk assessment.

---

## References

- CAPABILITY_REGISTRY.yaml
- LATENT_CAPABILITIES_DORMANT.yaml (PIN-326)
- PIN-325 Shadow Capability Forensic Audit
