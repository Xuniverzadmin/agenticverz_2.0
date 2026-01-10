# AURORA_L2 Frontend (Projection Builder)

**Status:** SCAFFOLD (empty placeholder)

## Purpose

This directory will contain the frontend projection builder for AURORA_L2.

## Architecture Change

In AURORA_L2, the projection builder **moves from backend to frontend**:

| Legacy | AURORA_L2 |
|--------|-----------|
| `scripts/tools/ui_projection_builder.py` | `frontend/aurora_l2/projection_builder.ts` |
| Python script, runs offline | TypeScript, runs at build time or runtime |
| Outputs `ui_projection_lock.json` | Outputs projection directly for React |

## Files (to be created)

| File | Purpose |
|------|---------|
| `projection_builder.ts` | Compiles intent store → UI projection |
| `projection_types.ts` | TypeScript types for projection schema |
| `intent_loader.ts` | Loads compiled intents from SQL/API |

## Data Flow

```
SQL Intent Store (backend)
        ↓
    API fetch
        ↓
projection_builder.ts
        ↓
React Context / State
        ↓
PanelContentRegistry.tsx (existing, unchanged)
```

## Migration Notes

The existing `ui_projection_lock.json` pattern remains valid during migration.
Frontend projection builder will produce compatible output.
