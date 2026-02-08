# POLICIES Domain — Canonical Software Literature

**Domain:** `policies`
**Status:** LARGEST HOC DOMAIN (77 files)
**Last Updated:** 2026-02-08
**Phase:** Phase-6 Architecture (HOC Multi-Tenant SaaS)

---

## Executive Summary

The **policies** domain is the largest and most complex domain in the HOC architecture, containing **77 files** across L5 and L6 layers. It implements the complete policy lifecycle: DSL compilation, runtime enforcement, conflict resolution, recovery evaluation, and lessons learned. This domain serves as the **governance control plane** for the entire system, enforcing customer-defined rules, limits, and protections across all operations.

**L2 Purity Update (2026-02-08):**
- L2 policy APIs no longer import L5 engines directly; they dispatch via hoc_spine (OperationRegistry / L4 bridges).
- L2 policy APIs no longer import L7 models (`app.models.*`). Enum usage is via L4-safe mirrors (e.g. `hoc_spine/schemas/domain_enums.py`).

### Reality Delta (2026-02-08)

- L2 purity preserved: policies L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain policies --json --advisory` reports 0 blocking, 0 advisory (transaction boundaries owned by L4).
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.

**New L4 Operation (GAP-174):** `policies.sandbox_execute` executes `L5_engines/sandbox_engine.py` through hoc_spine (handler: `hoc_spine/orchestrator/handlers/policies_sandbox_handler.py`).

**Strict T0 wiring fix:** policy plan generation now imports `get_planner` from `app.planners` (not `hoc.int.platform` facades) to preserve authority boundaries.

### Knowledge Access (RAG) — Policy-Governed Plane Authorization

- Knowledge access must be treated as an **explicit authorization gate**, not as a prompt-side behavior.
- Policies are the natural owner of the **`knowledge_access`** policy surface (deny-by-default, allow/deny plane lists, query constraints, logging rules).
- Enforcement is runtime-owned (hoc_spine mediation/retrieval choke point), not domain-owned transition logic.
- Canonical design literature + plan:
  - `literature/hoc_spine/KNOWLEDGE_PLANE_LITERATURE.md`
  - `docs/architecture/hoc/KNOWLEDGE_PLANE_LIFECYCLE_HARNESS_PLAN_V2.md`

### Domain Metrics

| Metric | Value |
|--------|-------|
| **Total Files** | 78 |
| **L5 Engines** | 63 (62 active .py + 1 `__init__.py`) |
| **L6 Drivers** | 15 (14 active .py + 1 `__init__.py`) |
| **L4 Operations** | 9 (via `policies_handler.py`) |
| **DSL Compiler Chain** | 11 files (PLang v2.0) |
| **Execution Kernel** | 7 files (mandatory choke point) |
| **Policy CRUD** | 9 files (rules, limits, proposals, capabilities) |
| **Enforcement Engines** | 6 files (prevention, protection, binding) |

---

## Layer Topology

### L5 Engines (63 files)

The policies L5 layer contains **62 active Python scripts** organized into 11 functional groups:

#### 1. DSL Compiler Chain (11 files)

The DSL compiler chain transforms customer-written policy DSL (PLang v2.0) into executable intermediate representation (IR) and bytecode.

| File | Responsibility | Key Outputs |
|------|---------------|-------------|
| `tokenizer.py` | Lexical analysis | Token stream |
| `grammar.py` | Grammar definitions | Grammar rules for PLang v2.0 |
| `dsl_parser.py` | DSL text parser | DSL → AST |
| `compiler_parser.py` | PLang v2.0 parser | Parsed policy AST |
| `ast.py` | AST node definitions | AST node classes |
| `ir_nodes.py` | IR node definitions | IR node classes |
| `ir_builder.py` | AST to IR transformation | AST → IR |
| `ir_compiler.py` | AST → bytecode compilation | Executable bytecode |
| `interpreter.py` | DSL interpreter | IR evaluation results |
| `validator.py` | Semantic validator | Validation errors/warnings |
| `content_accuracy.py` | Content accuracy validation | Accuracy checks |

**Flow:** DSL text → tokenizer → parser → AST → validator → IR builder → IR compiler → bytecode → interpreter

#### 2. Execution Kernel (7 files)

The execution kernel is the **mandatory single choke point** for all policy execution, ensuring deterministic, auditable, and governance-controlled policy evaluation.

| File | Responsibility | Pattern |
|------|---------------|---------|
| `kernel.py` | Mandatory execution kernel | Single choke point |
| `engine.py` | Policy rule evaluation engine | Rule executor |
| `decorator.py` | Ergonomic decorator over kernel | Simplified API |
| `state.py` | Phase-6 billing state enum | State definitions |
| `nodes.py` | AST node definitions | GovernanceMetadata nodes |
| `visitors.py` | AST visitor implementations | Visitor pattern |
| `folds.py` | Constant folding optimizations | Optimization pass |

**Architecture:** All policy execution MUST flow through `kernel.py`. The `decorator.py` provides an ergonomic wrapper, but it delegates to the kernel. The `engine.py` performs the actual rule evaluation within the kernel's control.

#### 3. Policy CRUD (9 files)

Policy CRUD engines handle create, read, update, delete, and query operations for policies, rules, limits, and proposals.

| File | Responsibility | Operations |
|------|---------------|-----------|
| `policy_rules_engine.py` | Rules CRUD engine; factory now accepts driver param for capability injection via DomainBridge (PIN-508 Phase 2B) | Create, update, delete rules |
| `policy_limits_engine.py` | Limits CRUD engine; constructor now accepts driver param for capability injection via DomainBridge (PIN-508 Phase 2C) | Create, update, delete limits |
| `policy_proposal_engine.py` | Proposal lifecycle engine | Proposal CRUD workflow |
| `policies_rules_query_engine.py` | Rules read-only queries | Rules listing, filtering |
| `policies_limits_query_engine.py` | Limits read-only queries; factory now accepts driver param for capability injection via DomainBridge (PIN-508 Phase 2B) | Limits listing, filtering |
| `policies_proposals_query_engine.py` | Proposals read-only queries | Proposals listing, filtering |
| `customer_policy_read_engine.py` | Customer policy reads | Business logic for reads |
| `policy_models.py` | Domain models and types | PolicyRule, Limit, Proposal |
| `domain_bridge_capabilities.py` (NEW) | Capability Protocols for cross-domain access via DomainBridge | LessonsQueryCapability, LimitsQueryCapability, PolicyLimitsCapability |

**Pattern:** Separation of concerns — write engines (CRUD) vs. read engines (queries) with dedicated query engines for each entity type.

**PIN-508 Phase 2 Capabilities:** New `domain_bridge_capabilities.py` (L5 Schemas) defines capability protocols for cross-domain access. See PIN-508 for full integration details.

#### 4. Facades (3 files)

Facades provide unified, high-level interfaces to complex subsystems.

| File | Responsibility | Subsystem |
|------|---------------|-----------|
| `policies_facade.py` | HOC policies facade; 14 methods (6 via L6 driver, 5 L5 delegation, 3 mixed), 20 result types (1185 LOC). Rewired 2026-02-02 (PIN-512 Cat-B Phase 2). | PoliciesFacadeDriver (L6), lessons_engine, engine, policy_graph_engine (L5) |
| `governance_facade.py` | Governance control facade | Kill switch, degraded mode, conflicts |
| `limits_facade.py` | Rate limits and quotas facade | Limits management |

**Note:** `policies_facade.py` was previously a re-export from legacy `app.services.policies_facade`. Stubbed 2026-01-31, rewired 2026-02-02 (PIN-512 Cat-B Phase 2). SQL queries extracted to PoliciesFacadeDriver (L6, 478 LOC). Delegation methods rewired from legacy `app.services.*` to HOC `app.hoc.cus.policies.L5_engines.*`.

#### 5. Enforcement & Prevention (6 files)

Enforcement engines handle runtime policy enforcement, prevention hooks, abuse protection, and binding moment evaluation.

| File | Responsibility | Enforcement Type |
|------|---------------|-----------------|
| `cus_enforcement_engine.py` | Customer enforcement engine; 9-decision enforcement logic with L6 driver injection (559 lines). Rewired from legacy 2026-02-02 (PIN-512 Cat-B). | CusEnforcementDriver (L6) |
| `prevention_engine.py` | Runtime enforcement | Real-time prevention |
| `prevention_hook.py` | Prevention hook | Content accuracy checks |
| `protection_provider.py` | Phase-7 abuse protection | Abuse detection/mitigation |
| `binding_moment_enforcer.py` | Binding moment evaluation | When policies apply |
| `phase_status_invariants.py` | Phase-status invariant enforcement | Invariant checking |

**Note:** `cus_enforcement_engine.py` was renamed from `cus_enforcement_service.py` (N1 naming violation), stubbed (2026-01-31), then rewired with real legacy implementation (2026-02-02, PIN-512 Cat-B). Now uses CusEnforcementDriver (L6) for all DB access. New L6 driver: `policies/L6_drivers/cus_enforcement_driver.py` (269 lines).

#### 6. Decision & Authority (5 files)

Decision engines handle policy evaluation, worker authorization, claim decisions, override authority, and eligibility gating.

| File | Responsibility | Decision Domain |
|------|---------------|----------------|
| `policy_command.py` | Policy evaluation and decision authority | Policy decisions |
| `worker_execution_command.py` | Worker execution authorization | Worker auth |
| `claim_decision_engine.py` | Recovery claim decisions | Claim approval/denial |
| `authority_checker.py` | Override authority checking | Admin overrides |
| `eligibility_engine.py` | Eligibility gating | Feature eligibility |

**Header Corrections (2026-01-31):** `policy_command.py`, `worker_execution_command.py`, and `claim_decision_engine.py` had incorrect L4 layer headers; corrected to L5.

#### 7. Conflict & Graph (3 files)

Conflict resolution and dependency graph engines handle policy conflicts, precedence, and dependency analysis.

| File | Responsibility | Analysis Type |
|------|---------------|--------------|
| `policy_conflict_resolver.py` | Conflict resolution | Pure logic resolution |
| `policy_graph_engine.py` | Conflict detection & dependency graph | Graph analysis |
| `policy_mapper.py` | MCP tool → policy gate mapping | Tool-to-policy mapping |

**Overlap Classification:** These three files address different aspects of conflict management (prevention, optimization, arbitration) and are NOT duplicates.

#### 8. Recovery & Learning (3 files)

Recovery and learning engines handle recovery decisions, lessons learned, and learning proof generation.

| File | Responsibility | Learning Phase |
|------|---------------|---------------|
| `recovery_evaluation_engine.py` | Recovery decision-making | Failure recovery |
| `lessons_engine.py` | Lessons learned creation/management; factory now accepts driver param for capability injection via DomainBridge (PIN-508 Phase 2A) | Knowledge capture |
| `learning_proof_engine.py` | Learning proof generation | Graduation gates |

**Legacy Disconnection (2026-01-31):** `lessons_engine.py` previously imported from HOC by legacy `app/services/policy/lessons_engine.py`. Legacy file has been emptied and disconnected.

**PIN-508 Phase 2A:** `lessons_engine.py` factory now accepts driver param for capability injection via DomainBridge.

#### 9. Simulation & Sandbox (2 files)

Simulation and sandbox engines provide pre-execution limit simulation and high-level sandbox policy enforcement.

| File | Responsibility | Simulation Type |
|------|---------------|----------------|
| `limits_simulation_engine.py` | Pre-execution limit simulation; context building + evaluation logic (275 lines). Rewired from legacy 2026-02-02 (PIN-512 Cat-B). | LimitsSimulationDriver (L6) |
| `sandbox_engine.py` | High-level sandbox with policy enforcement | Isolated execution |

**Note:** `limits_simulation_engine.py` was renamed from `limits_simulation_service.py` (N2 naming violation), stubbed (2026-01-31), then rewired with real legacy implementation (2026-02-02, PIN-512 Cat-B). Now uses LimitsSimulationDriver (L6) for all DB access. New L6 driver: `policies/L6_drivers/limits_simulation_driver.py`.

#### 10. Runtime & Commands (3 files)

Runtime command engines handle runtime domain commands and internal orchestration.

| File | Responsibility | Command Type |
|------|---------------|-------------|
| `runtime_command.py` | Runtime domain commands | Runtime ops |
| `policy_driver.py` | Internal orchestration for policy operations | Policy routing |

**Note:** `policy_command.py` is listed under Decision & Authority (section 6).

#### 11. Other Engines (6 files)

Additional engines providing deterministic execution, degraded mode, failure handling, kill switches, plans, and snapshots.

| File | Responsibility | Function |
|------|---------------|----------|
| `deterministic_engine.py` | Deterministic policy execution | Reproducibility |
| `degraded_mode.py` | Degraded mode state logic | Graceful degradation |
| `failure_mode_handler.py` | Failure mode handling | Fail-closed behavior |
| `kill_switch.py` | Runtime kill switch | Emergency shutdown |
| `keys_shim.py` | API Keys domain operations | Deprecated shim |
| `plan.py` | Phase-6 plan model | Plan definitions |
| `plan_generation_engine.py` | Plan generation | Plan creation |
| `limits.py` | Phase-6 limits derivation | Limit calculations |
| `intent.py` | Policy intent model | Intent definitions |
| `snapshot_engine.py` | Policy snapshot immutability | Snapshot creation |

---

### L6 Drivers (17 files)

The policies L6 layer contains **16 active Python scripts** providing data access and persistence for policies, proposals, graphs, conflicts, enforcement, simulation, and recovery.

#### 1. Policy Data Access (4 files)

| File | Responsibility | Data Operations |
|------|---------------|----------------|
| `policy_read_driver.py` | Policy read operations | SELECT queries |
| `policy_engine_driver.py` | Policy engine data access | Evaluations, violations |
| `policy_rules_driver.py` | Rules CRUD persistence | INSERT, UPDATE, DELETE |
| `policy_rules_read_driver.py` | Rules query persistence | SELECT with filters |

**Pattern:** Separation of read and write drivers for policies and rules.

#### 2. Proposal Data Access (3 files)

| File | Responsibility | Data Operations |
|------|---------------|----------------|
| `policy_proposal_read_driver.py` | Proposal lifecycle reads | SELECT proposals |
| `policy_proposal_write_driver.py` | Proposal lifecycle writes | INSERT, UPDATE proposal state |
| `proposals_read_driver.py` | Proposal list view queries | SELECT with pagination |

**Pattern:** Facade pattern with read/write separation for proposal lifecycle management.

#### 3. Graph & Conflict (3 files)

| File | Responsibility | Resolution Type |
|------|---------------|----------------|
| `policy_graph_driver.py` | Graph data access | Graph persistence |
| `arbitrator.py` | Runtime policy arbitration | Precedence sorting |
| `optimizer_conflict_resolver.py` | Policy conflict resolution with DB | Optimization-based resolution |

**Overlap Classification:** These three files serve different purposes (graph storage, runtime arbitration, optimization) and are NOT duplicates.

#### 4. Recovery (2 files)

| File | Responsibility | Recovery Phase |
|------|---------------|---------------|
| `recovery_matcher.py` | Failure pattern matching | Pattern recognition |
| `recovery_write_driver.py` | Recovery persistence | Recovery data writes |

#### 5. Facade & Enforcement Drivers (3 files — PIN-512 Category B)

| File | Responsibility | Data Operations |
|------|---------------|----------------|
| `policies_facade_driver.py` | Policies facade SQL queries — rules, limits, budgets, requests, drafts count (478 LOC). Extracted from legacy 2026-02-02 (PIN-512 Cat-B Phase 2). | SELECT with JOINs, subqueries, pagination |
| `cus_enforcement_driver.py` | Customer enforcement data access — IntegrationRow/UsageSnapshot DTOs, 5 fetch methods (259 LOC). Copied from legacy 2026-02-02 (PIN-512 Cat-B Phase 1). | SELECT enforcement data |
| `limits_simulation_driver.py` | Simulation data access — tenant quotas, policy limits (192 LOC). Copied from legacy 2026-02-02 (PIN-512 Cat-B Phase 1). | SELECT simulation context |

#### 6. Other Drivers (2 files)

| File | Responsibility | Function |
|------|---------------|----------|
| `scope_resolver.py` | Policy scope resolution | Scope determination |
| `symbol_table.py` | Policy symbol table | In-memory symbol storage |

---

## L4 Handler Operations

The `policies_handler.py` exposes **9 operations** routing to various L5 engines and facades:

| Operation | Target | Responsibility |
|-----------|--------|---------------|
| `policies.query` | `PoliciesFacade` | Policy queries |
| `policies.enforcement` | `CusEnforcementEngine` | Customer enforcement |
| `policies.governance` | `GovernanceFacade` | Governance controls |
| `policies.lessons` | `LessonsLearnedEngine` | Lessons management |
| `policies.policy_facade` | `PolicyDriver` | Policy orchestration |
| `policies.limits` | `PolicyLimitsService` | Limits management |
| `policies.rules` | `PolicyRulesService` | Rules management |
| `policies.rate_limits` | `LimitsFacade` | Rate limit facade |
| `policies.simulate` | `LimitsSimulationEngine` | Limit simulation |

---

## Naming Violations — RESOLVED

### N1: `cus_enforcement_service.py` → `cus_enforcement_engine.py`
- **Status:** RESOLVED (2026-01-31)
- **Action:** Renamed to `cus_enforcement_engine.py`
- **Legacy:** Disconnected from `app.services.cus_enforcement_engine`, now stubbed

### N2: `limits_simulation_service.py` → `limits_simulation_engine.py`
- **Status:** RESOLVED (2026-01-31)
- **Action:** Renamed to `limits_simulation_engine.py`
- **Legacy:** Disconnected from `app.services.limits.simulation_engine`, now stubbed

---

## Layer Header Corrections — RESOLVED

The following files had incorrect layer headers corrected on 2026-01-31:

| File | Old Header | New Header | Reason |
|------|-----------|-----------|--------|
| `governance_facade.py` | L6 | L5 | File is in `L5_engines/` |
| `policy_command.py` | L4 | L5 | File is in `L5_engines/` |
| `worker_execution_command.py` | L4 | L5 | File is in `L5_engines/` |
| `claim_decision_engine.py` | L4 | L5 | File is in `L5_engines/` |

---

## Legacy Dependencies — DISCONNECTED

As of **2026-01-31**, the following legacy imports have been disconnected:

| HOC File | Legacy Import | Action |
|----------|--------------|--------|
| `cus_enforcement_engine.py` | `app.services.cus_enforcement_engine` | Stubbed |
| `limits_simulation_engine.py` | `app.services.limits.simulation_engine` | Stubbed |
| `policies_facade.py` | `app.services.policies_facade` | Stubbed |
| N/A | `app/services/policy/lessons_engine.py` | Emptied and disconnected |

**Status:** All legacy-to-HOC and HOC-to-legacy imports for the policies domain have been severed. Stub files remain for compatibility during the rewiring phase.

---

## Architecture Violations — DEFERRED

The following architecture violations have been **documented** but are **deferred to the rewiring phase**:

### Correct Pattern
```
L6 policy driver → L5 policy engine → L4 runtime orchestrator → L5 target engine → L6 target driver → feedback return same route
```

### Violations

| ID | File | Violation | Correct Route |
|----|------|-----------|---------------|
| **V1** | `policy_proposal_engine.py` (L5) | Imports `logs/L6_drivers/audit_ledger` | Should route through L4 |
| **V2** | `policy_rules_engine.py` (L5) | Imports `logs/L6_drivers/audit_ledger` | Should route through L4 |
| **V3** | `policy_limits_engine.py` (L5) | Imports `logs/L6_drivers/audit_ledger` | Should route through L4 |
| **V4** | `recovery_evaluation_engine.py` (L5) | ~~Imports `incidents/L5_engines/recovery_rule_engine`~~ | **RESOLVED** (PIN-504 Phase 6): Pure functions extracted to `hoc_spine/schemas/recovery_decisions.py` |
| **V5** | `lessons_engine.py` (L5) | ~~Imports `incidents/L6_drivers/lessons_driver`~~ | **RESOLVED** (PIN-504 Phase 6): Lazy import inside `_get_driver()` method |

**Remediation Status:** V1-V3 resolved by AuditCoordinator (PIN-504 Phase 2). V4-V5 resolved by type extraction + lazy imports (PIN-504 Phase 6). All 5 violations **RESOLVED**.

---

## Overlap Analysis — ZERO DUPLICATES

All apparent overlaps have been classified as **intentional architectural patterns**:

### 1. Policy Read (L5 Engine vs L6 Driver)
- **Files:** `customer_policy_read_engine.py` (L5), `policy_read_driver.py` (L6)
- **Classification:** `L5_L6_SEPARATION`
- **Reason:** L5 contains business logic; L6 contains data access logic

### 2. Conflict Resolution (3 files)
- **Files:** `policy_conflict_resolver.py`, `policy_graph_engine.py`, `optimizer_conflict_resolver.py`
- **Classification:** `FALSE_POSITIVE`
- **Reason:** Prevention (pure logic), optimization (with DB), arbitration (runtime sorting)

### 3. Proposals (5 files)
- **Files:** `policy_proposal_engine.py`, `policy_proposal_read_driver.py`, `policy_proposal_write_driver.py`, `policies_proposals_query_engine.py`, `proposals_read_driver.py`
- **Classification:** `FACADE_PATTERN`
- **Reason:** Read/write separation with dedicated query engines

### 4. Rules (4 files)
- **Files:** `policy_rules_engine.py`, `policies_rules_query_engine.py`, `policy_rules_driver.py`, `policy_rules_read_driver.py`
- **Classification:** `FACADE_PATTERN`
- **Reason:** CRUD engine + query engine (L5) + CRUD driver + read driver (L6)

### 5. Facades (3 files)
- **Files:** `policies_facade.py`, `governance_facade.py`, `limits_facade.py`
- **Classification:** `FALSE_POSITIVE`
- **Reason:** Governance, policies, and limits are distinct subsystems

### 6. Recovery (3 files)
- **Files:** `recovery_evaluation_engine.py`, `recovery_matcher.py`, `recovery_write_driver.py`
- **Classification:** `L5_L6_SEPARATION`
- **Reason:** L5 decision-making, L6 pattern matching and persistence

---

## Domain Statistics

### File Distribution

| Layer | Total Files | Active Scripts | Init Files |
|-------|-------------|----------------|------------|
| L5 Engines | 63 | 62 | 1 |
| L6 Drivers | 15 | 14 | 1 |
| **Total** | **78** | **76** | **2** |

### Functional Group Distribution (L5)

| Group | Files | Percentage |
|-------|-------|-----------|
| DSL Compiler Chain | 11 | 17.7% |
| Policy CRUD | 9 | 14.5% |
| Execution Kernel | 7 | 11.3% |
| Enforcement & Prevention | 6 | 9.7% |
| Other Engines | 6 | 9.7% |
| Decision & Authority | 5 | 8.1% |
| Facades | 3 | 4.8% |
| Conflict & Graph | 3 | 4.8% |
| Recovery & Learning | 3 | 4.8% |
| Runtime & Commands | 3 | 4.8% |
| Simulation & Sandbox | 2 | 3.2% |

### Data Access Distribution (L6)

| Category | Files | Percentage |
|----------|-------|-----------|
| Policy Data Access | 4 | 28.6% |
| Proposal Data Access | 3 | 21.4% |
| Graph & Conflict | 3 | 21.4% |
| Recovery | 2 | 14.3% |
| Other Drivers | 2 | 14.3% |

---

## Key Architectural Patterns

### 1. Mandatory Execution Kernel (Single Choke Point)

**Pattern:** All policy execution MUST flow through `kernel.py`.

**Files:**
- `kernel.py` — The mandatory choke point
- `decorator.py` — Ergonomic wrapper (delegates to kernel)
- `engine.py` — Rule evaluation within kernel control

**Benefit:** Deterministic, auditable, governance-controlled policy execution.

### 2. DSL Compilation Pipeline

**Pattern:** Multi-stage transformation from DSL text to executable bytecode.

**Stages:**
1. Lexical analysis (tokenizer)
2. Parsing (parser + grammar)
3. AST construction (ast nodes)
4. Semantic validation (validator)
5. IR transformation (IR builder)
6. Bytecode compilation (IR compiler)
7. Interpretation (interpreter)

**Files:** 11 files in DSL Compiler Chain group.

### 3. CRUD + Query Separation

**Pattern:** Separate engines for write operations (CRUD) and read operations (queries).

**Examples:**
- `policy_rules_engine.py` (CRUD) + `policies_rules_query_engine.py` (queries)
- `policy_limits_engine.py` (CRUD) + `policies_limits_query_engine.py` (queries)
- `policy_proposal_engine.py` (CRUD) + `policies_proposals_query_engine.py` (queries)

**Benefit:** Clear separation of write and read responsibilities.

### 4. Facade Pattern

**Pattern:** Unified interfaces to complex subsystems.

**Examples:**
- `governance_facade.py` — Kill switch, degraded mode, conflicts
- `limits_facade.py` — Rate limits and quotas
- `policies_facade.py` — General policies (stubbed, pending HOC implementation)

**Benefit:** Simplified API surface for complex governance operations.

### 5. L5/L6 Separation

**Pattern:** Business logic in L5, data access in L6.

**Examples:**
- L5: `customer_policy_read_engine.py` (business logic) → L6: `policy_read_driver.py` (data access)
- L5: `recovery_evaluation_engine.py` (decisions) → L6: `recovery_matcher.py` (pattern matching), `recovery_write_driver.py` (persistence)

**Benefit:** Clean separation of concerns, testability.

---

## Cross-Domain Dependencies

### Outbound Dependencies (Policies → Other Domains)

| Target Domain | Purpose | Files |
|--------------|---------|-------|
| `logs` | Audit logging | V1, V2, V3 (via `audit_ledger`) |
| `incidents` | Recovery rules, lessons learned | V4, V5 |
| `integrations` | MCP tool mapping | `policy_mapper.py` |
| `account` | Customer scope resolution | `scope_resolver.py` |

**Note:** Dependencies V1-V5 were architecture violations (L5 → L6 cross-domain). All **RESOLVED** via PIN-504 (Phases 2 + 6): V1-V3 via AuditCoordinator injection, V4 via pure function extraction to `hoc_spine/schemas/recovery_decisions.py`, V5 via lazy import.

### Inbound Dependencies (Other Domains → Policies)

| Source Domain | Purpose | Target Files |
|--------------|---------|-------------|
| All domains | Policy enforcement | `prevention_engine.py`, `prevention_hook.py` |
| All domains | Rate limiting | `limits_facade.py` |
| All domains | Governance controls | `governance_facade.py` |
| Workers | Execution authorization | `worker_execution_command.py` |

---

## Critical Execution Paths

### 1. Policy Evaluation Path

```
External Request
  → L4 policies_handler.py (policies.enforcement)
  → L5 cus_enforcement_engine.py (stubbed, pending HOC implementation)
  → L5 kernel.py (mandatory choke point)
  → L5 engine.py (rule evaluation)
  → L6 policy_engine_driver.py (data access)
  → Database (policies table)
