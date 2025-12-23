# PIN-136: M25 Prevention Contract

**Status:** ENFORCED
**Category:** M25 Graduation / Contract
**Created:** 2025-12-23
**Milestone:** M25 Graduation

---

## Purpose

This document defines the **prevention contract** - the exact conditions under which an incident is counted as "prevented" rather than "created."

This contract is:
- **Immutable** for M25 graduation
- **Enforced in code** (see tests)
- **Required for trust**

---

## Prevention Contract Definition

A **prevention** is counted **ONLY IF** all of the following are true:

### Condition 1: Same Pattern Signature

```
prevention.signature_hash == original_pattern.signature_hash
```

The incoming request must match the same normalized signature as the pattern that created the policy.

### Condition 2: Same Tenant

```
prevention.tenant_id == policy.scope_id (when scope_type == 'tenant')
```

A policy scoped to `tenant_A` cannot prevent incidents for `tenant_B`.

### Condition 3: Same Feature Path (Optional)

If policy has `api_endpoint` in condition:

```
request.api_endpoint == policy.condition.api_endpoint
```

### Condition 4: Policy is ACTIVE

```
policy.mode == PolicyMode.ACTIVE
```

Shadow mode policies **do NOT** create prevention records. They only observe.

### Condition 5: No Incident Record Created

```
INSERT INTO incidents ... → BLOCKED (not executed)
```

If an incident record was created, it's not prevention - it's a new incident.

### Condition 6: Prevention Record Written

```
INSERT INTO prevention_records (
    id,
    incident_id_blocked,  -- The incident that WOULD have been created
    pattern_id,
    policy_id,
    tenant_id,
    prevented_at,
    is_simulated
) VALUES (...)
```

A prevention **must** be recorded for audit.

---

## What is NOT Prevention

The following do NOT count as prevention:

| Scenario | Why Not Prevention |
|----------|-------------------|
| Policy in SHADOW mode blocked a request | Shadow only observes |
| Different tenant hit the same pattern | Cross-tenant prevention not allowed |
| Different error type matched a generic policy | Pattern signature must match |
| Incident was created but marked "handled" | An incident is still an incident |
| Request was rate-limited (not blocked) | Rate limiting is mitigation, not prevention |

---

## Enforcement in Code

### Test Suite

```python
# backend/tests/test_m25_policy_overreach.py

class TestPreventionContract:
    def test_prevention_requires_same_tenant(self):
        """A prevention is only valid if same tenant."""
        ...

    def test_prevention_requires_active_policy(self):
        """Prevention only counts if policy is ACTIVE."""
        ...

    def test_prevention_must_not_create_incident(self):
        """Prevention means NO incident was created."""
        ...
```

### Database Schema

```sql
-- migration 042_m25_integration_loop.py (already applied)
CREATE TABLE prevention_records (
    id VARCHAR(64) PRIMARY KEY,
    incident_id_blocked VARCHAR(64),
    pattern_id VARCHAR(64) NOT NULL,
    policy_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    prevented_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for graduation queries
CREATE INDEX ix_prevention_pattern ON prevention_records(pattern_id, tenant_id);
```

---

## Graduation Gate Requirements

For M25 graduation, **Gate 1 (Prevention)** requires:

```sql
SELECT COUNT(*) >= 1
FROM prevention_records
WHERE policy_id = :policy_id
AND is_simulated = FALSE
AND prevented_at > :policy_activated_at
```

**Meaning:** At least one REAL prevention must occur after policy activation.

---

## Simulated vs Real Prevention

| Type | `is_simulated` | Counts for Graduation? |
|------|----------------|------------------------|
| Real prevention (production traffic) | `FALSE` | ✅ Yes |
| Simulated prevention (test script) | `TRUE` | ❌ No |

The pre-graduation evidence we collected is **simulated** (we were debugging).
Real graduation requires **real prevention** from normal traffic.

---

## Prevention Workflow

```
                        ┌──────────────┐
                        │ Same Pattern │
              ┌────────▶│  Signature?  │
              │         └──────┬───────┘
              │                │ Yes
              │         ┌──────▼───────┐
  Request     │         │ Same Tenant? │
  ─────────────┤         └──────┬───────┘
              │                │ Yes
              │         ┌──────▼───────┐
              │         │Policy ACTIVE?│
              │         └──────┬───────┘
              │                │ Yes
              │         ┌──────▼───────┐
              │         │  Block/Route │
              │         │   Request    │
              │         └──────┬───────┘
              │                │
              │         ┌──────▼───────┐
              └────────▶│   Write      │
                        │ Prevention   │
                        │   Record     │
                        └──────────────┘
```

---

## Related PINs

- PIN-135: M25 Integration Loop Wiring
- PIN-130: M25 Graduation System Design
- PIN-078: M19 Policy Layer

---

## Changelog

- 2025-12-23: Initial creation - Prevention contract defined and enforced
