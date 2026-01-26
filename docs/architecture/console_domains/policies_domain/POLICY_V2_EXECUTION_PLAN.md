# Policy Domain V2 — Execution Plan

**Status:** IN PROGRESS
**Created:** 2026-01-19
**Last Updated:** 2026-01-19
**Reference:** PIN-447, POLICY_DOMAIN_V2_DESIGN.md

---

## Phase 1: Add V2 Facade (Non-Breaking) ✅ COMPLETE

### 1.1 Create Facade API
- [x] Create `backend/app/api/policy.py` with 5 facade endpoints
- [x] Wire router to `backend/app/main.py`
- [x] Implement response models (PolicyContext, PolicySummary, etc.)

### 1.2 Facade Endpoints
- [x] `GET /api/v1/policy/active` — delegates to existing policies.active_policies
- [x] `GET /api/v1/policy/library` — delegates to existing policies.rules
- [x] `GET /api/v1/policy/lessons` — combines lessons + drafts summary
- [x] `GET /api/v1/policy/thresholds` — delegates to existing policies.limits
- [x] `GET /api/v1/policy/violations` — delegates to existing policy-layer violations

### 1.3 Detail Endpoints (O3)
- [x] `GET /api/v1/policy/active/{policy_id}`
- [x] `GET /api/v1/policy/thresholds/{threshold_id}`
- [x] `GET /api/v1/policy/violations/{violation_id}`
- [x] `GET /api/v1/policy/lessons/{lesson_id}`

---

## Phase 2: Capability Registry Update ✅ COMPLETE

### 2.1 Create Facade Capabilities
- [x] `AURORA_L2_CAPABILITY_policy.active.yaml`
- [x] `AURORA_L2_CAPABILITY_policy.library.yaml`
- [x] `AURORA_L2_CAPABILITY_policy.lessons.yaml`
- [x] `AURORA_L2_CAPABILITY_policy.thresholds.yaml`
- [x] `AURORA_L2_CAPABILITY_policy.violations.yaml`

### 2.2 Reclassify Internal Capabilities
- [ ] Mark existing `policies.*` capabilities as internal (update YAML files)
- [ ] Add `cross_domain: false` to internal capabilities
- [ ] Document capability mapping in registry

---

## Phase 3: SDSR Loop Assertions ✅ SCENARIOS CREATED

### 3.1 Create SDSR Scenarios
- [x] `SDSR-POL-LOOP-001.yaml` — Violation before incident
- [x] `SDSR-POL-LOOP-002.yaml` — Lesson references source
- [x] `SDSR-POL-LOOP-003.yaml` — Active policy has origin
- [x] `SDSR-POL-LOOP-004.yaml` — Activity resilience

### 3.2 Run Validation
- [ ] Execute SDSR scenarios
- [ ] Verify all assertions pass
- [ ] Update capability status to OBSERVED

---

## Phase 4: Cross-Domain Binding ✅ COMPLETE

### 4.1 Update Activity's policy_context ✅ COMPLETE
- [x] Add `facade_ref` to PolicyContext model
- [x] Add `threshold_ref` to PolicyContext model
- [x] Add `violation_ref` to PolicyContext model
- [x] Update `_extract_policy_context()` in activity.py

### 4.2 Update Incidents' policy binding ✅ COMPLETE
- [x] Add `policy_ref` to incident responses
- [x] Add `violation_ref` to incident responses
- [x] Add `lesson_ref` to resolved incident responses
- Note: Fields added as Optional (database schema evolution pending)

---

## Phase 5: CI Enforcement ✅ COMPLETE

### 5.1 Create Guardrails
- [x] Add capability boundary check to CI (INV-CAP-001)
- [x] Block internal.policy.* imports from Activity (INV-BOUND-002)
- [x] Block internal.policy.* imports from Incidents (INV-BOUND-002)
- [x] Created `.github/workflows/cross-domain-policy-guard.yml`

---

## Completion Checklist

- [x] All facade endpoints implemented
- [x] All facade capabilities registered
- [ ] All SDSR loop assertions passing (scenarios created, awaiting execution)
- [x] Cross-domain references in Activity working
- [x] Cross-domain references in Incidents working
- [x] CI guardrails active
- [x] Documentation complete (including Constitutional Layer)

---

## Progress Tracking

