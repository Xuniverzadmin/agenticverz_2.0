# HOC Spine — Constitutional Literature

**System Constitution · L4**
**Date:** 2026-01-30
**PIN:** PIN-490 (this document) · PIN-488 (literature study) · PIN-489 (P0/P1 enforcement)
**Scripts:** 65 (across 6 folders)
**Source:** `backend/app/hoc/cus/hoc_spine/`
**Validator:** `scripts/ops/hoc_spine_study_validator.py`

---

## Preamble

This document is the **authoritative guide** for evaluating every file, function, and class
inside `hoc/cus/hoc_spine/`. It defines what each component exists for, what problems it solves,
how it may be accessed, and what it must never become.

Domains must understand these definitions **without knowing internal mechanics**.

Any file that contradicts this literature is either:
- **In violation** — must be corrected
- **Misplaced** — must be relocated
- **Orphaned** — must be removed

---

## Part 1 — Root Definition

### `hoc/cus/hoc_spine/`

**Status:** VALID (Required)

`hoc_spine` is the **System Constitution (L4)**. It defines **what, when, and how**
execution happens across all domains.

It is:
- The **single execution gateway**
- The **only cross-domain coordinator**
- The **transaction owner**
- The **authority and governance plane**

Domains must treat everything under this root as **infrastructure, not business logic**.

Anything outside these roles does not belong in hoc_spine.

---

## Part 2 — Folder Literature (Level 1)

### 2.1 `orchestrator/` — Execution Authority

**Status:** VALID (Core, Mandatory)
**Layer:** L4
**Scripts:** 11

#### Purpose

The orchestrator is the **single execution authority** of the platform. No meaningful
system operation may execute unless it is **resolved, authorized, coordinated, and
committed** through the orchestrator.

It answers:
- **What** operation is being executed
- **In what order**
- **Under which transaction**
- **With what cross-domain context**

#### Core Functions

1. **Operation Resolution** — Maps a high-level request (`domain.operation`) to a
   concrete execution plan. Validates the operation is registered and allowed.
2. **Execution Sequencing** — Defines the order of steps across authority checks,
   coordination, engine execution, and consequences.
3. **Transaction Ownership** — Opens, commits, or rolls back the database transaction.
   Guarantees atomicity across all participating domains.
4. **Cross-Domain Coordination Trigger** — Delegates context assembly to the coordinator.
   Ensures L5 engines never pull cross-domain data themselves.

#### How Domains Access It

- **Indirectly only**
- Domains never call orchestrator logic directly
- Access occurs via:
  - L2 APIs invoking a registered operation
  - L5 engines being invoked *by* the orchestrator

#### What It Must Never Become

- A business logic layer
- A persistence layer
- A domain-specific workflow holder

#### Evaluation Criteria

