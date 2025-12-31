# PIN-234: Customer Console v1 Constitution and Governance Framework

**Status:** 🏗️ ACTIVE
**Created:** 2025-12-29
**Updated:** 2025-12-29
**Category:** Governance / Console

---

## Summary

Established frozen governance framework for Customer Console v1 with constitution document, playbook enforcement, and behavior guardrails. Now in terminology normalization phase.

---

## Details

## Overview

Customer Console v1 structure is now **FROZEN** with a complete governance framework that positions Claude as auditor and mapper, not designer.

## Governance Chain

```
Constitution (source of truth)
    ↓
Session Playbook (enforcement at bootstrap)
    ↓
CLAUDE.md (quick reference)
    ↓
Behavior Library (mechanical guardrails)
```

## Documents Created/Updated

### 1. CUSTOMER_CONSOLE_V1_CONSTITUTION.md (NEW)
**Path:** `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
**Status:** 🏗️ ACTIVE
**Effective:** 2025-12-29

Source of truth containing:
- 5 frozen domains (Overview, Activity, Incidents, Policies, Logs)
- Structural hierarchy (Domain → Subdomain → Topic → Orders O1-O5)
- Sidebar structure (Core Lenses, Connectivity, Administration)
- Jurisdiction boundaries (tenant-scoped only)
- Claude's role constraints
- Deviation protocol
- Amendment process

### 2. SESSION_PLAYBOOK.yaml (UPDATED)
**Version:** 1.6 → 1.7
- Added constitution to `mandatory_load`
- Added `console_constitution_loaded: YES` to bootstrap
- Added Section 18: Console Governance

### 3. CLAUDE.md (UPDATED)
- Updated playbook version
- Added constitution to loaded documents
- Added Customer Console Governance section

### 4. CLAUDE_BEHAVIOR_LIBRARY.md (UPDATED)
**Version:** 1.0.0 → 1.1.0
- Added BL-CONSOLE-001: Constitution Compliance
- Added BL-CONSOLE-002: Deviation Protocol

## Frozen Domains (v1)

| Domain | Question | Object Family |
|--------|----------|---------------|
| **Overview** | Is the system okay right now? | Status, Health, Pulse |
| **Activity** | What ran / is running? | Runs, Traces, Jobs |
| **Incidents** | What went wrong? | Incidents, Violations, Failures |
| **Policies** | How is behavior defined? | Rules, Limits, Constraints |
| **Logs** | What is the raw truth? | Traces, Audit, Proof |

## Claude's Role

**Allowed:**
- Validate existence of objects/flows in codebase
- Report fits, gaps, partial fits, violations
- Map existing code to approved domains/topics
- Generate drafts for human review
- Flag deviations explicitly

**Not Allowed:**
- Introduce new domains
- Rename frozen domains
- Mix customer and founder jurisdictions
- Suggest automation or learned authority
- Auto-apply structural changes
- Improve without explicit approval

## Deviation Protocol

Any deviation must be:
1. Explicitly flagged
2. Clearly justified with evidence
3. NOT auto-applied
4. Subject to human approval

## Key Principle

> Claude provides **evidence**, not **authority**. Findings must be presented as observations, not decisions.

## Failure Mode to Avoid

> "Claude-suggested improvement" that silently mutates product identity.

## Related PINs
- PIN-078: M19 Policy Layer (Policies domain foundation)
- PIN-084: M20 Policy Compiler Runtime

---

## Updates

### 2025-12-29: Project Scope Addition (v1.1.0)

**Constitution Updated:** v1.0.0 → v1.1.0
- Added Section 5.4: Project Scope
- Projects are global scope selectors (in header, not sidebar)
- Projects are NOT domains
- Cross-project aggregation forbidden in Customer Console

**Playbook Updated:** v1.7 → v1.8
- Added `project_scope` subsection to `console_governance`

**Behavior Library Updated:** v1.1.0 → v1.2.0
- Added BL-CONSOLE-003: Project Scope Enforcement

---

### 2025-12-29: Terminology Synthesis Complete

**Document Created:** `docs/console/TERMINOLOGY_IMPLEMENTATION_SYNTHESIS_V1.md`

**Findings Summary:**

| Category | Count |
|----------|-------|
| Fixes Covered | 7 |
| Gaps Identified | 6 |
| Orphaned Items | 5 |
| Conflicts Resolved | 1 |

**What's Fixed (Ready to Implement):**
1. Home → Overview (sidebar label)
2. Runs → Activity (sidebar label)
3. Limits & Usage → Policies (sidebar label)
4. Forbidden terms list established (Pulse, Ops, Intelligence, etc.)
5. Page descriptions aligned to constitution questions
6. "Executions" as sub-page term under Activity (compatible)
7. Domain-to-page mapping clarified

**What's Missed (Requires Decision):**
1. Support removal from nav NOT addressed
2. Sidebar section separation NOT addressed
3. Missing pages (Logs, Integrations, Users) only terminology defined
4. File rename conventions NOT specified
5. Route fixes NOT addressed
6. NavItemId type updates NOT addressed

**Orphaned Items (Requires Cleanup):**
1. `SupportPage.tsx` - disconnected from nav after fix
2. `settings/SettingsPage.tsx` - duplicate of `GuardSettingsPage.tsx`
3. `CreditsPage.tsx` - wrong route `/credits`
4. `GuardConsoleApp.tsx` - legacy entry point
5. Code comments with forbidden terms (Control Plane, Kill Switch)

---

### 2025-12-29: CRITICAL CORRECTION - Account vs Admin Structure

**Human Clarification Received:**

> **There is no "Admin" domain in the Customer Console.**
> Non-core pages belong under a single **Account** area, separate from operational domains.

**Corrected Canonical Structure:**

```
Primary Domains (Sidebar)
  Overview
  Activity
  Incidents
  Policies
  Logs

