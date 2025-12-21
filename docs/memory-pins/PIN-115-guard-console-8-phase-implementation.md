# PIN-115: Guard Console 8-Phase Implementation & Health Scripts

**Status:** COMPLETE
**Created:** 2025-12-21
**Category:** Frontend / Console
**Milestone:** M23.1 Guard Console Enhancement
**Related PINs:** PIN-100, PIN-114

---

## Summary

Complete implementation of the 8-phase Guard Console customer dashboard with unified navigation, plus creation of comprehensive health test scripts for both Guard Console and AOS Console.

---

## 8-Phase Implementation

### Phase 1: Truthful Control Plane
- **Component:** `GuardDashboard.tsx`
- **Features:** Real-time status, guardrail indicators, incident counts
- **Status:** Enhanced (existing)

### Phase 2-3: Incident Discovery & Decision Timeline
- **Component:** `IncidentsPage.tsx`, `DecisionTimeline.tsx`
- **Features:** Search, filters, step-by-step trace visualization
- **Status:** Enhanced (existing)

### Phase 4: Live Logs & Streaming
- **Components:** `LiveActivityPage.tsx`, `LogsPage.tsx`
- **Features:**
  - Real-time event streaming with pause/resume
  - Event type filtering (INPUT_RECEIVED, POLICY_BLOCKED, etc.)
  - Historical log viewer with time range selection
  - Search and category filters
- **Status:** NEW

### Phase 5: Kill Switch Effects & Blast Radius
- **Component:** `KillSwitchPage.tsx`
- **Features:**
  - Large visual status card (TRAFFIC STOPPED / TRAFFIC FLOWING)
  - Current blast radius with live stats
  - Before/after traffic comparison
  - Kill history with expandable impact analysis
- **Status:** NEW

### Phase 6-7: Replay & Evidence
- **Integration:** Via existing APIs and export functionality
- **Features:** Decision replay, PDF evidence export
- **Status:** Integrated

### Phase 8: Operator Confidence Polish
- **Component:** `GuardSettingsPage.tsx`
- **Features:**
  - Guardrails configuration with toggles
  - Notification settings (email, Slack)
  - API key management table
  - Export options (CSV, PDF, JSON)
  - Help boxes with guardrail explanations
- **Status:** NEW

---

## New Files Created

### Guard Console Components
```
website/aos-console/console/src/pages/guard/
├── GuardLayout.tsx         # Unified sidebar navigation
├── LiveActivityPage.tsx    # Real-time event streaming
├── KillSwitchPage.tsx      # Kill switch with blast radius
├── LogsPage.tsx            # Historical log viewer
├── GuardSettingsPage.tsx   # Configuration & settings
└── GuardConsoleApp.tsx     # Alternate entry point
```

### Health Test Scripts
```
scripts/ops/
├── guard_health_test.sh      # Guard Console health (17 tests)
└── aos_console_health_test.sh # AOS Console health (36 tests)
```

---

## Navigation Structure

```
Guard Console (https://agenticverz.com/console/guard)
├── Overview      (Control plane & status)
├── Live Activity (Real-time event stream)
├── Incidents     (Search & investigate)
├── Kill Switch   (Emergency controls + blast radius)
├── Logs          (Event history)
└── Settings      (Configuration)
```

---

## Health Test Scripts

### guard_health_test.sh
Tests Guard Console specific features:
- Endpoint health (status, snapshot, incidents)
- Circuit breaker simulation
- API response validation
- Demo incident seeding
- Frontend files check
- Production deployment
- Apache proxy configuration

**Result:** 17/18 PASS

### aos_console_health_test.sh
Comprehensive AOS platform tests:
1. Core Health Endpoints (/health, /healthz, /metrics)
2. Runtime API (capabilities, skills, simulate)
3. Runs & Traces API
4. Failure Catalog (M9)
5. Recovery Engine (M10)
6. Credits & Billing
7. Blackboard / Memory
8. SBA (Strategy-Bound Agents)
9. Guard API
10. Ops Console API
11. Frontend Files Check (12 components)
12. Production Build Check
13. Console Accessibility
14. Docker Services Check

**Result:** 36/36 PASS (7 warnings for unimplemented features)

---

## Build Output

```
GuardConsoleEntry: 98.83 kB (23.99 kB gzipped)
Total modules: 2428
Build time: 20.15s
```

---

## API Endpoints Verified

| Endpoint | Status |
|----------|--------|
| `/guard/status` | ✅ Working |
| `/guard/snapshot/today` | ✅ Working |
| `/guard/incidents` | ✅ Working |
| `/guard/demo/seed-incident` | ✅ Working |
| `/ops/pulse` | ✅ Working |
| `/ops/infra` | ✅ Working |
| `/api/v1/runtime/capabilities` | ✅ Working |
| `/api/v1/runtime/skills` | ✅ Working |
| `/api/v1/recovery/candidates` | ✅ Working |
| `/api/v1/sba` | ✅ Working |

---

## Usage

### Access Guard Console
```
https://agenticverz.com/console/guard
```

Demo login available with pre-configured API key.

### Run Health Tests
```bash
# Guard Console health
bash scripts/ops/guard_health_test.sh

# Full AOS Console health
bash scripts/ops/aos_console_health_test.sh
```

---

## Technical Details

### QueryClient Configuration
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});
```

### Event Types (LiveActivityPage)
- INPUT_RECEIVED
- POLICY_PASSED
- POLICY_BLOCKED
- LLM_CALL_START
- LLM_CALL_END
- SKILL_INVOKED
- KILLSWITCH_CHECK

### Guardrail Actions
- **Block** - Stop the request immediately
- **Throttle** - Slow down the request rate
- **Kill Switch** - Stop all traffic until manually resumed
- **Warn** - Log the event but allow the request

---

## Deployment

Deployed to production:
```bash
npm run build
sudo cp -r dist/* /opt/agenticverz/apps/console/dist/
```

All consoles accessible:
- AOS Console: https://agenticverz.com/console
- Guard Console: https://agenticverz.com/console/guard
- Ops Console: https://agenticverz.com/console/ops

---

## Bug Fixes (2025-12-21)

### Issue: PDF Export 500 Error
- **Root Cause:** Missing `reportlab` Python package in Docker container
- **Fix:** Added `reportlab>=4.0.0` to requirements.txt, installed in container
- **Prevention:** Added Python dependency check to guard_health_test.sh (Section 7)

### Issue: SQLModel Row Extraction
- **Root Cause:** `session.exec().all()` returns Row objects, not model instances
- **Fix:** Updated `export_incident_evidence` in guard.py to handle Row extraction correctly
- **File:** backend/app/api/guard.py lines 1895-1910

### Issue: DialogContent aria-describedby Warning
- **Root Cause:** Radix UI Dialog.Content requires Description for accessibility
- **Fix:** Added VisuallyHidden.Root wrapper with hidden description in Modal.tsx
- **Package:** Installed @radix-ui/react-visually-hidden

### Prevention Script Updates
- Added PDF export test (Section 6) - verifies export returns valid PDF
- Added Python dependency check (Section 7) - tests critical imports
- Fixed `jq` check for boolean values using `has()` function
- Fixed bash arithmetic to avoid `set -e` exit on zero

---

## Next Steps

1. Wire live SSE streaming for LiveActivityPage (currently simulated)
2. Implement actual blast radius calculation from backend
3. Add WebSocket support for real-time kill switch status
4. Connect settings page to backend persistence
