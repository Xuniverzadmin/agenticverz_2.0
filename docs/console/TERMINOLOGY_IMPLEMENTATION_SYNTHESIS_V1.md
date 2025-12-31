# Terminology Implementation Synthesis: Customer Console v1

**Status:** ANALYSIS COMPLETE
**Date:** 2025-12-29
**Reference:** User Proposal + `TERMINOLOGY_NORMALIZATION_MAP_V1.md` + `CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

---

## Executive Summary

| Category | Count | Status |
|----------|-------|--------|
| Fixes Covered by Proposal | 7 | Ready to implement |
| Gaps in Proposal | 6 | Requires decision |
| Orphaned Items | 5 | Requires cleanup plan |
| Conflicts | 1 | Requires resolution |

---

## 1. WHAT THE PROPOSAL FIXES

### 1.1 Sidebar Domain Renames (HIGH PRIORITY)

| Current | Proposed | Constitution | Status |
|---------|----------|--------------|--------|
| "Home" | "Overview" | Overview | **ALIGNED** |
| "Runs" | "Activity" | Activity | **ALIGNED** |
| "Limits & Usage" | "Policies" | Policies | **ALIGNED** |
| "Incidents" | "Incidents" | Incidents | OK (no change) |

**File:** `GuardLayout.tsx:28-37` (NAV_ITEMS array)

### 1.2 Page-Level Terminology (GOOD)

| Domain | Current Page Term | Proposed Page Term | Assessment |
|--------|-------------------|-------------------|------------|
| Overview | "Status overview" | "Overview" | Aligned |
| Activity | "Run history" | "Executions" | Acceptable (sub-page level) |
| Policies | "Budget & rate limits" | "Policy Library" | Aligned |
| Incidents | "Search & investigate" | "Open Incidents" | Aligned |

### 1.3 Forbidden Terms List (EXCELLENT)

The proposal establishes clear forbidden terms:

| Forbidden Term | Reason | Assessment |
|----------------|--------|------------|
| Pulse | Founder connotation | **CRITICAL - correctly identified** |
| Ops | Jurisdiction leak | **CRITICAL - correctly identified** |
| Governance | Too abstract | Correct |
| Intelligence | Implies learned authority | **CRITICAL - correctly identified** |
| Control Plane | Infrastructure term | Correct |
| Limits | Replaced by Policies | Correct |

This list is **valuable** and should be added to constitution appendix.

### 1.4 Description Alignment (GOOD)

| Domain | Constitution Question | Proposed Description |
|--------|----------------------|---------------------|
| Overview | "Is the system okay right now?" | System status |
| Activity | "What ran / is running?" | Live Activity / Executions |
| Incidents | "What went wrong?" | Open Incidents |
| Policies | "How is behavior defined?" | Policy Library |
| Logs | "What is the raw truth?" | Execution Logs |

---

## 2. WHAT THE PROPOSAL MISSES

### 2.1 "Support" Removal NOT Addressed

**Current State:** `support` is in NAV_ITEMS (line 36)
**Constitution:** Support is NOT in frozen sidebar structure
**Proposal:** Does not mention removing Support

**Impact:** Support page will remain orphaned in navigation

**Recommendation:** Add explicit instruction to:
- Remove `{ id: 'support', ... }` from NAV_ITEMS
- Keep `SupportPage.tsx` for future use (external link or help modal)

### 2.2 Sidebar Section Separation NOT Addressed

**Current State:** Single flat list of 8 items
**Constitution:** Three distinct sections required:
```
CORE LENSES (top): Overview, Activity, Incidents, Policies, Logs
CONNECTIVITY (middle): Integrations, API Keys
ADMINISTRATION (bottom): Users, Settings, Billing, Account
```

**Proposal:** Focuses on labels only, not structure

**Impact:** Mental model confusion persists

**Recommendation:** Add structural change requirement to implementation plan

### 2.3 Missing Domains NOT Addressed

| Domain | Section | Status | Proposal Coverage |
|--------|---------|--------|------------------|
| Logs | Core Lenses | MISSING | Terminology defined, no implementation |
| Integrations | Connectivity | MISSING | Not mentioned |
| Users | Administration | MISSING | Not mentioned |

**Impact:** 3 pages need to be created, not just renamed

### 2.4 Route Placement Issues NOT Addressed

| Current Route | Expected Route | Status |
|---------------|---------------|--------|
| `/credits` | `/guard/billing` | Wrong prefix |
| `/founder/timeline` | `/ops/timeline` | Wrong prefix |
| `/founder/controls` | `/ops/controls` | Wrong prefix |

**Proposal:** Only covers labels, not routes

### 2.5 File Renames NOT Addressed

If we rename domains, what happens to these files?

| Current File | Expected File | Status |
|-------------|---------------|--------|
| `CustomerHomePage.tsx` | `CustomerOverviewPage.tsx` | Needs rename |
| `CustomerRunsPage.tsx` | `CustomerActivityPage.tsx` | Needs rename |
| `CustomerLimitsPage.tsx` | `CustomerPoliciesPage.tsx` | Needs rename |

**Proposal:** Silent on file naming conventions

### 2.6 NavItemId Type Updates NOT Addressed

If `id` values change, these need updates:

```typescript
// Current
type NavItemId = 'home' | 'runs' | 'limits' | 'incidents' | ...

