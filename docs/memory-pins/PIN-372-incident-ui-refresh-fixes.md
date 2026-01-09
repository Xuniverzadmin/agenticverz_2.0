# PIN-372: Incident & UI Refresh Fixes + Session Tasks

**Status:** COMPLETE
**Created:** 2026-01-09
**Category:** Bug Fixes / Governance / Architecture
**Related PINs:** PIN-370 (SDSR), PIN-371 (Pipeline Integration)

---

## Summary

Documents all fixes and governance enhancements completed during the 2026-01-09 session, including critical UI fixes, architectural governance rules, and endpoint deprecation.

---

## Part A: UI & Backend Fixes

### Issue 1: Incidents Metrics Returning Zeros

**Symptom:** `/api/v1/incidents/metrics` returned `{"total_open":0,"total_resolved":0,...}` despite 45 incidents in database.

**Root Cause:** The metrics endpoint was querying the dropped `sdsr_incidents` table instead of the canonical `incidents` table.

**File:** `backend/app/api/incidents.py:205-223`

```python
# BEFORE (broken)
open_result = session.execute(
    text(f"SELECT COUNT(*) FROM sdsr_incidents WHERE ...")  # Table dropped!
)

# AFTER (fixed)
open_result = session.execute(
    text(f"SELECT COUNT(*) FROM incidents WHERE UPPER(status) NOT IN ('RESOLVED', 'CLOSED'){base_filter}")
)
```

**Why It Happened:** During PIN-370 consolidation, the `sdsr_incidents` table was dropped and merged into `incidents`. The metrics endpoint wasn't updated to reflect this change.

---

### Issue 2: Auth Logout on Hard Refresh

**Symptom:** Users were logged out after every browser hard refresh (Ctrl+Shift+R or F5).

**Root Cause:** Zustand persist middleware was not persisting `user` and `isAuthenticated` to localStorage.

**File:** `website/app-shell/src/stores/authStore.ts:85-97`

```typescript
// BEFORE (broken)
partialize: (state) => ({
  token: state.token,
  refreshToken: state.refreshToken,
  tenantId: state.tenantId,
  // user and isAuthenticated were MISSING
  onboardingComplete: state.onboardingComplete,
  onboardingStep: state.onboardingStep,
}),

// AFTER (fixed)
partialize: (state) => ({
  token: state.token,
  refreshToken: state.refreshToken,
  tenantId: state.tenantId,
  // FIX: Persist user and isAuthenticated for session persistence (PIN-370)
  user: state.user,
  isAuthenticated: state.isAuthenticated,
  onboardingComplete: state.onboardingComplete,
  onboardingStep: state.onboardingStep,
  audience: state.audience,
  isFounder: state.isFounder,
}),
```

**Why It Happened:** The `setTokens` action sets `isAuthenticated: true`, but this value wasn't included in the persist config. On page reload, zustand restored token but `isAuthenticated` defaulted to `false`.

---

### Issue 3: No Auto-Refresh on Tab Focus

**Symptom:** Data didn't refresh automatically when user switched back to the browser tab. Users had to manually refresh to see new incidents.

**Root Cause:** React Query was configured with `refetchOnWindowFocus: false`.

**File:** `website/app-shell/src/main.tsx:7-16`

```typescript
// BEFORE (broken)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
      refetchOnWindowFocus: false,  // Disabled!
    },
  },
});

// AFTER (fixed)
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15000,           // Reduced from 30s to 15s
      retry: 1,
      refetchOnWindowFocus: true, // FIX: Auto-refresh when returning to tab
      refetchOnMount: true,       // Refresh on component mount
    },
  },
});
```

**Why It Happened:** Initial development likely disabled this to reduce API calls during testing, but it was never re-enabled for production.

---

## Part B: Governance Enhancements

### Task 4: ARCH-CANON-001 - Canonical-First Fix Policy

**Added To:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Section 13

**Rule:** Claude is FORBIDDEN from creating new database tables, schemas, or public APIs when addressing functional gaps in an existing domain.

**Mandatory Behavior:**
- Fix lifecycle hooks, state transitions, mappings
- Fix queries, indexing, ownership boundaries
- Add fields/handlers to existing structures

