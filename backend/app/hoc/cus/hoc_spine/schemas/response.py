# capability_id: CAP-012
# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Standard API response envelope for consistent client experience (pure Pydantic DTO)
# Callers: All API routes (L2)
# Allowed Imports: None (foundational schema)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, API-002 Guardrail (Response Envelope Consistency)
# NOTE: Reclassified L2→L5 (2026-01-24) - Pure Pydantic schemas, no boundary crossing

"""
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
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Metadata included with every response."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of response generation",
    )
    request_id: str = Field(
        default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}",
        description="Unique identifier for request tracing",
    )
    # Optional pagination fields
    total: Optional[int] = Field(None, description="Total count for paginated responses")
    page: Optional[int] = Field(None, description="Current page number (1-indexed)")
    page_size: Optional[int] = Field(None, description="Items per page")
    has_more: Optional[bool] = Field(None, description="Whether more items exist")


class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standard API response envelope.

    All API endpoints should return this structure for consistency.
    """

    success: bool = Field(..., description="Whether the request succeeded")
    data: Optional[T] = Field(None, description="Response payload")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Response metadata")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if success=false")

    class Config:
        # Allow arbitrary types for generic data
        arbitrary_types_allowed = True


class ErrorDetail(BaseModel):
    """Structured error information."""

    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
    field: Optional[str] = Field(None, description="Field that caused the error (for validation)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


# =============================================================================
# Helper Functions
# =============================================================================


def ok(data: Any, request_id: Optional[str] = None) -> ResponseEnvelope:
    """
    Create a successful response envelope.

    Args:
        data: The response payload
        request_id: Optional request ID (auto-generated if not provided)

    Returns:
        ResponseEnvelope with success=True
    """
    meta = ResponseMeta()
    if request_id:
        meta.request_id = request_id

    return ResponseEnvelope(
        success=True,
        data=data,
        meta=meta,
    )


def error(
    message: str,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> ResponseEnvelope:
    """
    Create an error response envelope.

    Args:
        message: Human-readable error message
        code: Machine-readable error code
        details: Additional error context
        request_id: Optional request ID (auto-generated if not provided)

    Returns:
        ResponseEnvelope with success=False
    """
    meta = ResponseMeta()
    if request_id:
        meta.request_id = request_id

    error_detail = ErrorDetail(
        message=message,
        code=code,
        details=details,
    )

    return ResponseEnvelope(
        success=False,
        data=None,
        meta=meta,
        error=error_detail.model_dump(exclude_none=True),
    )


def paginated(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    request_id: Optional[str] = None,
) -> ResponseEnvelope:
    """
    Create a paginated response envelope.

    Args:
        items: List of items for current page
        total: Total count of all items
        page: Current page number (1-indexed)
        page_size: Number of items per page
        request_id: Optional request ID (auto-generated if not provided)

    Returns:
        ResponseEnvelope with pagination metadata
    """
    meta = ResponseMeta()
    if request_id:
        meta.request_id = request_id

    meta.total = total
    meta.page = page
    meta.page_size = page_size
    meta.has_more = (page * page_size) < total

    return ResponseEnvelope(
        success=True,
        data=items,
        meta=meta,
    )


def wrap_dict(data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """
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
    """
    return {
        "success": True,
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id or f"req-{uuid.uuid4().hex[:12]}",
        },
    }


def wrap_list(
    items: List[Any],
    total: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
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
    """
    meta: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id or f"req-{uuid.uuid4().hex[:12]}",
    }

    if total is not None:
        meta["total"] = total
    if page is not None:
        meta["page"] = page
    if page_size is not None:
        meta["page_size"] = page_size
        if total is not None and page is not None:
            meta["has_more"] = (page * page_size) < total

    return {
        "success": True,
        "data": items,
        "meta": meta,
    }


def wrap_error(
    message: str,
    code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an error response as a dictionary.

    Args:
        message: Error message
        code: Error code
        details: Additional context
        request_id: Optional request ID

    Returns:
        Dictionary with error envelope structure
    """
    error_obj: Dict[str, Any] = {"message": message}
    if code:
        error_obj["code"] = code
    if details:
        error_obj["details"] = details

    return {
        "success": False,
        "data": None,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id or f"req-{uuid.uuid4().hex[:12]}",
        },
        "error": error_obj,
    }
