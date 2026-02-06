# PIN-268: Guidance System Upgrade

**Status:** ACTIVE
**Created:** 2026-01-01
**Category:** CI Rediscovery / System Evolution
**Related PINs:** PIN-267 (test protection), PIN-266 (test tracker)

---

## Executive Summary

The system is now defensible but not yet self-guiding. This PIN tracks the transition from "block bad behavior" to "make correct behavior easiest."

---

## Current State Assessment

| Layer | Defensible | Guiding | Gap |
|-------|------------|---------|-----|
| L8 (Tests/CI) | YES | YES | Buckets + invariant markers active |
| L7 (Ops/Gov) | YES | PARTIAL | Playbooks retrospective |
| L6 (Infra) | YES | YES | Invariants documented and discoverable |
| L5 (Workers) | YES | YES | Intent enforced (0 violations) |
| L4 (Domain) | YES | PARTIAL | 21 services need intent |

---

## Guidance Upgrade Tasks

### GU-001: Invariant Documentation

**Priority:** HIGH
**Status:** COMPLETE (2026-01-01)

Create `docs/invariants/` directory with human-readable invariant docs generated from test files.

**Implementation:**
- Created `docs/invariants/INDEX.md` - Template and index
- Created `docs/invariants/M10_RECOVERY_INVARIANTS.md` - 7 invariants documented
- Created `docs/invariants/PB_S1_INVARIANTS.md` - 9 invariants documented

Template:
```markdown
# {Module} Invariants

## Schema Invariants
- {constraint}: {why it exists}

## Concurrency Invariants
- {race}: {root cause}, {correct pattern}

## Reference
- Tests: `tests/invariants/test_{module}_invariants.py`
- PIN: PIN-267
```

**Rule:** Every invariant test must have a doc entry.

---

### GU-002: CI Bucket Classification Markers

**Priority:** HIGH
**Status:** COMPLETE (2026-01-01)

Add pytest markers for test fix classification:

**Implementation:**
- Added `@pytest.mark.ci_bucket(bucket)` marker to `tests/conftest.py`
- Added `@pytest.mark.invariant` marker for tests that must not be weakened
- Added `@pytest.mark.pb_s1` and `@pytest.mark.pb_s1_behavioral` markers
- Applied `@pytest.mark.invariant` to `tests/invariants/test_m10_invariants.py`

```python
@pytest.mark.ci_bucket("A")  # Test wrong
@pytest.mark.ci_bucket("B")  # Infra missing
@pytest.mark.ci_bucket("C")  # System bug
```

**Rule:** Any test fix PR must declare bucket. Missing = blocked.

SESSION_PLAYBOOK addition:
```yaml
test_fix_discipline:
  status: ENFORCED
  rule: |
    Every test fix must declare its CI bucket (A/B/C).
    Missing classification = PR rejected.
  markers:
    - "@pytest.mark.ci_bucket('A')" # Test wrong
    - "@pytest.mark.ci_bucket('B')" # Infra missing
    - "@pytest.mark.ci_bucket('C')" # System bug
  enforcement: pre-commit + CI
```

---

### GU-003: Mandatory Intent Boilerplate

**Priority:** HIGH
**Status:** COMPLETE (2026-01-01)

Require FEATURE_INTENT declaration in critical modules.

**Implementation:**
- Created `docs/templates/INTENT_BOILERPLATE.md` - Copy-paste templates
- Added `feature-intent-guard` CI job to `.github/workflows/ci.yml`
- CI job runs with `--warn-only` initially (non-blocking)

**Current Coverage:**

| Directory | Violations | Status |
|-----------|------------|--------|
| `app/worker/` | 0 | CLEAN |
| `app/jobs/` | 0 | CLEAN |
| `app/services/` | 21 | REMEDIATION NEEDED |

