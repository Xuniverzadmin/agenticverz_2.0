# Transaction Authority Semantic Contract

**Status:** ✅ APPROVED — FROZEN
**Phase:** 3.5 (CLOSED 2025-12-30)
**Approved:** 2025-12-30
**Created:** 2025-12-30
**Predecessor:** RECOVERY_SEMANTIC_CONTRACT.md

---

## Purpose

This contract defines the **semantic meaning** of transaction authority in AOS.

**Core Principle:**
> Transaction authority is not a pattern. Transaction authority is **WHO has the right to commit state changes to the database, under what conditions, and why**.

**Critical Framing:**
> The 297 WRITE_OUTSIDE_WRITE_SERVICE signals are NOT bugs. They are **unclassified authority**. This contract classifies them.

---

## What This Contract Defines

| Defines | Does NOT Define |
|---------|-----------------|
| WHO may mutate WHAT | How to reduce signal counts |
| Transaction boundary ownership semantically | Code refactoring patterns |
| Exceptions to write conventions with justification | CI enforcement rules |
| Classification of existing observations | Future migration paths |

---

## Semantic Axes (4 Axes)

### Axis 1: Authority Classes (WHO)

**Question:** Who has the right to commit database state?

| Authority Class | Layer | Files | Semantic Meaning |
|----------------|-------|-------|------------------|
| Worker Self-Authority | L5 | 5 | Workers own their lifecycle state transitions |
| Write Service Delegation | L4 | 7 | APIs delegate writes to domain write services |
| Integration Self-Authority | L4 | 4 | Integration boundaries are self-complete execution contexts |
| Agent Execution Authority | L4/L5 | 12 | Multi-agent system has its own execution domain |
| System Bootstrap Authority | L7 | 3 | Bootstrap is pre-system, administrative context |
| Platform Substrate Authority | L6 | 5 | Platform-level state management |
| Domain Engine Self-Authority | L4 | 15 | Domain engines with self-contained transaction scope |
| Cost Simulation Authority | L4/L5 | 4 | Cost simulation has its own execution domain |
| Job Authority | L5 | 2 | Background jobs own their execution transactions |
| Budget Authority | L4 | 1 | Budget tracking is a cross-cutting concern |
| API Self-Authority | L2 | 4 | Some APIs own specific transaction scopes (requires examination) |

### Axis 2: Transaction Boundary Ownership (WHAT)

**Question:** What state does each authority class own?

| Authority Class | Owns | Cannot Touch |
|----------------|------|--------------|
| Worker Self-Authority | Run state (queued→running→terminal), outbox events, recovery execution | Policy definitions, agent configuration |
| Write Service Delegation | Entity CRUD delegated from APIs | Run state, worker state, integration state |
| Integration Self-Authority | Integration artifacts, loop events, bridge state | Core run execution, API responses |
| Agent Execution Authority | Agent jobs, items, credits, messages, registry | Core worker lifecycle, policy enforcement |
| System Bootstrap Authority | Initial agent/run creation, system setup | Runtime execution, policy evolution |
| Platform Substrate Authority | Tenants, auth state, feature flags, DB helpers | Business entities, execution state |
| Domain Engine Self-Authority | Domain-specific entities (incidents, patterns, predictions) | Cross-domain state, worker lifecycle |
| Cost Simulation Authority | Cost alerts, provenance, circuit breaker state | Policy enforcement, run completion |
| Job Authority | Job artifacts, storage state, graduation state | Live run execution, API responses |
| Budget Authority | Budget ledger entries | Run lifecycle, policy definitions |
| API Self-Authority | Specific API-scoped entities (policy, traces, integrations) | Worker state, other API domains |

### Axis 3: Transaction Scope Semantics (WHEN)

**Question:** When is each authority class permitted to commit?

