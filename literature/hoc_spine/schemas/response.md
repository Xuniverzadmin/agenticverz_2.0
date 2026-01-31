# response.py

**Path:** `backend/app/hoc/hoc_spine/schemas/response.py`  
**Layer:** L4 — HOC Spine (Schema)  
**Component:** Schemas

---

## Placement Card

```
File:            response.py
Lives in:        schemas/
Role:            Schemas
Inbound:         All API routes (L2)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Standard API Response Envelope
Violations:      none
```

## Purpose

Standard API Response Envelope

This module provides the standard response format for all API endpoints.
Consistent response structures enable:
- Predictable error handling in clients
- Request tracing via metadata
- Pagination support
- SDK code generation

Standard format:
    {
        "success": true,
        "data": { ... },
        "meta": {
            "timestamp": "2024-01-15T10:30:00Z",
            "request_id": "req-abc123"
        }
    }

Usage:
    from app.schemas.response import ResponseEnvelope, ok, error, paginated

    # Simple success response
    @router.get("/items/{id}")
    async def get_item(id: str) -> ResponseEnvelope:
        item = await fetch_item(id)
        return ok(item)

    # Error response
    @router.get("/items/{id}")
    async def get_item(id: str) -> ResponseEnvelope:
        item = await fetch_item(id)
        if not item:
            return error("Item not found", code="NOT_FOUND")
        return ok(item)

    # Paginated response
    @router.get("/items")
    async def list_items(page: int = 1) -> ResponseEnvelope:
        items, total = await fetch_items_paginated(page)
        return paginated(items, total=total, page=page, page_size=20)

## Import Analysis

**External:**
- `pydantic`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `ok(data: Any, request_id: Optional[str]) -> ResponseEnvelope`

Create a successful response envelope.

Args:
    data: The response payload
    request_id: Optional request ID (auto-generated if not provided)

Returns:
    ResponseEnvelope with success=True

### `error(message: str, code: Optional[str], details: Optional[Dict[str, Any]], request_id: Optional[str]) -> ResponseEnvelope`

Create an error response envelope.

Args:
    message: Human-readable error message
    code: Machine-readable error code
    details: Additional error context
    request_id: Optional request ID (auto-generated if not provided)

Returns:
    ResponseEnvelope with success=False

### `paginated(items: List[Any], total: int, page: int, page_size: int, request_id: Optional[str]) -> ResponseEnvelope`

Create a paginated response envelope.

Args:
    items: List of items for current page
    total: Total count of all items
    page: Current page number (1-indexed)
    page_size: Number of items per page
    request_id: Optional request ID (auto-generated if not provided)

Returns:
    ResponseEnvelope with pagination metadata

### `wrap_dict(data: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]`

Wrap a dictionary in the standard envelope format.

Use this when you need a dict instead of Pydantic model (e.g., for legacy endpoints).

Args:
    data: Dictionary to wrap (MUST be finalized output, see warnings below)
    request_id: Optional request ID

Returns:
    Dictionary with envelope structure

WARNING - API-002-CR-001 (Counter-rule):
    `data` must ONLY be:
    1. model_dump() output from Pydantic models
    2. Fully constructed response dictionaries

    NEVER pass:
    - Raw ORM/SQLModel entities
    - Internal domain objects
    - Partial computation results

    Example:
        # ✅ CORRECT
        return wrap_dict(result.model_dump())
        return wrap_dict({"key": "value"})

        # ❌ VIOLATION
        return wrap_dict(orm_entity)
        return wrap_dict(partial_result)

WARNING - API-002-CR-002 (Counter-rule for lists):
    When using {"items": [...], "total": len(results)}:
    - Valid ONLY for non-paginated endpoints
    - For paginated endpoints, total MUST come from COUNT(*) query

Reference: docs/architecture/GOVERNANCE_GUARDRAILS.md (API-002)

### `wrap_list(items: List[Any], total: Optional[int], page: Optional[int], page_size: Optional[int], request_id: Optional[str]) -> Dict[str, Any]`

Wrap a list in the standard envelope format.

Use this when you need a dict instead of Pydantic model.

Args:
    items: List to wrap
    total: Optional total count for pagination
    page: Optional current page
    page_size: Optional page size
    request_id: Optional request ID

Returns:
    Dictionary with envelope structure

### `wrap_error(message: str, code: Optional[str], details: Optional[Dict[str, Any]], request_id: Optional[str]) -> Dict[str, Any]`

Create an error response as a dictionary.

Args:
    message: Error message
    code: Error code
    details: Additional context
    request_id: Optional request ID

Returns:
    Dictionary with error envelope structure

## Classes

### `ResponseMeta(BaseModel)`

Metadata included with every response.

### `ResponseEnvelope(BaseModel, Generic[T])`

Standard API response envelope.

All API endpoints should return this structure for consistency.

### `ErrorDetail(BaseModel)`

Structured error information.

## Domain Usage

**Callers:** All API routes (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: ok
      signature: "ok(data: Any, request_id: Optional[str]) -> ResponseEnvelope"
      consumers: ["orchestrator"]
    - name: error
      signature: "error(message: str, code: Optional[str], details: Optional[Dict[str, Any]], request_id: Optional[str]) -> ResponseEnvelope"
      consumers: ["orchestrator"]
    - name: paginated
      signature: "paginated(items: List[Any], total: int, page: int, page_size: int, request_id: Optional[str]) -> ResponseEnvelope"
      consumers: ["orchestrator"]
    - name: wrap_dict
      signature: "wrap_dict(data: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]"
      consumers: ["orchestrator"]
    - name: wrap_list
      signature: "wrap_list(items: List[Any], total: Optional[int], page: Optional[int], page_size: Optional[int], request_id: Optional[str]) -> Dict[str, Any]"
      consumers: ["orchestrator"]
    - name: wrap_error
      signature: "wrap_error(message: str, code: Optional[str], details: Optional[Dict[str, Any]], request_id: Optional[str]) -> Dict[str, Any]"
      consumers: ["orchestrator"]
  classes:
    - name: ResponseMeta
      methods: []
      consumers: ["orchestrator"]
    - name: ResponseEnvelope
      methods: []
      consumers: ["orchestrator"]
    - name: ErrorDetail
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

