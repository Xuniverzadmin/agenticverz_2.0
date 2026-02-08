# Domain Lifecycle Harness Refactor Plan (V1)

**Scope:** HOC CUS domains (account, integrations, policies, api_keys, …)  
**Non-scope:** Knowledge plane lifecycle (handled separately).  
**Goal:** Provide a **hoc_spine lifecycle harness template** that domains can reuse for stateful entities, without creating a second “source of truth” state machine outside the domain.

## Status (2026-02-08)

- Phase A1 (Account / Tenant lifecycle SSOT): implemented using `Tenant.status` as the canonical persisted lifecycle field.
- Production call sites rewired to DB-backed lifecycle reads and L4-owned lifecycle operations (`account.lifecycle.query`, `account.lifecycle.transition`).
- Governance proof gates (current): `tests/governance/t0` green in strict mode; layer boundaries/cross-domain/purity/pairing all CLEAN.
- All four domain lifecycle phases complete: Phase A1 (Tenant), Phase A2 (Onboarding), Phase B–D (Integrations, Policies, API Keys) confirmed architecturally compliant — no changes needed.

---

## 1) Audit (Current Reality)

### 1.1 Tenant Lifecycle Duplication (Critical)

- Persisted tenant status exists: `Tenant.status` in `backend/app/models/tenant.py`.
- Account domain writes it via L5/L6: `backend/app/hoc/cus/account/L5_engines/tenant_engine.py`, `backend/app/hoc/cus/account/L6_drivers/tenant_driver.py`.
- Legacy Phase-9 tenant lifecycle rules still exist in auth but are DEPRECATED (kept for compatibility):
  - `backend/app/auth/tenant_lifecycle.py`
  - `backend/app/auth/lifecycle_provider.py`
- Request gates and founder endpoints now read the canonical lifecycle state through L4 (`account.lifecycle.query`) backed by account L5/L6.

**Outcome:** tenant lifecycle duplication is resolved (SSOT = `Tenant.status`). Remaining split is onboarding (next section).

### 1.2 Onboarding State Ownership (Split)

- Canonical endpoint→required onboarding state mapping is in hoc_spine authority (pure policy):
  - `backend/app/hoc/cus/hoc_spine/authority/onboarding_policy.py`
- Onboarding state mutations now flow through L4-owned operations and domain-owned L5/L6 (SSOT = `Tenant.onboarding_state`):
  - L4: `account.onboarding.query`, `account.onboarding.advance`
  - L5/L6: `account/L5_engines/onboarding_engine.py`, `account/L6_drivers/onboarding_driver.py`

**Outcome:** onboarding split authority removed. No legacy onboarding transition service remains.

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

### 3.1 Contracts (schemas) and Wiring Surface

- L4 contracts live in `backend/app/hoc/cus/hoc_spine/schemas/lifecycle_harness.py`:
  - `LifecycleReaderPort`, `LifecycleWriterPort`, `LifecycleGateDecision` Protocols
  - (Intentionally generic; domain-specific enums/state live in the domain)

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

### Phase A1: Account (Tenant Lifecycle SSOT) — COMPLETE

- Canonical persisted field: `Tenant.status` (`backend/app/models/tenant.py`).
- Domain-owned rules + transitions:
  - `backend/app/hoc/cus/account/L5_engines/tenant_lifecycle_engine.py`
  - `backend/app/hoc/cus/account/L5_schemas/tenant_lifecycle_enums.py`
  - `backend/app/hoc/cus/account/L5_schemas/lifecycle_dtos.py`
  - `backend/app/hoc/cus/account/L6_drivers/tenant_lifecycle_driver.py`
- L4-owned operations:
  - `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/lifecycle_handler.py`
- Consumers rewired to canonical read surface (no mock/provider authority):
  - `backend/app/api/middleware/lifecycle_gate.py`
  - `backend/app/hoc/api/fdr/account/founder_lifecycle.py`

**Invariant:** L4 owns the transaction boundary; L6 contains no commit/begin semantics; domain engines decide transitions.

### Phase A2: Account (Onboarding SSOT) — COMPLETE (2026-02-08)

Moved onboarding mutation ownership behind account L5/L6 + L4 operations.
All 6 HOC call sites rewired to `async_advance_onboarding()` / `async_get_onboarding_state()`.
Session context files now do real async DB reads (replaced COMPLETE stub).

New files:
- `backend/app/hoc/cus/account/L5_schemas/onboarding_enums.py` — OnboardingStatus enum mirror
- `backend/app/hoc/cus/account/L5_schemas/onboarding_dtos.py` — DTOs
- `backend/app/hoc/cus/account/L6_drivers/onboarding_driver.py` — pure data access (NO COMMIT)
- `backend/app/hoc/cus/account/L5_engines/onboarding_engine.py` — monotonic state machine
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` — L4 handlers + async helpers

Legacy duplicates removed:
- Deleted `backend/app/auth/onboarding_transitions.py`
- Deleted `backend/app/hoc/int/api_keys/engines/onboarding_transitions.py`

Pairing gap: 69 wired, 0 orphaned, 0 direct.
CI: 0 blocking purity, 0 advisory, all 30 init checks pass, 599 t0, 429 t4.

### Phase B: Integrations (Integration + MCP Server Lifecycle) — NO-OP (2026-02-08)

Already architecturally compliant. L5 engines own transitions, L6 drivers persist,
L4 handlers (`integrations_handler.py`, `mcp_handler.py`) are registered. Zero cross-domain violations.
No changes needed.

### Phase C: Policies (Rule/Proposal Lifecycle) — NO-OP (2026-02-08)

Already architecturally compliant. All state mutations flow through L4 → L5 → L6:

- **PolicyRule.status** (ACTIVE → RETIRED): `policy_rules_engine.py` (L5) → `policy_rules_driver.py` (L6) → `policies.rules` handler (L4) wraps in `begin()`
- **PolicyProposal.status** (DRAFT → APPROVED/REJECTED): `policy_proposal_engine.py` (L5) → `policy_proposal_write_driver.py` (L6) → L4 handler wraps transactions
- **Limit.status** (ACTIVE/DISABLED): `policy_limits_engine.py` (L5) → L6 driver → `policies.limits` handler (L4) wraps in `begin()`
- **LimitOverride.status** (PENDING → APPROVED/ACTIVE/EXPIRED/REJECTED/CANCELLED): Complex workflow, all through L4

Zero direct L2→DB writes. L4 owns all `begin()`/`commit()`. L5/L6 have zero explicit transaction calls.
No changes needed.

### Phase D: API Keys — NO-OP (2026-02-08)

Already architecturally compliant in the HOC layer:

- **APIKey creation/revocation**: `tenant_engine.py` (account L5) → `tenant_driver.py` (account L6) → `api_keys.write` handler (L4) commits
- **APIKey freeze/unfreeze**: `keys_engine.py` (api_keys L5) → `keys_driver.py` (api_keys L6) → L4 wraps transaction
- **APIKey reads**: `api_keys_facade.py` (L5) → `api_keys_facade_driver.py` (L6) → `api_keys.query` handler (L4)

Legacy `app/auth/api_key_driver.py` commits directly but is outside HOC (PIN-511 boundary).
No changes needed.

---

## 5) Verification (Mechanical)

- `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci`
- `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py`
- `pytest backend/tests/governance/t0 -q`
  - Current evidence (2026-02-08): `599 passed, 18 xfailed, 1 xpassed`
- `PYTHONPATH=. python3 scripts/ops/hoc_l5_l6_purity_audit.py --all-domains --advisory`
- `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py`