| Authority Class | Commit Trigger | Scope Boundary |
|----------------|----------------|----------------|
| Worker Self-Authority | Run lifecycle transition | Per-run, per-claim |
| Write Service Delegation | API request completion | Per-request |
| Integration Self-Authority | Integration event processing | Per-event |
| Agent Execution Authority | Job item processing | Per-item |
| System Bootstrap Authority | CLI command, startup | Per-command |
| Platform Substrate Authority | Auth/tenant operation | Per-operation |
| Domain Engine Self-Authority | Domain event processing | Per-event |
| Cost Simulation Authority | Cost event, alert | Per-event |
| Job Authority | Background job completion | Per-job |
| Budget Authority | Cost incurred | Per-cost-event |
| API Self-Authority | API endpoint completion | Per-request |

### Axis 4: Guarantees (WHAT IS PROMISED)

**Question:** What guarantees does each authority class provide?

| Authority Class | Guarantee | Mechanism |
|----------------|-----------|-----------|
| Worker Self-Authority | Exactly-once state transition | `UPDATE ... WHERE status = old RETURNING` |
| Write Service Delegation | Request-scoped consistency | Single transaction per request |
| Integration Self-Authority | At-least-once event processing | Retry with idempotency |
| Agent Execution Authority | Exactly-once item processing | `FOR UPDATE SKIP LOCKED` |
| System Bootstrap Authority | Idempotent initialization | Check-before-create |
| Platform Substrate Authority | Auth consistency | Session-scoped transactions |
| Domain Engine Self-Authority | Domain consistency | Per-domain invariants |
| Cost Simulation Authority | Cost accuracy | Provenance tracking |
| Job Authority | Job completion tracking | Status transitions |
| Budget Authority | Budget accuracy | Append-only ledger |
| API Self-Authority | Request consistency | Per-request transaction |

---

## Authority Class File Inventory

### 1. Worker Self-Authority (L5) — 5 files

Workers own their lifecycle state transitions. This is **semantically correct** per Phase 3.3 (Worker Lifecycle Contract).

| File | Authority Header | Justification |
|------|------------------|---------------|
| `worker/runner.py` | `Authority: Run state mutation (pending → running → succeeded/failed/halted)` | Worker owns run lifecycle |
| `worker/pool.py` | `Authority: Run claim (pending → running via ThreadPool dispatch)` | Pool owns dispatch |
| `worker/outbox_processor.py` | Implied | Outbox owns delivery state |
| `worker/recovery_evaluator.py` | Implied | Recovery owns evaluation state |
| `worker/recovery_claim_worker.py` | Implied | Recovery owns claim state |

**Convention Exception:** Workers are EXEMPT from write service delegation because they own their execution context.

### 2. Write Service Delegation (L4) — 7 files

APIs delegate writes to domain write services. This is the **standard pattern** for L2→L4 delegation.

| File | Purpose | Callers |
|------|---------|---------|
| `services/guard_write_service.py` | Guard entity writes | api/guard.py |
| `services/user_write_service.py` | User entity writes | api/users.py |
| `services/cost_write_service.py` | Cost entity writes | api/cost.py |
| `services/ops_write_service.py` | Ops entity writes | api/ops.py |
| `services/founder_action_write_service.py` | Founder action writes | api/founder.py |
| `services/worker_write_service_async.py` | Worker entity writes (async) | api/workers.py |
| `services/recovery_write_service.py` | Recovery entity writes | api/recovery.py |

**Convention:** These are the CANONICAL write services. They own the commit.

### 3. Integration Self-Authority (L4) — 4 files

Integrations are self-complete execution contexts with their own transaction boundaries.

| File | Authority | Justification |
|------|-----------|---------------|
| `integrations/bridges.py` | Loop event processing | Integration boundaries are self-complete |
| `integrations/dispatcher.py` | Integration dispatch | Event-driven execution |
| `integrations/cost_snapshots.py` | Cost snapshot capture | Periodic self-contained execution |
| `integrations/graduation_engine.py` | Graduation processing | Self-contained evaluation |

**Convention Exception:** Integrations are EXEMPT from write service delegation because they are external boundaries.

### 4. Agent Execution Authority (L4/L5) — 12 files

