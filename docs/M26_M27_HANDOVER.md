# M26 → M27 Handover Document

**Status:** ✅ COMPLETE, FROZEN, PRODUCTION-CREDIBLE
**Freeze Date:** 2025-12-23
**Scope Owner:** Infra / Core Systems

---

## 1. What M26 Guarantees (Authoritative Contract)

M26 formally guarantees the following invariants:

### Cost Attribution Invariant

> Every token spent is attributable to **tenant → user → feature → request**

No exceptions. No silent paths.

### Cost → Control Invariant

> Every HIGH / CRITICAL cost anomaly **must escalate** into the M25 loop
> and result in **an actionable artifact** (incident, recovery, policy).

If this invariant breaks, the system must **fail loudly**.

### Environment Determinism Invariant

> Any execution context that spends real money must validate secrets
> explicitly and fail fast if missing.

No implicit inheritance. No shell magic.

---

## 2. Prevention Stack (7 Layers, Mandatory)

| # | Layer | File | Purpose |
|---|-------|------|---------|
| 1 | CI SQL Guard | `scripts/ci/check_sqlmodel_exec.sh` | Blocks `session.exec(text())` |
| 2 | CI Env Guard | `scripts/ci/check_env_misuse.sh` | Blocks new `os.environ.get()` for secrets |
| 3 | Schema Parity | `app/utils/schema_parity.py` | Prevents model ↔ DB drift |
| 4 | Route Inventory | `tests/test_m26_prevention.py` | Ensures APIs are wired |
| 5 | Loop Contract | `tests/test_m26_prevention.py` | Guarantees anomaly → incident |
| 6 | Centralized Secrets | `app/config/secrets.py` | Single source of truth |
| 7 | Fail-Fast Startup | `app/main.py:lifespan()` | No silent money burns |

**Any PR that weakens these is invalid.**

---

## 3. M26 Code Freeze Rules

### Allowed

- Bug fixes
- Infra compatibility fixes
- Dependency updates (with tests)

### Forbidden

- New cost features
- UI expansion
- New anomaly types
- New budget semantics

**Reason:** M26 is a foundation, not a playground.

---

## 4. Known Non-Goals of M26 (Do NOT Backfill)

M26 explicitly does **NOT**:

- Auto-throttle traffic
- Auto-change models
- Auto-block users
- Auto-rewrite policies
- Enforce pricing plans

**M26 detects and escalates.**
**M27 decides and acts.**

This separation is intentional.

---

## 5. Technical Debt (Tracked)

### Environment Variable Misuse

- **Count:** 33 violations as of M26 freeze
- **Location:** Various service files using `os.environ.get()` directly
- **Guard:** CI will fail if count increases
- **Cleanup:** Optional M27+ work, not blocking

---

## 6. Artifacts Required Before M27 Starts

### Code & Infra

- [x] `backend/app/config/secrets.py` - Centralized secrets
- [x] `backend/app/utils/schema_parity.py` - Schema drift detection
- [x] `scripts/ci/check_sqlmodel_exec.sh` - SQL guard
- [x] `scripts/ci/check_env_misuse.sh` - Env guard
- [x] `backend/tests/test_m26_prevention.py` - Prevention tests
- [x] `scripts/ops/m26_real_cost_test.py` - Real cost test

### Proof & Documentation

- [x] `docs/test_reports/M26_REAL_TEST_PROOF_*.md`
- [x] `docs/memory-pins/PIN-141-m26-cost-intelligence.md`
- [x] `docs/memory-pins/PIN-142-secrets-env-contract.md`

**If any are missing → M27 must not start.**

---

## 7. M26 → M27 Interface (Conceptual)

M26 hands M27 **signals**, not decisions.

### M27 May Consume

- Cost anomaly severity
- Feature attribution
- User attribution
- Budget status
- Projection data

### M27 May NOT

- Alter cost records
- Bypass anomaly detection
- Suppress incidents
- Modify attribution logic

Think of M26 as:
> **The accounting ledger + smoke detector**

M27 is:
> **The fire response system**

---

## 8. M27 Safety Rails (Pre-Declared)

### Automation Boundaries

M27 actions must be:
- Reversible
- Explainable
- Auditable

No irreversible auto-actions without:
- Incident record
- Human override path

### Blast Radius Control

Any automatic action must be scoped to:
- User
- Feature
- Model

Never:
- Tenant-wide shutdowns
- Org-wide policy flips

---

## 9. Recommended M27 Phases

1. **M27 Design Spec** — Define allowed auto-actions
2. **M27 Safety Matrix** — What must never be automated
3. **M27 Dry-Run Mode** — Simulate actions without execution
4. **M27 Live Mode** — Guarded rollout with kill switches

**Do NOT jump straight into code.**

---

## 10. Final Sign-Off Statement

> **M26 is complete and frozen.**
>
> Cost attribution is real, tested with live spend,
> anomaly detection is wired to governance,
> and environment hygiene is enforced.
>
> M27 may proceed **only** by consuming M26 outputs,
> not by extending or modifying them.

---

## Signatures

| Role | Status | Date |
|------|--------|------|
| M26 Implementation | ✅ Complete | 2025-12-23 |
| Prevention Stack | ✅ 7 layers active | 2025-12-23 |
| Real Cost Test | ✅ 5/5 PASS ($0.0006) | 2025-12-23 |
| Code Freeze | ✅ Enforced | 2025-12-23 |
