# TODO — Iteration 3.7 (Agent L2 First-Principles Refactor)

**Created:** 2026-02-07  
**Last verified:** 2026-02-07  
**Status:** COMPLETE ✅  
**Scope:** `backend/app/hoc/api/cus/general/agents.py` (M12 Multi-Agent System)

---

## Completion Summary (Evidence-Backed)

- `backend/app/hoc/api/cus/general/agents.py`: **0** `app.agents.services.*` imports (L2 compliant).
- `backend/app/hoc/api/cus/general/agents.py`: **26** `registry.execute(...)` call sites (was 3 baseline; now L2 dispatch is the dominant pattern).
- L4 wiring: `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/agent_handler.py` registers:
  - `agents.job`
  - `agents.blackboard`
  - `agents.instance`
  - `agents.message`
  - `agents.activity`
- Gates:
  - `cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci` → PASS (0 blocking, 0 known exceptions)
  - `cd backend && PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py` → PASS

---

## Reality (Evidence-Backed Baseline)

- File size: `backend/app/hoc/api/cus/general/agents.py` is **2757** LOC.
- L2 violation: it imports `app.agents.services.*` directly (6 import sites).
- Registry usage: only **3** `registry.execute(...)` call sites exist in this file today.
- Router is mounted: `backend/app/main.py` imports and includes `agents_router`.

---

## First Principles (Non-Negotiable)

- L2 must not import “service/engine” modules outside L4/L5 boundaries.
- L2 must be HTTP boundary only: translate request → operation → return response.
- All orchestration must be owned by L4 hoc_spine (registry + handlers).
- If DB is involved, DB execution must not happen in L2.

---

## Goal

Make `backend/app/hoc/api/cus/general/agents.py` a compliant L2 router:
- **0** imports of `app.agents.services.*` in L2.
- Endpoints dispatch through hoc_spine via `registry.execute(...)`.
- Any required implementation is moved behind L4 handlers (and L5/L6 if needed).

---

## Acceptance Gates (Must All Pass)

From repo root:

```bash
cd backend
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
PYTHONPATH=. pytest -q tests/hoc_spine/test_api_v1_legacy_only.py
```

Targeted scans:

```bash
rg -n \"^from app\\.agents\\.services\\b|\\bapp\\.agents\\.services\\b\" backend/app/hoc/api/cus/general/agents.py
# result: 0 matches

rg -n \"\\bregistry\\.execute\\b\" backend/app/hoc/api/cus/general/agents.py | wc -l
# result: should match the number of endpoints after conversion (expected: >> 3)
```

---

## Work Plan (Streamed Batches)

1. Inventory endpoints in `agents.py` (path, method, summary) and map each to a target operation name.
2. Create/extend hoc_spine L4 handler module(s) to own M12 operations.
3. For each endpoint, replace direct `app.agents.services.*` calls with `registry.execute(\"agents.<op>\", OperationContext(...))`.
4. Keep batches small (5-8 endpoints per batch) and run gates after every batch.

---

## Notes / Constraints

- Do **not** “paper over” with new allowlists or new “adapter boundary” exemptions.
- Do **not** move/delete files unless explicitly commanded by the user.
- Do **not** update docs except when the user explicitly commands doc updates.