The M12 multi-agent system has its own execution domain.

| File | Authority | Justification |
|------|-----------|---------------|
| `agents/services/worker_service.py` | Item claiming | `FOR UPDATE SKIP LOCKED` pattern |
| `agents/services/job_service.py` | Job lifecycle | Job state ownership |
| `agents/services/credit_service.py` | Credit ledger | Credit transactions |
| `agents/services/message_service.py` | Message persistence | Message state |
| `agents/services/registry_service.py` | Agent registry | Registration state |
| `agents/services/governance_service.py` | Governance state | Policy enforcement state |
| `agents/services/invoke_audit_service.py` | Audit records | Audit trail |
| `agents/sba/service.py` | SBA execution | Agent execution |
| `agents/skills/agent_invoke.py` | Skill invocation | Execution state |
| `agents/skills/llm_invoke_governed.py` | LLM invocation | Governed execution |
| `skills/base.py` | Base skill execution | Skill state |

**Convention Exception:** Agent system is EXEMPT because M12 established a separate execution domain.

### 5. System Bootstrap Authority (L7) — 3 files

Bootstrap operations are pre-system administrative contexts.

| File | Authority | Justification |
|------|-----------|---------------|
| `cli.py` | CLI commands | Administrative execution |
| `main.py` | Startup initialization | System bootstrap |
| `db.py` | Schema/data bootstrap | Database initialization |

**Convention Exception:** Bootstrap is EXEMPT because it is pre-runtime.

### 6. Platform Substrate Authority (L6) — 5 files

Platform-level state management.

| File | Authority | Justification |
|------|-----------|---------------|
| `services/tenant_service.py` | Tenant state | Multi-tenant foundation |
| `auth/rbac_engine.py` | RBAC state | Authorization foundation |
| `auth/tenant_auth.py` | Tenant auth | Auth state |
| `config/flag_sync.py` | Feature flags | Configuration state |
| `utils/db_helpers.py` | DB utilities | Infrastructure support |

**Convention Exception:** Platform is EXEMPT because it is foundational.

### 7. Domain Engine Self-Authority (L4) — 15 files

Domain engines with self-contained transaction scopes.

| File | Authority | Justification |
|------|-----------|---------------|
| `services/incident_aggregator.py` | Incident aggregation | Domain consistency |
| `services/pattern_detection.py` | Pattern detection | Domain consistency |
| `services/prediction.py` | Predictions | Domain consistency |
| `services/policy_proposal.py` | Policy proposals | Domain consistency |
| `services/policy_violation_service.py` | Violations | Domain consistency |
| `services/recovery_matcher.py` | Recovery matching | Domain consistency |
| `services/orphan_recovery.py` | Orphan recovery | Domain consistency |
| `services/llm_failure_service.py` | LLM failures | Domain consistency |
| `services/cost_anomaly_detector.py` | Cost anomalies | Domain consistency |
| `services/worker_registry_service.py` | Worker registry | Domain consistency |
| `runtime/failure_catalog.py` | Failure catalog | Domain consistency |
| `workflow/checkpoint.py` | Checkpoints | Domain consistency |
| `tasks/recovery_queue_stream.py` | Recovery queue | Domain consistency |
| `memory/store.py` | Memory storage | Domain consistency |
| `memory/memory_service.py` | Memory service | Domain consistency |
| `memory/vector_store.py` | Vector storage | Domain consistency |

**Convention Observation:** These services do not have API callers—they are invoked by workers or other services. They own their domain.

### 8. Cost Simulation Authority (L4/L5) — 4 files

Cost simulation has its own execution domain.

| File | Authority | Justification |
|------|-----------|---------------|
| `costsim/circuit_breaker.py` | Circuit breaker state | Cost protection |
| `costsim/circuit_breaker_async.py` | Async circuit breaker | Cost protection |
| `costsim/provenance_async.py` | Cost provenance | Audit trail |
| `costsim/alert_worker.py` | Cost alerts | Alerting domain |

