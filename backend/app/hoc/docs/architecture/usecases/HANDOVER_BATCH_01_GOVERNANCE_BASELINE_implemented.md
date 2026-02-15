# HANDOVER_BATCH_01_GOVERNANCE_BASELINE — Implemented

**Date:** 2026-02-11
**Handover Source:** `HANDOVER_BATCH_01_GOVERNANCE_BASELINE.md`
**Status:** COMPLETE — all exit criteria met

---

## 1. Domain Authority Rules Locked in Verifiers

### New Checks in `uc_mon_validation.py` (Section 6: Authority Boundaries)

| Check | What It Verifies | Result |
|-------|------------------|--------|
| `authority.proposals_no_enforcement` | `policy_proposals.py` does NOT call enforcement ops (`policies.activate`, `policies.enforce`, etc.) | PASS |
| `authority.proposals_allowed_ops_only` | `policy_proposals.py` only uses `policies.proposals_query` + `policies.approval` | PASS |
| `authority.controls_canonical_only` | `controls.py` only dispatches to `controls.*` ops | PASS |
| `authority.incidents_canonical_only` | `incidents.py` only dispatches to `incidents.*` ops (allowlist: `logs.pdf` for export renders) | PASS |
| `authority.policies_no_direct_l5l6` | `policy_proposals.py` has no L5/L6 direct imports | PASS |
| `authority.controls_no_direct_l5l6` | `controls.py` has no L5/L6 direct imports | PASS |

### Authority Boundary Evidence

- **Proposals cannot mutate enforcement directly**: Verified. `policy_proposals.py` uses only `policies.proposals_query` (read) and `policies.approval` (human-gated). No `policies.activate`, `policies.enforce`, `policies.compile`, or `policies.publish` calls found.
- **Controls writes via canonical paths only**: Verified. All ops in `controls.py` use `controls.query` prefix.
- **Incident lifecycle writes via canonical paths only**: Verified. All ops use `incidents.query` or `incidents.export`. The 3 `logs.pdf` calls are PDF renderers for export endpoints (allowlisted).

## 2. Aggregator Upgraded to Eligible-Strict

`uc_mon_validation.py` now runs 32 checks (was 26). Added authority boundary section with 6 checks. Strict mode (`--strict`) exits 0.

## 3. CI Hygiene Check Added (Non-Blocking)

Added check #37 (`check_proposal_enforcement_isolation`) to `scripts/ci/check_init_hygiene.py`:
- Scans `policy_proposals.py` for enforcement-class L4 operation calls
- Currently advisory (non-blocking per Batch-01 guardrails)
- Total CI checks: 37 (was 36)

## 4. Route Mappings Verified Current

`uc_mon_route_operation_map_check.py` passes all checks. 73 routes across 6 domains remain accurate.

---

## Validation Command Outputs

### Route Map Verifier
```
96 checks: all routes verified
```

### Event Contract Verifier
```
Total: 46 | PASS: 46 | FAIL: 0
```

### Storage Contract Verifier
```
Total: 53 | PASS: 53 | FAIL: 0
```

### Deterministic Read Verifier
```
Total: 34 | PASS: 34 | WARN: 0 | FAIL: 0
```

### Aggregator (Strict)
```
Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0
Exit code: 0
```

### CI Hygiene
```
All checks passed. 0 blocking violations (0 known exceptions).
37 checks total.
```

---

## PASS/WARN/FAIL Matrix

| Verifier | PASS | WARN | FAIL |
|----------|------|------|------|
| Route map | 96 | 0 | 0 |
| Event contract | 46 | 0 | 0 |
| Storage contract | 53 | 0 | 0 |
| Deterministic read | 34 | 0 | 0 |
| Aggregator (strict) | 32 | 0 | 0 |
| CI hygiene | 37 | 0 | 0 |
| **Total** | **298** | **0** | **0** |

---

## Files Modified

| File | Change |
|------|--------|
| `scripts/verification/uc_mon_validation.py` | Added Section 6 (authority boundaries) — 6 new checks, total 32 |
| `scripts/ci/check_init_hygiene.py` | Added check #37 (`check_proposal_enforcement_isolation`) — advisory, non-blocking |

## Blockers

None. All exit criteria satisfied.
