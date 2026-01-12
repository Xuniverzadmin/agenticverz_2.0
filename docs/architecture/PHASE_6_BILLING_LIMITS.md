# Phase-6 — Billing, Plans & Limits (Design Template v1)

**Status:** DESIGN-ONLY (No gateway, no pricing)
**Created:** 2026-01-12
**Dependency:** Tenant.onboarding_state == `COMPLETE`
**Non-dependency:** Auth, onboarding, roles (all frozen)
**Reference:** PIN-399

---

## 6.0 Prime Directive

> **Billing never blocks onboarding.**
> **Limits never block identity or setup.**

A tenant must always be able to:

* sign up
* complete onboarding
* create API keys
* connect SDK

**before** any commercial enforcement applies.

---

## 6.1 Conceptual Separation (Do Not Collapse These)

Phase-6 introduces **three orthogonal concepts**:

| Concept           | Answers                          | Mutable?            |
| ----------------- | -------------------------------- | ------------------- |
| **Plan**          | What is this tenant entitled to? | Yes (admin/founder) |
| **Limits**        | How much can they use?           | Yes (derived)       |
| **Billing State** | Are they in good standing?       | Yes                 |

None of these:

* affect auth
* affect onboarding
* affect role assignment

---

## 6.2 Billing Applicability Gate

Billing logic is evaluated **only if**:

```text
tenant.onboarding_state == COMPLETE
```

Before COMPLETE:

* billing APIs return **neutral placeholders**
* limits are **not enforced**
* usage is **tracked but not blocked**

This preserves:

* ONBOARD-001
* customer parity
* trial friendliness

---

## 6.3 Billing State Model (Template)

This is **not** tied to a gateway.

```text
BillingState:
  TRIAL
  ACTIVE
  PAST_DUE
  SUSPENDED
```

### Semantics (Locked)

| State     | Meaning                     |
| --------- | --------------------------- |
| TRIAL     | Default after COMPLETE      |
| ACTIVE    | Valid paid plan             |
| PAST_DUE  | Payment issue, grace period |
| SUSPENDED | Usage blocked, data intact  |

No other states allowed in v1.

---

## 6.4 Plan Model (Abstract)

Plans are **named contracts**, not pricing logic.

```text
Plan:
  id: string
  name: string
  tier: enum (FREE, PRO, ENTERPRISE)
  limits_profile: string
```

Important:

* No prices
* No currency
* No billing cycle assumptions
* No gateway IDs

Those come later.

---

## 6.5 Limits Model (Derived, Not Stored)

Limits are **derived from plan**, never hand-edited.

Example limits (illustrative only):

```text
Limits:
  max_requests_per_day
  max_active_agents
  max_storage_mb
  max_monthly_cost
```

Rules:

* Limits are evaluated **at runtime**
* Limits are enforced **after COMPLETE**
* Limits may emit warnings before enforcement

---

## 6.6 Enforcement Semantics (Strict)

### What Limits Can Do

* Throttle
* Reject with explicit error
* Emit usage warnings

### What Limits Must NOT Do

* Mutate onboarding state
* Revoke API keys silently
* Affect auth or roles

---

## 6.7 Failure Contracts (Template)

When a limit is exceeded:

```json
{
  "error": "limit_exceeded",
  "limit": "max_requests_per_day",
  "current_value": 120345,
  "allowed_value": 100000,
  "plan": "FREE",
  "billing_state": "TRIAL"
}
```

When billing state blocks usage:

```json
{
  "error": "billing_suspended",
  "billing_state": "SUSPENDED",
  "next_action": "contact_support"
}
```

No generic 403s.
No permission language.
No onboarding language.

---

## 6.8 Mock-First Implementation Contract

Until a real gateway exists:

### Mock Provider Interface

```python
class BillingProvider(Protocol):
    def get_billing_state(self, tenant_id: str) -> BillingState: ...
    def get_plan(self, tenant_id: str) -> Plan: ...
    def get_limits(self, plan: Plan) -> Limits: ...
```

Initial implementation:

* hardcoded plan assignment
* hardcoded limits
* deterministic behavior
* no network calls

This ensures:

* zero refactor when Stripe/etc is added
* stable contracts for backend & frontend

---

## 6.9 API Surface (Design Only)

### Read APIs (Customer-Facing)

```
GET /api/v1/billing/status
GET /api/v1/billing/limits
GET /api/v1/billing/usage
```

These:

* are available only after COMPLETE
* are read-only
* never mutate state

---

### Mutation APIs (Founder / Internal Only)

```
POST /founder/billing/assign-plan
POST /founder/billing/set-state
```

Rules:

* explicit audit
* explicit reason
* no automatic transitions

---

## 6.10 Console Behavior (Template)

| Console               | Billing Visibility       |
| --------------------- | ------------------------ |
| customer console      | plan + limits + usage    |
| preflight-agenticverz | same as customer         |
| preflight-fops        | aggregated metrics       |
| fops.com              | full control + overrides |

Console origin still grants **no authority**.

---

## 6.11 Phase-6 Invariants (LOCKED)

### BILLING-001

> Billing never blocks onboarding.

### BILLING-002

> Limits are derived, not stored.

### BILLING-003

> Billing state does not affect roles.

### BILLING-004

> No billing mutation without audit.

### BILLING-005

> Mock provider must satisfy same interface as real provider.

---

## 6.12 Explicit Non-Goals (To Prevent Drift)

These are **NOT** part of Phase-6:

* No pricing math
* No subscriptions
* No coupons
* No proration
* No invoices
* No taxes
* No gateway webhooks

Those are **Phase-7+**.

---

## 6.13 Completion Criteria (Design Phase)

Phase-6 (design) is complete when:

* Plan, BillingState, Limits are defined
* Provider interface is fixed
* API surface is documented
* Invariants are written
* No code touches onboarding/auth/roles

---

## 6.14 Implementation Sequence (When Ready)

When implementation begins:

1. Create `BillingState` enum in `app/billing/state.py`
2. Create `Plan` model (no DB table yet)
3. Create `Limits` derivation (code only)
4. Create `MockBillingProvider`
5. Create read-only APIs
6. Add tests (no gateway mocking)
7. Wire to console

---

## Related Documents

- PIN-399: Onboarding State Machine (dependency)
- Phase-5: Post-Onboarding Roles (non-dependency)
- ONBOARD_STATE_MACHINE_V1.md: State definitions
