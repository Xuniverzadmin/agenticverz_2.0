# Console Truth Model

**Status:** FROZEN
**Date:** 2025-12-27
**Reference:** PIN-190, PIN-138, visibility_contract.yaml

---

## Truth Anchor

> **In Agenticverz, consoles are separated by IDENTITY and ORIGIN, not routes.**

---

## The Rule

Consoles are **NOT** separated by API prefix (e.g., `/api/ops`, `/api/user`).

Consoles **ARE** separated by:
1. **SUBDOMAIN** (Host header)
2. **AUTH AUDIENCE** (JWT audience claim)

---

## Console Topology

| Console | Subdomain | Audience | Purpose |
|---------|-----------|----------|---------|
| **customer** | console.agenticverz.com | aos-customer | Customer trust & control |
| **founder** | fops.agenticverz.com | aos-founder | Founder ops (internal) |
| preflight-customer | preflight-console.agenticverz.com | aos-internal | Mirrors customer |
| preflight-founder | preflight-fops.agenticverz.com | aos-internal | Mirrors founder |

**Two logical consoles.** Preflight consoles inherit visibility from parent.

---

## How Console Scope Enforcement Works

### Same Route, Different Console

The **same API route** behaves differently based on subdomain + auth:

```
GET /api/v1/feedback

Host: console.agenticverz.com      → 403 (customer: FORBIDDEN)
Host: fops.agenticverz.com          → 200 (founder: REQUIRED)
```

### Enforcement Flow

```
Request arrives
    ↓
Extract Host header → Identify console
    ↓
Extract JWT audience → Verify identity
    ↓
Lookup visibility declaration → REQUIRED / OPTIONAL / FORBIDDEN
    ↓
Return response or reject
```

---

## Visibility Declaration

Every artifact must declare visibility for **both** logical consoles:

```yaml
pattern_feedback:
  consoles:
    customer: FORBIDDEN   # Customers should not see raw patterns
    founder: REQUIRED     # Founders need to see patterns
```

| Value | Meaning |
|-------|---------|
| **REQUIRED** | Console MUST be able to access this data |
| **OPTIONAL** | Console MAY access this data |
| **FORBIDDEN** | Console MUST NOT access this data |

---

## Phase B vs Phase C Enforcement

| Phase | Mode | What Validator Checks |
|-------|------|----------------------|
| **Phase B** | DECLARATIVE | Both consoles declared for each artifact |
| **Phase C** | RUNTIME | Subdomain + auth returns expected status |

---

## Common Mistake (Killed)

### Wrong Mental Model

```
/api/ops/*    → Founder console
/api/guard/*  → Customer console
/api/user/*   → Customer console
```

**This is INCORRECT.** Routes are shared. Consoles are separated by origin.

### Correct Mental Model

```
Host: fops.agenticverz.com + aos-founder token  → Founder console
Host: console.agenticverz.com + aos-customer token  → Customer console
```

**Same routes.** Different identity. Different visibility.

---

## Validation

```bash
# Phase B: Declarative check
python3 scripts/ops/visibility_validator.py --check-all --check-console-scope

# Phase C: Runtime enforcement
python3 scripts/ops/visibility_validator.py --check-all --strict-console-scope
```

---

## References

| Document | Location |
|----------|----------|
| Visibility Contract | `docs/contracts/visibility_contract.yaml` |
| Subdomain Rollout Plan | `docs/memory-pins/PIN-190-phase-b-subdomain-rollout-plan.md` |
| Console Structure Audit | `docs/memory-pins/PIN-138-m28-console-structure-audit.md` |
| Validator | `scripts/ops/visibility_validator.py` |

---

*Generated: 2025-12-27*
*Frozen: 2025-12-27*
*Reference: Console Scope Enforcement Gate (CSEG)*
