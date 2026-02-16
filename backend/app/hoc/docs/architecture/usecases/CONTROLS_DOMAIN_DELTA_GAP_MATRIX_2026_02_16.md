# CONTROLS_DOMAIN_DELTA_GAP_MATRIX_2026_02_16

**Created:** 2026-02-16
**Scope:** control.set_threshold, killswitch.activate, override.apply
**Method:** Cross-reference business_invariants.py, operation specs, replay fixtures, property tests, failure injection, mutation gate

## Anchor Selection Rationale

- `control.set_threshold` — primary target with existing BI-CTRL-001 invariant
- `killswitch.activate` — safety-critical freeze/unfreeze operation; registered as `controls.killswitch.write` in handler. No invariant exists. Incorrect activation can lock out an entire entity.
- `override.apply` — limit override operation; registered as `controls.overrides` in handler. No invariant exists. Incorrect overrides can bypass safety limits.

## Gap Matrix

| Operation | Invariants | Specs | Runtime Assertions | Mutation | Property | Replay | Failure Injection |
|-----------|-----------|-------|-------------------|----------|----------|--------|-------------------|
| `control.set_threshold` | PRESENT_REUSED — BI-CTRL-001 (HIGH), _default_check validates numeric+non-negative | PRESENT_REUSED — SPEC-011 in registry | **MISSING** — no test_controls_runtime_delta.py | PRESENT_REUSED — shadow_compare.py scope | PRESENT_REUSED — threshold validation in `test_policies_threshold_properties.py` (generic) | PRESENT_REUSED — REPLAY-012 references BI-CTRL-001 | **MISSING** — no controls fault injection |
| `killswitch.activate` | **MISSING** — no BI-CTRL-002; _default_check has no handler | N/A — not in spec registry (runtime-only) | **MISSING** — no dispatch assertions | PRESENT_REUSED — shadow_compare.py scope | **MISSING** — no killswitch state machine tests | N/A — no replay fixture | **MISSING** — no killswitch fault injection |
| `override.apply` | **MISSING** — no BI-CTRL-003; _default_check has no handler | N/A — not in spec registry (runtime-only) | **MISSING** — no dispatch assertions | PRESENT_REUSED — shadow_compare.py scope | **MISSING** — no override property tests | N/A — no replay fixture | **MISSING** — no override fault injection |

## Summary

| Classification | Count | Details |
|---------------|-------|---------|
| PRESENT_REUSED | 7 | BI-CTRL-001, SPEC-011, REPLAY-012, mutation gate (×3), threshold property tests |
| PRESENT_STRENGTHEN | 0 | — |
| MISSING | 11 | BI-CTRL-002 (killswitch.activate), BI-CTRL-003 (override.apply), _default_check handlers (×2), runtime dispatch (×3), killswitch/override property tests, fault injection (×3) |

## Delta Plan

1. **BI-CTRL-002** (killswitch.activate, HIGH): entity_id required, entity must not already be frozen
2. **BI-CTRL-003** (override.apply, HIGH): limit_id required, override value must be non-negative
3. **_default_check handlers**: Add `killswitch.activate` and `override.apply` branches
4. **test_controls_runtime_delta.py**: Contract tests + OperationRegistry dispatch assertions (MONITOR/STRICT)
5. **Controls property tests**: Killswitch state machine (ACTIVE→FROZEN→ACTIVE cycle, terminal DECOMMISSIONED)
6. **Controls fault injection**: Timeouts, invalid thresholds, stale state, connection failures
