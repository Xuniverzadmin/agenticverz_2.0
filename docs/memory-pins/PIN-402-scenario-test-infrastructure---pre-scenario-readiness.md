# PIN-402: Scenario Test Infrastructure - Pre-Scenario Readiness

**Status:** 📋 PLANNED
**Created:** 2026-01-12
**Category:** Testing / Scenarios

---

## Summary

Pre-scenario readiness audit complete. 0 blockers, 2 watch items. Ready to implement scenario base harness and 5 initial scenario classes.

---

## Details

## Pre-Scenario Readiness Audit

**Date:** 2026-01-12
**Status:** READY TO PROCEED
**Blockers:** 0
**Watch Items:** 2

---

## Audit Results

### ✅ Green (Safe to Proceed)

| Layer | Status | Notes |
|-------|--------|-------|
| Auth & Identity | ✅ | FounderAuthContext, type-based verify_fops_token |
| Lifecycle & State Machines | ✅ | Three orthogonal systems, no aliasing |
| Observability (Phase-8) | ✅ | Immutable events, tenant-scoped, correlation IDs |
| Test Suite Health | ✅ | 4525 passed, 0 failed |
| Code Hygiene & Layering | ✅ | No upward imports, freeze enforcement intact |

### ⚠️ Watch Items (Not Blockers)

1. **Runtime Gate Ordering**
   - Current order: Auth → Onboarding → Lifecycle → Protection → Billing → Handler
   - Scenario tests must assert ordering explicitly
   - First scenario should validate: TERMINATED tenant blocked before billing/protection

2. **Legacy Routes**
   - 410 handlers exist and work
   - New deprecated paths must follow same pattern

---

## Planned Scenario Test Infrastructure

### Base Harness (`tests/scenarios/base.py`)

```python
class ScenarioHarness:
    # Lifecycle helpers
    def create_tenant(self, onboarding_state) -> str
    def advance_onboarding(self, tenant_id, to_state)
    def set_lifecycle_state(self, tenant_id, state)

    # Gate mocking
    def mock_billing_response(self, decision)
    def mock_protection_response(self, decision)

    # Auth helpers
    def get_sdk_headers(self, tenant_id) -> dict
    def get_founder_headers(self) -> dict

    # Observability assertions
    def assert_event_emitted(self, event_type, tenant_id, **kwargs)
    def assert_events_in_order(self, tenant_id, event_types)
    def get_events(self, tenant_id, event_type=None) -> list

    # Gate ordering assertion
    def assert_gate_order(self, tenant_id, expected_order)
```

---

## First 5 Scenario Classes

| # | Scenario | Key Assertions |
|---|----------|----------------|
| 1 | **Happy Path Tenant** | CREATED → COMPLETE → ACTIVE, SDK connects, billing allows, full timeline |
| 2 | **Abuse-Triggered Throttle** | ACTIVE tenant, protection THROTTLE, billing untouched, lifecycle unchanged |
| 3 | **Billing Limit Hit** | ACTIVE tenant, billing 402, protection ALLOW, observability correlates |
| 4 | **Termination Path** | ACTIVE → TERMINATED, keys revoked, SDK blocked, events in order |
| 5 | **Founder Force-Complete** | Stalled onboarding, founder intervention, audit emitted, lifecycle ACTIVE |

---

## Key Principles

1. **Gate Ordering Matters**
   ```
   Auth → Onboarding → Lifecycle → Protection → Billing → Handler
   ```

2. **Query Events, Not Logs**
   - Treat observability as an API
   - Scenarios should assert on event presence and order

3. **Test Real Paths**
   - No mocking auth contexts
   - Use real FOPS tokens for founder scenarios
   - Use real SDK headers for tenant scenarios

---

## Next Steps

1. Draft scenario base harness
2. Implement Happy Path Tenant scenario
3. Design full scenario test matrix
4. Define observability assertions per scenario


---

## Related PINs

- [PIN-336](PIN-336-.md)
- [PIN-398](PIN-398-.md)
- [PIN-399](PIN-399-.md)