| Task | Status | Date |
|------|--------|------|
| Execution plan created | ✅ | 2026-01-19 |
| Phase 1.1 Facade API | ✅ | 2026-01-19 |
| Phase 1.2 Facade endpoints | ✅ | 2026-01-19 |
| Phase 1.3 Detail endpoints | ✅ | 2026-01-19 |
| Phase 2.1 Capabilities | ✅ | 2026-01-19 |
| Phase 2.2 Reclassify | ⏳ | (deferred) |
| Phase 3.1 SDSR Scenarios | ✅ | 2026-01-19 |
| Phase 3.2 Run Validation | ⏳ | (requires SDSR execution) |
| Phase 4.1 Activity binding | ✅ | 2026-01-19 |
| Phase 4.2 Incidents binding | ✅ | 2026-01-19 |
| Phase 5 CI | ✅ | 2026-01-19 |
| Constitutional Document | ✅ | 2026-01-19 |
| Phase 6 Governance Metadata | ✅ | 2026-01-19 |

---

## Implementation Notes

### Phase 1 Notes (2026-01-19)
- Added V2 facade endpoints to existing `policy.py` (already had approval workflow endpoints)
- All endpoints tagged with `policy-v2-facade` for filtering
- Response models include `facade_ref` for cross-domain navigation
- Endpoints are read-only (OBSERVER mode)

### Phase 2 Notes (2026-01-19)
- Created 5 capability YAML files in `backend/AURORA_L2_CAPABILITY_REGISTRY/`
- Status set to DECLARED (awaiting SDSR observation)
- All marked as `cross_domain: true`, `facade_layer: v2`

### Phase 3 Notes (2026-01-19)
- Created 4 SDSR loop assertion scenarios
- Each scenario validates a specific feedback loop invariant
- Scenarios are read-only (no cleanup required)

### Phase 4 Notes (2026-01-19)
- Updated `PolicyContext` model with `facade_ref`, `threshold_ref`, `violation_ref`
- Updated `_extract_policy_context()` helper to populate navigation refs
- Refs are built from row data: `limit_id` → threshold_ref, `violation_id` → violation_ref
- Updated `IncidentSummary` with `policy_ref`, `violation_ref` (Optional, null for now)
- Updated `IncidentDetailResponse` with `policy_id`, `policy_ref`, `violation_id`, `violation_ref`, `lesson_ref`
- Fields are navigational refs only - Incidents are narrators, not judges (INV-DOM-001)

### Phase 5 Notes (2026-01-19)
- Created `.github/workflows/cross-domain-policy-guard.yml`
- Enforces INV-BOUND-002: Blocks internal.policy.* imports from Activity/Incidents
- Enforces INV-CAP-001: Validates only 5 policy.* capabilities exist
- Validates facade endpoints are read-only (warning mode)
- Created `docs/contracts/CROSS_DOMAIN_INVARIANTS.md` (constitutional layer)

### Phase 6 Notes (2026-01-19) — Governance Metadata
- Added `PolicyMetadata` schema to V2 facade responses (aos_sdk-grade traceability)
- Fields: created_by, created_at, approved_by, approved_at, effective_from, effective_until, origin, source_proposal_id, updated_at
- Added helper functions: `_build_policy_metadata_from_rule()`, `_build_policy_metadata_from_limit()`, `_build_policy_metadata_from_lesson()`, `_build_policy_metadata_from_violation()`
- Updated all facade response models: PolicyContextSummary, PolicyLibrarySummary, PolicyLessonSummary, ThresholdSummary, ViolationSummary
- Updated all facade endpoints to populate metadata field
- Documented metadata contract in `docs/contracts/CROSS_DOMAIN_INVARIANTS.md` Section IX (INV-META-001 to INV-META-004)
- Note: Some metadata fields (approved_by, approved_at, effective_from, effective_until) return null until underlying model schemas evolve

---

## Architectural Review Guidance (2026-01-19)

### Confirmed Correct
- Policy V2 Facade is a clean authority facade
- Feedback loop is implicit, artifact-driven, resilient, human-gated
- Activity binding uses navigational refs (not operational)

### Risk Mitigations Required

**Phase 4.2 - Incidents Binding (HIGH RISK)**
- Incidents MUST only store: `policy_id`, `violation_id`, `source_run_id`
- Incidents MUST consume `/policy/violations/{id}` (read-only)
- Incidents MUST NOT query `/policy/active` to reason
- Incidents are narrators, not judges

**Phase 5 - CI Guardrails (MANDATORY)**
- Block Activity importing `internal.policy.*`
- Block Incidents importing `internal.policy.*`
- Block any domain mutating `/policy/*`
- Block new `policy.*` capabilities without SDSR

### Constitutional Document Created
- `docs/contracts/CROSS_DOMAIN_INVARIANTS.md` (LOCKED)
- Contains 15 hard invariants with CI enforcement matrix

