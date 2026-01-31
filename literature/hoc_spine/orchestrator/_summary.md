# Orchestrator — Folder Summary

**Path:** `backend/app/hoc/hoc_spine/orchestrator/`
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

