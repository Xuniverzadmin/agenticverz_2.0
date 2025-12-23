# PIN-146: M28 Unified Console UI Implementation

**Status:** COMPLETE
**Date:** 2025-12-23
**Milestone:** M28 Unified Console

---

## Summary

This PIN documents the implementation of the M28 Unified Console UI components:
1. **Customer Home** - Calm status board for customers
2. **Founder Pulse** - Command cockpit for founders

These follow the "status board, not dashboard" principle - showing state, not stats.

---

## Customer Home (`/guard` → Home tab)

### Design Principles
- **3 States Only:** PROTECTED (green), ATTENTION NEEDED (amber), ACTION REQUIRED (red)
- **No charts** - anxiety-inducing
- **No animations** - distracting
- **Max 3 lines** of recent activity
- **Quick Actions** for immediate navigation

### Components
```
CustomerHomePage.tsx
├── Status Hero (PROTECTED/ATTENTION NEEDED/ACTION REQUIRED)
├── Today at a Glance (3 cards)
│   ├── Requests Today
│   ├── Incidents Blocked
│   └── AI Spend Today
├── Recent Activity (max 3 lines)
└── Quick Actions (View Incidents, View Cost, Manage API Keys)
```

### Files Modified
- `website/aos-console/console/src/pages/guard/CustomerHomePage.tsx` (NEW)
- `website/aos-console/console/src/pages/guard/GuardLayout.tsx` (added 'home' nav item)
- `website/aos-console/console/src/pages/guard/GuardConsoleEntry.tsx` (wired CustomerHomePage)

### Navigation Update
- 'home' is now the primary landing tab (was 'overview')
- Default route `/guard` shows Customer Home

---

## Founder Pulse (`/ops` → Pulse tab)

### Design Principles
- **4 States:** STABLE, ELEVATED, DEGRADED, CRITICAL
- **10-second situation awareness** - glance and know
- **Read-only by design** - observe, don't act
- **Critical signals visible in <3 seconds**
- **Tenants at risk ranked by severity**

### Components
```
FounderPulsePage.tsx
├── Status Bar (STABLE/ELEVATED/DEGRADED/CRITICAL)
├── Critical Signals (4 cards)
│   ├── Active Incidents
│   ├── Cost Anomaly Tenants
│   ├── Policy Drift
│   └── Infra Health
├── Live Feeds (2 columns)
│   ├── Incident Stream (left)
│   └── Cost Watch (left)
├── Tenants at Risk (right, ranked)
└── Recent System Actions (right, audit log)
```

### Files Modified
- `website/aos-console/console/src/pages/ops/FounderPulsePage.tsx` (NEW)
- `website/aos-console/console/src/pages/ops/OpsConsoleEntry.tsx` (added Pulse/Console tabs)

### Navigation Update
- Ops console now has Pulse/Console tab switcher
- Pulse is the default landing view

---

## Technical Notes

### No date-fns Dependency
Both components use a local `formatRelativeTime()` function instead of date-fns:
```typescript
function formatRelativeTime(date: Date): string {
  const diffMins = Math.floor((now - date) / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  // ...
}
```

### Data Sources
- **Customer Home:** Derives from `/guard/status` and `/guard/snapshot/today`
- **Founder Pulse:** Derives from `/ops/pulse`, `/ops/infra`, `/ops/customers`

### Type Safety
- CustomerHomePage uses `NavItemId` type from GuardLayout
- Both components use proper TypeScript interfaces for data structures

---

## Related PINs

- PIN-132: M28 Unified Console Blueprint (design spec)
- PIN-145: M28 Deletion Execution Report (cleanup)

---

## Conclusion

> Customers see calm. Founders see truth.
> Both in 10 seconds or less.

M28 UI implementation complete. Two views, two purposes, zero noise.