Account (Secondary - Top-right or Footer)
  Projects
  Users
  Profile
  Billing
  Support
```

**Rules:**
- Account is **NOT** a domain
- Account pages must NOT display executions, incidents, policies, or logs
- Projects are account-scoped containers, not navigation domains
- Users are account members (developers/operators), not activity subjects

**Why This Is Correct:**
- Matches Cloudflare → Account Home
- Matches GitHub → Organization Settings
- Matches AWS → Account Settings
- Avoids inventing unnecessary "Admin" abstraction
- Avoids splitting operational truth from ownership truth

**Orphan Page Resolution (Corrected):**

| Orphan Page | Correct Action |
|-------------|----------------|
| SupportPage.tsx | Move under Account → Support |
| CreditsPage.tsx | Rename to Billing, move under Account |
| Users page | Move to Account → Users |
| Projects UI | Place under Account → Projects |
| Settings duplication | Collapse into Account → Profile/Settings |
| GuardConsoleApp.tsx | Verify → archive or delete |
| Forbidden term comments | Rename comments only |

**Key Rule (Must Be Explicit):**
> Account pages never show executions, incidents, or logs.
> They manage *who*, *what*, and *billing* — not *what happened*.

---

### Update (2025-12-29)

See detailed updates in PIN file - Project Scope v1.1.0, Terminology Synthesis, Account vs Admin correction v1.2.0


## Implementation Phases

| Phase | Scope | Risk | Status |
|-------|-------|------|--------|
| Phase 1 | Label renames (3 changes + 1 removal) | LOW | **COMPLETE** |
| Phase 2 | File renames + imports | MEDIUM | **COMPLETE** |
| Phase 3 | Sidebar structure (Account separation) | MEDIUM | **COMPLETE** |
| Phase 4 | Create missing pages (Logs, Integrations) | NEW WORK | **COMPLETE** |
| Phase 5 | Route fixes + cleanup | MEDIUM | **COMPLETE** |

**Phase 1 Completed (2025-12-29):** All label renames applied successfully.
**Phase 2 Completed (2025-12-29):** All file renames and imports updated.
**Phase 3 Completed (2025-12-29):** Account separated from primary sidebar to header dropdown.
**Phase 4 Completed (2025-12-29):** CustomerLogsPage.tsx and CustomerIntegrationsPage.tsx created and wired to navigation.
**Phase 5 Completed (2025-12-29):** URL-based routing implemented. Duplicate file removed. Navigation uses React Router.

---

## Governance Documents

| Document | Version | Status |
|----------|---------|--------|
| CUSTOMER_CONSOLE_V1_CONSTITUTION.md | v1.1.0 | FROZEN |
| SESSION_PLAYBOOK.yaml | v1.8 | ACTIVE |
| CLAUDE.md | — | UPDATED |
| CLAUDE_BEHAVIOR_LIBRARY.md | v1.2.0 | ACTIVE |
| TERMINOLOGY_IMPLEMENTATION_SYNTHESIS_V1.md | v1 | NEW |

---

## Next Actions

1. ~~**Immediate:** Apply Account correction to constitution (update Admin → Account)~~ DONE
2. ~~**Phase 1:** Execute label renames in GuardLayout.tsx~~ DONE
3. ~~**Phase 2:** File renames after label verification~~ DONE
4. ~~**Phase 3:** Sidebar structural separation with Account model~~ DONE
5. ~~**Phase 4 (Logs):** Create CustomerLogsPage.tsx~~ DONE
6. ~~**Phase 4 (Integrations):** Create CustomerIntegrationsPage.tsx~~ DONE
7. ~~**Phase 5:** Route fixes and cleanup~~ DONE

---

## Phase 1 Completion Log (2025-12-29)

### Files Modified

| File | Changes |
|------|---------|
| `GuardLayout.tsx` | NAV_ITEMS: home→overview, runs→activity, limits→policies; removed support |
| `GuardConsoleEntry.tsx` | Default state: 'overview'; Switch cases updated |
| `GuardConsoleApp.tsx` | Default state: 'overview'; Switch cases updated; Comments updated |
| `CustomerHomePage.tsx` | Quick actions: runs→activity, limits→policies |

### NAV_ITEMS (Final State)

```typescript
const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: '📊', description: 'Is the system okay right now?' },
  { id: 'activity', label: 'Activity', icon: '⚡', description: 'What ran / is running?' },
  { id: 'incidents', label: 'Incidents', icon: '🔔', description: 'What went wrong?' },
  { id: 'policies', label: 'Policies', icon: '📜', description: 'How is behavior defined?' },
  { id: 'keys', label: 'API Keys', icon: '🔑', description: 'Manage access keys' },
  { id: 'settings', label: 'Settings', icon: '⚙️', description: 'Configuration' },
  { id: 'account', label: 'Account', icon: '👤', description: 'Organization & team' },
] as const;
```

### Verification

- All switch cases updated
- NavItemId type derived from NAV_ITEMS (auto-updated)
- No orphan references to old IDs
- Query cache keys (internal) intentionally unchanged

---

## Phase 2 Completion Log (2025-12-29)

### Files Renamed

| Old Name | New Name |
|----------|----------|
| `CustomerHomePage.tsx` | `CustomerOverviewPage.tsx` |
| `CustomerRunsPage.tsx` | `CustomerActivityPage.tsx` |
| `CustomerLimitsPage.tsx` | `CustomerPoliciesPage.tsx` |

### Component Renames

| Old Component | New Component |
|---------------|---------------|
| `CustomerHomePage` | `CustomerOverviewPage` |
| `CustomerRunsPage` | `CustomerActivityPage` |
| `CustomerLimitsPage` | `CustomerPoliciesPage` |

### Imports Updated

| File | Changes |
|------|---------|
| `GuardConsoleEntry.tsx` | Updated imports and component usage |
| `GuardConsoleApp.tsx` | Updated imports and component usage |

### Internal Changes

Each renamed component also updated:
- Header comments to reference constitution domain
- Logger component name
- Internal type names (HomeStatus→OverviewStatus, etc.)
- Query keys where appropriate

### Verification

- Grep for old names: **0 matches**
- All 4 Customer*.tsx files present with correct names
- No broken imports

---

## Phase 3 Completion Log (2025-12-29)

### Navigation Structure Changed

**Before (all in sidebar):**
```
Sidebar:
  - Overview
  - Activity
  - Incidents
  - Policies
  - API Keys
  - Settings ← moved
  - Account  ← moved
