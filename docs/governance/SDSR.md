# SDSR: Scenario-Driven System Realization

**Status:** ACTIVE
**Effective:** 2026-01-09
**Authority:** Governance Document
**Reference:** PIN-370

---

## Definition

> **Scenario-Driven System Realization (SDSR)** is a pipeline methodology where scenarios drive coordinated realization of backend state, capability execution, API behavior, and UI projection, using the same system contracts across preflight and customer environments.

**Core Principle:** UI reveals system truth — it never asserts it.

---

## Intent

SDSR exists to solve the "fake progress" problem where:
- UI simulation felt fake
- Backend felt unexercised
- Capabilities felt unproven
- APIs felt theoretical

**Root cause:** UI was treated as the validation target, not the observation layer.

**SDSR inverts this:** Backend-first. UI observes what the system did.

---

## The SDSR Loop

```
┌──────────────────────────────┐
│ 1. SCENARIO SPEC (YAML)      │  ← Human + Claude define intent
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 2. SYNTHETIC DATA INJECTION  │  ← Machine writes to DB
│    is_synthetic = true       │
│    synthetic_scenario_id     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 3. API REALIZATION           │  ← Real endpoints, real queries
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 4. UI PROJECTION             │  ← Observes backend state
│    (via L2.1 pipeline)       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 5. HUMAN VERIFICATION        │  ← Judges correctness
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 6. PROMOTION                 │  ← /precus → /cus
│    synthetic → real          │
└──────────────────────────────┘
```

---

## Environment Mapping

| Environment | Route | Data Origin | Purpose |
|-------------|-------|-------------|---------|
| Preflight | `/precus/*` | Synthetic | Scenario validation |
| Production | `/cus/*` | Real | Customer console |

**Same code. Same APIs. Same UI. Different data origin.**

---

## SDSR Rules (MANDATORY)

### Rule 1: Backend-First

> If the DB doesn't change, nothing happened — no matter what the UI shows.

- Scenarios must write to the database first
- APIs must query real data
- UI must render what the API returns

### Rule 2: Synthetic Data Marking

Every SDSR row must have:
```sql
is_synthetic = true
synthetic_scenario_id = 'SCENARIO-ID'
```

No exceptions. Every row traceable.

### Rule 3: UI Architecture Compliance

> **UI renders projection. UI does not bypass projection.**

The L2.1 projection pipeline defines:
```
Domain → Subdomain → Topic Tabs → Panels
```

SDSR data binding happens at the **panel level** via PanelContentRegistry.

**FORBIDDEN:** Custom pages that bypass the projection structure.

### Rule 4: No Intelligence in Injection

The `inject_synthetic.py` script is purely mechanical:
- No inference
- No guessing
- No helpful defaults
- Incomplete spec → fail loudly

### Rule 5: One Scenario = One Transaction

Atomic, repeatable, idempotent when cleaned.

### Rule 6: Scenarios Inject Causes, Not Consequences (CRITICAL)

> **Scenarios must NEVER simulate cross-domain behavior.
> Cross-domain reflection must emerge ONLY from backend capabilities.**

A scenario's job is to **introduce a cause**, not to fake consequences.

**Wrong (scripting outcomes - INVALID):**
```yaml
scenario:
  - create failed run        # Activity
  - create incident          # Incidents - FORBIDDEN
  - create policy suggestion # Policies - FORBIDDEN
  - create logs              # Logs - FORBIDDEN
```

**Correct (system truth):**
```yaml
scenario:
  - create failed run (Activity domain only)

backend_propagation:  # These happen automatically
  - incident engine reacts
  - policy engine reacts
  - logging/evidence reacts

ui:
  - each domain renders its own projection
```

### Rule 7: One Scenario, One Domain of Intent

Each scenario is **authored from exactly one domain's point of view**.

Examples:
- `ACTIVITY-FAILED-RUN-001` - Activity domain
- `INCIDENTS-THRESHOLD-BREACH-001` - Incidents domain
- `POLICIES-BUDGET-VIOLATION-001` - Policies domain

### Rule 8: Scenarios Declare Expectations, Not Cross-Domain Writes

Each scenario must declare **expectations** (assertions) for other domains, not writes.

```yaml
scenario_id: ACTIVITY-FAILED-RUN-001
domain: activity

writes:                    # ONLY Activity domain
  run:
    status: FAILED
    failure_code: EXEC_TIMEOUT

expects:                   # Cross-domain ASSERTIONS
  incidents:
    - type: EXECUTION_FAILURE
      severity: HIGH

  logs:
    - contains: "EXEC_TIMEOUT"

  policies:
    - suggestion_type: RETRY_POLICY_ADJUSTMENT
```

