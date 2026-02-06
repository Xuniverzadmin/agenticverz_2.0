# HOC Phase Plan — Granular TODOs + Acceptance Criteria

**Scope:** Streamline execution to **L2 → L4 → L5 → L6 → L7**, with L4 as orchestrator/authority/governance/consequences. Deprecate legacy `backend/app/services` wiring in `backend/app/main.py` and initiate HOC entrypoint under `backend/app/hoc/*`.

**Assumptions (per request):**
- L2.1 facades are out of scope for now.
- `backend/app/main.py` must be severed from HOC and legacy service wiring.
- HOC must be initialized through a dedicated HOC entrypoint (`backend/app/hoc/.../main.py`).

---

## Phase 1 — Truth Map (No Code Changes)

### 1.1 Inventory L2 Routers
**TODO**
- List every `APIRouter` in `backend/app/hoc/api/**`.
- Capture module path and router prefix/tags.

**Acceptance Criteria**
- A single inventory list exists with **all** router modules under `backend/app/hoc/api/**`.
- No router module with `APIRouter` is missing from the list.

### 1.2 Map L2 → L4 Calls
**TODO**
- For each L2 router module, document which L4 entry it calls (operation registry / orchestrator / bridge).

**Acceptance Criteria**
- Every L2 module is mapped to an L4 call or flagged as **missing L4 usage**.

### 1.3 Inventory L5 / L6
**TODO**
- Enumerate all L5 engines and L6 drivers under `backend/app/hoc/cus/**`.
- Capture file path and intended domain.

**Acceptance Criteria**
- Each domain has a listed set of L5 engines and L6 drivers.
- No `*_engine.py` or `*_driver.py` in HOC is missing from the list.

### 1.4 Domain Truth Map
**TODO**
- Produce a domain matrix: Domain → L2 routes → L4 entry → L5 engine(s) → L6 driver(s) → L7 models.

**Acceptance Criteria**
- Every customer domain in `backend/app/hoc/cus/` has an entry in the matrix.
- Any missing link is explicitly marked **GAP**.

### 1.5 Topology Violation Scan
**TODO**
- Flag any L2 module that:
- Imports `sqlalchemy`, `sqlmodel`, or `Session`.
- Imports from `L5_engines` or `L6_drivers`.
- Directly uses DB connection or ORM.

**Acceptance Criteria**
- A violation list exists with file paths and the specific violation type.

### 1.6 Service File Ban Scan
**TODO**
- List all `*_service.py` under `backend/app/hoc/**`.

**Acceptance Criteria**
- Every `*_service.py` file is listed for refactor or explicit exception.

---

## Phase 2 — Enforce L2 Boundary (L2 → L4 Only)

### 2.1 Remove Direct DB Access from L2
**TODO**
- For each violating L2 module, move DB calls into L6 drivers.

**Acceptance Criteria**
- No L2 module imports `sqlalchemy`, `sqlmodel`, or `Session` at runtime.

### 2.2 Remove Direct L2 → L5/L6 Imports
**TODO**
- Replace L2 direct engine/driver imports with L4 orchestrator calls.

**Acceptance Criteria**
- No L2 module imports from `L5_engines` or `L6_drivers`.
- L2 modules call L4 orchestrator (operation registry / bridges).

### 2.3 L2 Purity Check
**TODO**
- Ensure L2 contains only validation, auth/tenant extraction, and translation to operation params.

**Acceptance Criteria**
- L2 modules contain no business logic (non-trivial decisions or computations).

---

## Phase 3 — L4 Authority Consolidation

### 3.1 L4 Ownership Audit
**TODO**
- Confirm L4 (`hoc_spine`) owns execution authority, governance gates, lifecycle, and consequences.

**Acceptance Criteria**
- L4 modules centralize decision points; no domain layer bypasses them.

### 3.2 Operation Registry Completion
**TODO**
- Ensure all L2-exposed operations exist in the L4 operation registry.

**Acceptance Criteria**
- No L2 route calls a missing or undefined L4 operation.

### 3.3 Cross-Domain Coordination Lock
**TODO**
- Identify any cross-domain logic outside L4 and relocate into L4.

**Acceptance Criteria**
- Cross-domain coordination exists only in `hoc_spine`.

---

## Phase 4 — L5 / L6 Pattern Compliance

### 4.1 Replace `*_service.py`
**TODO**
- Convert every `*_service.py` in HOC into `_engine.py` or `_driver.py`.

**Acceptance Criteria**
- No `*_service.py` remains under `backend/app/hoc/**`.

### 4.2 Engine Purity
**TODO**
- Remove DB/ORM imports from L5 engines.

**Acceptance Criteria**
- L5 engines do not import `sqlalchemy`, `sqlmodel`, or session types.

### 4.3 Driver Purity
**TODO**
- Remove business decisions from L6 drivers.

**Acceptance Criteria**
- L6 drivers contain only I/O and return raw facts.

### 4.4 Layer Headers
**TODO**
- Add `# Layer:` headers to any missing `.py` in HOC.

**Acceptance Criteria**
- All HOC `.py` files have a valid `# Layer:` header (CI compliant).

---

## Phase 5 — Entry Point Rewire (Main Sever + HOC Init)

### 5.1 Sever `backend/app/main.py`
**TODO**
- Remove HOC router imports and `include_router` calls from `backend/app/main.py`.
- Remove legacy `backend/app/services` wiring used by HOC.

**Acceptance Criteria**
- `backend/app/main.py` has no HOC router imports and no HOC route includes.

### 5.2 Create HOC Entry Point
**TODO**
- Create a dedicated HOC FastAPI entrypoint under `backend/app/hoc/**/main.py`.
- Wire all HOC routers there.

**Acceptance Criteria**
- A single HOC entrypoint exists and includes all HOC routers.
- No HOC router is wired in more than one entrypoint.

### 5.3 Deployment Routing
**TODO**
- Update runtime configuration to point HOC service to the new entrypoint.

**Acceptance Criteria**
- HOC API is served from its entrypoint, not from `backend/app/main.py`.

---

## Phase 6 — Validation & Guards

### 6.1 Layer Boundary Check
**TODO**
- Run `scripts/ci/check_layer_boundaries.py`.

**Acceptance Criteria**
- Script passes with no violations.

### 6.2 Cross-Domain Validator
**TODO**
- Run `scripts/ops/hoc_cross_domain_validator.py`.

**Acceptance Criteria**
- Script passes with no cross-domain violations.

### 6.3 Rescan for Violations
**TODO**
- Re-scan L2 modules for DB access and L2 → L5/L6 imports.

**Acceptance Criteria**
- Zero L2 modules contain direct DB access or L2 → L5/L6 imports.

---

## Phase 7 — Phase 1 Completion Check

### 7.1 Truth Map Refresh
**TODO**
- Update Phase 1 truth map after refactors.

**Acceptance Criteria**
- Truth map accurately reflects live wiring and topology.

### 7.2 Availability Check
**TODO**
- Verify `hoc/cus` and `hoc/api` are accessible through the HOC entrypoint.

**Acceptance Criteria**
- All HOC routes are reachable from the HOC entrypoint.

### 7.3 Topology Confirmation
**TODO**
- Spot-check representative routes per domain to confirm L2 → L4 → L5 → L6 → L7 path.

**Acceptance Criteria**
- No representative route violates the topology.
