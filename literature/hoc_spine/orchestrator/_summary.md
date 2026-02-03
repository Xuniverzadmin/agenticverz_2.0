# Orchestrator — Folder Summary

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/`
**Layer:** L4
**Scripts:** 12 + 3 coordinators

---

## 1. Purpose

Sole execution entry point from L2. Owns transaction boundaries, operation resolution, and execution order. No code runs without going through here.

## 2. What Belongs Here

- Operation dispatcher (what runs)
- Cross-domain context assembly
- Start / end / phase transitions
- Job state machines and execution tracking

## 3. What Must NOT Be Here

- Execute domain business logic (that's L5)
- Own persistence (that's L6/L7)
- Import L5 engines directly (use protocols)

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [constraint_checker.py](constraint_checker.md) | Module: constraint_checker | Forbidden | no | OK |
| [execution.py](execution.md) | Module: execution | Forbidden | no | OK |
| [governance_orchestrator.py](governance_orchestrator.md) | Part-2 Governance Orchestrator (L4) | Forbidden | no | OK |
| [job_executor.py](job_executor.md) | Part-2 Job Executor (L5) | Forbidden | no | OK |
| [knowledge_plane.py](knowledge_plane.md) | KnowledgePlane - Knowledge plane models and registry. | Forbidden | no | OK |
| [offboarding.py](offboarding.md) | Offboarding Stage Handlers | Forbidden | no | OK |
| [onboarding.py](onboarding.md) | Onboarding Stage Handlers | Forbidden | no | OK |
| [operation_registry.py](operation_registry.md) | Operation Registry (L4 Orchestrator) | OWNS COMMIT | no | OK |
| [phase_status_invariants.py](phase_status_invariants.md) | Module: phase_status_invariants | Forbidden | no | OK |
| [plan_generation_engine.py](plan_generation_engine.md) | Domain engine for plan generation. | Forbidden | no | OK |
| [pool_manager.py](pool_manager.md) | Connection Pool Manager (GAP-172) | Forbidden | no | OK |
| [run_governance_facade.py](run_governance_facade.md) | Run Governance Facade (L4 Domain Logic) | Forbidden | no | OK |

### Coordinators Subfolder (`coordinators/`)

Cross-domain mediators created by PIN-504 (Loop Model C4 pattern).

| Script | Purpose | Cross-domain | Reference |
|--------|---------|--------------|-----------|
| `coordinators/__init__.py` | Package init for C4 coordinator infrastructure | — | PIN-504 |
| `coordinators/audit_coordinator.py` | Cross-domain audit dispatch (incidents/policies → logs) | yes | PIN-504 |
| `coordinators/signal_coordinator.py` | Dual threshold signal emission (controls + activity) | yes | PIN-504 |
| `coordinators/logs_coordinator.py` | Spine passthrough for logs read service access | yes | PIN-504 |
| `coordinators/run_evidence_coordinator.py` | Cross-domain evidence aggregation for runs (incidents + policies + controls) | yes | PIN-519 |
| `coordinators/run_proof_coordinator.py` | Integrity verification via traces (HASH_CHAIN model) | yes | PIN-519 |
| `coordinators/signal_feedback_coordinator.py` | Signal feedback queries from audit ledger | yes | PIN-519 |

## 5. Assessment

**Correct:** 12/12 scripts pass all governance checks.

**Missing (from reconciliation artifact):**

- Explicit OperationRegistry — operation→callable mapping
- Mandatory cross_domain_deps=[] declaration per operation
- Hard assertion: no L5 may call coordinator directly

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| constraint_checker.py | _none_ | 0 | 0 |
| execution.py | _none_ | 0 | 0 |
| governance_orchestrator.py | _none_ | 0 | 0 |
| job_executor.py | _none_ | 0 | 0 |
| knowledge_plane.py | _none_ | 0 | 0 |
| offboarding.py | _none_ | 0 | 0 |
| onboarding.py | _none_ | 0 | 0 |
| operation_registry.py | _none_ | 0 | 0 |
| phase_status_invariants.py | _none_ | 0 | 0 |
| plan_generation_engine.py | _none_ | 0 | 0 |
| pool_manager.py | _none_ | 0 | 0 |
| run_governance_facade.py | _none_ | 0 | 0 |


---

## PIN-507 Law 5 Remediation (2026-02-01)

**Handlers updated:** All 9 handler files (18 handler classes) in `hoc_spine/orchestrator/handlers/` now use explicit dispatch maps instead of `getattr()` reflection. Zero `asyncio.iscoroutinefunction()` calls remain. Mixed sync/async handlers use split `async_dispatch` / `sync_dispatch` dictionaries. Dispatch maps are local per-call (built after lazy facade import inside `execute()`). Error semantics (codes, messages, exception mapping) preserved exactly.

**Files:** `controls_handler.py`, `api_keys_handler.py`, `overview_handler.py`, `account_handler.py`, `analytics_handler.py`, `activity_handler.py`, `incidents_handler.py`, `integrations_handler.py`, `logs_handler.py`, `policies_handler.py`

---

## PIN-519 System Run Introspection (2026-02-03)

**New coordinators added:**

| Coordinator | Purpose | Cross-domain Sources | Reference |
|-------------|---------|----------------------|-----------|
| `run_evidence_coordinator.py` | Composes cross-domain impact for a run | incidents, policies, controls | PIN-519 |
| `run_proof_coordinator.py` | Verifies run integrity via trace HASH_CHAIN | logs (traces_store) | PIN-519 |
| `signal_feedback_coordinator.py` | Queries signal feedback from audit ledger | logs (audit_ledger_read_driver) | PIN-519 |

**Bridge extensions:**

| Bridge | New Capability | Reference |
|--------|----------------|-----------|
| `incidents_bridge.py` | `incidents_for_run_capability()` | PIN-519 |
| `policies_bridge.py` | `policy_evaluations_capability()` | PIN-519 |
| `controls_bridge.py` | `limit_breaches_capability()` | PIN-519 |
| `logs_bridge.py` | `traces_store_capability()`, `audit_ledger_read_capability()` | PIN-519 |

**Consumers:** `ActivityFacade.get_run_evidence()`, `ActivityFacade.get_run_proof()`, `ActivityFacade.get_signals()` (feedback)
