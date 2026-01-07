# PIN-325: Shadow Capability & Implicit Power Forensic Audit

**Status:** CRITICAL FINDINGS
**Created:** 2026-01-06
**Category:** Governance / Security Audit
**Scope:** Full System Forensic Sweep
**Prerequisites:** PIN-323 (L2-L2.1 Audit Reinforcement), PIN-324 (Console Classification)

---

## Objective

Prove (or falsify) that **no executable system capability exists** that is callable, impactful, or user-affecting without being **explicitly registered, classified, and governed**.

**Operating Mode:** Adversarial — assume malice by omission, treat code as ground truth, treat absence of declaration as a finding.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total HTTP Routes | 377 | Enumerated |
| Registered in Capability Registry | 16 (4.2%) | **CRITICAL GAP** |
| Shadow Capabilities (Unmapped Routes) | 185+ | **VIOLATION** |
| Implicit Authority Paths | 7 critical | **VIOLATION** |
| Frontend-Reachable Unprotected Routes | 7 quarantined | **VIOLATION** |
| Data Leakage Vectors | 30+ | **VIOLATION** |

**CONCLUSION:** The audit **FALSIFIES** the claim that all executable capabilities are governed. The system has significant shadow capabilities operating outside governance.

---

## Section A: Shadow Capabilities

### A1: Route Coverage Gap

| Category | Count | Percentage |
|----------|-------|------------|
| **CORRECTLY MAPPED** | 16 routes | 7.96% |
| **UNMAPPED (Shadow)** | 185 routes | **92.04%** |

### A2: Major Unmapped Route Groups

| Feature Domain | Routes | Capability Expected | Status |
|----------------|--------|---------------------|--------|
| Multi-Agent Orchestration | 45 | CAP-008 | **NO ALLOWED_ROUTES DEFINED** |
| Recovery Suggestion Engine (M10) | 14 | None exists | **NO CAPABILITY EXISTS** |
| Cost Intelligence | 27 | CAP-002 partial | **MOSTLY UNMAPPED** |
| Runtime API | 9 | CAP-016 | **NO ALLOWED_ROUTES DEFINED** |
| Trace Management | 9 | CAP-001 partial | **MOSTLY UNMAPPED** |
| Policy Enforcement | 8 | CAP-009 partial | **MOSTLY UNMAPPED** |

### A3: Severity Distribution

| Severity | Route Count | Examples |
|----------|-------------|----------|
| **CRITICAL** | 59 | `/agents/*`, `/api/v1/recovery/*`, `/blackboard/*`, `/jobs/*` |
| **HIGH** | 45 | `/cost/*`, `/api/v1/runtime/*`, `/traces/*` |
| **MEDIUM** | 51 | `/policy/*`, `/predictions/*`, `/tenants/*` |
| **LOW** | 30 | `/guard/*` (partially mapped) |

### A4: Why Routes Escaped Governance

1. **SDK-Only Classification Loophole**: CAP-008 marked `frontend_invocable: false` but routes are HTTP-accessible
2. **Missing Capability Definitions**: Recovery (M10) has NO capability entry
3. **Wildcard Mapping Vagueness**: CAP-014 uses `GET /api/v1/memory/*` without explicit route listing
4. **Incremental Route Addition**: New routes added without registry updates

---

## Section B: Implicit Authority

### B1: Recovery Auto-Execution Path (CRITICAL)

```
1. POST /api/v1/recovery/ingest (CAP-018) ← Only this is declared
   ↓
2. Background worker: recovery_evaluator.py (NO CAPABILITY CHECK)
   ↓
3. recovery_matcher.suggest() computes confidence
   ↓
4. recovery_rule_engine.should_auto_execute(confidence >= 0.8)
   ↓
5. Auto-executes recovery WITHOUT "recovery:execute" capability
```

**Impact:** Customer failures auto-remediated without explicit governance gate.

### B2: Circuit Breaker Auto-Disable (CRITICAL)

| Component | Location | Trigger | Effect |
|-----------|----------|---------|--------|
| CostSim Circuit Breaker | `costsim/circuit_breaker.py` | Drift > threshold | Auto-disables CostSim V2 |
| TTL Auto-Recovery | Same | Time expiration | Re-enables without approval |

### B3: Unregistered Write Services

| Write Service | API Caller | Capability Declared |
|---------------|------------|---------------------|
| `CostWriteService` | `/cost/features` | **NO** |
| `UserWriteService` | `/api/v1/onboarding/*` | **NO** |
| `IncidentWriteService` | Multiple | **NO** |
| `FounderActionWriteService` | `/ops/actions/*` | **NO** |
| `GuardWriteService` | `/guard/*` mutations | **NO** |

### B4: GET Endpoints with Side Effects

| Endpoint | Side Effect | Governed? |
|----------|-------------|-----------|
| `GET /ops/pulse` | Redis cache write | NO |
| `GET /ops/customers` | Stickiness score caching | NO |
| `GET /ops/customers/at-risk` | Risk classification inference | NO |

---

## Section C: Frontend-Reachable Risks

### C1: CORS Misconfiguration

```python
# /backend/app/main.py:578
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # UNSAFE
    allow_credentials=True,   # UNSAFE
    allow_methods=["*"],      # UNSAFE
    allow_headers=["*"],      # UNSAFE
)
```

