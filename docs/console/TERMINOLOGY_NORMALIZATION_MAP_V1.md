# Terminology Normalization Map: Customer Console v1

**Status:** MAP ONLY (No Changes Applied)
**Date:** 2025-12-29
**Auditor:** Claude (BL-CONSOLE-001 compliant)
**Reference:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`

---

## 1. Canonical Vocabulary (Frozen)

From the Customer Console v1 Constitution:

### Core Lenses (Frozen Domains)

| Domain | Canonical Label | Allowed Synonyms | Forbidden Terms |
|--------|-----------------|------------------|-----------------|
| Overview | "Overview" | "Status" | "Home", "Dashboard", "Pulse" |
| Activity | "Activity" | "Executions", "Agents" | "Runs", "Jobs", "Tasks" |
| Incidents | "Incidents" | — | "Errors", "Failures", "Issues" |
| Policies | "Policies" | "Policy Library" | "Limits", "Constraints", "Rules" |
| Logs | "Logs" | — | "Traces", "Audit", "Events" |

### Connectivity Section

| Item | Canonical Label | Allowed Synonyms |
|------|-----------------|------------------|
| Integrations | "Integrations" | — |
| API Keys | "API Keys" | "Keys" |

### Administration Section

| Item | Canonical Label | Allowed Synonyms |
|------|-----------------|------------------|
| Users | "Users" | "Team" |
| Settings | "Settings" | "Configuration" |
| Billing | "Billing" | — |
| Account | "Account" | "Organization" |

---

## 2. Current State vs Canonical

### Labels Requiring Change

| Current Label | Canonical Label | Change Type | Priority |
|---------------|-----------------|-------------|----------|
| "Home" | "Overview" | RENAME | HIGH |
| "Runs" | "Activity" | RENAME | HIGH |
| "Limits & Usage" | "Policies" | RENAME | HIGH |
| "Support" | — | REMOVE | MEDIUM |

### Labels Already Correct

| Current Label | Canonical Label | Status |
|---------------|-----------------|--------|
| "Incidents" | "Incidents" | OK |
| "API Keys" | "API Keys" | OK |
| "Settings" | "Settings" | OK |
| "Account" | "Account" | OK |

### Labels Missing (Gaps)

| Canonical Label | Section | Current State |
|-----------------|---------|---------------|
| "Logs" | Core Lenses | NOT IMPLEMENTED |
| "Integrations" | Connectivity | NOT IMPLEMENTED |
| "Users" | Administration | NOT IMPLEMENTED |
| "Billing" | Administration | WRONG ROUTE (`/credits`) |

---

## 3. File Locations (Exact)

### Primary Location: NAV_ITEMS Array

**File:** `website/aos-console/console/src/pages/guard/GuardLayout.tsx`
**Lines:** 28-37

```typescript
// CURRENT STATE (lines 28-37)
const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: '🏠', description: 'Status overview' },
  { id: 'runs', label: 'Runs', icon: '🚀', description: 'Run history & outcomes' },
  { id: 'limits', label: 'Limits & Usage', icon: '📊', description: 'Budget & rate limits' },
  { id: 'incidents', label: 'Incidents', icon: '📋', description: 'Search & investigate' },
  { id: 'keys', label: 'API Keys', icon: '🔑', description: 'Manage access keys' },
  { id: 'settings', label: 'Settings', icon: '⚙️', description: 'Configuration' },
  { id: 'account', label: 'Account', icon: '👤', description: 'Organization & team' },
  { id: 'support', label: 'Support', icon: '💬', description: 'Help & feedback' },
] as const;
```

---

## 4. Proposed Changes (For Human Review)

### Change 1: Home → Overview

**File:** `GuardLayout.tsx:29`

| Field | Current | Proposed |
|-------|---------|----------|
| id | `'home'` | `'overview'` |
| label | `'Home'` | `'Overview'` |
| icon | `'🏠'` | `'📊'` or `'🔍'` |
| description | `'Status overview'` | `'System status at a glance'` |

**Impact:**
- Sidebar label changes
- Header title changes (auto via NAV_ITEMS lookup)
- Internal navigation id changes (requires component updates)

---

### Change 2: Runs → Activity

**File:** `GuardLayout.tsx:30`

| Field | Current | Proposed |
|-------|---------|----------|
| id | `'runs'` | `'activity'` |
| label | `'Runs'` | `'Activity'` |
| icon | `'🚀'` | `'⚡'` or `'📋'` |
| description | `'Run history & outcomes'` | `'What ran and is running'` |

**Impact:**
- Sidebar label changes
- Header title changes
- Internal navigation id changes

---

### Change 3: Limits & Usage → Policies

**File:** `GuardLayout.tsx:31`

| Field | Current | Proposed |
|-------|---------|----------|
| id | `'limits'` | `'policies'` |
| label | `'Limits & Usage'` | `'Policies'` |
| icon | `'📊'` | `'📜'` or `'⚖️'` |
| description | `'Budget & rate limits'` | `'How behavior is defined'` |

**Impact:**
- Sidebar label changes
- Header title changes
- Internal navigation id changes
- Conceptual shift: Limits → Policies (broader abstraction)

---

### Change 4: Remove Support

**File:** `GuardLayout.tsx:36`

| Field | Current | Proposed |
|-------|---------|----------|
| (entire line) | `{ id: 'support', ... }` | REMOVE |

**Rationale:** Support is not in the frozen constitution sidebar structure.

**Impact:**
- Sidebar item removed
- SupportPage.tsx becomes orphaned (keep for future use)

---

## 5. Dependent Code Locations

When `id` values change, these locations need updates:

### Components Using NavItemId

| File | Usage | Lines (approx) |
|------|-------|----------------|
| `GuardLayout.tsx` | `type NavItemId` | 39 |
| `GuardConsoleEntry.tsx` | `activeTab` state | various |
| `CustomerHomePage.tsx` | imported type | various |

### Route Matching

| File | Pattern | Impact |
|------|---------|--------|
| `GuardConsoleEntry.tsx` | `switch (activeTab)` | Must match new ids |
| Routes in `routes/index.tsx` | Path matching | May need updates |

---

## 6. Description Alignment

Descriptions should match domain questions from constitution:

| Domain | Constitution Question | Proposed Description |
|--------|----------------------|---------------------|
| Overview | "Is the system okay right now?" | "System status at a glance" |
| Activity | "What ran / is running?" | "What ran and is running" |
| Incidents | "What went wrong?" | "Search & investigate" (OK) |
| Policies | "How is behavior defined?" | "How behavior is defined" |
| Logs | "What is the raw truth?" | "Raw execution records" |

---

## 7. Icon Recommendations

Current icons may need updating to match domain semantics:

| Domain | Current Icon | Options |
|--------|--------------|---------|
| Overview | 🏠 (home) | 📊 (chart), 🔍 (inspect), ✅ (status) |
| Activity | 🚀 (rocket) | ⚡ (action), 📋 (list), 🔄 (running) |
| Policies | 📊 (chart) | 📜 (scroll), ⚖️ (scale), 📋 (rules) |
| Logs | — | 📝 (records), 📄 (document), 🔍 (search) |

**Note:** Icon changes are cosmetic, not semantic. Lower priority.

---

## 8. Sidebar Section Separation

The constitution requires 3 distinct sections. Current implementation has no visual separation.

### Required Structure

```
┌─────────────────────────────┐
│ CORE LENSES                 │  ← Section header needed
│   Overview                  │
│   Activity                  │
│   Incidents                 │
│   Policies                  │
│   Logs                      │
├─────────────────────────────┤  ← Visual separator needed
│ CONNECTIVITY                │  ← Section header needed
│   Integrations              │
│   API Keys                  │
├─────────────────────────────┤  ← Visual separator needed
│ ADMINISTRATION              │  ← Section header needed
│   Users                     │
│   Settings                  │
│   Billing                   │
│   Account                   │
└─────────────────────────────┘
```

**Implementation:** Requires restructuring NAV_ITEMS into 3 arrays or adding section markers.

---

## 9. Summary of Changes

### High Priority (Terminology)

| # | Change | File | Line |
|---|--------|------|------|
| 1 | Home → Overview | GuardLayout.tsx | 29 |
| 2 | Runs → Activity | GuardLayout.tsx | 30 |
| 3 | Limits & Usage → Policies | GuardLayout.tsx | 31 |
| 4 | Remove Support | GuardLayout.tsx | 36 |

### Medium Priority (Structure)

| # | Change | Impact |
|---|--------|--------|
| 5 | Add section separators | Layout restructure |
| 6 | Add section headers | CSS/component change |

### Low Priority (Cosmetic)

| # | Change | Impact |
|---|--------|--------|
| 7 | Update icons | Visual only |
| 8 | Update descriptions | Text only |

---

## 10. Cascading Impact Analysis

### If `id: 'home'` → `id: 'overview'`

Files requiring update:
- `GuardLayout.tsx` - NAV_ITEMS
- `GuardConsoleEntry.tsx` - switch/case, default state
- Any component using `NavItemId` type

### If `id: 'runs'` → `id: 'activity'`

Files requiring update:
- `GuardLayout.tsx` - NAV_ITEMS
- `GuardConsoleEntry.tsx` - switch/case
- `CustomerRunsPage.tsx` - may need rename to `CustomerActivityPage.tsx`

### If `id: 'limits'` → `id: 'policies'`

Files requiring update:
- `GuardLayout.tsx` - NAV_ITEMS
- `GuardConsoleEntry.tsx` - switch/case
- `CustomerLimitsPage.tsx` - may need rename to `CustomerPoliciesPage.tsx`

---

## CONSOLE CONSTITUTION CHECK

```
- Constitution loaded: YES
- Frozen domains respected: 4/5 (Logs missing)
- Terminology changes identified: 4
- Human approval required: YES (before any changes)
- Deviations flagged: YES (see above)
- Auto-applied: NO
```

---

**This is a terminology map only. No changes have been made. All changes require human approval.**
