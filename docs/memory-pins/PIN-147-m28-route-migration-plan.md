# PIN-147: M28 Route Migration Plan — Authoritative

**Status:** EXECUTING
**Date:** 2025-12-23
**Milestone:** M28 Unified Console

---

## Summary

This PIN documents the **irreversible migration** from the current mixed-route architecture to two domain-isolated consoles:

- `console.agenticverz.com` → Customer Product
- `fops.agenticverz.com` → Founder Ops Cockpit

---

## The Invariant

> **Routes define power. Power defines trust. Trust defines your company.**

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 0 | Hard Preconditions | ✅ COMPLETE |
| Phase 1 | Domain & App Shell Setup | 🔄 IN PROGRESS |
| Phase 2 | DELETE FIRST | ✅ COMPLETE (PIN-145) |
| Phase 3 | Founder Ops Migration | 🔄 IN PROGRESS |
| Phase 4 | Customer Console Migration | 🔄 IN PROGRESS |
| Phase 5 | Redirect Strategy | ⏳ PENDING |
| Phase 6 | Verification & Kill Switch | ⏳ PENDING |
| Phase 7 | Cleanup | ⏳ PENDING (30 days) |

---

## Phase 0 — Hard Preconditions

### 0.1 Policy & Loop Freeze ✅

Confirmed via M25:
- No UI writes to policy tables
- No UI writes to loop state
- Evidence artifacts append-only

### 0.2 Route Ownership Lockfile ✅

Created: `/docs/M28_ROUTE_OWNERSHIP.md`

Format:
```
/path → CUSTOMER | FOUNDER | DELETE
```

This file is reviewed before every PR touching routing.

---

## Phase 1 — Domain & App Shell Setup

### 1.1 App Shell Structure

Current implementation uses single domain with path-based routing:

```
agenticverz.com/
├── /guard/*     → Customer Console (GuardConsoleEntry)
├── /ops/*       → Founder Console (OpsConsoleEntry)
└── /*           → Redirects to /guard
```

**Migration Target:**
```
console.agenticverz.com/
├── /home        → Customer Home (status board)
├── /guard/*     → Incident management
├── /keys        → API key management
├── /billing     → Credits & billing
└── /settings    → Console settings

fops.agenticverz.com/
├── /pulse       → Founder Pulse (10-second view)
├── /customers/* → Customer management
├── /traces/*    → Execution traces
├── /governance/* → SBA, policies
└── /infra/*     → Infrastructure status
```

### 1.2 DNS & TLS

Domains to provision:
- `console.agenticverz.com` (Customer)
- `fops.agenticverz.com` (Founder)

Current state: Using path-based routing on `agenticverz.com`

---

## Phase 2 — DELETE FIRST ✅

Completed in PIN-145:

### Backend Deletions
- `guard.py`: Removed `/guard/demo/seed-incident`, `/guard/validate/content-accuracy`
- `v1_killswitch.py`: Removed `/v1/demo/simulate-incident`
- `failures.py`: Archived to `.m28_deleted`
- `operator.py`: Archived to `.m28_deleted`

### Frontend Deletions
- 7 page directories archived to `.m28_deleted`
- Legacy redirects removed
- Routes cleaned in `index.tsx`

### Validation ✅
```bash
# Forbidden words eliminated from active routes:
# demo, simulation, jobs, metrics, operator, skills, failures, dashboard
```

---

## Phase 3 — Founder Ops Migration

### 3.1 Route Mapping

| Current | New (fops.agenticverz.com) |
|---------|---------------------------|
| `/ops/pulse` | `/pulse` |
| `/ops/customers` | `/customers` |
| `/ops/customers/{id}` | `/customers/{id}` |
| `/ops/customers/at-risk` | `/customers/at-risk` |
| `/ops/incidents/patterns` | `/incidents/patterns` |
| `/ops/infra` | `/infra` |
| `/traces` | `/traces` |
| `/traces/{runId}` | `/traces/{runId}` |
| `/recovery` | `/recovery` |
| `/integration/*` | `/integration/*` |
| `/sba` | `/governance/sba` |
| `/workers/*` | `/workers/*` |

### 3.2 Implementation Status

Current implementation in `OpsConsoleEntry.tsx`:
- Pulse tab → `FounderPulsePage.tsx`
- Console tab → `FounderOpsConsole.tsx`

Access rules:
- Founder routes unreachable via customer auth (enforced at API level)
- Separate session handling

---

## Phase 4 — Customer Console Migration

### 4.1 Route Mapping

| Current | New (console.agenticverz.com) |
|---------|------------------------------|
| `/guard` (home) | `/home` |
| `/guard/status` | `/home` |
| `/guard/incidents` | `/guard/incidents` |
| `/guard/incidents/{id}` | `/guard/incidents/{id}` |
| `/guard/replay/{call_id}` | `/guard/replay/{call_id}` |
| `/guard/killswitch/*` | `/guard/killswitch/*` |
| `/guard/keys` | `/keys` |
| `/credits` | `/billing` |

### 4.2 Implementation Status

Current implementation in `GuardConsoleEntry.tsx`:
- Home tab → `CustomerHomePage.tsx` (status board)
- Overview tab → `GuardDashboard.tsx`
- Incidents tab → `IncidentsPage.tsx`
- Kill Switch tab → `KillSwitchPage.tsx`
- Settings tab → `GuardSettingsPage.tsx`

### 4.3 Cost Surfaces (Derived Only)

| Data Source | Customer Route |
|-------------|----------------|
| Daily snapshots | `/costs/summary` |
| Today spend | `/home` (card) |
| Projections | `/costs/projection` |

Raw baselines never exposed to customers.

---

## Phase 5 — Redirect Strategy

### Allowed Redirects (max 30 days)

| Old | New |
|-----|-----|
| `/guard/*` | `console.agenticverz.com/guard/*` |
| `/ops/*` | `fops.agenticverz.com/*` |

### NOT Allowed

| Route | Status |
|-------|--------|
| `/dashboard` | 410 Gone |
| `/operator/*` | 410 Gone |
| `/jobs/*` | 410 Gone |
| `/skills` | 410 Gone |
| `/failures` | 410 Gone |

After 30 days → All old routes return **410 Gone**

---

## Phase 6 — Verification Checklist

- [x] No route exists without persona owner
- [x] Deleted routes return 404 (in current impl)
- [ ] No shared cookies between domains (pending domain split)
- [ ] Founder pages unreachable via customer auth (API-level)
- [ ] Customer pages show only derived data

### Kill Switch

If migration breaks production:
1. DNS flip back to old domain
2. Founder console stays dark
3. Customer traffic continues

---

## Phase 7 — Cleanup (After 30 Days)

- [ ] Remove redirects
- [ ] Remove legacy auth logic
- [ ] Remove unused API handlers
- [ ] Remove old navigation code paths
- [ ] Delete `.m28_deleted` archives

---

## Related Documents

- `docs/M28_ROUTE_OWNERSHIP.md` - Route lockfile
- PIN-145: M28 Deletion Execution Report
- PIN-146: M28 Unified Console UI
- PIN-132: M28 Unified Console Blueprint

---

## Next Steps

1. **Immediate:** Update frontend routes to match new structure
2. **DNS:** Provision `console.*` and `fops.*` subdomains
3. **Auth:** Implement domain-isolated auth middleware
4. **Deploy:** Blue-green deployment with kill switch

---

## Conclusion

> Routes define power. Power defines trust. Trust defines your company.

This migration enforces that invariant.
