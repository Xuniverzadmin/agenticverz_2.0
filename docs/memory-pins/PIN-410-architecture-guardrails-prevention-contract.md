# PIN-410: Architecture Guardrails & Prevention Contract

**Status:** LOCKED
**Category:** Governance / Architecture / Prevention
**Created:** 2026-01-13
**Author:** System
**Related:** CLAUDE_AUTHORITY.md Section 12-13, BL-ARCH-001 to BL-ARCH-005

---

## Summary

Final, durable, no-workarounds guardrail pack to prevent silent authority leaks, convenience-driven drift, and CI-green-but-wrong fixes **permanently**.

---

## Prime Directive (Non-Negotiable)

> **Architecture correctness is higher priority than test pass rate, delivery speed, or convenience.**

If forced to choose:
- RED CI with correct design → **ACCEPT**
- GREEN CI with workaround → **REJECT**

Claude must **stop and escalate**, not patch.

---

## Key Rules

### 1. Identity vs Authority (Hard Split)

| Concept   | Source                                  | Never Derived From   |
|-----------|-----------------------------------------|----------------------|
| Identity  | External IdP (Clerk, FOPS JWT, API key) | Frontend, env flags  |
| Authority | Backend domain logic                    | JWT claims, frontend |
| UX        | Frontend                                | Security assumptions |

### 2. "No Workaround" Rules (Absolute)

Claude is explicitly forbidden from:
- Adding fallbacks like `if not roles: assign dev role`
- Skipping JWT verification (aud, iss, exp, nbf)
- Introducing mock contexts to "fix tests"
- Editing tests to accept wrong behavior
- Using environment flags to change authority

### 3. Mandatory Stop Conditions

Claude must **halt and ask** when:
- Fix requires changing authority flow
- Fix requires adding default permissions
- Fix relies on test-only behavior
- Fix weakens an invariant
- Fix changes security behavior by environment

### 4. Design-First Order (Always)

1. Identify invariant(s)
2. Validate layer boundaries
3. Design correct abstraction
4. Update architecture docs
5. Implement
6. Fix tests

**Never:** Implement → rationalize, or Patch tests → backfill design

### 5. Layer Boundary Rules (Immutable)

| Layer       | Can Import                   | Cannot Import    |
|-------------|------------------------------|------------------|
| Domain (L4) | Python stdlib, domain models | FastAPI, Request |
| API (L3)    | Domain, FastAPI              | Frontend logic   |
| Frontend    | API contracts                | Authority logic  |

### 6. Test Integrity

**Tests MUST:**
- Reflect real execution paths
- Use real tokens or real providers
- Fail loudly when architecture breaks

**Tests MUST NOT:**
- Mock authority
- Patch auth contexts
- Bypass middleware
- Depend on execution order

### 7. Environment Parity Rule

> **Preflight changes visibility, never authority.**

Same auth rules, same lifecycle gates, same billing/protection behavior.

### 8. Final Safety Check

> **If this code were open-sourced tomorrow, would its security still be correct without tribal knowledge?**

If not an immediate **YES**, Claude must not proceed.

---

## Behavior Library Rules Added

| Rule ID | Name | Severity |
|---------|------|----------|
| BL-ARCH-001 | Architecture Correctness Priority | BLOCKER |
| BL-ARCH-002 | No Workaround Rules | BLOCKER |
| BL-ARCH-003 | Design-First Enforcement | BLOCKER |
| BL-ARCH-004 | Test Integrity Rules | BLOCKER |
| BL-ARCH-005 | Mandatory Escalation Stop Conditions | BLOCKER |

---

## Artifacts Updated

| Artifact | Location | Changes |
|----------|----------|---------|
| CLAUDE_AUTHORITY.md | `/root/agenticverz2.0/CLAUDE_AUTHORITY.md` | Added Section 12 (Architecture Guardrails) and Section 13 (Final Safety Check) |
| behavior_library.yaml | `docs/behavior/behavior_library.yaml` | Added BL-ARCH-001 through BL-ARCH-005 rules |

---

## Claude Architecture Contract (YAML)

```yaml
claude_architecture_contract:
  priority_order:
    - invariants
    - architecture
    - correctness
    - tests
    - speed

  forbidden_actions:
    - add_default_roles
    - bypass_auth_for_env
    - weaken_jwt_validation
    - mock_authority
    - patch_tests_to_accept_wrong_behavior

  mandatory_actions:
    - escalate_on_authority_change
    - update_docs_on_design_change
    - prefer_red_ci_over_wrong_fix

  escalation_phrase: |
    STOP — architectural decision required.
```

---

## Result

If Claude follows this:
- Auth will not be revisited again
- No silent authority leaks can re-enter
- Tests become trustworthy
- Architecture stays boring and correct

---

## References

- `CLAUDE_AUTHORITY.md` Section 12-13
- `docs/behavior/behavior_library.yaml` (BL-ARCH-* rules)
- `docs/playbooks/SESSION_PLAYBOOK.yaml`
