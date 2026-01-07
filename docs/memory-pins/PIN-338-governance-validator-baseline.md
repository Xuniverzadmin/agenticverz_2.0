# PIN-338: Governance Validator Baseline

**Status:** BASELINE CAPTURED
**Date:** 2026-01-06
**Git Commit:** 25937e4a (with uncommitted PIN-337 changes)
**Branch:** main

---

## Summary

This run establishes the post-PIN-337 governance baseline. No enforcement changes applied.

---

## Kernel Usage Validation

| Metric | Count |
|--------|-------|
| Total EXECUTE paths | 5 |
| Compliant (kernel routed) | 3 |
| Deferred (known, tracked) | 2 |
| Violations | 0 |

### Deferred Paths

| Worker | Location |
|--------|----------|
| BusinessBuilderWorker | `workers/business_builder/worker.py:93` |
| AlertWorker | `costsim/alert_worker.py:59` |

---

## Capability Binding Validation

| Metric | Count |
|--------|-------|
| Total bindings | 18 |
| Valid bindings | 18 |
| Unknown capability IDs | 0 |
| Invalid bindings | 0 |

---

## Evidence Artifacts

- `artifacts/pin_338_kernel_usage.txt`
- `artifacts/pin_338_capability_binding.txt`

---

## Statement

> This run establishes the post-PIN-337 governance baseline. No enforcement changes applied.

Governance is now in **steady state**.