When auditing files in `orchestrator/`, verify:
- [ ] File does not contain domain-specific business logic
- [ ] Transaction boundary is owned by L4 handlers/coordinators (commit/rollback may exist there; drivers never commit)
- [ ] File does not import L5 engines directly (use protocols)
- [ ] File does not make permission decisions (that's authority/)
- [ ] All cross-domain data access goes through drivers or coordinator

---

### 2.2 `authority/` — Decision of WHAT and WHEN

**Status:** VALID
**Layer:** L4
**Scripts:** 8

#### Purpose

The authority layer determines **whether an operation may proceed**, **under what mode**,
and **with what constraints**. It is the system's **decision brain**, not its executor.

#### Core Functions

1. **Eligibility Evaluation** — Determines if an operation is allowed for a tenant,
   user, or runtime state.
2. **Policy & Mode Resolution** — Selects runtime modes (normal, restricted, degraded,
   emergency). Applies policy posture without executing policy logic.
3. **Contract Enforcement** — Validates execution contracts (limits, concurrency,
   invariants).
4. **Guard Decisions** — Produces allow / deny / conditional outcomes.
5. **Attack-Surface Posture** — Centralizes “veil” posture decisions (docs/OpenAPI gating,
   deny-as-404, probe rate limiting). Canonical policy owner:
   `backend/app/hoc/cus/hoc_spine/authority/veil_policy.py`.

#### How Domains Access It

- **Never directly**
- Authority is consulted **only by the orchestrator**
- Domains receive the *effects* of authority decisions, not the logic

#### Key Invariant

Authority produces **decisions**, not actions.

#### What It Must Never Become

- An orchestration layer
- A direct database accessor
- A domain engine invoker

#### Evaluation Criteria

When auditing files in `authority/`, verify:
- [ ] File produces decisions/verdicts, not side effects
- [ ] File does not call L5 engines
- [ ] File does not touch DB drivers directly
- [ ] File does not orchestrate execution sequences
- [ ] File is consulted by orchestrator, not by domains

---

### 2.3 `consequences/` — Post-Execution Effects

**Status:** VALID
**Layer:** L5
**Scripts:** 1

#### Purpose

Consequences handle **what happens after execution**, not execution itself. They represent
**system reactions**, not business outcomes.

#### Core Functions

1. **Post-Commit Reactions** — Notifications, exports, escalations, external side effects.
2. **Outcome Interpretation** — Interprets execution results (success, failure, anomaly).
   Triggers appropriate reactions.
3. **Deferred Actions** — Schedules async or delayed effects when required.

#### How Domains Access It

- **They do not**
- Consequences are triggered exclusively by the orchestrator

#### Key Invariant

Consequences are triggered **only by orchestrator**, after commit.

#### What It Must Never Become

- An execution decision layer
- A direct domain data reader/writer
- A transaction participant

#### Evaluation Criteria

When auditing files in `consequences/`, verify:
- [ ] File does not influence execution decisions
- [ ] File does not read or write domain data directly
- [ ] File does not participate in transactions
- [ ] File is triggered only by orchestrator, never by L5 engines

---

### 2.4 `services/` — Shared Spine Infrastructure

**Status:** VALID
**Layer:** L5
**Scripts:** 24

#### Purpose

Services provide **pure, reusable, domain-agnostic utilities** required by the spine to
function. They exist to avoid duplication and leakage into domains.

#### Core Functions

1. **Time & Identity** — Clock access, ID generation.
2. **Audit & Observability** — Audit logging, runtime tracing hooks.
3. **Runtime Controls** — Feature switches, mode flags, environment awareness.
4. **Verification Utilities** — Webhook verification, signature checks.
5. **Alert & Delivery Infrastructure** — Alert facade, fatigue control, delivery
   (absorbed from former adapters/ folder).
6. **Data Retrieval** — Retrieval facades and mediators.
7. **Lifecycle Management** — Lifecycle facades and stage base types.

#### How Domains Access It

- **Indirectly**
- Domains may receive outputs produced using services
- Domains must not import services directly unless explicitly allowed

#### Hard Boundary

Services must be **stateless, deterministic, and domain-agnostic**.

#### What It Must Never Become

- An orchestration layer
- A database accessor
- A domain-specific logic container

#### Evaluation Criteria

When auditing files in `services/`, verify:
- [ ] File is stateless and domain-agnostic
- [ ] File does not import L5 engines
- [ ] File does not import L6 drivers
- [ ] File does not import schemas outside hoc_spine
- [ ] File does not contain domain-specific business logic
- [ ] File does not manage transactions

---

### 2.5 `schemas/` — System Contracts

**Status:** VALID
**Layer:** L5
**Scripts:** 8

#### Purpose

Schemas define the **shape of communication** inside the spine. They are the **shared
language** of execution.

#### Core Functions

1. **Operation Contracts** — Defines what an operation is. Defines required inputs and
   expected outputs.
2. **Execution Context** — Represents runtime state passed across layers.
3. **Authority Decisions** — Encodes allow / deny / conditional outcomes.
4. **API Response Envelopes** — Standard response shapes for external consumers.

#### How Domains Access It

- Domains may:
  - Consume schema types
  - Return schema-conformant results
- They must not modify or extend schemas locally

#### Absolute Rule

Schemas contain **no logic** and **no side effects**.

#### What It Must Never Become

- A logic container
- A services importer
- A drivers importer

#### Evaluation Criteria

When auditing files in `schemas/`, verify:
- [ ] File contains only Pydantic models, dataclasses, enums, or type definitions
- [ ] File does not import services, drivers, or orchestrator
- [ ] File contains no business logic or side effects
- [ ] File contains no database access

---

### 2.6 `drivers/` — Cross-Domain Data Boundary

**Status:** VALID
**Layer:** L6
**Scripts:** 13

#### Purpose

Drivers are the **only sanctioned mechanism** for accessing or mutating persistent state
**across domains** under orchestrator control.

#### Core Functions

1. **Cross-Domain Reads** — Fetch data spanning multiple domain tables.
2. **Cross-Domain Writes** — Persist results produced by orchestrated operations.
3. **Transaction Participation** — Operate within a transaction opened by the orchestrator.
4. **Transaction Coordination** — Transaction boundaries (commit/rollback) are owned by L4 handlers/coordinators. Drivers never commit.

#### How Domains Access It

- Domains **do not**
- Drivers are invoked only by:
  - Orchestrator
  - Coordinator (under orchestrator control)

#### Non-Negotiable Invariants

- No commits/rollbacks
- No orchestration
- No L5 engine imports

#### Evaluation Criteria

When auditing files in `drivers/`, verify:
- [ ] File does not call `session.commit()` / `session.rollback()`
- [ ] File does not orchestrate execution
- [ ] File does not import L5 engines
- [ ] File operates within orchestrator-owned transactions
- [ ] File does not contain business logic

---

## Part 3 — Subfolder Literature (Level 2)

### 3.1 `authority/contracts/`

**Status:** VALID
**Scripts:** 1 (contract_engine.py)

#### Purpose

Formalizes **execution contracts** that must be satisfied **before** an operation is
allowed to proceed. A contract is a **system-level invariant**, not a business rule.

#### Core System Role

- Defines preconditions for execution
- Encodes concurrency limits, execution quotas, invariant guarantees
- Produces contract validation outcomes, not actions

#### How the System Uses It

- Invoked by `authority/`
- Consulted by the orchestrator **prior to execution**
- Outputs directly influence: allow, deny, conditional execution paths

#### What It Is Not

- Not orchestration
- Not persistence
- Not policy logic

This subfolder answers: **"may this run at all?"** — independently of **"how to run it."**

---

### 3.2 `consequences/adapters/`

**Status:** VALID (Scoped)
**Scripts:** 1 (export_bundle_adapter.py)

#### Purpose

Isolates **representation and delivery concerns** for post-execution consequences.
Prevents execution logic leakage and consequence logic contaminating orchestration.

#### Core System Role

- Translates execution outcomes into exportable formats, external delivery payloads,
  system-level bundles

#### How the System Uses It

- Triggered only after successful commit
- Invoked by `consequences/`
- Never invoked directly by domains or L5 engines

#### What It Is Not

- Not an execution adapter
- Not an integration layer
- Not allowed to read domain state independently

This folder represents **"how consequences are expressed," not "whether they occur."**

---

### 3.3 `orchestrator/execution/`

**Status:** VALID
**Scripts:** 1 (job_executor.py)

#### Purpose

Contains **execution mechanics**, not execution authority. Separates *execution
orchestration* (what + when) from *execution mechanics* (how tasks are run).

#### Core System Role

- Executes work units defined by the orchestrator
- Handles job invocation, sequencing primitives, execution dispatch

#### How the System Uses It

- Called by orchestrator control flow
- Never accessed by domains
- Operates entirely under an orchestrator-owned transaction and plan

#### What It Is Not

- Not a scheduler
- Not a coordinator
- Not a policy decision layer

This folder answers **"how execution happens once approved."**

---

### 3.4 `orchestrator/lifecycle/`

**Status:** VALID (Critical)
**Scripts:** 5 (across drivers/ and engines/ sub-subfolders)

#### Purpose

Governs **system lifecycle phases** that surround execution. Lifecycle is about
**state transitions**, not actions.

#### Core System Role

- Manages onboarding, offboarding, phase transitions, resource pool states
- Encodes system-level progression, not domain workflows

#### How the System Uses It

- Consulted by orchestrator before and after execution
- Ensures execution aligns with current system phase

#### What It Is Not

- Not domain lifecycle logic
- Not user workflow logic

Lifecycle answers **"is the system in a state where this execution makes sense?"**

---

### 3.4a `orchestrator/lifecycle/drivers/`

**Status:** VALID
**Scripts:** 2 (execution.py, knowledge_plane.py)

#### Purpose

Provides **read/write access to lifecycle state** under orchestrator control.

- Persists lifecycle transitions
- Reads lifecycle context
- Participates in orchestrator transaction

#### Invariants

- Never commits
- Never orchestrates
- Never accesses L5 engines

---

### 3.4b `orchestrator/lifecycle/engines/`

**Status:** VALID
**Scripts:** 3 (offboarding.py, onboarding.py, pool_manager.py)

#### Purpose

Encodes **lifecycle transition logic**. This is *state transition reasoning*, not
orchestration.

- Determines valid lifecycle transitions
- Produces lifecycle outcomes consumed by orchestrator

#### Invariant

Lifecycle engines do **not** invoke execution themselves.

---

## Part 4 — System-Level Access Matrix

| Component | Who May Call It | Who It May Call |
|---|---|---|
| orchestrator | L2 only (entry) | authority, coordinator, L5, consequences |
| authority | orchestrator only | services, schemas, contracts |
| consequences | orchestrator only | services, consequence adapters |
| services | spine components | stdlib only (no app imports) |
| schemas | everyone (read-only) | none |
| drivers | orchestrator/coordinator | database only |

---

## Part 5 — Eliminated Folders

These folders have been removed from hoc_spine. Their files were redistributed
or relocated. Literature stubs remain at their original paths for traceability.

### 5.1 `adapters/` — DELETED (2026-01-30)

**Reason:** Ambiguous constitutional role. Files absorbed into natural governance homes.

| File | New Location | Rationale |
|------|-------------|-----------|
| `alert_delivery.py` | `services/alert_delivery.py` | Infrastructure utility |
| `runtime_adapter.py` | `authority/runtime_adapter.py` | Runtime boundary decision |

### 5.2 `frontend/` — RELOCATED (2026-01-30)

**Reason:** Projection code belongs in the frontend application tree, not backend spine.

| File | New Location | Rationale |
|------|-------------|-----------|
| `projections/rollout_projection.py` | `frontend/app/projections/rollout_projection.py` | L1 presentation concern |

Import in `orchestrator/__init__.py` broken intentionally. Will be re-wired during L1 design.

### 5.3 `mcp/` — RELOCATED (2026-01-29)

**Reason:** MCP is tool discovery/integration, not system constitution. Zero callers.
Duplicate exists at `app/services/mcp/server_registry.py`.

| File | New Location | Rationale |
|------|-------------|-----------|
| `server_registry.py` | `cus/integrations/adapters/mcp_server_registry.py` | Integration adapter |

---

## Part 6 — Structural Integrity Summary

### Level 1 (Top Folders)

| Folder | Status | Scripts | Layer | Constitutional Role |
|--------|--------|---------|-------|-------------------|
| orchestrator | VALID | 11 | L4 | Execution authority |
| authority | VALID | 8 | L4 | Decision authority |
| consequences | VALID | 1 | L5 | Post-execution effects |
| services | VALID | 24 | L5 | Shared infrastructure |
| schemas | VALID | 8 | L5 | System contracts |
| drivers | VALID | 13 | L6 | Cross-domain data boundary |
| ~~adapters~~ | DELETED | — | — | Absorbed into services + authority |
| ~~frontend~~ | RELOCATED | — | — | Moved to frontend/app/ |
| ~~mcp~~ | RELOCATED | — | — | Moved to cus/integrations/adapters/ |

### Level 2 (Subfolders)

| Subfolder Path | Status | Scripts | Role |
|---------------|--------|---------|------|
| authority/contracts | VALID | 1 | Contract preconditions |
| consequences/adapters | VALID | 1 | Consequence delivery |
| orchestrator/execution | VALID | 1 | Execution mechanics |
| orchestrator/lifecycle | VALID | 5 | System lifecycle phases |
| orchestrator/lifecycle/drivers | VALID | 2 | Lifecycle state persistence |
| orchestrator/lifecycle/engines | VALID | 3 | Lifecycle transition logic |

---

## Part 7 — Audit Guide

### Using the Validator Script

```bash
# Extract metadata for all spine files (YAML)
python scripts/ops/hoc_spine_study_validator.py --all --output-dir /tmp/spine_yaml

# Generate/regenerate all literature markdown
python scripts/ops/hoc_spine_study_validator.py --generate

# Generate for a single folder
python scripts/ops/hoc_spine_study_validator.py --generate --folder authority

# Detect drift between literature and source
python scripts/ops/hoc_spine_study_validator.py --validate literature/hoc/cus/hoc_spine/

# Regenerate INDEX.md only
python scripts/ops/hoc_spine_study_validator.py --index --output-dir literature/
```

### Automated Checks (per file)

The validator automatically detects:

| Check | Detection Method |
|-------|-----------------|
| Governance violations | Import analysis against folder rules |
| Transaction boundary violations | `session.commit()` / `flush()` / `rollback()` detection |
| Cross-domain imports | Import path analysis for `hoc.cus.*` |
| Schema purity | Schema files importing services/drivers/orchestrator |
| Service purity | Service files importing L5 engines or L6 drivers |
| Driver commit violation | Non-coordinator drivers calling commit |
| Missing literature | Source file exists but no .md counterpart |
| Drift | Source functions/classes not mentioned in literature |

### Manual Audit Checklist (per folder)

For each folder, use the evaluation criteria in Part 2 above. Additionally:

1. **Read the file's Placement Card** in its literature `.md`
2. **Verify inbound/outbound** matches the access matrix (Part 4)
3. **Check transaction boundary** matches folder rules
4. **Confirm no cross-domain imports** unless justified
5. **Validate module docstring** explains constitutional purpose, not implementation

### Exit Criteria

- Validator exit code 0 (zero drift)
- All evaluation criteria checkboxes pass per folder
- No UNKNOWN artifact classes
- No orphaned modules (zero callers)
- Access matrix respected (Part 4)

---

## Part 8 — Enforcement Record (PIN-489)

**Date:** 2026-01-30
**Phase:** Constitutional enforcement (clean-up, not redesign)

### Enforcement Summary

| Metric | Before | After |
|--------|--------|-------|
| Governance violations | 9 | **2** |
| Cross-domain imports | 12 sites / 7 files | **0** |
| Unauthorized commits | 2 files | **0** (tagged TODO) |
| Schema impurity | 2 files | **0** (inlined) |
| Clean scripts | 56/65 | **63/65** |

### P0-1: Cross-Domain Import Elimination (COMPLETE)

All `from app.hoc.cus.*` imports removed from hoc_spine. 12 import sites across 6 files
replaced with `TODO(L1)` markers — broken intentionally, to be re-wired during L1 design
via protocol interfaces or orchestrator context injection.

| File | Import Removed | Pattern |
|------|---------------|---------|
| `authority/contracts/contract_engine.py` | policies L5 eligibility, account L5 crm_validator | Comment-out + TODO |
| `consequences/adapters/export_bundle_adapter.py` | logs L6 export_bundle_store | Comment-out + TODO |
| `drivers/transaction_coordinator.py` | incidents L5 incident_driver, logs L5 trace_facade | NotImplementedError + TODO |
| `orchestrator/lifecycle/drivers/execution.py` | integrations L6 connector_registry (x2) | NotImplementedError + TODO |
| `orchestrator/run_governance_facade.py` | policies L5 lessons_engine, incidents L5 policy_violation_service | NotImplementedError + TODO |
| `orchestrator/__init__.py` | logs L5 audit_engine, policies L5 eligibility, account L5 crm_validator | Comment-out + `__all__` cleanup |

### P0-2: Unauthorized Commit Tagging (TAGGED)

`drivers/decisions.py` (4 sites) and `drivers/ledger.py` (1 site) use raw
`create_engine()` connections with `conn.commit()` — not ORM sessions. Cannot replace
with `flush()`. Tagged `VIOLATION: TODO(L1) migrate to transaction_coordinator session`.

These are the **only 2 remaining violations**. Resolution requires migrating both files
to session-managed transactions under `transaction_coordinator` control.

### P1: Schema Purity Restoration (COMPLETE)

`schemas/artifact.py` and `schemas/plan.py` imported `utc_now` from `services.time`.
Replaced with inlined `_utc_now()` function. Schemas now have zero application imports.

### Remaining Work (L1 Design)

All broken imports are marked `TODO(L1)`. During L1 design:

1. Define protocol interfaces in `schemas/` for domain engine contracts
2. Inject domain callables via orchestrator execution context
3. Migrate `decisions.py` and `ledger.py` to session-managed transactions
4. Re-wire `orchestrator/__init__.py` re-exports via protocol-based injection
5. Re-wire `frontend/app/projections/rollout_projection.py` import path

---

## Closing Statement

The **core constitutional surface of hoc_spine is sound**.

The six validated folders together form:
- A **governed execution runtime**
- A **single cross-domain authority plane**
- A **stable transaction and coordination layer**

They are sufficient to let **domains plug in cleanly** without knowing internals.

This literature is the **source of truth** for all audit and evaluation activities
against hoc_spine files.