**Impact:** Any website can make cross-origin requests to backend.

### C2: Quarantined Routes Still Accessible

| Route | Frontend Status | HTTP Accessible? | Auth Required |
|-------|-----------------|------------------|---------------|
| `/agents` | Quarantined | **YES** | X-Tenant-ID only |
| `/agents/register` | Quarantined | **YES** | X-Tenant-ID only |
| `/blackboard/{key}` | Quarantined | **YES** | X-Tenant-ID only |
| `/jobs` | Quarantined | **YES** | X-Tenant-ID only |
| `/agents/{id}/messages` | Quarantined | **YES** | X-Tenant-ID only |

**Root Cause:** "Not linked in UI" ≠ "Not accessible"

### C3: Protection Gaps

| Protection Layer | Status |
|------------------|--------|
| RBAC on agent routes | **NOT APPLIED** |
| JWT validation | **BYPASSED** via X-Tenant-ID |
| Capability registry check | **NOT IMPLEMENTED** |
| Rate limiting on agents | **NOT APPLIED** |

---

## Section D: Data Surface Leakage

### D1: Logging Leakage (30+ statements)

| Source | Data Type | Risk |
|--------|-----------|------|
| `logger.info/debug/warning/error()` | `tenant_id`, `user_id`, `agent_id` | **CRITICAL** |

### D2: Prometheus Metrics Leakage (8+ metrics)

| Metric | Labels Exposed | Risk |
|--------|----------------|------|
| `nova_llm_tokens_total` | `tenant_id`, `agent_id` | **HIGH** |
| `nova_llm_cost_cents_total` | `tenant_id`, `agent_id` | **HIGH** |
| `nova_llm_tenant_budget_remaining_cents` | `tenant_id` | **HIGH** |

### D3: Event Emission Leakage

| Channel | Data Exposed | Risk |
|---------|--------------|------|
| Redis `aos.events` | `tenant_id` in all event payloads | **HIGH** |

---

## Section E: Constitutional Violations

| Violation | Contract | Finding |
|-----------|----------|---------|
| **CV-001** | Every route must map to one capability | 185 routes unmapped |
| **CV-002** | Customer routes must be READ-ONLY | Write operations with advisory auth only |
| **CV-003** | CAP-008 is SDK-only | All 45 routes HTTP-accessible |
| **CV-004** | Tenant data must be domain-governed | Logging/metrics expose outside domains |

---

## Negative Assertion (Part 6)

> "Is there any executable behavior that affects system state, influences decisions, or exposes tenant data that is NOT represented in the Capability Registry and Console Classification?"

**ANSWER: YES**

**Evidence:**
- 185 unmapped API routes (92% of total)
- 7 implicit authority paths with auto-execution
- 7 frontend-reachable quarantined routes
- 30+ data leakage vectors

**Confidence Statement:**

> Given this audit, the probability of undiscovered executable capability is: **HIGH**, because 92% of API routes are unmapped, critical auto-execution paths have no capability gates, CORS allows universal access, and data leakage exists across logging/metrics/events infrastructure.

---

## Summary Table

| Section | Finding Count | Critical | High | Medium |
|---------|---------------|----------|------|--------|
| A: Shadow Capabilities | 185 routes | 59 | 45 | 81 |
| B: Implicit Authority | 7 paths | 5 | 2 | 0 |
| C: Frontend-Reachable | 7 routes | 3 | 4 | 0 |
| D: Data Leakage | 30+ vectors | 8 | 22 | 0 |
| E: Constitutional | 4 violations | 2 | 2 | 0 |
| **TOTAL** | **233+ findings** | **77** | **75** | **81** |

---

## Evidence Locations

| Finding | Evidence Path |
|---------|---------------|
| Route enumeration | `backend/app/main.py:510-575` |
| Capability registry | `docs/capabilities/CAPABILITY_REGISTRY.yaml` |
| Auto-execute threshold | `backend/app/services/recovery_rule_engine.py:428` |
| CORS config | `backend/app/main.py:578-584` |
| Prometheus metrics | `backend/app/metrics.py:76-110` |
| Event emission | `backend/app/integrations/events.py:276-333` |
| Quarantine directory | `website/app-shell/src/quarantine/` |

---

## Next Actions (NOT IMPLEMENTED — Audit Only)

Potential remediation paths (for human decision):
1. Convert findings into CAPABILITY_REGISTRY deltas
2. Decide what must be killed vs governed
3. Add anti-shadow CI guards
4. Fix CORS configuration
5. Implement capability gates on auto-execution paths

---

## References

- PIN-323: L2-L2.1 Audit Reinforcement (COMPLETE)
- PIN-324: Capability Console Classification (COMPLETE)
- CAPABILITY_REGISTRY.yaml
- CONSOLE_CLASSIFICATION.yaml

---

## Updates

### 2026-01-06: PIN Created
- Full forensic audit completed
- 377 HTTP routes enumerated
- 185 shadow capabilities identified (92% unmapped)
- 7 implicit authority paths found
- 7 frontend-reachable risks documented
- 30+ data leakage vectors catalogued
- 4 constitutional violations confirmed
- Negative assertion answered: YES, undiscovered capabilities exist
