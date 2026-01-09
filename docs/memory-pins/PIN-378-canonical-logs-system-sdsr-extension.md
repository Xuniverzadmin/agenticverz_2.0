# PIN-378: Canonical Logs System - SDSR Extension

**Status:** COMPLETE
**Created:** 2026-01-09
**Category:** Logs / SDSR Integration
**Milestone:** SDSR v1 Freeze

---

## Summary

Implemented SDSR extension for the Canonical Logs System. Extended `aos_traces` and `aos_trace_steps` tables with synthetic data columns and incident correlation. Updated `pg_store.py` to support SDSR inheritance.

---

## Details

### Problem Statement

The Logs domain needed SDSR integration per PIN-370. Logs are execution evidence (truth-grade), not events. The canonical foundation already exists in `aos_traces` + `aos_trace_steps` tables, but they lacked:
- SDSR marking (is_synthetic, synthetic_scenario_id)
- Incident cross-domain correlation (incident_id)
- Log-level semantics for UI rendering (source, level)

### Solution: Canonical Extension

Per ARCH-CANON-001 (Canonical-First Fix), we extended the existing tables rather than creating new ones.

### Migration 078

**aos_traces extensions:**
- `incident_id` (VARCHAR 100) - Cross-domain correlation to incidents
- `is_synthetic` (BOOLEAN, default false) - SDSR marker inherited from run
- `synthetic_scenario_id` (VARCHAR 64) - Scenario ID for traceability

**aos_trace_steps extensions:**
- `source` (VARCHAR 50, default 'engine') - Origin: engine, external, replay
- `level` (VARCHAR 16, default 'INFO') - Log level derived from status

### Level Derivation

Level is derived from step status per these rules:
| Status | Level |
|--------|-------|
| success | INFO |
| skipped | INFO |
| retry | WARN |
| failure | ERROR |

### SDSR Inheritance Rule

```
run.is_synthetic → aos_traces.is_synthetic
aos_trace_steps inherit via trace_id (no separate SDSR columns)
```

### Key Principle

> inject_synthetic.py MUST NOT write to aos_traces/aos_trace_steps.
> Traces appear naturally when runs execute. Synthetic marking is inherited.

### Files Modified

| File | Change |
|------|--------|
| `backend/alembic/versions/078_aos_traces_sdsr_columns.py` | New migration |
| `backend/app/traces/pg_store.py` | Added SDSR parameters to start_trace, record_step, store_trace |
| `website/app-shell/src/api/traces.ts` | Extended with SDSR types and filtering |
| `website/app-shell/src/components/panels/PanelContentRegistry.tsx` | Added Logs domain panels (LOG-ET-TD-O1/O2/O3) |

### Database Columns Added

**aos_traces:**
- incident_id
- is_synthetic (with partial index)
- synthetic_scenario_id

**aos_trace_steps:**
- source
- level (with indexes for log queries)

### Indexes Created

- `idx_aos_traces_synthetic_scenario` (partial, is_synthetic=true)
- `idx_aos_traces_incident` (partial, incident_id IS NOT NULL)
- `idx_aos_trace_steps_level`
- `idx_aos_trace_steps_trace_level` (composite)

### API Compatibility

The `pg_store.py` methods accept optional SDSR parameters with defaults:
- Existing callers continue working unchanged
- New callers can pass is_synthetic, synthetic_scenario_id, incident_id
- Level is auto-derived from status

### Cross-Domain Correlation

```
run → aos_traces (via run_id) → incidents (via incident_id) → prevention_records
      ^-- is_synthetic inherited    ^-- correlation enabled
```

### UI Implementation (COMPLETE)

The Logs UI is now implemented via the L2.1 projection pipeline:

**API Layer (`website/app-shell/src/api/traces.ts`):**
- Extended with SDSR types: `LogLevel`, `StepSource`
- Extended `Trace` interface: `is_synthetic`, `synthetic_scenario_id`, `incident_id`
- Extended `TraceStep` interface: `source`, `level`
- Added `TraceQueryParams` for SDSR filtering
- Added `getTracesSummary()` and `getTracesByIncident()` functions

**Panel Renderers (`website/app-shell/src/components/panels/PanelContentRegistry.tsx`):**

| Panel ID | Component | Description |
|----------|-----------|-------------|
| LOG-ET-TD-O1 | TraceSummary | Total traces, status breakdown, SDSR count |
| LOG-ET-TD-O2 | TraceList | List view with SDSR badges, incident links |
| LOG-ET-TD-O3 | TraceDetail | Trace header + step timeline with level/source |

**Helper Components:**
- `TraceListItem` - Reusable trace row with status, SDSR badge, incident link
- `TraceStatusBadge` - Status indicator (completed/running/failed/pending)
- `StepTimelineItem` - Step row with level badge, source, skill name, duration

**SDSR Features in UI:**
- Purple SDSR badge when `is_synthetic=true`
- Orange incident link when `incident_id` is present
- Level colors: INFO (slate), WARN (yellow), ERROR (red)
- Source colors: engine (blue), external (cyan), replay (purple)
- Retry indicator when `retry_count > 0`

---

## Verification

```bash
# Migration applied successfully
set -a && source .env && set +a && alembic upgrade head

# Columns verified
SELECT column_name FROM information_schema.columns
WHERE table_name = 'aos_traces' AND column_name IN ('incident_id', 'is_synthetic', 'synthetic_scenario_id');
-- Returns: incident_id, is_synthetic, synthetic_scenario_id

SELECT column_name FROM information_schema.columns
WHERE table_name = 'aos_trace_steps' AND column_name IN ('source', 'level');
-- Returns: source, level
```

---

## Related PINs

- [PIN-370](PIN-370-sdsr-scenario-driven-system-realization.md) - SDSR Foundation
- [PIN-377](PIN-377-auth-architecture-issuer-based-routing-implementation.md) - Auth Architecture
- [PIN-373](PIN-373-sdsr-policy-domain-integration.md) - Policy SDSR Integration

---

## Next Steps

1. Update trace emission points (workflow engine, runner) to pass run.is_synthetic
2. ~~Implement Logs UI panel that queries aos_traces/aos_trace_steps~~ (DONE)
3. ~~Wire LogsPanel to PanelContentRegistry~~ (DONE)
4. Logs → Incidents deep linking (click incident link to navigate)
5. Console naming layer (DB view or API naming doc)

---

## Commits

- Migration 078: aos_traces SDSR columns
- pg_store.py: SDSR parameter support
- traces.ts: SDSR types and filtering API
- PanelContentRegistry.tsx: Logs domain panels (LOG-ET-TD-O1/O2/O3)
