# PIN-444: Test Methods Design Document

**Status:** ✅ COMPLETE
**Created:** 2026-01-18
**Category:** Documentation / Testing

---

## Summary

Added comprehensive TEST_METHODS.md documenting AOS testing methodology

---

## Details

## Summary

Created `docs/design/TEST_METHODS.md` - a comprehensive guide to AOS testing methodology.

## Document Contents

### Test Method Taxonomy

| Method | Purpose |
|--------|---------|
| **Unit Tests** | Function correctness |
| **Integration Tests (LIT)** | Cross-layer seams (L2↔L3, L2↔L6) |
| **Browser Tests (BIT)** | UI page rendering |
| **SDSR Scenarios** | End-to-end system realization |
| **Preflight Checks** | CI gate validation |

### Key Sections

1. **SDSR Testing**
   - Execution modes (WORKER_EXECUTION vs STATE_INJECTION)
   - Attribution in scenarios (HUMAN, SYSTEM, SERVICE)
   - Pipeline flow: YAML → inject → observe → apply
   - Exit codes and error handling

2. **Attribution Testing (PIN-443)**
   - Default SYSTEM attribution
   - Explicit HUMAN/SERVICE actors
   - origin_system_id patterns

3. **Capability Validation**
   - DECLARED → OBSERVED → TRUSTED → DEPRECATED lifecycle
   - SDSR-driven capability promotion

4. **Test Principles (P1-P6)**
   - Real scenarios against real infrastructure
   - Full data propagation verification
   - Human semantic verification required

5. **Quick Reference**
   - Test commands for each type
   - Key file locations
   - Related documents

## File Location

`docs/design/TEST_METHODS.md`

## Related Documents

- SDSR_SYSTEM_CONTRACT.md
- SDSR_E2E_TESTING_PROTOCOL.md
- RUN_VALIDATION_RULES.md
- CAPABILITY_SURFACE_RULES.md

## Commit

a8003cc9
