# PIN-111: Founder Ops Console UI

**Status:** ✅ COMPLETE
**Created:** 2025-12-20
**Category:** Frontend / Ops Console / M24
**Milestone:** M24 Phase-2.1

---

## Summary

Implemented the Founder Ops Console - a single-page, read-only, signal-first dashboard for founders and ops. This is "AI Mission Control" - one screen with system truth, at-risk customers, and founder playbooks.

**Access URL:** https://agenticverz.com/console/ops

---

## Design Principles

### What This UI IS
- ✅ **Founder/Ops/Trust Console** - One screen, read-only, signal-first
- ✅ **AI Mission Control** - Glanceable system truth
- ✅ **TV-friendly** - Designed for 1920×1080, dark mode only

### What This UI is NOT
- ❌ Not an admin CRUD panel
- ❌ Not a settings-heavy dashboard
- ❌ Not something customers click around daily

---

## Layout

**Grid:** 2×2 layout with top strip

### TOP STRIP - System Truth (always visible)

```
🟢 SYSTEM: HEALTHY  |  🔥 INCIDENTS: 6  |  💰 COST TODAY: $0.27  |  ⏱ p95 LATENCY: 0ms
📦 DB: 0.02/10 GB (0.2%)  |  🧠 REDIS: 0/256 MB (0.0%)  |  👥 ACTIVE (24h): 12
```

**Data Sources:**
- `GET /ops/pulse` - System health, incidents, cost, latency
- `GET /ops/infra` - DB storage, Redis memory, connections

**Rules:**
- Green/Yellow/Red only
- No charts - just facts
- This is what you glance at before sleeping

### LEFT PANEL - Customers at Risk

```
⚠️ AT-RISK CUSTOMERS (3)

• tenant-8214...
  - Stickiness ↓ (δ=0.71)
  - 5 aborts in last 14d
  - Suggested: "Schedule 15-min call"
```

**Data Source:** `GET /ops/customers/at-risk`

**Features:**
- Shows WHY, not just WHO
- Suggested interventions inline (call, email, slack, policy adjust)
- Triggering signals for explainability
- Empty state: "No customers at risk (yet)"
- Click to expand → shows interventions with signals

### CENTER - Founder Playbooks

```
📘 FOUNDER PLAYBOOKS (5)

[ Silent Churn Recovery ] - HIGH
  Trigger: Stickiness ↓ + No activity 7d
  Action: Email nudge + replay enable

[ Policy Friction Loop ] - MEDIUM
  Trigger: ≥3 POLICY_BLOCK_REPEAT
  Action: Relax guard → monitor 24h
```

**Data Source:** `GET /ops/playbooks`

**Configured Playbooks:**
1. Silent Churn Recovery (HIGH)
2. Policy Friction Resolution (MEDIUM)
3. Flow Abandonment Recovery (HIGH)
4. Engagement Recovery (CRITICAL)
5. Legal-Only Customer Expansion (MEDIUM)

