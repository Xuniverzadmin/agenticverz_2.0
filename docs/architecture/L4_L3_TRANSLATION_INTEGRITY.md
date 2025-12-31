# L4 → L3 Translation Integrity

**Status:** PHASE B COMPLETE
**Generated:** 2025-12-31
**Method:** L3 adapter enumeration + domain logic detection
**Reference:** LAYERED_SEMANTIC_COMPLETION_CONTRACT.md (Phase B)

---

## Purpose

This document verifies that L3 adapters translate data and context without altering domain meaning.

**Translation Definition (FROZEN):**
> L3 translation = shape, transport, protocol, context binding — never rules, thresholds, or classification.

---

## Guardrails Acknowledged

1. ✅ L4 is authoritative ground truth
2. ✅ Phase B is descriptive only — no adapter redesign
3. ✅ Translation = shape, transport, protocol, context binding

---

## Summary Statistics

| Classification | Count | Percentage |
|----------------|-------|------------|
| ✅ Valid L3 (no domain logic) | 8 | 61.5% |
| ⚠️ Violation (domain logic present) | 4 | 30.8% |
| ⚠️ Borderline (minor domain logic) | 1 | 7.7% |
| **Total L3 Adapters** | **13** | 100% |

**Total LOC:** 4,126 (average 317 LOC per adapter)

---

## L3 Adapters Enumerated

### Valid L3 Translators (No Violations)

| # | File | Component | LOC | Transforms |
|---|------|-----------|-----|------------|
| 1 | `skills/adapters/claude_adapter.py` | ClaudeAdapter | 344 | Prompt → Anthropic API → LLMResponse |
| 2 | `planners/stub_adapter.py` | StubPlanner | 91 | Goal → Single-step fallback plan |
| 3 | `planners/anthropic_adapter.py` | AnthropicPlanner | 383 | Goal → Claude API → PlannerOutput |
| 4 | `events/nats_adapter.py` | NatsAdapter | 62 | Topic + Payload → NATS message |
| 5 | `auth/oauth_providers.py` | OAuthProviders | 322 | OAuth code → User info (Google/Azure) |
| 6 | `events/publisher.py` | BasePublisher | 106 | Adapter factory → Event backend |
| 7 | `planner/interface.py` | PlannerInterface | 451 | Schema definitions + validation |
| 8 | `skills/adapters/metrics.py` | MetricsInstrumentation | 368 | LLM response → Prometheus metrics |

**Notes:**
- Adapter #8 (metrics.py) contains cost estimation but is infrastructure, not domain logic.
- All 8 adapters are pure translators with no rules, thresholds, or classification.

---

## Violations Detected

### VIOLATION-B01: OpenAI Adapter (HIGH)

| Field | Value |
|-------|-------|
| File | `skills/adapters/openai_adapter.py` |
| LOC | 505 |
| Domain Logic | Safety limits embedded in adapter |

**Evidence:**
- `_check_safety_limits()`: Enforces rate limits (`REQUESTS_PER_MINUTE`)
- `max_cost_cents_per_request`: Budget enforcement threshold
- `ALLOWED_MODELS`: Model allowlisting restriction logic
- ~150 LOC of safety/policy logic

**Classification:** These are thresholds and constraints, not translation.

**Expected Authority:** L4 PolicyEngine or L4 CostGuard

---

### VIOLATION-B02: CostSim V2 Adapter (HIGH)

| Field | Value |
|-------|-------|
| File | `costsim/v2_adapter.py` |
| LOC | 546 |
| Domain Logic | Cost/risk modeling, feasibility decisions |

**Evidence:**
- `_estimate_step_v2()`: ML coefficient application, skill-specific cost heuristics
- Risk assessment with configurable threshold
- Budget feasibility checks
- Confidence score computation (classification)
- ~230 LOC of cost/risk modeling

**Classification:** These are classification and decision operations.

**Expected Authority:** L4 CostAnomalyDetector or L4 PolicyEngine

---

### VIOLATION-B03: Clerk Auth Provider (MEDIUM)

| Field | Value |
|-------|-------|
| File | `auth/clerk_provider.py` |
| LOC | 368 |
| Domain Logic | Role-to-level mapping, tenant isolation |

**Evidence:**
- `_roles_to_level()`: Role-to-approval-level mapping (admin→5, manager→4, team_lead→3)
- Tenant isolation enforcement: Verifies `user.tenant_id` matches request
- ~30 LOC of authorization classification

**Classification:** Authorization classification belongs in L4.

