# Domain Lifecycle Harness Refactor Plan (V1)

**Scope:** HOC CUS domains (account, integrations, policies, api_keys, …)  
**Non-scope:** Knowledge plane lifecycle (handled separately).  
**Goal:** Provide a **hoc_spine lifecycle harness template** that domains can reuse for stateful entities, without creating a second “source of truth” state machine outside the domain.

---

## 1) Audit (Current Reality)

### 1.1 Tenant Lifecycle Duplication (Critical)

- Persisted tenant status exists: `Tenant.status` in `backend/app/models/tenant.py`.
- Account domain writes it via L5/L6: `backend/app/hoc/cus/account/L5_engines/tenant_engine.py`, `backend/app/hoc/cus/account/L6_drivers/tenant_driver.py`.
- Separately, Phase-9 tenant lifecycle exists in auth as enum+provider:
  - `backend/app/auth/tenant_lifecycle.py`
  - `backend/app/auth/lifecycle_provider.py`
- Request gates and founder endpoints consume the auth provider, not the account domain state:
  - `backend/app/api/middleware/lifecycle_gate.py`
  - `backend/app/hoc/api/fdr/account/founder_lifecycle.py`

**Outcome:** two “ACTIVE/SUSPENDED/TERMINATED/ARCHIVED” systems that can drift.

### 1.2 Onboarding State Ownership (Split)

- Canonical endpoint→required onboarding state mapping is in hoc_spine authority (pure policy):
  - `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`
- Onboarding mutations are performed by an auth service that writes `Tenant.onboarding_state`:
  - `backend/app/auth/onboarding_transitions.py`
- Multiple L2/middleware call sites invoke onboarding transitions directly:
  - `backend/app/auth/gateway_middleware.py`
  - `backend/app/hoc/api/int/general/sdk.py`
  - `backend/app/hoc/api/int/agent/onboarding.py`

### 1.3 Other Domain Lifecycles Already Exist (Good Inputs)

- Integrations: `CusIntegrationStatus` in `backend/app/models/cus_models.py`.
- MCP servers: `McpServerStatus` in `backend/app/models/mcp_models.py`.
- Policies: `PolicyRuleStatus` in `backend/app/models/policy_control_plane.py`.
- API Keys: key status fields exist in `backend/app/models/tenant.py` (APIKey).

---

## 2) Target (First Principles)

### 2.1 “Template in hoc_spine, State in Domain”

- hoc_spine provides a **generic harness**:
  - authority gating interface (allowed/blocked + reason)
  - idempotency request shape
  - audit record shape (domain-agnostic)
  - transaction boundary conventions (L4 owns commit)
- Domains provide:
  - the enum/state model, transition rules, and actor policy
  - persistence and side effects via domain L5/L6

### 2.2 Single Source of Truth Rule

For each stateful entity (tenant, integration, policy rule, api key):
- exactly one persisted state field is canonical
- all gates and endpoints read that canonical state via the owning domain’s read surface

---

## 3) hoc_spine Deliverable: Lifecycle Harness Kit

### 3.1 New Contracts (schemas) and Behaviors (utilities)

- `hoc_spine/schemas/` (types/protocols only, no standalone functions beyond allowed Law-6 patterns):
  - `LifecycleActor`, `LifecycleTransitionRequest`, `LifecycleTransitionResult`
  - `LifecycleStateReader` / `LifecycleStateWriter` Protocols
- `hoc_spine/utilities/` (behavior):
  - transition validation helpers (monotonic where needed, allowed transitions table)
  - idempotency key constructors
  - audit payload constructors

### 3.2 L4 Handler Pattern (Harness Wrapper)

- L4 handler:
  - validates params/actor
  - loads current state via domain reader
  - calls domain transition engine
  - commits (L4 owns commit)
  - emits dispatch audit and lifecycle audit payload (domain-agnostic)

Domains never import hoc_spine L4; they implement logic and are called by L4.

---

## 4) Domain Rollout Plan (Phased)

### Phase A: Account (Tenant Lifecycle + Onboarding)

1. Choose persistence for tenant runtime lifecycle:
   - Option A: normalize `Tenant.status` to represent lifecycle states.
   - Option B: add a dedicated persisted field `Tenant.lifecycle_state` (recommended if `status` is overloaded).
2. Move Phase-9 lifecycle rules into account-owned engine:
   - `backend/app/hoc/cus/account/auth/L5_engines/tenant_lifecycle_engine.py`
3. Rewire consumers to account-owned reader/writer:
   - `backend/app/api/middleware/lifecycle_gate.py`
   - `backend/app/hoc/api/fdr/account/founder_lifecycle.py`
4. Onboarding transitions:
   - move mutation ownership to account domain (engine+driver), keep hoc_spine policy table canonical.

### Phase B: Integrations (Integration + MCP Server Lifecycle)

1. Add L5 engines for status transitions:
   - `CusIntegrationStatus` and `McpServerStatus`
2. Provide L4 handler operations for:
   - state query (read-only)
   - controlled mutations (enable/disable/error)

### Phase C: Policies (Rule/Proposal Lifecycle)

1. Ensure all rule/proposal transitions are domain-owned and L4-wrapped where cross-domain/human approvals apply.
2. Use harness kit for audit/idempotency where transitions are externally triggered.

### Phase D: API Keys

1. Centralize API key status transitions in api_keys domain L5.
2. Ensure tenant termination effects are coordinated at L4 when they touch multiple domains.

---

## 5) Verification (Mechanical)

- `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`
- `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`
- `pytest backend/tests/governance/t0 -q`
- `pytest backend/tests/e2e/test_phase9_lifecycle_e2e.py -q`