- `writes` → **only the scenario's domain**
- `expects` → **cross-domain assertions**
- If any `expects` fail → **backend bug, not scenario bug**

---

## Cross-Domain Propagation (Backend Responsibility)

### The Principle

> If a failed Activity run does NOT create an Incident, influence Policies, or appear in Logs, then **the backend is broken**, not the scenario.

### Backend Responsibility Matrix

| Cross-Domain Effect | Owner (must be backend) | Scenario Role |
|---------------------|-------------------------|---------------|
| Run → Incident | Incident Engine | EXPECT only |
| Incident → Policy | Policy Engine | EXPECT only |
| Run → Logs | Logging / Evidence | EXPECT only |
| Incident → Logs | Logging / Evidence | EXPECT only |
| Policy → Memory | Memory / Learning | EXPECT only |

If any of these don't fire:
- ❌ Scenario is correct
- ❌ UI is correct
- ✅ **Backend capability is incomplete**

This is exactly what SDSR is meant to expose.

### What inject_synthetic.py MUST and MUST NOT Do

**MUST do:**
- Inject **only the initiating cause**
- Assert that expected downstream artifacts appear
- Fail loudly if they don't

**MUST NOT do:**
- Create incidents directly (Incident Engine's job)
- Insert policy suggestions (Policy Engine's job)
- Write logs or evidence rows (Logging system's job)

### How UI Fits

UI does **nothing special** for cross-domain linkage.

| Domain | Renders |
|--------|---------|
| Activity | Runs |
| Incidents | Incidents |
| Policies | Suggestions |
| Logs | Traces |

The *same underlying data* is rendered differently per domain.

> If UI "needs help" to show linkage → **backend contract is wrong**.

---

## Domain Execution Order (Recommended)

### Loop for EACH Domain

1. Pick **one domain**
2. Write **one causal scenario**
3. Inject **only that domain's cause**
4. Verify: same cause surfaces in other domains
5. Fix backend gaps
6. Freeze that domain
7. Move on

**No parallelism. No shortcuts.**

### Domain Dependency Order

```
Activity (cause)
    ↓
Incidents (reactive)
    ↓
Policies (reactive)
    ↓
Logs (evidence)
```

---

## UI Architecture Gate

### The Problem

Custom pages that bypass projection violate the mental model:
- Sidebar structure becomes inconsistent
- Topic tabs disappear
- Panel hierarchy breaks
- SDSR data binding location becomes unclear

### The Solution: PanelContentRegistry

```
┌─────────────────────────────────────────────────────────┐
│ routes/index.tsx                                         │
│   → Uses DomainPage (projection-driven)                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ DomainPage.tsx                                           │
│   → Domain → Subdomain → Topic Tabs → Panels             │
│   → Renders FullPanelSurface for each panel              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ FullPanelSurface                                         │
│   → Checks PanelContentRegistry                          │
│   → If registered: render real data                      │
│   → If not: render placeholder                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ PanelContentRegistry.tsx                                 │
│   → Maps panel_id → content renderer                     │
│   → Content renderer fetches from real API               │
│   → Returns JSX for panel content area                   │
└─────────────────────────────────────────────────────────┘
```

### Registered Panels (Activity Domain)

| Panel ID | Topic | Content Renderer |
|----------|-------|------------------|
| ACT-EX-AR-O1 | ACTIVE_RUNS | ActiveRunsSummary |
| ACT-EX-AR-O2 | ACTIVE_RUNS | ActiveRunsList |
| ACT-EX-CR-O1 | COMPLETED_RUNS | CompletedRunsSummary |
| ACT-EX-CR-O2 | COMPLETED_RUNS | CompletedRunsList |
| ACT-EX-RD-O1 | RUN_DETAILS | RunDetailsSummary |

### Adding New Domain Data Binding

To bind SDSR data to a new panel:

1. **Create API endpoint** in `backend/app/api/`
2. **Create API client** in `website/app-shell/src/api/`
3. **Add content renderer** in `PanelContentRegistry.tsx`
4. **Register panel_id** in the `PANEL_CONTENT_REGISTRY` map

**DO NOT:**
- Create custom pages that bypass DomainPage
- Replace projection imports in routes/index.tsx
- Render data outside the panel content area

---

## Claude Behavioral Constraints (SDSR Mode)

When operating under SDSR, Claude **MUST NOT**:

| Forbidden Action | Why |
|------------------|-----|
| Treat UI simulation as success | UI is observation, not validation |
| Log actions without state change | Logs without state = fake progress |
| Skip backend realization | Backend is the source of truth |
| Invent UI-only data | Data must come from backend/API |
| Bypass projection architecture | UI structure is frozen (L2.1) |
| Create custom pages for data display | Use PanelContentRegistry |

Claude **MUST**:

| Required Action | Why |
|-----------------|-----|
| Ask when UI architecture is unclear | Prevents structural violations |
| Use PanelContentRegistry for data binding | Respects projection pipeline |
| Verify DB changes before claiming success | Backend-first validation |
| Mark all synthetic data appropriately | Traceability requirement |

---

## Conflict Resolution

When Claude encounters ambiguity about UI architecture:

```
UI ARCHITECTURE CONFLICT DETECTED

I'm uncertain whether this change respects the projection-driven architecture.

Options:
1. Bind data at panel level via PanelContentRegistry (recommended)
2. Create a custom page (requires explicit approval)
3. Clarify the UI structure requirement

Which approach should I take?
```

**Default:** Always choose option 1 (PanelContentRegistry) unless explicitly told otherwise.

---

## Validation Checklist

Before any SDSR-related UI work:

```
SDSR UI ARCHITECTURE CHECK
- Does this use DomainPage for structure? YES / NO
- Does data binding happen via PanelContentRegistry? YES / NO
- Is the panel_id registered in the registry? YES / NO
- Does the API endpoint exist? YES / NO
- Is synthetic data properly marked? YES / NO
- Does the UI show SDSR badges where appropriate? YES / NO

If any answer is NO → STOP and resolve before proceeding.
```

---

## Files & Locations

| Component | Location |
|-----------|----------|
| Scenario specs | `scripts/sdsr/scenarios/*.yaml` |
| Injection script | `scripts/sdsr/inject_synthetic.py` |
| Panel content registry | `website/app-shell/src/components/panels/PanelContentRegistry.tsx` |
| DomainPage | `website/app-shell/src/pages/domains/DomainPage.tsx` |
| Projection lock | `website/app-shell/public/projection/ui_projection_lock.json` |
| Activity API | `backend/app/api/activity.py` |
| API client | `website/app-shell/src/api/activity.ts` |

---

## Outcomes (Success Criteria)

A domain is SDSR-complete when:

1. **Backend:** Synthetic data exists with proper marking
2. **API:** Endpoint returns real data (including synthetic)
3. **UI:** Panels render data from PanelContentRegistry
4. **Structure:** Projection hierarchy preserved (Domain → Subdomain → Topic → Panel)
5. **Verification:** Human can see SDSR badges and verify data matches DB

---

## Domain Status

### Domain Execution Order

```
Activity (cause) ← COMPLETE
    ↓
Incidents (reactive) ← IN PROGRESS (backend gaps identified)
    ↓
Policies (reactive) ← PENDING
    ↓
Logs (evidence) ← PENDING
```

### Activity Domain

**Status:** ✅ COMPLETE + E2E VALIDATED

| Component | Status |
|-----------|--------|
| Scenario | `ACTIVITY-RETRY-001.yaml` |
| Backend | `/api/v1/activity/runs` working |
| UI | PanelContentRegistry bound |
| Freeze | Ready for freeze |

### Incidents Domain

**Status:** 🔴 BLOCKED (Backend Gaps)

| Component | Status |
|-----------|--------|
| Scenario | `INCIDENTS-EXEC-FAILURE-001.yaml` created |
| Backend | **5 capabilities MISSING** |
| UI | Not yet wired |
| Freeze | Waiting on backend |

**Backend Gaps Identified:**

| Capability | Status |
|------------|--------|
| `incidents` table | MISSING |
| Incident Engine | MISSING |
| Run → Incident trigger | MISSING |
| Incident → Logs propagation | MISSING |
| Incident → Policy signals | MISSING |

### Policies Domain

**Status:** ⏸️ PENDING (Waiting on Incidents)

### Logs Domain

**Status:** ⏸️ PENDING (Waiting on Policies)

---

## Related Documents

- [PIN-370](../memory-pins/PIN-370-sdsr-scenario-driven-system-realization.md) - Full implementation details
- [SESSION_PLAYBOOK.yaml](../playbooks/SESSION_PLAYBOOK.yaml) - Governance rules
- [CLAUDE_ENGINEERING_AUTHORITY.md](CLAUDE_ENGINEERING_AUTHORITY.md) - Engineering constraints

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-09 | Initial creation - SDSR governance document |
| 2026-01-09 | Added Rules 6-8, Cross-Domain Propagation section |
| 2026-01-09 | Added Domain Status section, Incidents gaps identified |
