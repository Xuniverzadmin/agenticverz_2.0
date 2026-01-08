# PIN-355: Preflight Console Navigation Investigation

**Status:** INVESTIGATION
**Created:** 2026-01-08
**Category:** Frontend / Navigation
**Owner:** platform
**Console:** preflight-console.agenticverz.com

---

## Summary

Investigation of navigation issues in the preflight customer console (`/precus/*`). Three issues identified: no cross-console navigation, domain clicks not navigating, and panel routes missing the `/precus` prefix.

---

## Issues Identified

### Issue 1: No Cross-Console Navigation

**Severity:** HIGH

The `ProjectionSidebar` uses relative paths without the `/precus` prefix.

**Location:** `src/components/layout/ProjectionSidebar.tsx:56-62`

```typescript
const DOMAIN_ROUTES: Record<DomainName, string> = {
  Overview: '/overview',      // Should be '/precus/overview'
  Activity: '/activity',      // Should be '/precus/activity'
  Incidents: '/incidents',
  Policies: '/policies',
  Logs: '/logs',
};
```

**Additional Finding:** No links exist to other consoles (`/cus`, `/fops`, `/prefops`) anywhere in the preflight layout.

---

### Issue 2: Domain Clicks Only Toggle Expand/Collapse

**Severity:** HIGH

The `DomainSection` component renders a button that toggles expansion, not a navigation link.

**Location:** `src/components/layout/ProjectionSidebar.tsx:111-129`

```typescript
<button
  onClick={onToggle}  // Only toggles, doesn't navigate
  className={...}
>
  <span>{domain.domain}</span>
</button>
```

Clicking a domain expands/collapses the panel list but does NOT navigate to the domain page.

---

### Issue 3: Panel Routes Missing `/precus` Prefix

**Severity:** HIGH

When panels are clicked, `PanelNavItem` creates incorrect routes.

**Location:** `src/components/layout/ProjectionSidebar.tsx:158-161`

```typescript
const panelPath = `${basePath}/${panelSlug}`;
// Result: /overview/system-health (missing /precus)
// Should be: /precus/overview/system-health
```

---

### Issue 4: DomainPage Shows Static Summary Only

**Severity:** MEDIUM

The `DomainPage` component renders a read-only summary view:
- Domain header with stats
- Expandable subdomain sections
- Panel metadata cards

**Missing:**
- Clickable navigation to individual panels
- Actual panel content rendering
- Interactive data views

**Location:** `src/pages/domains/DomainPage.tsx`

---

## Architecture Gap

```
Current Flow (Broken):
┌───────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ ProjectionSidebar │ ──→ │ NavLink to      │ ──→ │ DomainPage      │
│ (domains list)    │     │ /overview       │     │ (summary only)  │
└───────────────────┘     └─────────────────┘     └─────────────────┘
                                ↑
                                └── Missing /precus prefix!

Expected Flow:
┌───────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ ProjectionSidebar │ ──→ │ NavLink to      │ ──→ │ DomainPage      │
│ (domains+panels)  │     │ /precus/overview│     │ (with panels)   │
└───────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Files Requiring Attention

| File | Issue |
|------|-------|
| `src/components/layout/ProjectionSidebar.tsx` | DOMAIN_ROUTES missing `/precus` prefix |
| `src/components/layout/ProjectionSidebar.tsx` | DomainSection uses button, not NavLink |
| `src/components/layout/Header.tsx` | No console switcher |
| `src/pages/domains/DomainPage.tsx` | Static summary, no panel navigation |
| `src/routes/index.tsx` | No panel-level route components |

---

## Route Structure Reference

**Current routes defined in `routes/index.tsx`:**

```
/precus                    → Redirect to /precus/overview
/precus/overview           → OverviewPage (summary)
/precus/overview/*         → OverviewPage (catches sub-paths)
/precus/activity           → ActivityPage
/precus/activity/*         → ActivityPage
/precus/incidents          → IncidentsPage
/precus/incidents/*        → IncidentsPage
/precus/policies           → PoliciesPage
/precus/policies/*         → PoliciesPage
/precus/logs               → LogsPage
/precus/logs/*             → LogsPage
```

The wildcard routes exist but:
1. Sidebar doesn't use `/precus` prefix
2. DomainPage doesn't handle sub-routes differently

---

## Data Status

**Data is null** - Expected at this stage. The projection visualization shows panel metadata from `ui_projection_lock.json`, not runtime data.

---

## Fixes Required (NOT APPLIED)

1. **ProjectionSidebar:** Add `/precus` prefix to DOMAIN_ROUTES or derive from routing context
2. **ProjectionSidebar:** Change domain button to NavLink for navigation
3. **Header:** Add console switcher for cross-console navigation
4. **DomainPage:** Add panel-level navigation or render actual panel content

---

## Related PINs

- PIN-352: L2.1 UI Projection Pipeline
- PIN-353: Routing Authority Infrastructure Freeze
- PIN-354: Web Server Infrastructure Documentation

---

## Next Steps

Awaiting founder decision on navigation architecture:
1. Should domains be clickable links or expand-only?
2. Should panels navigate to separate pages or render inline?
3. What cross-console navigation is needed?