**21 Services Missing Intent (to be fixed incrementally):**
1. policy_violation_service.py
2. governance_signal_service.py
3. cost_anomaly_detector.py
4. evidence_report.py
5. budget_enforcement_engine.py
6. external_response_service.py
7. user_write_service.py
8. cost_write_service.py
9. policy_proposal.py
10. incident_aggregator.py
11. llm_failure_service.py
12. pattern_detection.py
13. founder_action_write_service.py
14. worker_write_service_async.py
15. prediction.py
16. guard_write_service.py
17. event_emitter.py
18. tenant_service.py
19. ops_write_service.py
20. worker_registry_service.py
21. ops_incident_service.py

**Rule:** New files in critical directories without FEATURE_INTENT = CI warning (blocking after remediation)

---

### GU-004: Danger Fences for Known Races

**Priority:** MEDIUM
**Status:** COMPLETE (2026-01-01)

Add explicit helper functions that encapsulate known-dangerous patterns.

**Implementation:**
- Created `app/infra/danger_fences.py` - Danger fence module
- Added `enqueue_recovery_candidate_safely()` helper for dual-constraint race
- Added `RecoveryEnqueueError` exception for race condition handling
- Added `DANGER_FENCES` registry for discoverability
- Added invariant test skip protection hook to `tests/conftest.py`
- Added `--allow-invariant-skip` CLI option for explicit override

**Key Functions:**

```python
from app.infra import enqueue_recovery_candidate_safely, RecoveryEnqueueError

# This function handles the uq_rc_fmid_sig dual-constraint race
# with retry logic and proper logging
result = enqueue_recovery_candidate_safely(
    session=session,
    failure_match_id=failure_match_id,
    error_signature=error_signature,
    ...
)
```

**Danger Fence Registry:**

| Fence Name | Race Condition | Documentation |
|------------|----------------|---------------|
| `recovery_candidate_enqueue` | `uq_rc_fmid_sig` dual-constraint | M10_RECOVERY_INVARIANTS.md |

**Rule:** Any code touching recovery enqueue must use this helper.

**Forbidden Patterns:**
- Direct `INSERT INTO recovery_candidates` without using the helper
- `ON CONFLICT (failure_match_id, error_signature)` - won't work with partial index

---

## Implementation Order

| Order | Task | Blocks |
|-------|------|--------|
| 1 | GU-001 (Invariant docs) | Nothing (can do now) |
| 2 | GU-002 (Bucket markers) | Test fix PRs |
| 3 | GU-003 (Intent boilerplate) | New critical files |
| 4 | GU-004 (Danger fences) | Recovery refactors |

---

## Success Criteria

The system is "self-guiding" when:

1. An engineer can discover invariants BEFORE writing code
2. Test fixes require explicit classification (no guessing)
3. Intent is declared at authoring time, not CI time
4. Known races have explicit, named escape hatches

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-01 | Create PIN-268 | Track defensible→guiding transition |
| 2026-01-01 | Prioritize GU-001 | Invariants must be discoverable |
| 2026-01-01 | Defer GU-003/004 | Can be added incrementally |
| 2026-01-01 | Complete GU-001 | 3 docs, 16 invariants documented |
| 2026-01-01 | Complete GU-002 | Markers registered in conftest.py |
| 2026-01-01 | Complete GU-003 | Templates + CI job added, 21 violations tracked |
| 2026-01-01 | Complete GU-004 | Danger fence module + invariant skip protection |

---

## References

- PIN-267 (Test System Protection Rule)
- PIN-266 (Test Repair Execution Tracker)
- `tests/invariants/` (invariant test files)
- `docs/invariants/` (invariant documentation)
- `docs/invariants/INDEX.md` (template and index)
- `docs/templates/INTENT_BOILERPLATE.md` (copy-paste templates)
- `docs/playbooks/SESSION_PLAYBOOK.yaml`
- `tests/conftest.py` (marker definitions, invariant skip protection)
- `scripts/ci/check_feature_intent.py` (intent checker)
- `.github/workflows/ci.yml` (feature-intent-guard job)
- `app/infra/danger_fences.py` (danger fence helpers)