**Explicitly Forbidden:**
| Action | Why Forbidden |
|--------|---------------|
| Creating parallel tables (`sdsr_*`, `*_v2`) | Fragments analytics, policy, exports |
| Creating shadow APIs | Duplicates maintenance |
| "Temporary" structures | Temporary becomes permanent |

---

### Task 5: ARCH-FRAG-ESCALATE-001 - Fragmentation Escalation Protocol

**Added To:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Section 15

**Rule:** Fragmentation is not forbidden, but it is NEVER Claude's decision.

**When to Escalate:** If canonical fix would:
- Break backward compatibility
- Violate regulatory constraints
- Corrupt production data
- Invalidate existing customers

**Required Action:** Produce Fragmentation Escalation Report and STOP.

---

### Task 6: Canonical Repair Order

**Added To:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Section 14

**4-Step Process:**
1. **Find** the canonical structure (table, model, API, engine)
2. **Explain** why behavior is missing (hook absent, event not emitted, etc.)
3. **Fix** by extension, not duplication
4. **Re-run** scenario to verify

---

### Task 7: Migration Discipline (Raw SQL Constraint)

**Added To:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Section 16

**Principle:** Raw SQL in Alembic is a last resort, not a pattern.

**When Acceptable:**
- Cleaning up damage from architectural drift
- Complex data migrations
- `IF EXISTS` patterns not supported by `op`

**When NOT Acceptable:**
- Convenience / avoiding `op` verbosity
- Performance micro-optimization

---

### Task 8: ADR Requirement for New Tables

**Created:** `docs/templates/ARCHITECTURE_DECISION.md`

**Rule:** When proposing a new table, API, or service, Claude MUST:
1. Create ADR using template
2. Get explicit user approval
3. Reference ADR in migration/code comments

**ADR Required For:**
| Change | ADR Required |
|--------|--------------|
| New database table | YES |
| New public API endpoint | YES |
| New domain service/engine | YES |
| Adding fields to existing table | NO |
| Adding handlers to existing engine | NO |

---

## Part C: Endpoint & Engine Changes

### Task 9: Deprecate `/api/v1/incidents/trigger`

**File:** `backend/app/api/incidents.py:314-395`

**Change:** Added `deprecated=True` to FastAPI decorator and deprecation logging.

```python
@router.post("/trigger", response_model=TriggerIncidentResponse, deprecated=True)
def trigger_incident_for_run(...):
    """
    [DEPRECATED] Trigger incident creation for a failed run.

    DEPRECATION NOTICE (PIN-370):
    This endpoint is deprecated. Incidents are now created AUTOMATICALLY
    by the worker via Incident Engine when a run fails.
    """
    import logging
    logger = logging.getLogger("nova.api.incidents")
    logger.warning(
        f"DEPRECATED: /api/v1/incidents/trigger called for run_id={request.run_id}. "
        "Incidents are now auto-created by worker. This endpoint will be removed."
    )
```

**Migration Path:**
- Remove calls to this endpoint
- Incidents are auto-created on run failure
- Use `GET /incidents/by-run/{run_id}` to check for incidents

---

### Task 10: Severity Normalization in Incident Engine

**File:** `backend/app/services/incident_engine.py`

**Change:** Added normalization contract comment block and ensured severity/status stored as UPPERCASE.

```python
# NORMALIZATION CONTRACT (PIN-370)
# This engine is the SINGLE source of truth for incident field normalization.
# All incidents created by this engine use:
#   - severity: UPPERCASE (CRITICAL, HIGH, MEDIUM, LOW)
#   - status: UPPERCASE (OPEN, ACKNOWLEDGED, RESOLVED, CLOSED)
#   - category: UPPERCASE (EXECUTION_FAILURE, POLICY_VIOLATION, etc.)
#
# API layer (incidents.py) MUST NOT re-normalize. It should pass through
# values as stored, with defensive UPPER() only for legacy data.

"severity": severity.upper(),  # NORMALIZED: always uppercase
"status": "OPEN",  # NORMALIZED: always uppercase
```

---

## Part D: Documentation Created

### Task 11: PIN-370 Updates

**File:** `docs/memory-pins/PIN-370-sdsr-scenario-driven-system-realization.md`

**Updates Added:**
- Consolidation details (sdsr_incidents → incidents)
- Issues encountered and fixes applied
- Changelog entries

