# common.py

**Path:** `backend/app/hoc/cus/hoc_spine/schemas/common.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            common.py
Lives in:        schemas/
Role:            Schemas
Inbound:         contracts/*, engines
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Common Data Contracts - Shared Infrastructure Types
Violations:      none
```

## Purpose

Common Data Contracts - Shared Infrastructure Types

These are NON-DOMAIN contracts used by both consoles:
- Health checks
- Error responses
- Pagination

These are the ONLY contracts allowed to be shared between domains.
Domain-specific data MUST NOT be in this module.

Frozen: 2025-12-23 (M29)

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Classes

### `HealthDTO(BaseModel)`

GET /health response.

Non-authenticated health check.

### `HealthDetailDTO(BaseModel)`

GET /health/detail response (if authenticated).

Detailed health with component status.

### `ErrorDTO(BaseModel)`

Standard error response.

All 4xx/5xx responses use this format.

### `ValidationErrorDTO(BaseModel)`

422 Validation error response.

Pydantic validation errors.

### `PaginationMetaDTO(BaseModel)`

Pagination metadata.

### `CursorPaginationMetaDTO(BaseModel)`

Cursor-based pagination metadata.

### `ActionResultDTO(BaseModel)`

Generic action result (activate, deactivate, etc.).

### `ContractVersionDTO(BaseModel)`

GET /api/v1/contracts/version response.

Contract version for client compatibility checks.

## Domain Usage

**Callers:** contracts/*, engines

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: HealthDTO
      methods: []
      consumers: ["orchestrator"]
    - name: HealthDetailDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ErrorDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ValidationErrorDTO
      methods: []
      consumers: ["orchestrator"]
    - name: PaginationMetaDTO
      methods: []
      consumers: ["orchestrator"]
    - name: CursorPaginationMetaDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ActionResultDTO
      methods: []
      consumers: ["orchestrator"]
    - name: ContractVersionDTO
      methods: []
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['pydantic']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

