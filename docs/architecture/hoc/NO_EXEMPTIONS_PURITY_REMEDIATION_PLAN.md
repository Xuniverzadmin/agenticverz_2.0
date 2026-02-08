# No-Exemptions Purity Remediation Plan (HOC L5/L6)

**Status:** ACTIVE (Codex-owned)  
**Created:** 2026-02-07  
**Scope:** `backend/app/hoc/cus/**` + purity auditors in `backend/scripts/ops/`  
**Binding References:**
- `docs/architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md` (RATIFIED)
- `docs/architecture/architecture_core/LAYER_MODEL.md` (LOCKED)
- `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md` (LOCKED)

## Governance

- **No hidden exemptions.** Purity tools must scan everything in scope.
- **No “skip lists” to make audits green.** If something cannot be made pure immediately, it must remain visible as a violation until fixed.
- **Plan ownership:** Only **Codex** updates this plan (status, sequencing, completion). Claude must not edit this file.
- **Change discipline:** No file moves/deletes unless explicitly approved by the user.

## Architecture Target (Uniform Pattern)

Execution path stays linear:

`L2.1 → L2 → L4 hoc_spine → L5 engine → L6 driver → L7 models`

Uniform purity invariants:

- **L5 (engines/schemas/support)**
  - MUST NOT import `app.models.*` at runtime (TYPE_CHECKING allowed).
  - MUST NOT import `app.db` at runtime.
  - MUST NOT import DB client libs at runtime (`asyncpg`, `psycopg2`, `sqlalchemy`, `sqlmodel`).
  - MUST NOT open connections or control transactions (`connect/commit/rollback`).
  - MUST receive session/driver from L4; MUST NOT reach up into `hoc_spine.orchestrator.*`.

- **L6 (drivers)**
  - MUST NOT commit/rollback (transaction boundary is L4).
  - MUST accept primitives/DTOs and perform DB I/O only.

## Starting Point (Reality Snapshot)

Current purity auditor: `backend/scripts/ops/hoc_l5_l6_purity_audit.py`

It currently contains exemption mechanisms:

- `L5_EXEMPT_FILES` (skips entire files)
- `L5_LAZY_MODELS_EXEMPT` (downgrades lazy `app.models` imports)
- L6 bridge commit is downgraded to advisory

This plan removes the need for *any* exemptions by fixing design.

## Phase Plan (Do Not Reorder Without Codex Update)

### Phase 0 — Purity Tool Becomes a Truth Instrument

**Status:** PENDING  
**Goal:** The purity audit must be mechanically trustworthy without skip lists.

Work:
- Remove `L5_EXEMPT_FILES` and `L5_LAZY_MODELS_EXEMPT` from `backend/scripts/ops/hoc_l5_l6_purity_audit.py`.
- Improve commit/rollback detection to avoid false positives:
  - Flag only when receiver name looks DB-ish (`session/conn/tx/db/engine`), not `self.rollback()`.
- Keep scope expansion:
  - Scan `L5_engines/`, `L5_schemas/`, and recursive `L5_support/`.

Acceptance:
- `python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --json --advisory` shows real violations (no hidden skips).
- No new false positives for known domain methods (e.g. loop-events rollback).

### Phase 1 — Integrations: External SQL Gateway Moves Effects to L6

**Status:** PENDING  
**Goal:** `asyncpg.connect()` and network DB effects move out of L5.

Work:
- Introduce `backend/app/hoc/cus/integrations/L5_schemas/sql_gateway_protocol.py` (Protocol + DTOs for query inputs/outputs).
- Add `backend/app/hoc/cus/integrations/L6_drivers/sql_gateway_driver.py`:
  - Owns `asyncpg` import and connection lifecycle.
  - Executes parameterized templates provided by L5.
- Update `backend/app/hoc/cus/integrations/L5_engines/sql_gateway.py`:
  - Keep template selection + parameter validation in L5.
  - Delegate all I/O to the L6 driver.

Acceptance:
- Purity audit reports **no L5 DB client imports** for integrations.

### Phase 2 — Analytics: Cost Anomaly Detector Stops Importing app.db / ORM

**Status:** PENDING  
**Goal:** L5 uses DTOs; L6 maps to ORM.

Work:
- Create `backend/app/hoc/cus/analytics/L5_schemas/cost_anomaly_dtos.py`:
  - `DetectedAnomaly` persistence DTO(s) and any enums needed by L5.
- Update `backend/app/hoc/cus/analytics/L6_drivers/cost_anomaly_*` drivers to accept DTOs and construct/update ORM.
- Update `backend/app/hoc/cus/analytics/L5_engines/cost_anomaly_detector_engine.py`:
  - Replace `from app.db import CostAnomaly, utc_now` with:
    - `from app.hoc.cus.hoc_spine.services.time import utc_now`
    - DTO construction only (no ORM class usage).

Acceptance:
- Purity audit reports **no** `app.db` runtime imports in analytics L5.
- Purity audit reports **no** ORM instantiation in analytics L5 (heuristic).

### Phase 3 — Logs: Audit Ledger ORM Construction Moves to L6

**Status:** PENDING  
**Goal:** L5 emits audit intent; L6 constructs ORM rows.

Work:
- Add a sync L6 writer for sqlmodel `Session`:
  - `backend/app/hoc/cus/logs/L6_drivers/audit_ledger_write_driver_sync.py`
- Update `backend/app/hoc/cus/logs/L5_engines/audit_ledger_engine.py`:
  - Remove lazy `from app.models.audit_ledger import AuditLedger`.
  - Call sync L6 writer to create rows.
- Fix runtime wiring bug:
  - `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py` currently imports `audit_ledger_service` (non-existent); it must import the correct module or driver.

Acceptance:
- Purity audit reports **0** `app.models` imports in logs L5 at runtime.
- Incidents write handler executes without import error.

### Phase 4 — Policies: Eliminate L6 Standalone Commits (_write_conn)

**Status:** PENDING  
**Goal:** L4 owns commit boundary; L6 never commits.

Work:
- Refactor `backend/app/hoc/cus/policies/L6_drivers/policy_engine_driver.py`:
  - Remove `conn.commit()` from `_write_conn()`.
  - Require writes to run under `managed_connection()` (or accept an explicit conn from L4).
- Update L4 callers to ensure managed contexts are used for all policy writes:
  - Start from `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py` which already has a managed write context but is currently unused.

Acceptance:
- Purity audit reports **0** L6 commits/rollbacks across all domains.
- No write path silently auto-commits outside L4.

## Verification (Run After Each Phase)

- `python3 backend/scripts/ci/check_init_hygiene.py --ci`
- `python3 backend/scripts/ci/check_layer_boundaries.py --ci`
- `python3 backend/scripts/ops/hoc_cross_domain_validator.py`
- `pytest -q backend/tests/hoc_spine/test_hoc_spine_import_guard.py`
- `python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --json --advisory`

## Known Difficulties / Risk

- Policies: the singleton + connection-based PolicyEngine pattern means removing `_write_conn()` commits can require many callsite rewires.
- Logs: there are both sync and async session paths; uniform design requires a clear driver boundary for each.
- Integrations SQL Gateway: “external DB connector” is functionally an effectful adapter; it must live in L6 even if it targets non-internal DBs.
