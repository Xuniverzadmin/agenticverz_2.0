# HANDOVER_UC_MON_DETERMINISM_EXECUTION.md

## Objective
Close the remaining UC-MON determinism gap by wiring `as_of` contract into priority read APIs, then promote validators from advisory to strict readiness.

## Current State
1. UC-MON verifiers have `0 FAIL`.
2. Deterministic read verifier reports `5 WARN` (missing `as_of` wiring on priority endpoints).
3. Strict mode currently exits non-zero due to WARNs (expected).

## Scope (This Handover)
1. `activity` read APIs
2. `incidents` read APIs
3. `analytics` read APIs (priority: feedback/predictions first)
4. `logs/traces` read APIs

## Canonical Inputs
1. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_USECASE_PLAN.md`
2. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_IMPLEMENTATION_METHODS.md`
3. `backend/scripts/verification/uc_mon_deterministic_read_check.py`
4. `backend/scripts/verification/uc_mon_validation.py`

## Step-by-Step Execution

### Step 1: Add `as_of` request contract to L2 endpoints
Target files:
1. `backend/app/hoc/api/cus/activity/activity.py`
2. `backend/app/hoc/api/cus/incidents/incidents.py`
3. `backend/app/hoc/api/cus/analytics/feedback.py`
4. `backend/app/hoc/api/cus/analytics/predictions.py`
5. `backend/app/hoc/api/cus/logs/traces.py`

Required change pattern:
1. Add optional query param: `as_of: Optional[str] = Query(None, ...)`
2. Parse once per request:
- if provided: validate ISO-8601 UTC
- if absent: create one server timestamp and use consistently in that request
3. Pass normalized `as_of` into L4 operation params/context.

Acceptance:
1. No endpoint uses moving `now()` multiple times for deterministic filtering in one request.
2. Endpoint preserves backward compatibility (param optional).

### Step 2: Return `as_of` in response metadata
Required response behavior:
1. Include `as_of` in response envelope or metadata block.
2. For derived outputs, include version marker when available:
- `data_version` / `dataset_version` / equivalent.

Acceptance:
1. Same filters + same `as_of` returns stable ordering and values.
2. Response always exposes effective `as_of`.

### Step 3: TTL/expiry evaluation must use `as_of`
Where applicable (activity feedback / override expiry reads):
1. Replace wall-clock evaluation with request `as_of`.
2. Keep behavior deterministic for repeated queries at same `as_of`.

Acceptance:
1. Expired/non-expired state is reproducible for same `as_of`.

### Step 4: Update deterministic verifier checks
File:
1. `backend/scripts/verification/uc_mon_deterministic_read_check.py`

Required updates:
1. Keep token checks, add stronger assertions where possible (function signatures, response metadata keys).
2. Report explicit endpoint-level results with PASS/WARN/FAIL.

Acceptance:
1. `as_of` checks move from WARN to PASS for targeted endpoints.

### Step 5: Run validation suite
Commands:
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 scripts/verification/uc_mon_deterministic_read_check.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py
PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict
```

Acceptance:
1. Deterministic-read verifier: `0 WARN`, `0 FAIL` for targeted endpoints.
2. UC-MON validator normal mode: `0 FAIL`.
3. UC-MON validator strict mode: exit `0`.

## Required Implementation Evidence Document
Create:
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_UC_MON_DETERMINISM_EXECUTION_implemented.md`

Must include:
1. File-by-file diff summary.
2. Endpoint-by-endpoint `as_of` wiring matrix.
3. Validator outputs before/after.
4. Remaining blockers (if any).
5. Recommendation:
- stay advisory
- or promote strict-ready.

## Guardrails
1. Do not remove existing response fields; additive changes only.
2. Keep tenant/project scoping untouched.
3. Do not mark UC-MON GREEN in this step; this is determinism closure only.
4. If strict mode still fails, document exact failing checks and stop status promotion.