**Convention Exception:** Cost simulation is EXEMPT because it is a self-contained subsystem.

### 9. Job Authority (L5) — 2 files

Background jobs own their execution transactions.

| File | Authority | Justification |
|------|-----------|---------------|
| `jobs/storage.py` | Storage jobs | Job execution |
| `jobs/graduation_evaluator.py` | Graduation jobs | Job execution |

**Convention Exception:** Jobs are EXEMPT because they are background execution contexts.

### 10. Budget Authority (L4) — 1 file

Budget tracking is a cross-cutting concern.

| File | Authority | Justification |
|------|-----------|---------------|
| `utils/budget_tracker.py` | Budget ledger | Cost tracking |

**Convention Observation:** Budget is cross-cutting but has well-defined scope.

### 11. API Self-Authority (L2) — 4 files (Requires Examination)

Some APIs have direct writes. These require examination for semantic justification.

| File | Observation | Status |
|------|-------------|--------|
| `api/policy.py` | Direct policy writes | NEEDS CLASSIFICATION |
| `api/traces.py` | Direct trace writes | NEEDS CLASSIFICATION |
| `api/integration.py` | Direct integration writes | NEEDS CLASSIFICATION |
| `api/v1_proxy.py` | Proxy writes | NEEDS CLASSIFICATION |

**Note:** These 4 files represent the only L2 files with direct writes. They may be:
- Justified exceptions (specific transaction scope requirements)
- Candidates for write service extraction (Phase 2B continuation)

This contract does NOT recommend action—only classification.

---

## Classification of WRITE_OUTSIDE_WRITE_SERVICE Observations

### Summary Statistics

| Authority Class | File Count | Signal Count (Est.) | Classification |
|----------------|------------|---------------------|----------------|
| Worker Self-Authority | 5 | ~25 | JUSTIFIED EXCEPTION |
| Write Service Delegation | 7 | 0 | COMPLIANT (not flagged) |
| Integration Self-Authority | 4 | ~30 | JUSTIFIED EXCEPTION |
| Agent Execution Authority | 12 | ~60 | JUSTIFIED EXCEPTION |
| System Bootstrap Authority | 3 | ~18 | JUSTIFIED EXCEPTION |
| Platform Substrate Authority | 5 | ~25 | JUSTIFIED EXCEPTION |
| Domain Engine Self-Authority | 15 | ~75 | JUSTIFIED EXCEPTION |
| Cost Simulation Authority | 4 | ~25 | JUSTIFIED EXCEPTION |
| Job Authority | 2 | ~10 | JUSTIFIED EXCEPTION |
| Budget Authority | 1 | ~5 | JUSTIFIED EXCEPTION |
| API Self-Authority | 4 | ~24 | NEEDS EXAMINATION |

**Total:** 297 signals across 64 files

### Classification Breakdown

**JUSTIFIED EXCEPTION (60 files, ~273 signals):**
- Workers, integrations, agents, bootstrap, platform, domain engines, jobs, budget
- These have semantic authority to own their transactions
- The write service pattern does NOT apply to them

**NEEDS EXAMINATION (4 files, ~24 signals):**
- api/policy.py, api/traces.py, api/integration.py, api/v1_proxy.py
- These are L2 files with direct writes
- May be justified or may be candidates for extraction

### The Semantic Truth

**The 297 signals break down as:**

| Category | Signals | Meaning |
|----------|---------|---------|
| Worker Authority | ~25 | Workers own their lifecycle (Phase 3.3) |
| Domain Authority | ~150 | Domain engines own their domains |
| External Boundaries | ~60 | Integrations, agents, jobs are self-complete |
| Platform Foundation | ~25 | Platform is foundational |
| Bootstrap | ~18 | Bootstrap is pre-runtime |
| Unclassified API | ~24 | Needs examination |

---

## Relationship to Previous Phases

### Phase 3.3: Worker Lifecycle Semantics

**Connection:** Phase 3.3 established that workers own their lifecycle states.

