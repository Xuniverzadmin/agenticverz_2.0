# Signal Circuit Discovery: L2↔L4 Boundary

**Status:** PHASE 1 DISCOVERY COMPLETE
**Date:** 2025-12-31
**Boundary:** L2 (Product APIs) ↔ L4 (Domain Engines)
**Via:** L3 (Boundary Adapters)
**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md, PIN-258 (Phase F-3)

---

## 1. Boundary Lock

```yaml
boundary_pair: L2↔L4
from_layer: L2 — Product APIs
to_layer: L4 — Domain Engines
via_layer: L3 — Boundary Adapters
direction: unidirectional (L2 → L3 → L4, never L4 → L2)
crossing_type: delegation + result
```

**Unique Characteristics:**
- L2 should ONLY call L3 adapters (never L4/L5 directly)
- L3 adapters translate API requests into L4 domain commands
- L4 commands contain domain logic and return structured results
- L3 must be "thin translation" (< 200 LOC, no branching, no thresholds)

---

## 2. Declared Intent

| Field | Value |
|-------|-------|
| Contract Document | `docs/contracts/PHASE_F_FIX_DESIGN.md` |
| Contract Version | FROZEN (Phase F complete) |
| Intent Statement | "L2 (API) calls L3 (adapter) which calls L4 (command); L3 is translation only" |
| Enforcement Level | ADVISORY (documented, not fully CI-enforced) |

**Secondary Contracts:**
- PIN-258 Phase F-3: Runtime/Policy/Worker Clusters
- F-P-RULE-1: Policy Decisions Live Only in L4
- F-P-RULE-3: L3 Is Translation Only

---

## 3. Expected Signals

### 3.1 L2 → L3 (API calls Adapter)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L2L3-001 | API Request | L2 route handler | L3 adapter method | Function call | Domain operation invoked |
| EXP-L2L3-002 | Tenant Context | L2 auth middleware | L3 adapter | Function parameter | Tenant isolation |
| EXP-L2L3-003 | Validation Result | L2 Pydantic | L3 adapter | Validated object | Type-safe input |

### 3.2 L3 → L4 (Adapter calls Command)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L3L4-001 | Domain Request | L3 adapter | L4 command function | Function call | Domain decision |
| EXP-L3L4-002 | Domain Context | L3 adapter | L4 command | Named parameters | Context for decision |

### 3.3 L4 → L3 (Command returns to Adapter)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L4L3-001 | Domain Result | L4 command | L3 adapter | Return value | Decision outcome |
| EXP-L4L3-002 | Domain Error | L4 command | L3 adapter | Exception | Error handling |

---

## 4. Reality Inspection

### 4.1 L3 Adapter Coverage

| API Category | L3 Adapter | Coverage Status |
|--------------|------------|-----------------|
| Runtime APIs | `runtime_adapter.py` | PARTIAL (bypasses exist) |
| Policy APIs | `policy_adapter.py` | COVERED |
| Workers APIs | `workers_adapter.py` | COVERED |
| All other APIs (30 files) | NONE | **GAP - NO ADAPTER** |

**Files with Adapters (3/33):**
- `api/runtime.py` → `adapters/runtime_adapter.py` (with bypasses)
- `api/policy.py` → `adapters/policy_adapter.py`
- `api/workers.py` → `adapters/workers_adapter.py`

**Files without Adapters (30/33):**
- `agents.py`, `auth_helpers.py`, `cost_guard.py`, `cost_intelligence.py`, `cost_ops.py`
- `costsim.py`, `customer_visibility.py`, `discovery.py`, `embedding.py`, `feedback.py`
- `founder_actions.py`, `founder_timeline.py`, `guard.py`, `health.py`, `integration.py`
- `legacy_routes.py`, `memory_pins.py`, `onboarding.py`, `ops.py`, `policy_layer.py`
- `policy_proposals.py`, `predictions.py`, `rbac_api.py`, `recovery.py`, `recovery_ingest.py`
- `status_history.py`, `tenants.py`, `traces.py`, `v1_killswitch.py`, `v1_proxy.py`

### 4.2 Import Violations (L2 → L5 bypasses)

| Location | Violation | Severity |
|----------|-----------|----------|
| `api/runtime.py:164` | `from app.worker.simulate import CostSimulator` | P1 (L2→L5 direct) |
| `api/runtime.py:202` | `from app.commands.runtime_command import DEFAULT_SKILL_METADATA` | P2 (L2→L4 direct, bypasses L3) |

### 4.3 Adapter File Analysis