**Features:**
- Click = expand → full logic
- Shows trigger conditions, suggested actions, expected outcomes
- No editing in v1 (don't overbuild)

### TOP RIGHT PANEL - All Customers

```
👥 ALL CUSTOMERS (12)

Sort: [Stickiness ↓] [Friction] [Recent]

• tenant-abc123
  Stickiness: 0.85 ↑ (7d: 0.82, 30d: 0.79)
  Friction: 5.2 🟢
  Last seen: 2h ago

• tenant-def456
  Stickiness: 0.72 ↓ (7d: 0.78, 30d: 0.81)
  Friction: 15.8 🟡
  Last seen: 1d ago
```

**Data Source:** `GET /ops/customers`

**Features:**
- Sort controls: Stickiness (default), Friction, Recent activity
- Color-coded friction: 🟢 < 10 < 🟡 < 20 < 🔴
- Stickiness trend arrows (↑ rising, ↓ falling, → stable)
- 7d/30d stickiness comparison

### BOTTOM RIGHT - Timeline (Placeholder)

```
No ops_events yet.
System is waiting for real activity.
```

**Future:** Scrollable event feed, time-ordered, filterable by customer/incident.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | React + Vite |
| Styling | Tailwind CSS |
| Icons | Lucide React |
| Polling | 15-second interval |
| Mode | Dark mode only |
| Size | 18KB (gzipped: 4.42KB) |

---

## Files Created

| File | Purpose |
|------|---------|
| `website/aos-console/console/src/api/ops.ts` | API client with TypeScript types |
| `website/aos-console/console/src/pages/ops/FounderOpsConsole.tsx` | Main page component |
| Updated `routes/index.tsx` | Added `/ops` route |
| Updated `Sidebar.tsx` | Added "Ops Console" nav item |

---

## API Endpoints Wired

| Endpoint | Purpose | Poll Interval |
|----------|---------|---------------|
| `/ops/pulse` | System health | 15s |
| `/ops/infra` | Infrastructure metrics | 15s |
| `/ops/customers/at-risk` | At-risk customers | 15s |
| `/ops/customers` | All customers | 15s |
| `/ops/playbooks` | Founder playbooks | 15s |

---

## Apache Configuration

Added proxy rule for `/ops` endpoint:
```apache
# Ops Console API
ProxyPass        /ops http://127.0.0.1:8000/ops
ProxyPassReverse /ops http://127.0.0.1:8000/ops
```

---

## Screenshots (Conceptual)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🟢 SYSTEM: HEALTHY │ 🔥 INCIDENTS: 6 │ 💰 $0.27 │ ⏱ 0ms │ 📦 0.02GB │ 12 👥  │
├─────────────────────────────────────┬───────────────────────────────────────┤
│                                     │                                       │
│  ⚠️ AT-RISK CUSTOMERS (3)            │  👥 ALL CUSTOMERS (12)                │
│                                     │                                       │
│  ⚠️ tenant-8214...                   │  Sort: [Stickiness] [Friction]        │
│     δ=0.71 ↓, 5 aborts              │                                       │
│     → Call                          │  • tenant-abc123                      │
│                                     │    Stickiness: 0.85 ↑                 │
│  ⚠️ tenant-4ac6...                   │    Friction: 5.2 🟢                   │
│     δ=0.68 ↓, 3 aborts              │                                       │
│                                     │  • tenant-def456                      │
│                                     │    Stickiness: 0.72 ↓                 │
├─────────────────────────────────────┼───────────────────────────────────────┤
│                                     │                                       │
│  📘 FOUNDER PLAYBOOKS (5)            │  ⏳ TIMELINE                           │
│                                     │                                       │
│  📘 Silent Churn Recovery           │  Waiting for real activity...        │
│     HIGH - Stickiness ↓ + No 7d     │                                       │
│                                     │                                       │
│  📘 Policy Friction Resolution      │                                       │
│     MEDIUM - ≥3 POLICY_BLOCK        │                                       │
│                                     │                                       │
└─────────────────────────────────────┴───────────────────────────────────────┘
│ Polling 15s │ 3 at-risk │ 12 customers │ 5 playbooks │ Uptime: 100%         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Commits

- `35a46a7` - feat(ops-console): Implement Founder Ops Console - AI Mission Control

---

## Related PINs

- [PIN-105](PIN-105-ops-console-founder-intelligence.md) - Ops Console Founder Intelligence
- [PIN-107](PIN-107-m24-phase2-friction-intel.md) - M24 Phase-2 Friction Intelligence
- [PIN-110](PIN-110-enhanced-compute-stickiness-job.md) - Enhanced Stickiness Job
- [PIN-112](PIN-112-compute-stickiness-scheduler.md) - Compute Stickiness Scheduler

---

## Updates

### 2025-12-20: Added Customers Panel (M24 Phase-2.1)

**Changes:**
- Added `CustomersPanel` component displaying all customer segments
- Changed layout from 3-column to 2×2 grid:
  - Top Left: At-Risk Customers
  - Top Right: All Customers (NEW)
  - Bottom Left: Founder Playbooks
  - Bottom Right: Timeline (placeholder)
- Wired `/ops/customers` endpoint (parallel fetch with other ops data)
- Added sort controls: Stickiness (default), Friction, Recent activity
- Customer cards show: Tenant ID, Stickiness trend, 7d/30d values, Friction score (color-coded), Last seen
- Updated footer status bar with customer count

**Endpoint Mapping Complete (5/5):**

| Endpoint | UI Panel |
|----------|----------|
| `/ops/pulse` | Top strip |
| `/ops/infra` | Top strip |
| `/ops/customers/at-risk` | At-Risk panel |
| `/ops/customers` | All Customers panel |
| `/ops/playbooks` | Playbooks panel |

### 2025-12-20: Dark Mode Default & Skeleton Loading UI

**Problem:** Console was loading with white flash and slow perceived loading.

**Changes:**

1. **Dark Mode Default** (`website/aos-console/console/src/index.css`):
   - Changed `:root` to use dark mode colors by default
   - Light mode now requires explicit `[data-theme='light']` attribute
   - Added `html { background-color: #030712; }` to prevent flash

2. **White Flash Prevention** (`website/aos-console/console/index.html`):
   - Added inline critical CSS styles
   - Set `style="background-color: #030712;"` on html, body elements
   - Added `<meta name="theme-color" content="#030712">`

3. **Skeleton Loading UI** (`FounderOpsConsole.tsx`):
   - Replaced spinner with skeleton layout during initial load
   - Skeleton shows 2x2 grid structure with animated pulse
   - Improves perceived loading time

**Result:** No more white flash on page load. Console loads visually faster.

### 2025-12-20: Standalone Console Entry Points

**Problem:** Both Guard and Ops consoles redirected to /console/login, requiring users to authenticate through the main AOS console first.

**Solution:** Created standalone entry points with independent authentication.

**New Files:**
- `website/aos-console/console/src/pages/guard/GuardConsoleEntry.tsx`
- `website/aos-console/console/src/pages/ops/OpsConsoleEntry.tsx`

**Routing Changes** (`routes/index.tsx`):
- Added `/guard` and `/ops` as PUBLIC routes (before ProtectedRoute)
- Each console handles its own API key authentication
- API keys stored in localStorage per-console

**Access URLs:**
- Guard Console: `https://agenticverz.com/console/guard`
- Ops Console: `https://agenticverz.com/console/ops`
- AOS Console: `https://agenticverz.com/console` (requires login)

**Prevention Script Added:**
- `scripts/ops/verify_console_routes.sh` - Verifies route configuration

**Authentication Flow:**
1. User visits `/console/guard` or `/console/ops`
2. Entry component checks localStorage for API key
3. If not found, shows login form
4. On valid key, shows console content
5. Key stored in localStorage for session persistence

### 2025-12-20: Dark Mode Only Console

**Problem:** Console had both light and dark mode support, causing unnecessary complexity and potential white flash issues.

**Solution:** Converted entire console to dark mode only - removed all light mode support.

**Changes:**

1. **HTML Configuration** (`index.html`):
   - Added `class="dark"` to force Tailwind dark mode
   ```html
   <html lang="en" class="dark" style="background-color: #030712;">
   ```

2. **Tailwind Configuration** (`tailwind.config.js`):
   - Updated to class-based dark mode strategy
   ```javascript
   darkMode: 'class',  // Dark mode only via html.dark class
   ```

3. **CSS Variables** (`index.css`):
   - Rewrote with dark-only color scheme
   - Added CSS variables for consistent theming:
     - `--color-bg-primary: #0f172a` (slate-900)
     - `--color-bg-secondary: #030712` (gray-950)
     - `--color-bg-card: #1e293b` (slate-800)
     - `--color-text-primary: #f8fafc` (slate-50)
   - Added dark scrollbar styling
   - Set `color-scheme: dark`

4. **Removed Theme Toggle** (`Header.tsx`):
   - Removed theme toggle button from header
   - Removed `useUIStore` theme state import

5. **Simplified Component Styles**:
   - Removed all `dark:` prefixed Tailwind classes from:
     - `Header.tsx`
     - `Sidebar.tsx`
     - `StatusBar.tsx`
     - `AppLayout.tsx`
     - `LoginPage.tsx`
     - `routes/index.tsx` (LoadingFallback)

**Result:**
- Zero white flash on any page load
- Consistent dark theme across all pages
- Simpler CSS with no light/dark branching
- Reduced bundle size (no theme toggle logic)
- TV-friendly ops console for founders