```

### 2. DSL Compilation Path

```
Customer DSL Input
  → L5 tokenizer.py (lexical analysis)
  → L5 dsl_parser.py (parsing)
  → L5 ast.py (AST construction)
  → L5 validator.py (semantic validation)
  → L5 ir_builder.py (AST → IR)
  → L5 ir_compiler.py (IR → bytecode)
  → L5 interpreter.py (execution)
```

### 3. Conflict Resolution Path

```
Policy Creation/Update
  → L5 policy_rules_engine.py (CRUD)
  → L5 policy_graph_engine.py (conflict detection)
  → L5 policy_conflict_resolver.py (pure logic resolution)
  → L6 optimizer_conflict_resolver.py (optimization with DB)
  → L6 policy_graph_driver.py (graph persistence)
```

### 4. Recovery Evaluation Path

```
Incident Detection
  → L5 recovery_evaluation_engine.py (decision-making)
  → L6 recovery_matcher.py (failure pattern matching)
  → L5 claim_decision_engine.py (claim approval/denial)
  → L6 recovery_write_driver.py (recovery persistence)
  → L5 lessons_engine.py (lessons learned creation)
```

### 5. Limit Simulation Path

```
Pre-Execution Check
  → L4 policies_handler.py (policies.simulate)
  → L5 limits_simulation_engine.py (stubbed, pending HOC implementation)
  → L5 limits_facade.py (rate limits facade)
  → L6 policy_engine_driver.py (limit data access)
  → Simulation Result (dry-run, no side effects)
