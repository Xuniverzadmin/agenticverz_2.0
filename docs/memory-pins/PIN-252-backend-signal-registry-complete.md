# PIN-252: Backend Signal Registry Complete

**Status:** 📋 FROZEN
**Created:** 2025-12-31
**Category:** Architecture / Signal Registry

---

## Summary

Complete backend signal registry with 47 signals (45 Python + 2 non-Python), explicit file exclusions, and honest UNKNOWNs

---

## Details

## Summary

Backend signal registry is now FROZEN as baseline for auditor development.

## Key Deliverables

| Document | Purpose |
|----------|---------|
| `docs/architecture/SIGNAL_REGISTRY_COMPLETE.md` | Master registry (47 signals) |
| `docs/architecture/SIGNAL_REGISTRY_PYTHON_BASELINE.md` | Python-only baseline (45 signals) |
| `docs/architecture/RUNTIME_ASSETS.md` | Non-signal runtime inputs (12 files) |
| `docs/architecture/L1_L2_L8_BINDING_AUDIT.md` | Layer binding verification |

## Signal Counts

| Category | Count |
|----------|-------|
| Python Signals | 45 |
| Non-Python Signals | 2 |
| **Total Registered** | **47** |
| UNKNOWNs | 7 |
| Orphaned | No confirmed orphans |

## Valid Non-Python Signals

| UID | Signal | Source | Persistence |
|-----|--------|--------|-------------|
| SIG-200 | IdempotencyDecision | idempotency.lua | Redis |
| SIG-206 | FailureCatalogMatch | failure_catalog.json | PostgreSQL (GUARANTEED) |

## Files Removed from Registry (Misclassified)

| Removed UID | Former Name | Correct Classification |
|-------------|-------------|------------------------|
| SIG-201 | FeatureFlagState | RUNTIME-CONFIG |
| SIG-202 | RBACPolicyMatrix | RUNTIME-CONFIG |
| SIG-203 | SkillSchemaValidation | RUNTIME-SCHEMA |
| SIG-204 | OutcomeSchemaValidation | RUNTIME-SCHEMA |
| SIG-205 | SkillContractLoad | RUNTIME-SCHEMA |

## File Inventory

| Category | Count |
|----------|-------|
| Total backend files | 634 |
| Python files | 580 |
| Non-Python files | 54 |
| Runtime-relevant Python | 336 |
| Excluded (L7/L8) | 298 |

## Signal Definition (Locked)

> A signal is a runtime-generated artifact created or mutated as a result of execution.

NOT signals: config files (read), validation schemas (enforcement), static data, build/ops artifacts.

## Next Steps

1. Build auditor rules.yaml grounded in this registry
2. Define CI gate wording (block vs warn)
3. Implement signal_auditor.py script

## Lessons Learned

1. Config/schema files are INPUTS, not OUTPUTS - never classify as signals
2. "0 UNKNOWN" at scale is implausible - honest uncertainty is expected
3. Explicit file exclusion lists are required, not summary counts
4. Signal persistence must be verified (conditional vs guaranteed)
