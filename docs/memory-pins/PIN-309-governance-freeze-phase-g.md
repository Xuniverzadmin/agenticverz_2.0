# PIN-309: Governance Freeze - Phase G

**Status:** COMPLETE
**Created:** 2026-01-05
**Category:** Governance / Freeze

---

## Summary

Implemented governance freeze to prevent regression and drift from capability governance state.

---

## Objective

Move the system from "correct" to "non-regressable" by locking capability states, freezing permission taxonomy, enforcing plane purity, and generating a governance baseline report.

---

## Implementation

### Phase G1: Registry Mutation Freeze

**Rule:** No capability state change without PIN reference

**Implementation:**
- `check_registry_mutation()` - validates PIN-XXX pattern in PR body or commit message
- `check_registry_diff_for_state_changes()` - detects state transitions and CLOSED→PARTIAL regressions
- CI job: `registry-mutation-guard`

**Blocking Violations:**
- State change without `PIN-XXX` reference
- CLOSED → PARTIAL regression (requires explicit justification)

### Phase G2: Plane Purity Enforcement

**Rule:** Route and authority planes must match

**Implementation:**
- `HUMAN_ONLY_ROUTES` - routes that must use HumanAuthContext
- `MACHINE_ONLY_ROUTES` - routes that cannot use HumanAuthContext
- `READ_ONLY_CAPABILITIES` - capabilities that cannot have POST/PUT/DELETE endpoints
- `check_plane_purity()` - validates route/authority alignment
- CI job: `plane-purity-guard`

**Route Classifications:**
| Category | Routes |
|----------|--------|
| HUMAN_ONLY | `/fdr/`, `/admin/`, `/console/`, `/guard/` |
| MACHINE_ONLY | `/api/v1/workers/`, `/api/v1/agents/`, `/api/v1/runtime/`, `/webhook/` |

### Phase G3: Taxonomy Lock

**Rule:** Permission changes require version bump

**Implementation:**
- `TAXONOMY_PATH` - frozen taxonomy document
- `check_taxonomy_lock()` - validates version in PR body for permission additions
- `get_taxonomy_permissions()` - extracts declared permissions
- CI job: `taxonomy-lock-guard`

**Blocking Violations:**
- New permission without `TAXONOMY_VERSION:` bump
- No `MIGRATION_NOTE:` in PR body for permission changes

### Phase G4: Worker Auth Compliance

**Rule:** Workers use API keys only, never HumanAuthContext

**Implementation:**
- `WORKER_FILES`, `WEBHOOK_FILES` - path patterns
- `FORBIDDEN_AUTH_PATTERNS` - patterns that indicate human auth usage
- `check_worker_auth_compliance()` - scans for violations
- CI job: `worker-auth-guard`

**Forbidden Patterns in Workers:**
- `HumanAuthContext`
- `verify_console_token`
- `jwt.decode`
- `AuthorizationHeader`

### Phase G5: Governance Baseline Report

**Implementation:**
- `generate_governance_baseline()` - creates full governance snapshot
- Output: `/docs/reports/GOVERNANCE_BASELINE_YYYYMMDD.md`

**Report Contents:**
- Capability states (CLOSED, FROZEN, READ_ONLY, PARTIAL, etc.)
- Authority surfaces declared
- CI invariants active
- Known intentional gaps
- Blocking gaps
- Frozen artifacts
- Verification commands
- Baseline hash

---

## Files Modified

| File | Change |
|------|--------|
| `scripts/ops/capability_registry_enforcer.py` | Added Phase G functions and commands |
| `.github/workflows/capability-registry.yml` | Added G1-G5 CI jobs |
| `docs/reports/GOVERNANCE_BASELINE_20260105.md` | NEW - Baseline report |

---

## CI Commands

```bash
# G1: Registry mutation check
python3 scripts/ops/capability_registry_enforcer.py registry-mutation --commit-message "MSG"

# G2: Plane purity check
python3 scripts/ops/capability_registry_enforcer.py plane-purity --scan-all

# G3: Taxonomy lock check
python3 scripts/ops/capability_registry_enforcer.py taxonomy-lock --diff-file diff.txt

# G4: Worker auth check
python3 scripts/ops/capability_registry_enforcer.py worker-auth --scan-all

# G5: Generate baseline
python3 scripts/ops/capability_registry_enforcer.py governance-baseline --output FILE
```

---

## Verification

```bash
# All guards pass
python3 scripts/ops/capability_registry_enforcer.py registry-mutation
python3 scripts/ops/capability_registry_enforcer.py plane-purity --scan-all
python3 scripts/ops/capability_registry_enforcer.py taxonomy-lock
python3 scripts/ops/capability_registry_enforcer.py worker-auth --scan-all
python3 scripts/ops/capability_registry_enforcer.py authority-guard --scan-all
```

---

## Governance State After

| Metric | Value |
|--------|-------|
| Total Capabilities | 17 |
| CLOSED | 11 |
| READ_ONLY | 2 |
| PARTIAL | 3 |
| PLANNED | 1 |
| Authority Surfaces | 16 |
| Active CI Guards | 10 (T1-T4, G1-G5, authority-guard) |

---

## Reference

- PIN-306: Capability Registry Governance
- PIN-307: CAP-006 Authentication Gateway Closure
- PIN-308: Authority Closure - Replay and Prediction Capabilities
- docs/reports/GOVERNANCE_BASELINE_20260105.md

---

## Related PINs

- [PIN-306](PIN-306-.md)
- [PIN-307](PIN-307-.md)
- [PIN-308](PIN-308-.md)
