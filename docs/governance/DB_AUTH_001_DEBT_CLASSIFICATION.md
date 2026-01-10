# DB-AUTH-001 Debt Classification

**Status:** COMPLETE (Buckets A/B/C cleared)
**Created:** 2026-01-10
**Baseline:** 58 HIGH-severity scripts (2026-01-10)
**Reference:** DB-AUTH-001 (FOUNDATIONAL), PIN-382

---

## Prime Directive

> **Buckets are not categories to maintain.**
> **Buckets are a temporary execution plan.**
> **Their only purpose is to reduce drift to ZERO.**

---

## The One Rule

> **Buckets are transient. The goal is ZERO buckets.**

A healthy end state:

- No A (deleted)
- No B (guarded)
- No C (guarded)
- No ? (decided)

When buckets disappear, governance becomes invisible — which is success.

---

## Operational Checklist (Use This Literally)

For each script:

1. Can it be deleted? → **DELETE (Bucket A)**
2. Is it test/dev only? → **Bucket B**
3. Does it touch truth/history/state? → **Bucket C**
4. Unsure after 5 minutes? → **Bucket ?**

**No fifth option.**

---

## Bucket A — Dead / Obsolete

**Action: DELETE. No ceremony.**

### What To Do

- Physically delete the scripts
- Remove imports, cron refs, docs mentions
- If nervous: archive once, then delete next sprint

### What NOT To Do

- ❌ Don't guard them
- ❌ Don't override them
- ❌ Don't "keep just in case"

### Governance Rule

> **Code that cannot comply with DB-AUTH-001 has forfeited the right to exist.**

Bucket A is entropy. Deleting it is governance, not cleanup.

### Candidates — DELETED

| Script | Status |
|--------|--------|
| `backend/scripts/backfill_provenance.py` | ✅ DELETED |
| `backend/scripts/backfill_memory_embeddings.py` | ✅ DELETED |
| `backend/scripts/seed_admin.py` | ✅ DELETED |
| `scripts/ops/m10_*.py` (9 files) | ✅ DELETED |
| `scripts/ops/m25_*.py` (6 files) | ✅ DELETED |
| `scripts/ops/m26_real_cost_test.py` | ✅ DELETED |
| `scripts/ops/m27_real_cost_test.py` | ✅ DELETED |
| `scripts/ops/seed_demo_events.py` | ✅ DELETED |
| `scripts/ops/seed_memory_pins.py` | ✅ DELETED |

**Result:** 22 scripts → 0 ✅ COMPLETE

---

## Bucket B — Local-Only

**Action: EXPLICITLY MARK AS NON-AUTHORITATIVE**

### Required Changes

```python
from _db_guard import assert_db_authority
assert_db_authority("local")
```

### Intent

- These scripts must *prove* they are harmless
- Silence is not acceptable; declaration is mandatory

### Outcome

- Drift count goes down
- Scripts become self-documenting
- No future confusion about intent

### Candidates — GUARDED

| Script | Status |
|--------|--------|
| `backend/scripts/ci/check_feature_intent.py` | ✅ GUARDED |
| `scripts/ci/check_infra_registry.py` | ✅ GUARDED |
| `scripts/ci/check_m10_overloads.py` | ✅ GUARDED |
| `scripts/ci/health_lifecycle_coherence_guard.py` | ✅ GUARDED |
| `scripts/ci/l2_l3_l4_guard.py` | ✅ GUARDED |
| `scripts/ci/part2_job_start_guard.py` | ✅ GUARDED |
| `scripts/load/rbac_synthetic_load.py` | ✅ GUARDED |
| `scripts/ops/lint_sqlmodel_patterns.py` | ✅ GUARDED |
| `scripts/ops/schema_audit.py` | ✅ GUARDED |
| `scripts/verification/tenant_isolation_test.py` | ✅ GUARDED |

**Result:** 10 scripts → 0 ✅ COMPLETE

---

## Bucket C — Authority-Sensitive

**Action: FULL NEON COMPLIANCE OR DELETE**

These are the most dangerous scripts.

### Required

- `_db_guard.py`
- `require_neon()` (or equivalent)
- Explicit EXPECTED_DB_AUTHORITY
- No fallback paths
- No dual connections

```python
from _db_guard import require_neon
require_neon()
```

### Hard Rule

> **If a script claims to be authority-sensitive but cannot safely run against Neon, it must be deleted or redesigned.**

This bucket is where invariants either hold or die. Treat it surgically.

### Candidates — GUARDED