**Authority Transfer:**
- Worker Self-Authority is **confirmed** by Phase 3.3
- `Authority:` header in worker files is the semantic declaration
- Workers are EXEMPT from write service pattern

### Phase 3.4: Recovery Semantics

**Connection:** Phase 3.4 established that recovery has its own authority structure.

**Authority Transfer:**
- RecoveryClaimWorker owns candidate claiming
- RecoveryEvaluator owns suggestion generation
- RecoveryMatcher owns pattern matching
- These are classified under Worker Self-Authority and Domain Engine Self-Authority

### Transaction Authority vs Recovery Authority

| Phase 3.4 Authority | Phase 3.5 Classification |
|---------------------|-------------------------|
| RecoveryClaimWorker | Worker Self-Authority |
| RecoveryEvaluator | Worker Self-Authority |
| RecoveryMatcher | Domain Engine Self-Authority |
| RecoveryRuleEngine | Domain Engine Self-Authority |
| OrphanRecovery | Domain Engine Self-Authority |
| RecoveryWriteService | Write Service Delegation |

---

## Prohibitions

### P1: No Unclassified Authority

Every file with DB writes MUST have a classified authority.

**Current State:** 60/64 files classified with justification. 4 files need examination.

### P2: No Authority Leakage

Authority classes MUST NOT exceed their boundary.

| Authority Class | Cannot Write To |
|----------------|-----------------|
| Worker Self-Authority | Policy definitions, agent configuration |
| Domain Engine Self-Authority | Other domains, worker lifecycle |
| API Self-Authority | Worker state, other API domains |

### P3: No Silent Authority Expansion

New files with DB writes MUST declare their authority class.

**Enforcement:** Semantic Auditor will flag WRITE_OUTSIDE_WRITE_SERVICE for new files.

---

## Invariants

### TI-1: Authority Declaration

Files with DB writes SHOULD have an `Authority:` header or be classified in this contract.

### TI-2: Transaction Scope Consistency

Each authority class MUST maintain consistent transaction scope (per-run, per-request, per-event, etc.).

### TI-3: Write Service Pattern Applicability

The write service pattern applies ONLY to L2→L4 delegation. It does NOT apply to:
- Workers (L5)
- Integrations (external boundaries)
- Bootstrap (pre-runtime)
- Platform (foundational)

---

## Ambiguities Resolved

### Ambiguity 1: Why are 297 signals not bugs?

**Resolution:** Because the write service pattern is a convention for L2→L4 delegation, not a universal rule.

Workers, integrations, domain engines, and platform services have semantic authority to own their transactions.

### Ambiguity 2: What should happen to these signals?

**Resolution:** Nothing. They are classified authority, not violations.

The Semantic Auditor emits observations. Observations become knowledge through classification.

### Ambiguity 3: Who owns the transaction boundary?

**Resolution:** The authority class owns it.

- For APIs: Write Service owns the commit
- For Workers: Worker owns the commit
- For Domain Engines: Engine owns the commit

### Ambiguity 4: Should we "fix" the code to reduce signals?

**Resolution:** No. Phase 3.5 is about classification, not enforcement.

The signals are correct. The classification makes them meaningful.

---

## File Inventory Summary

| Authority Class | Files | Layer | Pattern |
|----------------|-------|-------|---------|
| Worker Self-Authority | 5 | L5 | Self-owned |
| Write Service Delegation | 7 | L4 | API delegation |
| Integration Self-Authority | 4 | L4 | Self-owned |
| Agent Execution Authority | 12 | L4/L5 | Self-owned |
| System Bootstrap Authority | 3 | L7 | Self-owned |
| Platform Substrate Authority | 5 | L6 | Self-owned |
| Domain Engine Self-Authority | 15 | L4 | Self-owned |
| Cost Simulation Authority | 4 | L4/L5 | Self-owned |
| Job Authority | 2 | L5 | Self-owned |
| Budget Authority | 1 | L4 | Self-owned |
| API Self-Authority | 4 | L2 | Needs examination |