// After rename
type NavItemId = 'overview' | 'activity' | 'policies' | 'incidents' | ...
```

**Impact:** Breaking change for any code referencing old ids

---

## 3. ORPHANED ITEMS

### 3.1 SupportPage.tsx

**Current:** Exists and is in navigation
**After Fix:** Will not be in navigation
**Status:** ORPHANED (keep for future external help link)

### 3.2 Duplicate Settings Pages

**Files Found:**
- `GuardSettingsPage.tsx`
- `settings/SettingsPage.tsx`

**Status:** Need to determine which is canonical

### 3.3 CreditsPage.tsx

**Current Route:** `/credits`
**Expected Route:** `/guard/billing`
**Status:** ORPHANED at wrong route

### 3.4 GuardConsoleApp.tsx

**Purpose:** "Alternative entry (dev/backup)"
**Status:** May be orphaned, needs verification

### 3.5 Old Comment References

**File:** `GuardLayout.tsx:5-11`
```typescript
* - Overview (Control Plane)  // <-- "Control Plane" is forbidden term
* - Live Activity (Phase 4)
* - Kill Switch (Phase 5)     // <-- Kill Switch is founder-only
```

**Status:** Comments need cleanup

---

## 4. CONFLICTS IDENTIFIED

### 4.1 "Executions" vs "Activity"

**Constitution says:**
- Domain name: "Activity"
- Object family: Runs, Traces, Jobs

**Proposal says:**
- Use "Executions" as page name
- "Run" may exist as field/label, not page

**Analysis:** This is NOT a conflict because:
- Sidebar domain = "Activity" (frozen)
- Page names within domain can be "Executions", "Live Activity", etc.

**Resolution:** Proposal is compatible with constitution

---

## 5. IMPLEMENTATION CHECKLIST (Derived)

### Phase 1: Label Renames (Safe, No Behavior Change)

```
[ ] GuardLayout.tsx:29 - Change 'home' → 'overview', 'Home' → 'Overview'
[ ] GuardLayout.tsx:30 - Change 'runs' → 'activity', 'Runs' → 'Activity'
[ ] GuardLayout.tsx:31 - Change 'limits' → 'policies', 'Limits & Usage' → 'Policies'
[ ] GuardLayout.tsx:36 - Remove support entry entirely
[ ] Update descriptions to match constitution questions
```

### Phase 2: File Renames (Requires Import Updates)

```
[ ] CustomerHomePage.tsx → CustomerOverviewPage.tsx
[ ] CustomerRunsPage.tsx → CustomerActivityPage.tsx
[ ] CustomerLimitsPage.tsx → CustomerPoliciesPage.tsx
[ ] Update all imports in GuardConsoleEntry.tsx
[ ] Update all imports in routes/index.tsx
```

### Phase 3: Structural Changes (Requires Layout Refactor)

```
[ ] Restructure NAV_ITEMS into 3 sections
[ ] Add section headers/dividers in sidebar
[ ] Create CustomerLogsPage.tsx (new page)
[ ] Create CustomerIntegrationsPage.tsx (new page)
[ ] Create CustomerUsersPage.tsx (new page)
```

### Phase 4: Route Fixes (Requires Route Config Changes)

```
[ ] Move /credits → /guard/billing
[ ] Add /guard/logs route
[ ] Add /guard/integrations route
[ ] Add /guard/users route
```

### Phase 5: Cleanup (Orphan Resolution)

```
[ ] Clean up comments in GuardLayout.tsx (remove "Control Plane", "Kill Switch")
[ ] Resolve GuardSettingsPage.tsx vs settings/SettingsPage.tsx
[ ] Decide fate of SupportPage.tsx
[ ] Verify GuardConsoleApp.tsx is needed
```

---

## 6. RECOMMENDATION

### Approve Proposal With Additions

The user's proposal is **GOOD** but **INCOMPLETE**. Recommend approving with these additions:

1. **Explicitly state Support is removed from nav**
2. **Add file rename conventions**
3. **Add sidebar section separation requirement**
4. **Note missing pages need creation, not just rename**

### Implementation Order

```
1. First Pass: Labels only (Phase 1) - Low risk, immediate value
2. Second Pass: File renames (Phase 2) - Medium risk, cleanup
3. Third Pass: Structure (Phase 3) - Higher risk, requires testing
4. Fourth Pass: Routes (Phase 4) - Requires coordination
5. Final Pass: Cleanup (Phase 5) - Housekeeping
```

---

## 7. WHAT REMAINS UNCHECKED

### Not Validated Yet

| Item | Reason | Risk |
|------|--------|------|
| Jurisdiction violations (GAP-011 to GAP-018) | Out of scope for terminology | HIGH |
| API response terminology | Backend contracts not checked | MEDIUM |
| Error message terminology | Not in proposal scope | LOW |
| Help text / tooltips | Not in proposal scope | LOW |

### Needs Human Decision

| Item | Options | Impact |
|------|---------|--------|
| SupportPage.tsx fate | Remove nav / Keep as modal / External link | UX |
| Duplicate settings pages | Pick canonical / Merge | Code cleanup |
| File naming convention | camelCase / kebab-case / PascalCase | Consistency |

---

## CONSOLE CONSTITUTION CHECK

```
- Constitution loaded: YES
- Proposal aligns with frozen domains: YES
- Proposal addresses all gaps: NO (6 gaps)
- Orphaned items identified: YES (5 items)
- Conflicts resolved: YES (1 conflict)
- Human approval required: YES (for additions)
- Auto-applied: NO
```

---

**This is an analysis document. No changes have been made. All implementation requires human approval.**