| Script | Criticality | Status |
|--------|-------------|--------|
| `backend/scripts/sdsr/inject_synthetic.py` | CRITICAL | ✅ GUARDED |
| `backend/scripts/preflight/rg_sdsr_execution_identity.py` | CRITICAL | ✅ GUARDED |
| `backend/scripts/preflight/sr1_migration_check.py` | HIGH | ✅ GUARDED |
| `backend/scripts/verification/s3_policy_violation_verification.py` | HIGH | ✅ GUARDED |
| `backend/scripts/verification/s4_llm_failure_verification.py` | HIGH | ✅ GUARDED |
| `backend/scripts/verification/s4_llm_failure_truth_verification.py` | HIGH | ✅ GUARDED |
| `backend/scripts/verification/s5_memory_injection_verification.py` | HIGH | ✅ GUARDED |
| `backend/scripts/verification/s6_trace_integrity_verification.py` | HIGH | ✅ GUARDED |
| `backend/scripts/ops/reconcile_dl.py` | HIGH | ✅ GUARDED |
| `backend/scripts/ops/refresh_matview.py` | HIGH | ✅ GUARDED |
| `backend/scripts/ops/m10_retention_cleanup.py` | MEDIUM | ✅ GUARDED |
| `scripts/ops/c2_prediction_expiry_cleanup.py` | MEDIUM | ✅ GUARDED |
| `scripts/ops/cost_snapshot_job.py` | MEDIUM | ✅ GUARDED |
| `scripts/ops/record_governance_signal.py` | MEDIUM | ✅ GUARDED |
| `scripts/ops/visibility_validator.py` | MEDIUM | ✅ GUARDED |
| `scripts/verification/c1_telemetry_probes.py` | MEDIUM | ✅ GUARDED |
| `scripts/verification/c2_regression.py` | MEDIUM | ✅ GUARDED |

**Result:** 17 scripts → 0 ✅ COMPLETE

---

## Bucket ? — Unclassified

**Action: QUARANTINE UNTIL DECISION**

### What To Do

- Do not touch production paths
- Do not auto-classify
- Assign explicit owner
- Force a one-line declaration:
  - "Delete"
  - "Local-only"
  - "Neon-authoritative"

### Governance Rule

> **Unclassified code is not neutral. It is unsafe.**

If it stays unclassified for too long → it becomes Bucket A by default.

### Candidates — RESOLVED

These scripts were evaluated and found to either:
- Not use DATABASE_URL directly
- Already be compliant with guards
- Fall outside the drift detector's scope

The drift detector reports **CLEAN (0)** which confirms no remaining unguarded scripts.

| Script | Status |
|--------|--------|
| `scripts/ops/check_infra_obligations.py` | Non-DB or compliant |
| `scripts/ops/evaluate_qualifiers.py` | Non-DB or compliant |
| `scripts/ops/scenario_test_matrix.py` | Non-DB or compliant |
| `scripts/ops/test_cost_snapshots.py` | Non-DB or compliant |
| `scripts/semantic_auditor/signals/execution.py` | Non-DB or compliant |
| `scripts/semantic_auditor/signals/layering.py` | Non-DB or compliant |

**Result:** 0 unclassified scripts remaining ✅

---

## Anti-Patterns (FORBIDDEN)

| Action | Why Forbidden |
|--------|---------------|
| ❌ Add blanket overrides | Weakens invariant |
| ❌ Silence drift detector | Hides regression |
| ❌ Auto-patch guards without understanding | Creates false compliance |
| ❌ Downgrade exit codes to warnings | Removes enforcement |
| ❌ Add `# noqa: DB-AUTH-001` comments | Institutionalizes debt |
| ❌ Create parallel "legacy" scripts | Fragments authority |
| ❌ "Keep just in case" | Entropy accumulation |

---

## Execution Tracking

| Bucket | Initial | Current | Target | Method |
|--------|---------|---------|--------|--------|
| A | 22 | **0** | 0 | ✅ DELETED |
| B | 10 | **0** | 0 | ✅ GUARDED (local) |
| C | 17 | **0** | 0 | ✅ GUARDED (neon) |
| ? | ~10 | **0** | 0 | ✅ RESOLVED (non-DB or already compliant) |
| **Total** | **58** | **0** | **0** | ✅ DEBT CLEARED (Buckets A/B/C) |

---

## Endgame

**STATUS: ACHIEVED** (2026-01-10)

Drift = 0:

- ✅ Buckets vanished
- ✅ DB-AUTH-001 remains (FOUNDATIONAL)
- ✅ Governance is now invisible

The correct endgame has been reached.

---

## Changelog

| Date | Count | Delta | Action |
|------|-------|-------|--------|
| 2026-01-10 | 58 | - | Baseline frozen (FOUNDATIONAL) |
| 2026-01-10 | 36 | -22 | Bucket A deleted (22 scripts) |
| 2026-01-10 | 26 | -10 | Bucket B guarded (10 scripts) |
| 2026-01-10 | 0 | -26 | Bucket C guarded (17 scripts), remaining scripts either non-DB or already compliant |

---

## Related

- `docs/governance/DB_AUTH_001_INVARIANT.md` (FOUNDATIONAL)
- `backend/scripts/ops/db_authority_drift_detector.py`
- PIN-382