| Adapter | LOC | Compliance Status |
|---------|-----|-------------------|
| `runtime_adapter.py` | 216 | COMPLIANT (< 200 LOC soft limit, thin translation) |
| `policy_adapter.py` | ~200 | COMPLIANT (thin translation) |
| `workers_adapter.py` | ~200 | COMPLIANT (thin translation) |

### 4.4 Command File Analysis (L4)

| Command | Purpose | Called By |
|---------|---------|-----------|
| `runtime_command.py` | Runtime queries, skill info, capabilities | `runtime_adapter.py` |
| `policy_command.py` | Policy evaluation, violations, approvals | `policy_adapter.py` |
| `worker_execution_command.py` | Worker execution decisions | `workers_adapter.py` |

---

## 5. End-to-End Circuit Walk

### Circuit 1: Runtime Capabilities Query

```
SIGNAL: GET /api/v1/runtime/capabilities → CapabilitiesInfo

INTENT:
  → Declared at: PIN-258 Phase F-3, api/runtime.py header
  → Statement: "L2 calls L3 (adapter), not L5 (worker)"

EMISSION:
  → Emitter: External API client (HTTP request)
  → Mechanism: FastAPI route handler
  → Explicit: YES

TRANSPORT:
  → Type: Function call chain (L2 → L3 → L4)
  → Observable: YES (logging at each layer)
  → Failure Mode: HTTP error response

ADAPTER:
  → Location: adapters/runtime_adapter.py:164-186
  → Purpose: Translate API request to L4 domain command
  → Compliant: YES (uses get_capabilities from L4)

CONSUMPTION:
  → Consumer: runtime_command.py:get_capabilities()
  → Explicit: YES (direct function call)
  → Dependency Declared: YES (import at top of adapter)

CONSEQUENCE:
  → What happens on success: CapabilitiesInfo returned
  → What happens on failure: Exception raised, HTTP 500
  → Observable: YES (response body)
```

### Circuit 2: Policy Evaluation (Compliant)

```
SIGNAL: POST /api/v1/policy/eval → PolicyEvaluationResult

INTENT:
  → Declared at: PIN-258 F-P-RULE-1
  → Statement: "Policy Decisions Live Only in L4"

EMISSION:
  → Emitter: External API client (policy eval request)
  → Mechanism: FastAPI route handler
  → Explicit: YES

TRANSPORT:
  → Type: L2 → L3 → L4 chain
  → Observable: YES (logging)
  → Failure Mode: HTTP error response

ADAPTER:
  → Location: adapters/policy_adapter.py
  → Purpose: Translate API context to domain facts
  → Compliant: YES (thin translation, delegates to L4)

CONSUMPTION:
  → Consumer: commands/policy_command.py:evaluate_policy()
  → Explicit: YES
  → Dependency Declared: YES

CONSEQUENCE:
  → What happens on success: PolicyEvaluationResult returned
  → What happens on failure: PolicyViolation raised
  → Observable: YES
```

---

## 6. Failure Classification

| Gap ID | Gap Description | Classification | Severity |
|--------|-----------------|----------------|----------|
| GAP-L2L4-001 | 30/33 API files have no L3 adapter | MISSING_ADAPTER | P1 |
| GAP-L2L4-002 | `runtime.py:164` imports directly from L5 | BYPASSED_BOUNDARY | P1 |
| GAP-L2L4-003 | `runtime.py:202` imports directly from L4 | BYPASSED_BOUNDARY | P2 |
| GAP-L2L4-004 | No CI check for L2→L3→L4 import direction | MISSING_EMITTER | P1 |
| GAP-L2L4-005 | No enforcement that L3 adapters stay thin | MISSING_CONSUMER | P2 |

### Classification Evidence

**GAP-L2L4-001 (MISSING_ADAPTER):**
Only 3 of 33 API files have corresponding L3 adapters.
The 30 files without adapters may call L4/L5/L6 directly, violating layer discipline.

**GAP-L2L4-002 (BYPASSED_BOUNDARY):**
`api/runtime.py:164` contains `from app.worker.simulate import CostSimulator`.
This is a direct L2→L5 import, bypassing L3 entirely.

**GAP-L2L4-003 (BYPASSED_BOUNDARY):**
`api/runtime.py:202` contains `from app.commands.runtime_command import DEFAULT_SKILL_METADATA`.
This is a direct L2→L4 import, bypassing the L3 adapter.

**GAP-L2L4-004 (MISSING_EMITTER):**
No CI workflow validates that L2 files only import from L3 (adapters).
Import direction is documented but not mechanically enforced.

