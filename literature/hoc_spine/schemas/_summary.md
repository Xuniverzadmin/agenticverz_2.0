# Schemas — Folder Summary

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/`
**Layer:** L5
**Scripts:** 10

---

## 1. Purpose

Shared contracts, not models. Defines operation shapes, execution context, and authority decisions. No logic, no imports from services, drivers, or orchestrator.

## 2. What Belongs Here

- Pydantic DTOs for API responses
- Operation and plan schemas
- Agent/skill configuration models
- RAC audit models

## 3. What Must NOT Be Here

- Import services
- Import drivers
- Import orchestrator
- Contain business logic

## 4. Script Inventory

| Script | Purpose | Transaction | Cross-domain | Verdict |
|--------|---------|-------------|--------------|---------|
| [agent.py](agent.md) | Agent API request/response schemas (pure Pydantic DTOs) | Forbidden | no | OK |
| [artifact.py](artifact.md) | Artifact API schemas (pure Pydantic DTOs) | Forbidden | no | OK |
| [common.py](common.md) | Common Data Contracts - Shared Infrastructure Types | Forbidden | no | OK |
| [plan.py](plan.md) | Plan API schemas (pure Pydantic DTOs) | Forbidden | no | OK |
| [protocols.py](protocols.md) | L1 Re-wiring Protocol Interfaces (PIN-513) | Forbidden | no | OK |
| [rac_models.py](rac_models.md) | Runtime Audit Contract (RAC) Models | Forbidden | no | OK |
| [response.py](response.md) | Standard API Response Envelope | Forbidden | no | OK |
| [retry.py](retry.md) | Retry API schemas | Forbidden | no | OK |
| [run_introspection_protocols.py](run_introspection_protocols.md) | Run introspection protocols (PIN-519) | Forbidden | no | OK |
| [skill.py](skill.md) | Skill API schemas (pure Pydantic DTOs) | Forbidden | no | OK |

## 5. Assessment

**Correct:** 10/10 scripts pass all governance checks.

**Missing (from reconciliation artifact):**

- AuthorityDecision schema
- ExecutionContext schema (unified)

## 6. L5 Pairing Aggregate

| Script | Serves Domains | Wired L5 Consumers | Gaps |
|--------|----------------|--------------------|------|
| agent.py | _none_ | 0 | 0 |
| artifact.py | _none_ | 0 | 0 |
| common.py | _none_ | 0 | 0 |
| plan.py | _none_ | 0 | 0 |
| protocols.py | _none_ | 0 | 0 |
| rac_models.py | _none_ | 0 | 0 |
| response.py | _none_ | 0 | 0 |
| retry.py | _none_ | 0 | 0 |
| run_introspection_protocols.py | activity | 1 (ActivityFacade) | 0 |
| skill.py | _none_ | 0 | 0 |

---

## PIN-519 Run Introspection Protocols (2026-02-03)

**New file:** `run_introspection_protocols.py`

Defines protocols and result types for run introspection:

| Protocol | Purpose | Implementor |
|----------|---------|-------------|
| `RunEvidenceProvider` | Cross-domain evidence queries | `RunEvidenceCoordinator` (L4) |
| `RunProofProvider` | Integrity verification queries | `RunProofCoordinator` (L4) |
| `SignalFeedbackProvider` | Signal feedback queries | `SignalFeedbackCoordinator` (L4) |

**Configuration:**
```python
INTEGRITY_CONFIG = {
    "model": "HASH_CHAIN",      # NONE | HASH_CHAIN | MERKLE_TREE
    "trust_boundary": "SYSTEM", # LOCAL | SYSTEM
    "storage": "POSTGRES",      # SQLITE | POSTGRES
}
```

