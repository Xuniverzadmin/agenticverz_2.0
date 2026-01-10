# SDSR Observations Directory

**Status:** ACTIVE
**Authority:** System Only

---

## Purpose

This directory contains SDSR observation artifacts that advance AURORA_L2 capability state.

**Only SDSR may write files here.**
**Only the observation applier may read and process files here.**

---

## File Naming Convention

```
SDSR_OBSERVATION_<SCENARIO_ID>.json
```

Example: `SDSR_OBSERVATION_E2E_004.json`

---

## What Goes Here

1. **Observation files** emitted by SDSR on successful scenario execution
2. Each observation documents:
   - Which capabilities were exercised
   - What state transitions were observed
   - Evidence of real behavior

---

## Who May Write Here

| Actor | Allowed |
|-------|---------|
| SDSR runner | YES |
| Backend team | NO |
| UI | NO |
| Claude | NO (unless running SDSR) |
| Manual editing | FORBIDDEN |

---

## Processing Flow

```
1. SDSR scenario passes
2. SDSR emits SDSR_OBSERVATION_<scenario_id>.json here
3. System runs: python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py --observation <file>
4. Capability status advances: DECLARED → OBSERVED
5. Pipeline recompiles: ./scripts/tools/run_aurora_l2_pipeline.sh
6. UI button enables
```

---

## Schema

See: `../SDSR_OBSERVATION_SCHEMA.json`

---

## Core Invariant

> Capabilities are not real because backend says so.
> They are real only when the system demonstrates them.

This directory is where that demonstration gets recorded.