**Total:** 64 files with DB writes, 60 classified, 4 pending examination.

---

## References

- WORKER_LIFECYCLE_SEMANTIC_CONTRACT.md: Worker lifecycle and authority
- RECOVERY_SEMANTIC_CONTRACT.md: Recovery authority structure
- EXECUTION_SEMANTIC_CONTRACT.md: Execution model guarantees
- PIN-250: Phase 2B Write Service Extraction
- PIN-251: Phase 3 Semantic Alignment
- docs/reports/SEMANTIC_AUDIT_REPORT.md: 297 WRITE_OUTSIDE_WRITE_SERVICE signals

---

## SSA Results (Semantic Stability Assertion)

### Files Verified

| File | Authority Class | Header Present | SSA Result |
|------|-----------------|----------------|------------|
| `worker/runner.py` | Worker Self-Authority | YES (`Authority: Run state mutation`) | MATCH |
| `worker/pool.py` | Worker Self-Authority | YES (`Authority: Run claim`) | MATCH |
| `services/worker_write_service_async.py` | Write Service Delegation | YES (Layer: L4, Role: DB write delegation) | MATCH |
| `services/incident_aggregator.py` | Domain Engine Self-Authority | YES (Layer: L4 Domain Engine) | MATCH |
| `services/tenant_service.py` | Platform Substrate Authority | YES (Layer: L6 Platform Substrate) | MATCH |
| `api/policy.py` | API Self-Authority | NO (docstring only) | NEEDS HEADER |
| `api/traces.py` | API Self-Authority | NO (docstring only) | NEEDS HEADER |

### SSA Summary

- **5/7 MATCH**: Files have semantic headers matching their authority class
- **2/7 NEEDS HEADER**: API files lack semantic headers (classification correct, header missing)

**Note:** The 2 files needing headers are among the 4 API files flagged as "NEEDS EXAMINATION". The lack of semantic headers is consistent with the observation.

---

## Session Handoff

**Status:** ✅ APPROVED — FROZEN (2025-12-30)

> **PHASE 3.5 CLOSED:** This contract is now frozen and immutable.
> Transaction authority semantics are locked. Future changes require formal amendment process.

**Ratification Sequence (COMPLETE):**
1. ✅ Discovered 11 authority classes
2. ✅ Classified 64 files with DB writes
3. ✅ Justified 60 files as convention exceptions
4. ✅ Identified 4 files needing examination (intentionally flagged, not forced)
5. ✅ Documented relationship to Phase 3.3 and 3.4
6. ✅ SSA executed: 5/7 MATCH, 2 need headers (consistent with classification)
7. ✅ Final review: Scope constraint honored
8. ✅ APPROVED and FROZEN

**Approval Notes:**
- WRITE_OUTSIDE_WRITE_SERVICE signals are now semantically classified
- write-service pattern applies only to L2→L4 delegation
- Workers, recovery, agents, platform code are self-authoritative by design
- Unresolved API self-authority files remain intentionally flagged

**Scope Constraint Honored:**
- ✅ Defined WHO may mutate WHAT
- ✅ Defined transaction boundary ownership semantically
- ✅ Named and justified exceptions to write conventions
- ✅ Classified WRITE_OUTSIDE_WRITE_SERVICE observations
- ✅ Did NOT propose code changes
- ✅ Did NOT recommend signal reduction
- ✅ Did NOT add enforcement rules

---

## Phase 3 Complete

> **Phase 3 is COMPLETE. PRODUCT work is UNLOCKED.**

| Phase | Name | Status |
|-------|------|--------|
| 3.1 | Auth Semantics | CLOSED |
| 3.2 | Execution Model Semantics | CLOSED |
| 3.3 | Worker Lifecycle Semantics | CLOSED |
| 3.4 | Recovery & Consistency Semantics | CLOSED |
| 3.5 | Transaction Authority Semantics | **CLOSED** |

All semantic pillars are now defined. The system has explicit meaning.