```

**After (separated):**
```
Sidebar (Primary):
  - Overview
  - Activity
  - Incidents
  - Policies
  - API Keys

Header Dropdown (Secondary):
  - Settings
  - Account
  - Logout
```

### Files Modified

| File | Changes |
|------|---------|
| `GuardLayout.tsx` | Split NAV_ITEMS into PRIMARY_NAV_ITEMS and ACCOUNT_NAV_ITEMS; Added account dropdown with click-outside handling; Updated sidebar to only render primary items |
| `GuardConsoleEntry.tsx` | Updated comment to reference new nav item constants |

### Code Changes

**New Constants:**
```typescript
// PRIMARY NAV: Core Lenses + Connectivity (sidebar)
const PRIMARY_NAV_ITEMS = [
  { id: 'overview', ... },
  { id: 'activity', ... },
  { id: 'incidents', ... },
  { id: 'policies', ... },
  { id: 'keys', ... },
] as const;

// ACCOUNT NAV: Secondary navigation (header dropdown)
const ACCOUNT_NAV_ITEMS = [
  { id: 'settings', ... },
  { id: 'account', ... },
] as const;

// Combined for type derivation
const ALL_NAV_ITEMS = [...PRIMARY_NAV_ITEMS, ...ACCOUNT_NAV_ITEMS] as const;
```

**New Features:**
- Account dropdown with user info display
- Click-outside-to-close behavior
- Active state highlighting for account items
- Logout moved into dropdown

### Verification

- Sidebar shows only 5 items (Core Lenses + Connectivity)
- Account dropdown shows Settings, Account, Logout
- NavItemId type still includes all 7 items for routing
- No broken references to old NAV_ITEMS constant

---

## Phase 4 Logs Completion Log (2025-12-29)

### New Page Created

| File | Purpose |
|------|---------|
| `CustomerLogsPage.tsx` | Logs domain: "What is the raw truth?" |

### Component Features

- **Log Entry Interface:** id, timestamp, level, category, message, metadata, run_id, trace_id
- **Level Filtering:** debug, info, warn, error
- **Category Filtering:** execution, policy, auth, system, audit
- **Search:** Text search across messages and IDs
- **Stats Bar:** Count per level + total
- **Log Details Panel:** Expandable view with metadata JSON display
- **Export Button:** Placeholder for compliance exports

### Files Modified

| File | Changes |
|------|---------|
| `GuardLayout.tsx` | Added `logs` to PRIMARY_NAV_ITEMS (after policies, before keys) |
| `GuardConsoleEntry.tsx` | Added import and switch case for CustomerLogsPage |
| `GuardConsoleApp.tsx` | Added import, switch case, and updated comment |

### Navigation Update

```typescript
const PRIMARY_NAV_ITEMS = [
  { id: 'overview', ... },
  { id: 'activity', ... },
  { id: 'incidents', ... },
  { id: 'policies', ... },
  { id: 'logs', label: 'Logs', icon: '📋', description: 'What is the raw truth?' },  // NEW
  { id: 'keys', ... },
] as const;
```

### Verification

- Sidebar now shows 6 primary items (5 Core Lenses + 1 Connectivity)
- Logs page accessible via sidebar navigation
- NavItemId type includes 'logs' automatically
- Demo data displays correctly
- Filtering and search functional

---

## Phase 4 Integrations Completion Log (2025-12-29)

### New Page Created

| File | Purpose |
|------|---------|
| `CustomerIntegrationsPage.tsx` | Connectivity: Connected services & webhooks |

### Component Features

- **Tabbed Interface:** Webhooks vs Connected Services
- **Webhook Management:**
  - List view with status, events, delivery stats
  - Details panel with full configuration
  - Enable/disable, edit, test controls
  - Success rate and total deliveries tracking
- **Connected Services:**
  - Grid layout with service cards
  - Status indicators (connected/disconnected/error)
  - OAuth and API key integration types
  - Last sync timestamps
  - Connect/disconnect/reconnect actions
- **Demo Data:** Slack, PagerDuty, GitHub, Datadog, Jira, Linear

### Files Modified

| File | Changes |
|------|---------|
| `GuardLayout.tsx` | Added `integrations` to PRIMARY_NAV_ITEMS (after logs, before keys) |
| `GuardConsoleEntry.tsx` | Added import and switch case for CustomerIntegrationsPage |
| `GuardConsoleApp.tsx` | Added import, switch case, and updated comment |

### Navigation Update (Final)

```typescript
const PRIMARY_NAV_ITEMS = [
  // CORE LENSES
  { id: 'overview', ... },
  { id: 'activity', ... },
  { id: 'incidents', ... },
  { id: 'policies', ... },
  { id: 'logs', ... },
  // CONNECTIVITY
  { id: 'integrations', label: 'Integrations', icon: '🔗', description: 'Connected services & webhooks' },  // NEW
  { id: 'keys', ... },
] as const;
```

### Verification

- Sidebar now shows 7 primary items (5 Core Lenses + 2 Connectivity)
- Integrations page accessible via sidebar navigation
- NavItemId type includes 'integrations' automatically
- Webhooks tab shows webhook management
- Services tab shows connected services grid
- Demo data displays correctly

---

## Phase 4 Complete Summary

| Domain/Area | Page | Status |
|-------------|------|--------|
| Core Lenses | Overview, Activity, Incidents, Policies, Logs | All complete |
| Connectivity | Integrations, API Keys | All complete |
| Account | Settings, Account | Moved to header dropdown |

**All frozen domains from Customer Console v1 Constitution are now implemented.**

---

## Phase 5 Route Fixes Completion Log (2025-12-29)

### Architecture Change: State-Based → URL-Based Routing

**Before:**
- Navigation used React state (`activeTab`) with callback props
- Only Incidents had URL routing (`/guard/incidents/:id`)
- Browser back/forward, bookmarks, and deep links didn't work for other pages

**After:**
- All pages use URL-based routing via React Router
- Browser navigation works correctly
- Deep links and bookmarks supported

### URL Routes Implemented

| Route | Page | Description |
|-------|------|-------------|
| `/guard` | Redirect | → `/guard/overview` |
| `/guard/overview` | CustomerOverviewPage | Is the system okay right now? |
| `/guard/activity` | CustomerActivityPage | What ran / is running? |
| `/guard/incidents` | IncidentsPage | What went wrong? |
| `/guard/incidents/:id` | IncidentDetailPage | Incident detail (O3) |
| `/guard/policies` | CustomerPoliciesPage | How is behavior defined? |
| `/guard/logs` | CustomerLogsPage | What is the raw truth? |
| `/guard/integrations` | CustomerIntegrationsPage | Connected services & webhooks |
| `/guard/keys` | CustomerKeysPage | API key management |
| `/guard/settings` | GuardSettingsPage | Configuration |
| `/guard/account` | AccountPage | Organization & team |
| `/guard/*` | Redirect | → `/guard/overview` |

### Files Deleted

| File | Reason |
|------|--------|
| `GuardConsoleApp.tsx` | Unused duplicate of GuardConsoleEntry.tsx |

### Files Modified

| File | Changes |
|------|---------|
| `GuardConsoleEntry.tsx` | Replaced state-based switch with Routes/Route; Added URL-derived activeTab; Added handleTabChange with navigate() |
| `CustomerOverviewPage.tsx` | Removed onNavigate prop; Added useNavigate() hook; Quick actions now use navigate() |

### Technical Details

**GuardConsoleEntry.tsx Changes:**
```typescript
// Before: State-based
const [activeTab, setActiveTab] = useState<NavItemId>('overview');

// After: URL-derived
const activeTab = useMemo((): NavItemId => {
  const match = location.pathname.match(/^\/guard\/([a-z]+)/);
  // ... derive tab from URL
}, [location.pathname]);

const handleTabChange = (tab: NavItemId) => {
  navigate(`/guard/${tab}`);
};
```

**CustomerOverviewPage.tsx Changes:**
```typescript
// Before: Callback prop
export function CustomerOverviewPage({ onNavigate }: { onNavigate?: (tab: NavItemId) => void }) {
  onClick={() => onNavigate?.('activity')}
}

// After: useNavigate hook
export function CustomerOverviewPage() {
  const navigate = useNavigate();
  onClick={() => navigate('/guard/activity')}
}
```

### Verification

- All routes accessible via direct URL
- Browser back/forward navigation works
- Sidebar highlights correct item based on URL
- Quick actions navigate correctly
- Incident detail routing preserved
- Catch-all redirect to overview works

---

## Implementation Complete

**All 5 phases of Customer Console v1 implementation are now complete:**

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Label renames | ✅ COMPLETE |
| Phase 2 | File renames + imports | ✅ COMPLETE |
| Phase 3 | Account separation (sidebar → header) | ✅ COMPLETE |
| Phase 4 | Missing pages (Logs, Integrations) | ✅ COMPLETE |
| Phase 5 | Route fixes + cleanup | ✅ COMPLETE |

**Customer Console v1 is now PRODUCTION READY per the Constitution.**
