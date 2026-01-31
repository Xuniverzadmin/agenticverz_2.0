# Schemas — Folder Summary

**Path:** `backend/app/hoc/hoc_spine/schemas/`  
**Layer:** L5  
**Scripts:** 8

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
| [rac_models.py](rac_models.md) | Runtime Audit Contract (RAC) Models | Forbidden | no | OK |
| [response.py](response.md) | Standard API Response Envelope | Forbidden | no | OK |
| [retry.py](retry.md) | Retry API schemas | Forbidden | no | OK |
| [skill.py](skill.md) | Skill API schemas (pure Pydantic DTOs) | Forbidden | no | OK |

## 5. Assessment

**Correct:** 8/8 scripts pass all governance checks.

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
| rac_models.py | _none_ | 0 | 0 |
| response.py | _none_ | 0 | 0 |
| retry.py | _none_ | 0 | 0 |
| skill.py | _none_ | 0 | 0 |