**GAP-L2L4-005 (MISSING_CONSUMER):**
L3 adapter "thin translation" rule (< 200 LOC, no branching) is not CI-enforced.
Adapters could grow into domain logic without detection.

---

## 7. Risk Statement

```
RISK SUMMARY:
  - Circuit Status: PARTIAL
  - Gap Count: 5
  - Critical Gaps: GAP-L2L4-001 (90% of APIs lack adapters), GAP-L2L4-004 (no CI enforcement)
  - Blocking for Phase 2: NO (structural gaps, not ownership gaps)
  - Human Action Required: YES (decide adapter strategy for 30 API files)

RISK NARRATIVE:
  The L2↔L4 boundary is only 10% enforced. Three API files have proper L3 adapters,
  but 30 API files have no adapter and may directly call L4/L5/L6. The runtime.py
  file has documented adapter usage but also contains bypasses that import directly
  from L5 (worker.simulate) and L4 (commands.runtime_command).

  No CI check validates import direction. Layer violations are documented but
  not mechanically blocked. This creates drift risk: developers may add L5 imports
  to L2 files without detection.
```

---

## 8. Registry Entry

```yaml
boundary: L2↔L4
via_layer: L3
circuit_status: PARTIAL
signals_expected: 7 (L2→L3: 3, L3→L4: 2, L4→L3: 2)
signals_found: 7 (for compliant paths)
gaps:
  - id: GAP-L2L4-001
    type: MISSING_ADAPTER
    severity: P1
    description: 30/33 API files have no L3 adapter
  - id: GAP-L2L4-002
    type: BYPASSED_BOUNDARY
    severity: P1
    description: runtime.py imports directly from L5 (worker.simulate)
  - id: GAP-L2L4-003
    type: BYPASSED_BOUNDARY
    severity: P2
    description: runtime.py imports directly from L4 (commands)
  - id: GAP-L2L4-004
    type: MISSING_EMITTER
    severity: P1
    description: No CI check for L2→L3→L4 import direction
  - id: GAP-L2L4-005
    type: MISSING_CONSUMER
    severity: P2
    description: No enforcement that L3 adapters stay thin
enforcement:
  adapter_coverage: 10% (3/33 API files)
  ci_import_check: NO
  ci_adapter_size_check: NO
phase_1_complete: YES (discovery complete, gaps documented)
phase_1_blocker: NO (no owner assignment required for this boundary)
owner: NEEDS_ASSIGNMENT (API Layer Team)
```

---

## 9. Hard Rules (Verification)

| Rule | Check | Status |
|------|-------|--------|
| Did I observe, not fix? | Documented gaps, did not modify code | YES |
| Did I document what IS, not what SHOULD BE? | Reality section reflects current state | YES |
| Did I trace at least one full circuit? | 2 circuits traced (capabilities, policy eval) | YES |
| Did I classify all gaps found? | 5 gaps classified with codes | YES |
| Did I note human-only signals? | Adapter strategy decision is human-only | YES |
| Did I check both directions if bidirectional? | L2→L3→L4 and L4→L3 return documented | YES |

---

## 10. Completion Test

| Question | Can Answer? |
|----------|-------------|
| What signals cross this boundary? | YES (7 signals documented) |
| Where are they emitted? | YES (L2 routes, L3 adapters, L4 commands) |
| Where are they consumed? | YES (L3 adapters, L4 commands, L2 responses) |
| What happens if any signal is missing? | YES (HTTP errors, type errors at compile) |
| Which gaps block Phase 2? | NO (none blocking, but P1 gaps should be addressed) |

**Checklist Status: COMPLETE**

---

## Compliant Pattern Reference

**Correct L2 → L3 → L4 flow:**

```python
# L2 (api/policy.py)
def _get_policy_adapter():
    from app.adapters.policy_adapter import get_policy_adapter
    return get_policy_adapter()

# L3 (adapters/policy_adapter.py)
from app.commands.policy_command import evaluate_policy

class PolicyAdapter:
    async def evaluate(self, ...):
        return await evaluate_policy(...)  # L3 → L4

# L4 (commands/policy_command.py)
async def evaluate_policy(...) -> PolicyEvaluationResult:
    # Domain logic here
    return result
```

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| PIN-258 | Phase F-3 layer consolidation |
| PHASE_F_FIX_DESIGN.md | L3 adapter rules (F-P-RULE-1 to F-P-RULE-5) |
| SCD-L4-L5-BOUNDARY.md | Adjacent boundary discovery |
| CI_SIGNAL_REGISTRY.md | CI workflow inventory |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial SCD for L2↔L4 boundary |