```

---

## Domain Responsibilities

### Core Responsibilities

1. **Policy Lifecycle Management**
   - Policy creation, update, deletion
   - Policy versioning and snapshots
   - Policy proposals and approval workflows

2. **DSL Compilation & Execution**
   - PLang v2.0 parsing and compilation
   - AST construction and validation
   - IR transformation and bytecode generation
   - Deterministic policy interpretation

3. **Runtime Enforcement**
   - Real-time policy enforcement
   - Prevention hooks with content accuracy
   - Binding moment evaluation (when policies apply)
   - Phase-status invariant enforcement

4. **Conflict Resolution**
   - Policy conflict detection
   - Dependency graph analysis
   - Precedence-based arbitration
   - Optimization-based conflict resolution

5. **Rate Limiting & Quotas**
   - Rate limit enforcement
   - Quota tracking and enforcement
   - Pre-execution limit simulation
   - Limit derivation and calculation

6. **Governance & Control**
   - Kill switch (emergency shutdown)
   - Degraded mode management
   - Failure mode handling (fail-closed)
   - Override authority checking

7. **Recovery & Learning**
   - Recovery claim decisions
   - Failure pattern matching
   - Lessons learned creation and management
   - Learning proof generation (graduation gates)

8. **Decision Authority**
   - Policy evaluation decisions
   - Worker execution authorization
   - Eligibility gating
   - Claim approval/denial

---

## Testing & Validation

### Deterministic Execution

The `deterministic_engine.py` ensures that policy execution is reproducible and deterministic, critical for:
- Audit compliance
- Debugging and troubleshooting
- Regression testing
- Governance verification

### Content Accuracy Validation

The `content_accuracy.py` and `prevention_hook.py` enforce content accuracy checks:
- DSL syntax validation
- Semantic correctness
- Type safety
- Business rule compliance

### Sandbox Execution

The `sandbox_engine.py` provides isolated policy execution for:
- Testing new policies
- Simulating policy changes
- Dry-run evaluations
- Customer experimentation

---

## Security & Compliance

### Fail-Closed Behavior

The `failure_mode_handler.py` ensures fail-closed behavior:
- On error, deny access (do not permit)
- Log all failure events
- Escalate to governance facade
- Maintain audit trail

### Abuse Protection

The `protection_provider.py` implements Phase-7 abuse protection:
- Abuse detection and classification
- Mitigation strategies
- Rate limiting for suspicious activity
- Escalation to security team

### Audit Logging

Policies L5 engines log to `logs/L6_drivers/audit_ledger` (via architecture violations V1, V2, V3):
- Policy CRUD operations
- Enforcement decisions
- Conflict resolutions
- Recovery evaluations

**Note:** These direct L6 imports will be rewired through L4 orchestration.

---

## Phase-6 Architecture Alignment

### Multi-Tenant SaaS

The policies domain is fully aligned with Phase-6 multi-tenant SaaS architecture:
- Customer-scoped policies (via `scope_resolver.py`)
- Tenant isolation (via execution kernel)
- Shared policy infrastructure
- Per-customer policy customization

### Billing State Integration

The `state.py` defines Phase-6 billing states:
- Free tier policies
- Paid tier policies
- Enterprise tier policies
- Custom tier policies

### Plan Generation

The `plan.py` and `plan_generation_engine.py` support Phase-6 plan generation:
- Dynamic plan creation
- Limit derivation from plans
- Plan-based eligibility gating
- Upgrade/downgrade workflows

---

## Migration Status

### Legacy Disconnection (2026-01-31)

| Status | Description |
|--------|-------------|
| COMPLETE | All legacy imports disconnected |
| COMPLETE | Naming violations N1, N2 resolved |
| COMPLETE | Layer header corrections applied |
| STUBBED | `cus_enforcement_engine.py`, `limits_simulation_engine.py`, `policies_facade.py` |
| DEFERRED | Architecture violations V1-V5 (rewiring phase) |

### Pending HOC Implementation

The following stubbed files require HOC-native implementation:

1. **`cus_enforcement_engine.py`** — Customer enforcement engine
2. **`limits_simulation_engine.py`** — Pre-execution limit simulation
3. **`policies_facade.py`** — HOC policies facade

---

## Domain Lock Status

**Status:** LARGEST DOMAIN (77 files)
**Lock File:** `/root/agenticverz2.0/backend/app/hoc/cus/policies/*_DOMAIN_LOCK_FINAL.md` (if exists)

The policies domain is the **largest and most complex** domain in HOC, serving as the **governance control plane** for the entire system. All policy-related operations, enforcement, conflict resolution, and recovery decisions flow through this domain.

---

## References

### Related Domains

- **incidents** — Recovery rules, lessons learned (V4, V5 dependencies)
- **logs** — Audit logging (V1, V2, V3 dependencies)
- **integrations** — MCP tool mapping
- **account** — Customer scope resolution

### Key Architecture Documents

- `docs/architecture/hoc/HOC_LAYER_INVENTORY.csv` — Complete HOC layer inventory
- `scripts/ops/hoc_layer_inventory.py` — Inventory generation script
- `backend/app/hoc/cus/policies/*_DOMAIN_LOCK_FINAL.md` — Domain lock file (if exists)

### Literature Files

- `/root/agenticverz2.0/literature/hoc_domain/incidents/INCIDENTS_CANONICAL_SOFTWARE_LITERATURE.md`
- `/root/agenticverz2.0/literature/hoc_domain/activity/ACTIVITY_CANONICAL_SOFTWARE_LITERATURE.md`

---

## Appendix: Complete File Listing

### L5 Engines (62 active scripts)

**DSL Compiler Chain (11):**
1. `ast.py`
2. `compiler_parser.py`
3. `content_accuracy.py`
4. `dsl_parser.py`
5. `grammar.py`
6. `interpreter.py`
7. `ir_builder.py`
8. `ir_compiler.py`
9. `ir_nodes.py`
10. `tokenizer.py`
11. `validator.py`

**Execution Kernel (7):**
12. `kernel.py`
13. `engine.py`
14. `decorator.py`
15. `state.py`
16. `nodes.py`
17. `visitors.py`
18. `folds.py`

**Policy CRUD (9):**
19. `policy_rules_engine.py`
20. `policy_limits_engine.py`
21. `policy_proposal_engine.py`
22. `policies_rules_query_engine.py`
23. `policies_limits_query_engine.py`
24. `policies_proposals_query_engine.py`
25. `customer_policy_read_engine.py`
26. `policy_models.py`
27. `domain_bridge_capabilities.py` (NEW — PIN-508 Phase 2)

**Facades (3):**
28. `policies_facade.py`
29. `governance_facade.py`
30. `limits_facade.py`

**Enforcement & Prevention (6):**
31. `cus_enforcement_engine.py`
32. `prevention_engine.py`
33. `prevention_hook.py`
34. `protection_provider.py`
35. `binding_moment_enforcer.py`
36. `phase_status_invariants.py`

**Decision & Authority (5):**
37. `policy_command.py`
38. `worker_execution_command.py`
39. `claim_decision_engine.py`
40. `authority_checker.py`
41. `eligibility_engine.py`

**Conflict & Graph (3):**
42. `policy_conflict_resolver.py`
43. `policy_graph_engine.py`
44. `policy_mapper.py`

**Recovery & Learning (3):**
45. `recovery_evaluation_engine.py`
46. `lessons_engine.py`
47. `learning_proof_engine.py`

**Simulation & Sandbox (2):**
48. `limits_simulation_engine.py`
49. `sandbox_engine.py`

**Runtime & Commands (2):**
50. `runtime_command.py`
51. `policy_driver.py`

**M20 Policy Runtime (3):** — PIN-514 canonical location
52. `intent.py` — IntentEmitter, Intent, IntentPayload, IntentType
53. `deterministic_engine.py` — DeterministicEngine, ExecutionContext, ExecutionResult
54. `dag_executor.py` — DAGExecutor, StageResult, ExecutionTrace (NEW — PIN-514)

**Other Engines (8):**
55. `degraded_mode.py`
56. `failure_mode_handler.py`
57. `kill_switch.py`
58. `keys_shim.py`
59. `plan.py`
60. `plan_generation_engine.py`
61. `limits.py`
62. `snapshot_engine.py`

**Plus:** `__init__.py` (1)

### L6 Drivers (14 active scripts)

**Policy Data Access (4):**
1. `policy_read_driver.py`
2. `policy_engine_driver.py`
3. `policy_rules_driver.py`
4. `policy_rules_read_driver.py`

**Proposal Data Access (3):**
5. `policy_proposal_read_driver.py`
6. `policy_proposal_write_driver.py`
7. `proposals_read_driver.py`

**Graph & Conflict (3):**
8. `policy_graph_driver.py`
9. `arbitrator.py`
10. `optimizer_conflict_resolver.py`

**Recovery (2):**
11. `recovery_matcher.py`
12. `recovery_write_driver.py`

**Other Drivers (2):**
13. `scope_resolver.py`
14. `symbol_table.py`

**Plus:** `__init__.py` (1)

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat A: Dead Import Repointed (1)

| File | Old Import | New Import |
|------|-----------|------------|
| `adapters/founder_contract_review_adapter.py` | `app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine.ContractState` | `app.hoc.cus.hoc_spine.authority.contracts.contract_engine.ContractState` |

`cus/general/` was abolished per PIN-485. `ContractState` migrated to `hoc_spine/authority/contracts/` (confirmed 100% match per Phase 5 D690).

### Cat B: Stale Docstring Reference Corrected (1)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `failure_mode_handler.py` | `app.services.governance.profile: get_governance_config` | `app.hoc.cus.hoc_spine.authority.profile_policy_mode: get_governance_config` |

Active import (line 97) was already correct. Only the docstring Imports section was stale.

### Cat C: Existing TODO Rewire Stubs — No Action

3 files with 12 TODO rewire stubs (from consolidation PIN-495). Await Loop Model wiring.

### Cat D: L2→L5 Bypass Violations (5 — DOCUMENT ONLY)

| L2 File | Line(s) | Import | Domains Reached |
|---------|---------|--------|-----------------|
| `recovery/recovery.py` | 34, 35 | `policies.L6_drivers.recovery_matcher`, `recovery_write_driver` | policies L6 |
| `recovery/recovery_ingest.py` | 50 | `policies.L6_drivers.recovery_write_driver` | policies L6 |
| `policies/workers.py` | 1280, 1290 | ~~`policies.L6_drivers.recovery_matcher`~~ | **RESOLVED** (PIN-504 Phase 6): Uses L5 `RecoveryEvaluationEngine` |

**Status:** `workers.py` resolved. Recovery domain files (`recovery.py`, `recovery_ingest.py`) deferred to PIN-505.

### Cat E: Cross-Domain Violations (Inbound — 2 → 1 — PARTIALLY RESOLVED)

| Source File | Source Domain | Import Target | Status |
|------------|--------------|--------------|--------|
| `incidents/L5_engines/incident_engine.py` | incidents | ~~`policies.L5_engines.lessons_engine`~~ | **RESOLVED** (PIN-504 Phase 6): LessonsCoordinator (L4) injected |
| `integrations/adapters/customer_policies_adapter.py` | integrations | `policies.L5_engines.customer_policy_read_engine` | DEFERRED |

### Tally

36/36 checks PASS (32 consolidation + 4 cleansing).

---

**END OF POLICIES DOMAIN CANONICAL SOFTWARE LITERATURE**

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-507 Law 0 Remediation (2026-02-01)

**Legacy `app/services/policy/__init__.py`:** Removed stale re-export of `LessonsLearnedEngine` / `get_lessons_learned_engine` from disconnected shim `lessons_engine.py`. The class was moved to HOC `policies/L5_engines/lessons_engine.py` during PIN-468.

**Legacy `app/services/limits/` (3 files):** `policy_limits_service.py`, `policy_rules_service.py`, and `app/services/policy_proposal.py` — import of `AuditLedgerServiceAsync` rewired from abolished `app.services.logs.audit_ledger_service_async` → `app.hoc.cus.logs.L6_drivers.audit_ledger_driver`. Transitional `services→hoc` dependencies with comments at import sites.

**Legacy `app/api/policy_layer.py` and `app/services/governance/facade.py`:** Import of `get_policy_facade` rewired from non-existent `app.services.policy.facade` → `app.services.policy` (package-level `__init__` re-export). The file was renamed to `policy_driver.py` during consolidation.

## PIN-508 DomainBridge Capabilities Integration (2026-02-01)

### Phase 2: Cross-Domain Capability Protocols

**New File (L5 Schemas):**
- `domain_bridge_capabilities.py` — Defines capability protocols for cross-domain access via DomainBridge:
  - `LessonsQueryCapability` — Capability for querying lessons from incidents domain
  - `LimitsQueryCapability` — Capability for querying limits information
  - `PolicyLimitsCapability` — Capability for policy limit operations

### Phase 2A: Factory Pattern Enhancements

**Modified File — `lessons_engine.py` (L5 Engines):**
- Factory now accepts `driver` parameter for capability injection via DomainBridge
- Enables cross-domain lessons learned queries from incidents domain

### Phase 2B: Query Engine Capability Injection

**Modified Files:**
- `policies_limits_query_engine.py` — Factory now accepts `driver` parameter for capability injection
- Enables cross-domain limits query operations via DomainBridge

### Phase 2C: Constructor Parameter Updates

**Modified File — `policy_limits_engine.py` (L5 Engines):**
- Constructor now accepts `driver` parameter for capability injection
- Supports DomainBridge-driven policy limit operations

### Phase 5: Stub Engine Markings

**Files marked as STUB_ENGINE (methods raise NotImplementedError):**
- `cus_enforcement_engine.py` — Customer enforcement engine (PIN-508 Phase 5)
- `limits_simulation_engine.py` — Pre-execution limit simulation (PIN-508 Phase 5)
- `policies_facade.py` — HOC policies facade; 13 methods raise NotImplementedError (PIN-508 Phase 5)

These files maintain backward compatibility while explicitly signaling incomplete implementation. Full HOC-native implementations pending DomainBridge integration completion.

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-510 Phase 1B — Lazy Fallback Assertion Guards (2026-02-01)

Two policies L5 engines now have assertion-guarded legacy fallbacks:

| Engine | Factory/Constructor | Guard |
|--------|-------------------|-------|
| `policies_limits_query_engine.py` | `get_limits_query_engine()` | `HOC_REQUIRE_L4_INJECTION` env flag |
| `policy_limits_engine.py` | `PolicyLimitsEngine.__init__()` | `HOC_REQUIRE_L4_INJECTION` env flag |

**Behavior:**
- `HOC_REQUIRE_L4_INJECTION` unset: fallback works, logs warning
- `HOC_REQUIRE_L4_INJECTION=1`: raises RuntimeError (enforced in CI/prod)
- After all callers migrate: remove fallback code entirely

Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-512 Category C — Unwired L6 Driver Wiring (2026-02-02)

### int/policies: limit_enforcer.py — Real Enforcement (P1)

- Rewired from allow-all stub to real enforcement via LimitsReadDriver (L6) + RateLimiter (Redis token bucket)
- Cost checks: queries BUDGET limits, blocks if exceeded
- Token checks: queries RATE/TOKENS_* limits, blocks if exceeded
- Rate checks: uses Redis token bucket via `rate_limiter.allow()`
- Fail-closed: if session unavailable or driver errors → DENY. 174→286 LOC.

### int/policies: usage_monitor.py — DB Persistence (P2)

- Rewired from log-only to DB persistence via new `usage_record_driver.py` (L6)
- Records 3 meters per step: cost_cents, tokens_used, step_latency_ms
- Fire-and-forget: all in try/except, logs warnings on failure. 141→177 LOC.

### int/policies: usage_record_driver.py — NEW L6 Driver (P2)

- **Path:** `app/hoc/int/policies/drivers/usage_record_driver.py`
- **Role:** Persists usage records to `usage_records` table via `UsageRecord` model
- **Methods:** `insert_usage()` — session.flush() (L6 never commits). 88 LOC.

## PIN-514 Runtime Convergence (2026-02-03)

**M20 Policy Runtime consolidated to canonical L5_engines location per HOC Topology V2.0.0.**

### New L5 Engine: dag_executor.py

- **Path:** `app/hoc/cus/policies/L5_engines/dag_executor.py`
- **Role:** DAG-based parallel policy executor for M20 runtime
- **Exports:** `DAGExecutor`, `StageResult`, `ExecutionTrace`
- **Key methods:**
  - `execute()` — Execute policies in topological order
  - `_execute_stage()` — Parallel execution within stages
  - `get_execution_plan()` — Get execution plan for a module
  - `visualize_plan()` — ASCII visualization of DAG
- **Callers:** L4 dag_executor, workers, test_m20_runtime
- **LOC:** 316

### Existing L5 Engines Relocated

| Engine | Exports | Role |
|--------|---------|------|
| `intent.py` | IntentEmitter, Intent, IntentPayload, IntentType | M18/M19 intent emission with fail-closed validation |
| `deterministic_engine.py` | DeterministicEngine, ExecutionContext, ExecutionResult | Policy IR execution with governance validation |

### Deleted: app/policy/runtime/

Non-canonical location removed. All imports updated to use `app.hoc.cus.policies.L5_engines.*`.

### Import Path Migration

| File | Description |
|------|-------------|
| `hoc/int/integrations/engines/worker.py` | M20 runtime import updated |
| `workers/business_builder/worker.py` | M20 runtime import updated |
| `api/workers.py` | Moat status check updated |
| `hoc/api/cus/policies/workers.py` | Moat status check updated |
| `hoc/cus/hoc_spine/drivers/dag_executor.py` | L4 driver import updated |
| `tests/test_m20_runtime.py` | Test imports updated |

### Wiring Contract

New contract created: `docs/contracts/POLICY_RUNTIME_WIRING_CONTRACT.md`

Documents:
- 3 injection points (intent_validator, emission_sink, policy_validator)
- Intent type classification (enforcement vs observability)
- Fail-closed semantics for enforcement intents
- Environment wiring matrix (tests → staging → production)

**Canonical import:** `from app.hoc.cus.policies.L5_engines.intent import IntentEmitter`

Reference: `docs/memory-pins/PIN-514-runtime-convergence.md`, `docs/memory-pins/PIN-515-production-wiring-contract.md`

## PIN-519 System Run Introspection (2026-02-03)

### New L6 Driver: policy_enforcement_driver.py

**Purpose:** Read-only async queries for policy enforcement records associated with runs.

| Method | Purpose |
|--------|---------|
| `fetch_policy_evaluations_for_run(tenant_id, run_id, max_results)` | Fetch all policy evaluations for a run |
| `fetch_enforcement_by_id(tenant_id, enforcement_id)` | Fetch single enforcement record |

**Returns:** List of enforcement records with rule details (enforcement_id, rule_id, action_taken, triggered_at, details, rule_name, rule_type, severity)

**Factory:** `get_policy_enforcement_read_driver(session)`

### PoliciesBridge Extension

**New Capability:**

| Capability | Purpose | Consumer |
|------------|---------|----------|
| `policy_evaluations_capability(session)` | Returns PolicyEnforcementReadDriver for run-scoped queries | RunEvidenceCoordinator |

**Usage:**
```python
policies_bridge = get_policies_bridge()
reader = policies_bridge.policy_evaluations_capability(session)
evaluations = await reader.fetch_policy_evaluations_for_run(tenant_id, run_id)
```

## PIN-520 L4 Injection Pattern (Iter3.1)

**Date:** 2026-02-06
**Reference:** PIN-520, TODO_ITER3.1.md

### L5 Purity Achieved

L5 engines in the policies domain no longer import from `hoc_spine.orchestrator` or `hoc_spine.authority`. Dependencies are now injected by L4 callers.

### Changes Made

| File | Violation Removed | Pattern Applied |
|------|-------------------|-----------------|
| `governance_facade.py` | runtime_switch imports (5 locations) | Constructor injection via ModuleType |
| `failure_mode_handler.py` | profile_policy_mode import | Module-level setter injection |
| `eligibility_engine.py` | cross-domain type coupling | Imports from account/L5_schemas (schema-only types) |

### L4 Bridge Capabilities Added (policies_bridge.py)

| Capability | Purpose | Injected Into |
|------------|---------|---------------|
| `governance_runtime_capability()` | Runtime switch module | GovernanceFacade |
| `governance_config_capability()` | Governance config getter | failure_mode_handler |

### Adapter Protocol Added (founder_contract_review_adapter.py)

| Protocol | Purpose |
|----------|---------|
| `ContractStatePort` | L2 adapter receives contract state via Protocol, not direct L4 import |

### Injection Point

```python
# L4 caller pattern for governance facade
bridge = get_policies_engine_bridge()
facade = GovernanceFacade(runtime_module=bridge.governance_runtime_capability())

# L4 caller pattern for failure mode handler
from app.hoc.cus.policies.L5_engines.failure_mode_handler import set_governance_config_getter
bridge = get_policies_engine_bridge()
set_governance_config_getter(bridge.governance_config_capability())
```

### Evidence

```bash
# Zero hoc_spine.orchestrator imports in L5 engines
rg "from app\\.hoc\\.cus\\.hoc_spine\\.orchestrator" app/hoc/cus/policies/L5_engines/
# Result: No matches found

# Zero hoc_spine.authority imports in adapters
rg "from app\\.hoc\\.cus\\.hoc_spine\\.authority" app/hoc/cus/policies/adapters/
# Result: No matches found
```