---

### Task 12: PIN-371 - SDSR to UI Pipeline Integration

**File:** `docs/memory-pins/PIN-371-sdsr-ui-pipeline-integration.md`

**Content:**
- Complete architecture overview (Backend → API → Frontend)
- Layer-by-layer documentation (L4/L5/L6, L2, L1)
- Data flow sequence diagram
- Panel ID registry
- Verification steps

---

### Task 13: Self-Check Updates

**File:** `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` Section 19

**Added Item 9:**
```
9. Am I creating a new table/API when a canonical one exists? (ARCH-CANON-001)
   → If yes: STOP, fix the canonical structure instead
   → If canonical fix is unsafe: produce Fragmentation Escalation Report
   → NEVER create parallel structures without explicit approval
```

---

### Task 14: SESSION_PLAYBOOK.yaml Updates

**File:** `docs/playbooks/SESSION_PLAYBOOK.yaml`

**Added Section 39:** `canonical_first_policy` (v2.39)

**Added to Blocking Rules Table in CLAUDE.md:**
| Rule | Category | Enforcement |
|------|----------|-------------|
| ARCH-CANON-001 | Canonical-First Fix | BLOCKING |
| ARCH-FRAG-ESCALATE-001 | Fragmentation Escalation | BLOCKING |

---

## Files Modified Summary

| File | Category | Changes |
|------|----------|---------|
| `backend/app/api/incidents.py` | Fix + Deprecation | Fixed metrics queries, deprecated trigger endpoint |
| `backend/app/services/incident_engine.py` | Contract | Added normalization contract |
| `website/app-shell/src/stores/authStore.ts` | Fix | Auth persistence |
| `website/app-shell/src/main.tsx` | Fix | React Query auto-refresh |
| `docs/governance/CLAUDE_ENGINEERING_AUTHORITY.md` | Governance | Sections 13-16, self-check item 9 |
| `docs/templates/ARCHITECTURE_DECISION.md` | Template | NEW - ADR template |
| `docs/playbooks/SESSION_PLAYBOOK.yaml` | Governance | Section 39 |
| `CLAUDE.md` | Governance | ARCH-CANON-001 summary |
| `docs/memory-pins/PIN-370-*.md` | Documentation | Updates |
| `docs/memory-pins/PIN-371-*.md` | Documentation | NEW - Pipeline integration |

---

## Verification

### API Verification

```bash
# Test metrics endpoint
curl -s "http://localhost:8000/api/v1/incidents/metrics"
# Expected: {"total_open":40,"total_resolved":5,"by_severity":{"critical":2,"high":23,"medium":4,"low":0}}

# Test incidents list
curl -s "http://localhost:8000/api/v1/incidents?per_page=5"
# Expected: List of 5 incidents with proper severity/status
```

### UI Verification

1. **Data Display:**
   - Navigate to: `https://preflight-console.agenticverz.com/precus/incidents`
   - Verify: Open Incidents Summary shows count (40)
   - Verify: Severity badges show (2 CRITICAL, 23 HIGH, 4 MEDIUM)

2. **Session Persistence:**
   - Login to console
   - Hard refresh (Ctrl+Shift+R)
   - Verify: Still logged in, no redirect to login page

3. **Auto-Refresh:**
   - Open console in one tab
   - Create new incident via API or worker
   - Switch away from tab, wait 15+ seconds
   - Switch back to tab
   - Verify: New incident appears without manual refresh

---

## Prevention

### Why These Issues Occurred

1. **Metrics bug:** No integration test verifying metrics against canonical table after migration
2. **Auth bug:** Manual testing didn't include hard refresh scenarios
3. **Refresh bug:** Disabled for dev convenience, never re-enabled
4. **Architectural drift:** sdsr_incidents created as shortcut instead of fixing canonical incidents table

### Preventive Measures Added

1. **ARCH-CANON-001:** Claude cannot create parallel tables without explicit approval
2. **Fragmentation Escalation:** Requires user decision, not Claude assumption
3. **ADR Requirement:** New tables require Architecture Decision Record
4. **Normalization Contract:** Engine owns field normalization, not API
5. **Raw SQL Guidance:** Use `op.*` functions, raw SQL is last resort

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-09 | Initial creation documenting all session fixes and governance updates |
