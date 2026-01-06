# P1-1.1 Backend Layer Map

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Layer | Files | Description |
|-------|-------|-------------|
| L2 | 43 | Product APIs |
| L3 | 37 | Boundary Adapters |
| L4 | 231 | Domain Engines |
| L5 | 27 | Execution & Workers |
| L6 | 88 | Platform Substrate |
| L7 | 2 | Ops & Deployment |
| L8 | 1 | Catalyst / Meta |
| **TOTAL** | **429** | |

## BLCA Status

```
Files scanned: 708
Violations found: 0
Status: CLEAN
```

## Layer Headers

- **With explicit headers:** 306 files (71%)
- **Inferred from path:** 123 files (29%)

## Directory → Layer Mapping

| Directory | Layer | Purpose |
|-----------|-------|---------|
| `app/api/` | L2 | REST endpoints |
| `app/adapters/` | L3 | Thin translation (<200 LOC) |
| `app/services/` | L4 | Business rules |
| `app/models/` | L4 | Domain models |
| `app/auth/` | L4 | Authorization engine |
| `app/workflow/` | L4 | Workflow engine |
| `app/skills/` | L4 | Skill implementations |
| `app/agents/` | L4 | Agent domain |
| `app/routing/` | L4 | CARE routing |
| `app/costsim/` | L4 | Cost simulation |
| `app/memory/` | L4 | Memory domain |
| `app/policy/` | L4 | Policy engine |
| `app/worker/` | L5 | Background jobs |
| `app/infra/` | L6 | Infrastructure |
| `app/db/` | L6 | Database access |

## Files Requiring Headers

The following 123 files have layer inferred from path (should add explicit headers):

### L2 (API) - 12 files without headers
- `app/api/cost_guard.py`
- `app/api/legacy_routes.py`
- `app/api/predictions.py`
- `app/api/onboarding.py`
- `app/api/costsim.py`
- `app/api/tenants.py`
- `app/api/health.py`
- `app/api/cost_intelligence.py`
- `app/api/status_history.py`
- `app/api/feedback.py`
- `app/api/founder_timeline.py`
- `app/api/cost_ops.py`

### L4 (Domain) - 89 files without headers
- Various `__init__.py` files
- Legacy domain code

### L6 (Platform) - 22 files without headers
- Infrastructure utilities

## Violations

**None detected.** BLCA verification passed.

## Acceptance Criteria

- [x] Every backend file mapped to exactly one layer
- [x] Violations explicitly listed (none found)
- [x] Layer distribution documented
