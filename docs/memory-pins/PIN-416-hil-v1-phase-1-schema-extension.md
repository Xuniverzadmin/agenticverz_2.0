# PIN-416: HIL v1 Phase 1 — Schema Extension

**Status:** COMPLETE
**Created:** 2026-01-14
**Category:** UI Pipeline / Human Interpretation Layer
**Milestone:** HIL v1 Phase 1

---

## Summary

Completed Phase 1 of the Human Interpretation Layer (HIL) v1 implementation.
This phase establishes the schema foundation for classifying panels as either
`execution` (raw data) or `interpretation` (summaries/aggregations).

---

## What Was Done

### 1. HIL v1 Contract Document

Created `design/l2_1/HIL_V1_CONTRACT.md` defining:

- **Panel Classification**: `execution` vs `interpretation`
- **Provenance Declaration**: Required for interpretation panels
- **Aggregation Types**: COUNT, SUM, TREND, STATUS_BREAKDOWN, TOP_N, LATEST
- **Domain Intent**: Core question each domain answers
- **Governance Rules**: HIL-001 through HIL-006
- **Backend Contract**: Endpoint requirements for interpretation panels

### 2. Schema Extension

Updated `backend/aurora_l2/schema/intent_spec_schema.json` (v1.0 → v1.1):

```json
{
  "panel_class": {
    "type": "string",
    "enum": ["execution", "interpretation"],
    "default": "execution"
  },
  "provenance": {
    "type": "object",
    "required": ["source_panels", "aggregation", "endpoint"],
    "properties": {
      "source_panels": { "type": "array", "items": { "type": "string" } },
      "aggregation": { "type": "string", "enum": [...] },
      "endpoint": { "type": "string", "pattern": "^/api/v1/" }
    }
  }
}
```

Added conditional validation:
- `interpretation` panels MUST have `provenance`
- `execution` panels MUST NOT have `provenance`

### 3. Domain Intent Registry

Created `design/l2_1/AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml`:

| Domain | Intent | Question |
|--------|--------|----------|
| Overview | system_health | Is the system okay right now? |
| Activity | execution_visibility | What ran / is running? |
| Incidents | failure_understanding | What went wrong? |
| Policies | behavior_governance | How is behavior defined? |
| Logs | evidence_trail | What is the raw truth? |

### 4. First Interpretation Panel Spec

Created `design/l2_1/intents/ACT-EX-SUM-O1.yaml`:

- **Panel Class**: interpretation
- **Provenance**: ACT-EX-AR-O2, ACT-EX-CR-O2
- **Aggregation**: STATUS_BREAKDOWN
- **Endpoint**: /api/v1/activity/summary
- **Status**: CANDIDATE (pending Phase 3 implementation)

### 5. AURORA_L2.md Update

Added Section 18 "Human Interpretation Layer (HIL v1)" with:
- Panel classification table
- Provenance example
- Key invariants
- Execution plan status

---

## Files Created/Modified

| File | Action |
|------|--------|
| `design/l2_1/HIL_V1_CONTRACT.md` | Created |
| `design/l2_1/AURORA_L2_DOMAIN_INTENT_REGISTRY.yaml` | Created |
| `design/l2_1/intents/ACT-EX-SUM-O1.yaml` | Created |
| `backend/aurora_l2/schema/intent_spec_schema.json` | Modified (v1.0 → v1.1) |
| `design/l2_1/AURORA_L2.md` | Modified (added Section 18) |

---

## Key Decisions

1. **Default panel_class is `execution`**: All 54 existing migrated panels remain execution panels unless explicitly reclassified.

2. **Provenance is mandatory for interpretation**: No interpretation panel can exist without explicit source panel references.

3. **Backend-owned aggregation**: Frontend is forbidden from computing summaries. All aggregations come from dedicated backend endpoints.

4. **Activity domain first**: The first interpretation panel (ACT-EX-SUM-O1) will be in the Activity domain as a pilot.

---

## HIL v1 Execution Plan

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ COMPLETE | Schema extension (documentation) |
| Phase 2 | ⏳ PENDING | Runtime support (compiler + frontend) |
| Phase 3 | ⏳ PENDING | First implementation (Activity domain) |
| Phase 4 | ⏳ PENDING | Expand to other domains |

---

## Next Steps (Phase 2)

1. Update `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` to propagate `panel_class` to projection
2. Update frontend projection loader to read `panel_class`
3. Add visual grouping/styling for interpretation panels
4. Add provenance badge component

---

## Related PINs

- PIN-370 — SDSR System Contract
- PIN-379 — E2E Pipeline
- PIN-352 — L2.1 UI Projection Pipeline (SUPERSEDED)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-14 | Phase 1 complete — schema extension and documentation |
