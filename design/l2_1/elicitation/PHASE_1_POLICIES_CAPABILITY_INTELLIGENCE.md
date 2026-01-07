# PHASE 1 — CAPABILITY INTELLIGENCE EXTRACTION
## Domain: Policies

**Status:** EVIDENCE-BACKED
**Date:** 2026-01-07
**L2.1 Surfaces:**
- `POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES`
- `POLICIES.ACTIVE_POLICIES.RATE_LIMITS`
- `POLICIES.ACTIVE_POLICIES.APPROVAL_RULES`
- `POLICIES.POLICY_AUDIT.POLICY_CHANGES`

---

## OUTPUT 1 — DERIVED CAPABILITY INTELLIGENCE TABLE

### Capability: CAP-POL-CONSTRAINTS (Get Policy Constraints)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-POL-CONSTRAINTS` | `guard_policies.py:55` |
| capability_name | Get Policy Constraints | `GET /guard/policies` |
| description | Get policy constraints summary (budget, rate limits, guardrails) | `guard_policies.py:55-83` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single tenant's constraints |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Aggregated view |
| latency_profile | **LOW** | L4 service query |
| execution_style | **ASYNC** | `guard_policies.py:56` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerPoliciesAdapter` | `customer_policies_adapter.py:102` |
| operators | `CustomerPoliciesAdapter.get_policy_constraints()` → `CustomerPolicyReadService.get_policy_constraints()` | `customer_policies_adapter.py:126-155` |
| input_contracts | `tenant_id (REQUIRED via query param)` | Route signature |
| output_contracts | `CustomerPolicyConstraints {tenant_id, budget, rate_limits[], guardrails[], last_updated}` | `customer_policies_adapter.py:87-94` |
| side_effects | **NONE** | Pure read |
| failure_modes | 500 Internal error | `guard_policies.py:81-83` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `guard_policies.py:55-83`, `customer_policies_adapter.py:126-155` |
| risk_flags | None - clean architecture |

---

### Capability: CAP-POL-GUARDRAIL (Get Guardrail Detail)

| Field | Value | Evidence |
|-------|-------|----------|
| capability_id | `CAP-POL-GUARDRAIL` | `guard_policies.py:91` |
| capability_name | Get Guardrail Detail | `GET /guard/policies/guardrails/{guardrail_id}` |
| description | Get detail for a specific guardrail | `guard_policies.py:91-127` |
| mode | **READ** | No state mutation |
| scope | **SINGLE** | Single guardrail |
| mutates_state | **NO** | Read-only |
| bulk_support | **NO** | Single entity |
| latency_profile | **LOW** | L4 service query |
| execution_style | **ASYNC** | `guard_policies.py:92` |
| reversibility | **N/A** | Read operation |
| authority_required | **NONE** | Console token + tenant scope |
| adapters | `CustomerPoliciesAdapter` | `customer_policies_adapter.py:102` |
| operators | `CustomerPoliciesAdapter.get_guardrail_detail()` → `CustomerPolicyReadService.get_guardrail_detail()` | `customer_policies_adapter.py:157-191` |
| input_contracts | `guardrail_id (REQUIRED)`, `tenant_id (REQUIRED via query param)` | Route params |
| output_contracts | `CustomerGuardrail {id, name, description, enabled, category, action_on_trigger}` | `customer_policies_adapter.py:76-85` |
| side_effects | **NONE** | Pure read |
| failure_modes | 404 Guardrail not found, 500 Internal error | `guard_policies.py:116-127` |
| observability | **YES** — API logs | FastAPI middleware |
| replay_feasible | **YES** | Deterministic |
| confidence_level | **HIGH** | Full code evidence, proper L2→L3→L4 |
| evidence_refs | `guard_policies.py:91-127`, `customer_policies_adapter.py:157-191` |
| risk_flags | **No threshold values exposed** - intentional per governance |

---

## OUTPUT 2 — ADAPTER & OPERATOR CROSSWALK

| adapter_id | operator_name | capability_id | sync/async | side_effects | l2_1_surface | layer_route |
|------------|---------------|---------------|------------|--------------|--------------|-------------|
| CustomerPoliciesAdapter | get_policy_constraints() | CAP-POL-CONSTRAINTS | async | None | POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES | L2_1 |
| CustomerPoliciesAdapter | get_policy_constraints() | CAP-POL-CONSTRAINTS | async | None | POLICIES.ACTIVE_POLICIES.RATE_LIMITS | L2_1 |
| CustomerPoliciesAdapter | get_guardrail_detail() | CAP-POL-GUARDRAIL | async | None | POLICIES.ACTIVE_POLICIES.APPROVAL_RULES | L2_1 |
| CustomerPolicyReadService | get_policy_constraints() | CAP-POL-CONSTRAINTS | sync | None | - | L4 |
| CustomerPolicyReadService | get_guardrail_detail() | CAP-POL-GUARDRAIL | sync | None | - | L4 |

### Layer Architecture (CLEAN)

```
L2 (guard_policies.py) — API routes + console auth
      ↓
L3 (CustomerPoliciesAdapter) — Translation + tenant isolation
      ↓
L4 (CustomerPolicyReadService) — Domain logic
      ↓
