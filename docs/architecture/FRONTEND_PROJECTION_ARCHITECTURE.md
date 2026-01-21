# Frontend Projection Architecture — V2 Constitution

**Status:** ACTIVE
**Created:** 2026-01-20
**Reference:** `CUSTOMER_CONSOLE_V2_CONSTITUTION.md`, `FRONTEND_L1_BUILD_PLAN.md`

---

## Executive Summary

The frontend UI projection is now governed by the **V2 Constitution**, decoupled from the legacy AURORA L2 pipeline. This document describes the authoritative source, protection mechanisms, and file relationships.

**Key Decision:** V2 Constitution is the single source of truth for UI navigation structure.

---

## 1. Authority Stack

| Priority | Source | Role |
|----------|--------|------|
| 1 | `design/v2_constitution/ui_projection_lock.json` | **Authoritative source** |
| 2 | `website/app-shell/src/contracts/ui_plan_scaffolding.ts` | TypeScript fallback data |
| 3 | `website/app-shell/public/projection/ui_projection_lock.json` | Runtime projection (copied from #1) |

**Rule:** If any lower source contradicts the authoritative source, the lower source is wrong.

---

## 2. V2 Constitution Structure

The V2 Constitution defines an 8-domain hierarchy:

```
Domain → Subdomain → Topic → Panel
```

### 2.1 Domains (Frozen)

| Order | Domain | Route | Description |
|-------|--------|-------|-------------|
| 0 | Overview | `/overview` | System health at a glance |
| 1 | Activity | `/activity` | Agent runs and executions |
| 2 | Incidents | `/incidents` | Policy violations and failures |
| 3 | Policies | `/policies` | Rules and constraints |
| 4 | Logs | `/logs` | Audit trail and raw records |
| 5 | Analytics | `/analytics` | Usage and cost insights |
| 6 | Connectivity | `/connectivity` | Integrations and API access |
| 7 | Account | `/account` | Account settings and billing |

### 2.2 Subdomain/Topic Structure

| Domain | Subdomains | Topics |
|--------|------------|--------|
| Overview | summary | highlights, decisions |
| Activity | llm_runs | live, completed, signals |
| Incidents | events | active, resolved, historical |
| Policies | governance, limits | active/lessons/policy_library, controls/violations |
| Logs | records | llm_runs, system_logs, audit_logs |
| Analytics | insights, usage_statistics | cost_intelligence, policies_usage/productivity |
| Connectivity | integrations, api | sdk_integration, api_keys |
| Account | profile, billing, team, settings | overview, subscription/invoices, members, account_management |

---

## 3. File Locations and Roles

### 3.1 Authoritative Source (V2 Constitution)

```
design/v2_constitution/ui_projection_lock.json
```

- **Role:** Single source of truth for UI projection
- **Editable:** Yes (manually maintained)
- **Generator:** MANUAL (not auto-generated)
- **Source field:** `"source": "V2 Constitution Manual Sync"`

### 3.2 TypeScript Scaffolding

```
website/app-shell/src/contracts/ui_plan_scaffolding.ts
```

- **Role:** Fallback data when projection panels are empty
- **Sync requirement:** Must match V2 Constitution structure
- **Contains:** Domain/subdomain/topic definitions with questions and descriptions

### 3.3 Runtime Projection

```
website/app-shell/public/projection/ui_projection_lock.json
```

- **Role:** File consumed by frontend at runtime
- **Source:** Copied from V2 Constitution during build
- **Editable:** No (overwritten during build)

### 3.4 Legacy AURORA Location (Deprecated)

```
design/l2_1/ui_contract/ui_projection_lock.json
```

- **Role:** Legacy AURORA output location
- **Status:** Synced with V2 Constitution to prevent build errors
- **Future:** Will be removed once all references are cleaned up

---

## 4. Protection Mechanisms

### 4.1 AURORA Pipeline Deprecation Guard

**File:** `scripts/tools/run_aurora_l2_pipeline.sh`

The AURORA L2 pipeline is deprecated and blocked by default:

```bash
# Lines 35-69: Deprecation guard
if [ "$ALLOW_AURORA_OVERRIDE" != "1" ]; then
    echo "ABORTED: AURORA pipeline is deprecated."
    exit 0
fi
```

**Override:** Only for debugging with `ALLOW_AURORA_OVERRIDE=1`

### 4.2 Build Script Source

**File:** `scripts/ops/build_preflight_console.sh`

Step 4 explicitly copies from V2 Constitution:

```bash
# Lines 95-100
cp "$REPO_ROOT/design/v2_constitution/ui_projection_lock.json" \
   "$APP_SHELL/public/projection/"
```

### 4.3 Validation Script Source

**File:** `website/app-shell/scripts/projection-stage-check.cjs`

Design file validation points to V2 Constitution:

```javascript
// Lines 29-32
const DESIGN_FILE = path.join(__dirname, '..', '..', '..',
    'design', 'v2_constitution', 'ui_projection_lock.json');
```

---

## 5. Build Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  AUTHORITATIVE SOURCE                                        │
│  design/v2_constitution/ui_projection_lock.json              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  BUILD: build_preflight_console.sh                           │
│  Step 4: Copy to public/projection/                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  VALIDATION: projection-stage-check.cjs                      │
│  Validates stage and design sync                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  RUNTIME: public/projection/ui_projection_lock.json          │
│  Consumed by ui_projection_loader.ts                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  FALLBACK: ui_plan_scaffolding.ts                            │
│  Used when projection panels are empty                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Modification Procedures

### 6.1 To Update Domain/Subdomain/Topic Structure

1. Edit `design/v2_constitution/ui_projection_lock.json`
2. Update `website/app-shell/src/contracts/ui_plan_scaffolding.ts` to match
3. Run build: `./scripts/ops/build_preflight_console.sh`
4. Verify: Check `public/projection/` has updated content

### 6.2 To Add a New Panel

1. Add panel to domain in `design/v2_constitution/ui_projection_lock.json`
2. Register panel in `src/components/panels/PanelContentRegistry.tsx`
3. Create panel component
4. Rebuild and verify

### 6.3 To Sync Legacy Location (if needed)

```bash
cp design/v2_constitution/ui_projection_lock.json \
   design/l2_1/ui_contract/ui_projection_lock.json
```

---

## 7. Validation Commands

### 7.1 Stage Check (Pre-build)

```bash
node website/app-shell/scripts/projection-stage-check.cjs
```

Validates:
- Projection file exists
- Stage is valid (LOCKED, PHASE_2A1_APPLIED, PHASE_2A2_SIMULATED)
- Public and design files are in sync

### 7.2 Projection Sync (npm script)

```bash
cd website/app-shell && npm run projection:sync
```

Copies V2 Constitution to public/projection/.

---

## 8. Troubleshooting

### 8.1 "PROJECTION_ASSERTION_FAILED: Invalid domain name"

**Cause:** Projection file has wrong domain names (e.g., uppercase OVERVIEW instead of Overview)

**Fix:** Verify V2 Constitution file has correct casing and rebuild.

### 8.2 "Design sync error during build"

**Cause:** public/projection/ differs from design source

**Fix:** Run `npm run projection:sync` or rebuild with `build_preflight_console.sh`

### 8.3 Old subdomains appearing in sidebar

**Cause:** `ui_plan_scaffolding.ts` has stale data

**Fix:** Update scaffolding to match V2 Constitution structure.

---

## 9. Historical Context

### 9.1 Why Decouple from AURORA?

The AURORA L2 pipeline was designed to compile intents and capabilities into UI projection. However:

1. **Complexity:** Multi-stage pipeline with Phase A validation, capability binding, etc.
2. **Fragility:** Pipeline failures could overwrite correct structure with stale data
3. **Mismatch:** AURORA output structure didn't match V2 Constitution requirements

### 9.2 Decoupling Date

**2026-01-20:** V2 Constitution established as authoritative source. AURORA pipeline deprecated.

### 9.3 Root Cause of Previous Issues

The `ui_plan_scaffolding.ts` file contained old subdomain names (SYSTEM_HEALTH, EXECUTIONS, etc.) that were displayed when projection panels were empty. This was identified as the root cause of "legacy subdomains reappearing" after builds.

---

## 10. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| V2 Constitution | `docs/contracts/CUSTOMER_CONSOLE_V2_CONSTITUTION.md` | Domain/subdomain definitions |
| Frontend Build Plan | `docs/architecture/FRONTEND_L1_BUILD_PLAN.md` | Build strategy and routing |
| Projection Loader | `src/contracts/ui_projection_loader.ts` | Runtime projection loading |
| Scaffolding | `src/contracts/ui_plan_scaffolding.ts` | Fallback data definitions |
| AURORA Pipeline (deprecated) | `scripts/tools/run_aurora_l2_pipeline.sh` | Legacy pipeline (blocked) |

---

## 11. Key Invariants

1. **V2 Constitution is truth:** All projection data derives from V2 Constitution
2. **No AURORA regeneration:** Pipeline is blocked unless explicitly overridden
3. **Scaffolding must match:** TypeScript fallback must mirror V2 Constitution
4. **Build copies, not generates:** Projection is copied, not compiled
5. **Validation enforces sync:** Stage check ensures design/public alignment