**Expected Authority:** L4 RBACEngine

---

### VIOLATION-B04: OIDC Provider (MEDIUM)

| Field | Value |
|-------|-------|
| File | `auth/oidc_provider.py` |
| LOC | 307 |
| Domain Logic | Role extraction and mapping |

**Evidence:**
- `get_roles_from_token()`: Extracts roles from multiple Keycloak claim paths
- `map_keycloak_roles_to_aos()`: Role name mapping (realm-admin→admin, developer→dev)
- Role path parsing (`"/admin"` → role `"admin"`)
- ~80 LOC of role classification

**Classification:** Role classification belongs in L4.

**Expected Authority:** L4 RBACEngine

---

### VIOLATION-B05: Tenant LLM Config (MEDIUM)

| Field | Value |
|-------|-------|
| File | `skills/adapters/tenant_config.py` |
| LOC | 273 |
| Domain Logic | Model selection policy, task-based optimization |

**Evidence:**
- `get_effective_model()`: Model selection based on allowlist + fallback logic
- `get_model_for_tenant()`: Task-based model optimization (planning→cheap, high_value→expensive)
- Budget and rate limit configuration (policy parameters)
- ~60 LOC of policy/decision logic

**Classification:** Policy decisions belong in L4.

**Expected Authority:** L4 PolicyEngine or L4 CostGuard

---

## Violation Summary

| ID | Adapter | Severity | Domain Logic Type | LOC |
|----|---------|----------|-------------------|-----|
| B01 | OpenAIAdapter | HIGH | Safety limits, budget enforcement | ~150 |
| B02 | CostSimV2Adapter | HIGH | Cost modeling, risk classification | ~230 |
| B03 | ClerkAuthProvider | MEDIUM | Role mapping, tenant isolation | ~30 |
| B04 | OIDCProvider | MEDIUM | Role extraction, role mapping | ~80 |
| B05 | TenantLLMConfig | MEDIUM | Model selection policy | ~60 |

**Total domain logic in L3:** ~550 LOC (13% of total L3 code)

---

## Pattern Analysis

### What L4 Authority Should Govern Each Violation

| Violation | Current Location | Expected L4 Authority |
|-----------|------------------|----------------------|
| B01 (safety limits) | OpenAIAdapter | PolicyEngine, CostGuard |
| B02 (cost modeling) | CostSimV2Adapter | CostAnomalyDetector |
| B03 (role mapping) | ClerkAuthProvider | RBACEngine |
| B04 (role extraction) | OIDCProvider | RBACEngine |
| B05 (model selection) | TenantLLMConfig | PolicyEngine |

### Violation Clustering

| L4 Authority | Violation Count | Expected Consolidation |
|--------------|-----------------|------------------------|
| PolicyEngine | 2 (B01, B05) | Policy decisions |
| CostGuard/Detector | 2 (B01, B02) | Budget/cost rules |
| RBACEngine | 2 (B03, B04) | Role classification |

---

## Conformance Assessment

| Metric | Value |
|--------|-------|
| Total L3 adapters | 13 |
| Valid translators | 8 (61.5%) |
| Domain logic violations | 5 (38.5%) |
| Total violation LOC | ~550 |
| Violation % of L3 code | 13% |

---

## Phase B Completion Checklist

- [x] L3 adapters enumerated (13 total)
- [x] Each adapter inspected for domain logic
- [x] Violations identified and classified (5 violations)
- [x] Expected L4 authorities documented
- [x] No adapter redesign proposed
- [x] No fixes attempted

---

## Cross-Reference with Phase A

| Phase A Shadow Logic | Phase B Violation |
|---------------------|-------------------|
| SHADOW-001 (auto-execute threshold) | Not in L3 (L5 issue) |
| SHADOW-002 (category heuristics) | Not in L3 (L5 issue) |
| SHADOW-003 (recovery mode heuristics) | Not in L3 (L5 issue) |

**Observation:** Phase A shadow logic is in L5 (workers). Phase B violations are in L3 (adapters). No overlap — these are distinct layer issues.

---

## Next Phase

**Phase C: L3 → L2 API Truthfulness**

Prerequisites:
- Phase B artifact exists (this document)
- Violations documented (5 items)
- No blocking violations

**Status:** Phase B COMPLETE. Ready for Phase C.

---

**Generated by:** Claude Opus 4.5
**Contract:** LAYERED_SEMANTIC_COMPLETION_CONTRACT.md
**Constraint:** Claude did NOT fix violations, only recorded them.
