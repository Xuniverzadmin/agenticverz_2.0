# Integrations Domain Delta Gap Matrix (2026-02-16)

**Created:** 2026-02-18
**Executor:** Claude
**Parent:** `HOC_INTEGRATIONS_DOMAIN_DELTA_RUNTIME_CORRECTNESS_ITERATION_2026_02_16_plan.md`
**Reference:** Controls domain delta pattern (`CONTROLS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16.md`)

## 1. Anchor Selection Rationale

Three anchor operations selected per plan requirements:

| Anchor | Operation | Domain | Justification |
|--------|-----------|--------|---------------|
| A1 | `integration.enable` | integrations | Existing invariant anchor (BI-INTEG-001); primary write operation for enabling connector integrations |
| A2 | `integration.disable` | integrations | Expected spec anchor (SPEC-008) with no invariant — delta opportunity for disable-path safety |
| A3 | `integrations.query:list_integrations` | integrations | PR-8 read boundary; strict allowlist facade; single-dispatch semantics must be provable |

## 2. Gap Matrix (3 Anchors x 7 Dimensions)

### A1: `integration.enable`

| Dimension | Artifact/Control | Classification | Evidence | Notes |
|-----------|-----------------|----------------|----------|-------|
| Invariant | BI-INTEG-001 | PRESENT_REUSED | `business_invariants.py:157-171` | HIGH severity; connector must be registered before enable |
| Spec | SPEC-007 | PRESENT_REUSED | `OPERATION_SPEC_REGISTRY_V1.md:278-308` | Full spec with preconditions, postconditions, rollback |
| Runtime Assertions | — | MISSING | No `test_integrations_runtime_delta.py` exists | Need OperationRegistry.execute() dispatch tests for enable path |
| Mutation | — | MISSING | No integrations-specific mutation coverage | Need mutation gate coverage for enable invariant |
| Property | — | MISSING | No `test_integrations_lifecycle_properties.py` exists | Need lifecycle state property tests (enable/disable transitions) |
| Replay | REPLAY-008 | PRESENT_REUSED | `tests/fixtures/replay/replay_008_integration_enable.json` | Existing fixture; replay validates against BI-INTEG-001 |
| Failure Injection | — | MISSING | No integrations section in `test_driver_fault_safety.py` | Need timeout, missing context, unregistered connector faults |

### A2: `integration.disable`

| Dimension | Artifact/Control | Classification | Evidence | Notes |
|-----------|-----------------|----------------|----------|-------|
| Invariant | — | MISSING | No BI-INTEG-002 in `business_invariants.py` | Need: integration must exist and be enabled before disable |
| Spec | SPEC-008 | PRESENT_REUSED | `OPERATION_SPEC_REGISTRY_V1.md:313-343` | Full spec with preconditions, postconditions, rollback |
| Runtime Assertions | — | MISSING | No runtime tests | Need OperationRegistry.execute() dispatch tests for disable path |
| Mutation | — | MISSING | No integrations-specific mutation coverage | Need mutation gate coverage for disable invariant |
| Property | — | MISSING | No property tests | Need disable-from-non-enabled-state property tests |
| Replay | REPLAY-009 | PRESENT_REUSED | `tests/fixtures/replay/replay_009_integration_disable.json` | Existing fixture; replay validates disable flow |
| Failure Injection | — | MISSING | No integrations fault injection | Need disable-on-nonexistent, disable-already-disabled faults |

### A3: `integrations.query:list_integrations`

| Dimension | Artifact/Control | Classification | Evidence | Notes |
|-----------|-----------------|----------------|----------|-------|
| Invariant | — | MISSING | No list invariant in registry | Need: BI-INTEG-003 for read-boundary contract (tenant scoping) |
| Spec | — | MISSING | No SPEC for integrations.query in registry | Read operations not in SPEC registry; PR-8 contract serves as equivalent |
| Runtime Assertions | PR-8 facade tests | PRESENT_STRENGTHEN | `tests/api/test_integrations_public_facade_pr8.py` (7 tests) | Tests L2 facade; need additional OperationRegistry.execute() dispatch proof |
| Mutation | — | MISSING | No mutation coverage for list path | Check existing scope; may already be covered structurally |
| Property | — | MISSING | No property tests for list behavior | Need deterministic ordering, pagination boundary properties |
| Replay | — | MISSING | No replay fixture for list operation | List is a read operation; replay less critical |
| Failure Injection | — | MISSING | No list-specific fault injection | Need empty result, timeout, tenant-mismatch faults |

## 3. Summary Tally

| Classification | Count | Details |
|----------------|-------|---------|
| PRESENT_REUSED | 6 | BI-INTEG-001, SPEC-007, SPEC-008, REPLAY-008, REPLAY-009, PR-8 tests |
| PRESENT_STRENGTHEN | 1 | PR-8 facade tests (need registry dispatch proof added) |
| MISSING | 14 | BI-INTEG-002, BI-INTEG-003, all runtime assertions, all mutation, all property, all enable/disable/list failure injection |

## 4. Execution Priority

1. **INT-DELTA-02**: Add BI-INTEG-002 (disable), BI-INTEG-003 (list tenant scope) + _default_check handlers
2. **INT-DELTA-03**: Create `test_integrations_runtime_delta.py` with enable/disable/list dispatch assertions
3. **INT-DELTA-04**: Create `test_integrations_lifecycle_properties.py` + run mutation gate
4. **INT-DELTA-05**: Add TestIntegrationsFaultInjection to fault safety suite + run replay/data quality
5. **INT-DELTA-06**: Architecture checks + gatepack closure + evidence document
