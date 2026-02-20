# capability_id: CAP-012
# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Common contract definitions (pure Pydantic DTOs)
# Callers: contracts/*, engines
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, Contract System
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure Pydantic schemas, no boundary crossing


"""
Common Data Contracts - Shared Infrastructure Types

These are NON-DOMAIN contracts used by both consoles:
- Health checks
- Error responses
- Pagination

These are the ONLY contracts allowed to be shared between domains.
Domain-specific data MUST NOT be in this module.

Frozen: 2025-12-23 (M29)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================================================
# HEALTH
# =============================================================================


class HealthDTO(BaseModel):
    """
    GET /health response.

    Non-authenticated health check.
    """

    status: str = Field(description="healthy, degraded, unhealthy")
    version: str
    timestamp: str


class HealthDetailDTO(BaseModel):
    """
    GET /health/detail response (if authenticated).

    Detailed health with component status.
    """

    status: str
    version: str
    timestamp: str
    components: Dict[str, str] = Field(description="Component name -> status")
    uptime_seconds: int = Field(ge=0)


# =============================================================================
# ERRORS
# =============================================================================


class ErrorDTO(BaseModel):
    """
    Standard error response.

    All 4xx/5xx responses use this format.
    """

    error: str = Field(description="Error code: AUTH_FAILED, NOT_FOUND, etc.")
    message: str = Field(description="Human-readable message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    request_id: Optional[str] = Field(None, description="For tracing")


class ValidationErrorDTO(BaseModel):
    """
    422 Validation error response.

    Pydantic validation errors.
    """

    error: str = "VALIDATION_ERROR"
    message: str = "Request validation failed"
    details: List[Dict[str, Any]] = Field(description="Field-level errors")


# =============================================================================
# PAGINATION
# =============================================================================


class PaginationMetaDTO(BaseModel):
    """Pagination metadata."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_prev: bool


class CursorPaginationMetaDTO(BaseModel):
    """Cursor-based pagination metadata."""

    cursor: Optional[str] = None
    next_cursor: Optional[str] = None
    has_more: bool
    limit: int = Field(ge=1, le=100)


# =============================================================================
# ACTION RESULTS
# =============================================================================


class ActionResultDTO(BaseModel):
    """Generic action result (activate, deactivate, etc.)."""

    success: bool
    action: str = Field(description="What was done")
    message: str = Field(description="Human-readable result")
    affected_id: Optional[str] = Field(None, description="ID of affected resource")
    timestamp: str


# =============================================================================
# CONTRACT VERSION
# =============================================================================


class ContractVersionDTO(BaseModel):
    """
    GET /api/v1/contracts/version response.

    Contract version for client compatibility checks.
    """

    version: str
    frozen_at: str
    domains: List[str] = Field(description="Available domains: guard, ops")
    breaking_changes: List[str] = Field(default_factory=list, description="Breaking changes since last version")
