# Protective Governance Contract

**Status:** ACTIVE
**Effective:** 2025-12-30
**Reference:** docs/HOUSEKEEPING_BASELINE.md

This contract defines **long-term protection** against regression,
noise, and silent debt growth.

This contract is **enforced by CI**.

---

## 1. Monotonicity Contract

- Error counts must **never increase**.
- Warning counts must **never increase**.
- Quarantined artifacts must **never increase** without approval.

Baseline is defined in:
`docs/HOUSEKEEPING_BASELINE.md`

Enforcement:
`scripts/ci/lint_regression_guard.sh`

---

## 2. Quarantine Contract

- All quarantines must be registered in `docs/technical-debt/QUARANTINE_LEDGER.md`.
- Inline suppressions without ledger entries are invalid.
- Config-level suppressions count as debt.

Unregistered debt is **automatically invalid**.

---

## 3. Debt Currency Contract

New debt may be introduced only if:
- Equal or greater debt is removed, OR
- An explicit exception is approved.

Debt is **fungible but bounded**.

Exception approval requires:
1. Justification in PR description
2. Ledger entry with expiry
3. Ceiling check (must not breach)

---

## 4. Typing Scope Contract

| Layer | Typing Expectation |
|------|--------------------|
| L1–L3 | Strict             |
| L4    | Medium             |
| L5    | Medium             |
| L6    | Loose              |
| L7–L8 | Optional           |

Typing tools must not enforce stricter rules outside this scope.

This prevents unrealistic expectations and false failures.

---

## 5. Tool Authority Contract

| Tool  | Authority                   |
|-------|-----------------------------|
| mypy  | Structural correctness      |
| ruff  | Hygiene only                |
| tests | Behavioral correctness      |
| CI    | Final gatekeeper            |

No tool may act outside its authority.

Tool upgrades require:
1. Preview of new warnings
2. Baseline update in same PR
3. No surprise regressions

---

## 6. Regression-Only Enforcement

CI enforces **no regression**, not perfection.

- Cleanup is intentional work, not a requirement.
- Stagnation at baseline is acceptable.
- Improvement locks in new baseline.

This preserves velocity while preventing decay.

---

## 7. Session Safety Clause

Even if humans or AI misbehave,
the repository **must not regress**.

This contract exists to guarantee that invariant.

Guards active:
- Pre-commit hooks
- CI monotonicity checks
- Quarantine ceiling checks
- Boundary validators

---

## 8. Violation Response

| Violation Type | Response |
|----------------|----------|
| Error count increased | CI blocks merge |
| Unregistered debt added | CI blocks merge |
| Ceiling breached | CI blocks merge |
| Tool authority exceeded | Review required |

All violations are **blocking**, not warning.

---

## Contract Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial contract after housekeeping |

---

## References

- `docs/HOUSEKEEPING_BASELINE.md` - Frozen baselines
- `docs/HOUSEKEEPING_CLASSIFICATION.md` - Error classification
- `docs/technical-debt/QUARANTINE_LEDGER.md` - Debt registry
- `scripts/ci/lint_regression_guard.sh` - Enforcement script