L6 (Database)
```

**Architectural Status:** CLEAN - proper L2→L3→L4 layering.

---

## OUTPUT 3 — CAPABILITY RISK & AMBIGUITY REPORT

### CAP-POL-CONSTRAINTS

**Risk Flags:** NONE

**Notes:**
- Clean L2→L3→L4 architecture
- Returns aggregated view of budget, rate limits, guardrails
- No internal threshold logic exposed
- Uses `verify_console_token` for auth

**Confidence:** HIGH

---

### CAP-POL-GUARDRAIL

**Risk Flags:**

1. **INTENTIONAL REDACTION**
   - Threshold values NOT exposed (internal implementation detail)
   - Only category and action visible
   - This is governance-correct per PIN-281

**Confidence:** HIGH

---

## STOP CONDITIONS ENCOUNTERED

None - Policies domain is well-structured.

---

## L2.1 SURFACE MAPPING

| Capability ID | L2.1 Surface | Action ID (Seed) | Layer Route | Status |
|---------------|--------------|------------------|-------------|--------|
| CAP-POL-CONSTRAINTS | `POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES` | `ACT-POLICY-BUDGET-VIEW` | L2_1 | ✅ Aligned |
| CAP-POL-CONSTRAINTS | `POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES` | `ACT-POLICY-BUDGET-DOWNLOAD` | L2_1 | **GAP: No download** |
| CAP-POL-CONSTRAINTS | `POLICIES.ACTIVE_POLICIES.RATE_LIMITS` | `ACT-POLICY-RATE-VIEW` | L2_1 | ✅ Aligned |
| CAP-POL-CONSTRAINTS | `POLICIES.ACTIVE_POLICIES.RATE_LIMITS` | `ACT-POLICY-RATE-DOWNLOAD` | L2_1 | **GAP: No download** |
| CAP-POL-GUARDRAIL | `POLICIES.ACTIVE_POLICIES.APPROVAL_RULES` | `ACT-POLICY-APPROVAL-VIEW` | L2_1 | ✅ Aligned |
| CAP-POL-GUARDRAIL | `POLICIES.ACTIVE_POLICIES.APPROVAL_RULES` | `ACT-POLICY-APPROVAL-DOWNLOAD` | L2_1 | **GAP: No download** |
| (none) | `POLICIES.POLICY_AUDIT.POLICY_CHANGES` | `ACT-POLICY-AUDIT-VIEW` | L2_1 | **GAP: No audit endpoint** |
| (none) | `POLICIES.POLICY_AUDIT.POLICY_CHANGES` | `ACT-POLICY-AUDIT-DOWNLOAD` | L2_1 | **GAP: No audit endpoint** |

---

## ADDITIONAL CAPABILITIES IN SEED (Not Implemented)

### GC_L Actions (WRITE/ACTIVATE)

| Seed Action ID | Action Name | Layer Route | Implementation Status |
|----------------|-------------|-------------|----------------------|
| `ACT-POLICY-BUDGET-CREATE` | Create Budget Policy | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-BUDGET-UPDATE` | Update Budget Policy | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-BUDGET-ACTIVATE` | Activate Budget Policy | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-BUDGET-DEACTIVATE` | Deactivate Budget Policy | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-RATE-UPDATE` | Update Rate Limit | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-RATE-ACTIVATE` | Activate Rate Limit | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-APPROVAL-CREATE` | Create Approval Rule | GC_L | **NOT IMPLEMENTED** |
| `ACT-POLICY-APPROVAL-ACTIVATE` | Activate Approval Rule | GC_L | **NOT IMPLEMENTED** |

**Gap:** ALL GC_L (write/activate) actions are in seed but have NO backend implementation.

### Download Actions

| Seed Action ID | Action Name | Implementation Status |
|----------------|-------------|----------------------|
| `ACT-POLICY-BUDGET-DOWNLOAD` | Download Policies | **NOT IMPLEMENTED** |
| `ACT-POLICY-RATE-DOWNLOAD` | Download Rate Limits | **NOT IMPLEMENTED** |
| `ACT-POLICY-APPROVAL-DOWNLOAD` | Download Approval Rules | **NOT IMPLEMENTED** |
| `ACT-POLICY-AUDIT-DOWNLOAD` | Download Audit Trail | **NOT IMPLEMENTED** |

### Audit Surface

| Seed Surface | Action | Implementation Status |
|--------------|--------|----------------------|
| `POLICIES.POLICY_AUDIT.POLICY_CHANGES` | View/Download | **NO API EXISTS** |

**Critical Gap:** Policy audit trail surface has no Customer Console API.

---

## PHASE 1 COMPLETION STATUS

| Criterion | Status |
|-----------|--------|
| All capabilities present in intelligence table | ✅ 2 capabilities documented |
| All adapters/operators cross-referenced | ✅ Clean L2→L3→L4 |
| All UNKNOWNs explicit | ✅ None |
| All risks surfaced | ✅ Intentional redaction noted |
| No UI or binding assumptions | ✅ Code-only evidence |

**Phase 1 Status:** COMPLETE (for Policies domain)

**Overall Assessment:**
- READ operations clean and aligned
- ALL GC_L (write/activate) operations NOT implemented
- Policy audit surface NOT implemented
- Download actions NOT implemented

---

## References

- `backend/app/api/guard_policies.py` — L2 API routes
- `backend/app/adapters/customer_policies_adapter.py` — L3 adapter
- `backend/app/services/policy/customer_policy_read_service.py` — L4 service
- PIN-280, PIN-281 — L2 Promotion Governance
