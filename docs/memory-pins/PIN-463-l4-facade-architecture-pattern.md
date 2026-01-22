# PIN-463: L4 Facade Architecture Pattern

**Status:** REFERENCE
**Created:** 2026-01-22
**Category:** Architecture / Patterns
**Reference:** PIN-411 (Unified Facades), W4_FACADE_ARCHITECTURE.md

---

## Purpose

This PIN documents the canonical pattern for creating L4 domain facades in the AOS backend. All customer-facing domains use this pattern for consistent architecture.

---

## 1. Layer Architecture Overview

### Complete Layer Model

| Layer | Name | Purpose |
|-------|------|---------|
| L1 | Product Experience | UI (React frontend) |
| L2 | Product APIs | FastAPI routes, HTTP handling |
| **L3** | **Boundary Adapters** | **External system translation (< 200 LOC)** |
| **L4** | **Domain Engines** | **Business logic, facades (this PIN)** |
| **L5** | **Execution & Workers** | **Background jobs, async processing** |
| L6 | Platform Substrate | Database, Redis, external services |
| L7 | Ops & Deployment | Systemd, Docker |
| L8 | Catalyst / Meta | CI, tests, validators |

### Primary Flow: L2 → L4 → L6 (This PIN)

The facade pattern covers **synchronous request-response** flows:

```
┌─────────────────────────────────────────────────────────────────┐
│  L1 - Frontend (React)                                          │
│  Calls: /api/v1/{domain}/*                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  L2 - Product APIs (FastAPI routers)                            │
│  File: backend/app/api/aos_{domain}.py                          │
│  Role: HTTP handling, request validation, response formatting   │
│  Imports: L4 facade only (never direct SQL or L6 models)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  L4 - Domain Facade (Singleton)                                 │
│  File: backend/app/services/{domain}_facade.py                  │
│  Role: Business logic, data access, tenant isolation            │
│  Returns: Typed dataclass results (never ORM models)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  L6 - Platform (Database, Redis, External Services)             │
└─────────────────────────────────────────────────────────────────┘
```

### Complete Picture: All Data Paths

```
                    ┌─────────────┐
                    │  L1 - UI    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  L2 - API   │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │ L3 Adapter  │  │ L4 Facade   │  │ L5 Worker   │
   │ (external)  │  │ (domain)    │  │ (async)     │
   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ L6 Platform │
                    │ (DB, Redis) │
                    └─────────────┘
```

| Path | When Used | Example |
|------|-----------|---------|
| **L2 → L4 → L6** | Sync reads/writes (console APIs) | `GET /api/v1/incidents` |
| L2 → L3 → L6 | External system calls | Clerk auth, LLM API calls |
| L2 → L5 → L4 → L6 | Background jobs | Run execution, telemetry |

---

## 1.1 When L3 (Boundary Adapters) is Used

L3 adapters translate between **external systems** and internal domain models:

```
External World                    Internal System
─────────────────────────────────────────────────
                     L3
Clerk JWT      →  [ClerkAdapter]     → ActorContext
OpenAI API     →  [OpenAIAdapter]    → LLMResponse
Anthropic API  →  [AnthropicAdapter] → LLMResponse
Webhook        →  [WebhookAdapter]   → InternalEvent
```

**Examples in codebase:**
- `app/auth/clerk_provider.py` - Adapts Clerk JWTs to internal auth context
- `app/services/cus_openai_provider.py` - Adapts OpenAI SDK
- `app/services/cus_anthropic_provider.py` - Adapts Anthropic SDK

**L3 Rules:**
- Thin layer (< 200 lines of code)
- No business logic - only format translation
- If you need business logic, it belongs in L4

**When L3 is NOT needed:**
- Internal data flows (DB → API) - use L4 facade directly
- No external boundary to cross

---

## 1.2 When L5 (Execution & Workers) is Used

L5 handles **asynchronous/background processing** outside the request-response cycle:

```
REQUEST-RESPONSE (Sync)          BACKGROUND (Async)
───────────────────────          ──────────────────
L2 → L4 → L6                     L2 → L5 → L4 → L6

User clicks                      POST /runs
    ↓                                ↓
API call                         Queue job
    ↓                                ↓
Query DB                         Worker executes
    ↓                                ↓
Response                         Store results
    ↓
UI updates                       (User polls for status)
```

**Examples in codebase:**
- `app/worker/` - Worker runtime
- `app/worker/runtime/executor.py` - Run executor
- Background telemetry processing
- Scheduled aggregation jobs

**When L5 is used:**
| Use Case | Example |
|----------|---------|
| Run execution | Agent runs, workflow execution |
| Telemetry ingestion | Background SDK telemetry processing |
| Scheduled jobs | Periodic aggregation, cleanup |
| Async events | Incident creation from failed runs |
| Long-running tasks | Health checks, credential validation |

**When L5 is NOT needed:**
- Synchronous read APIs (console list/detail endpoints)
- User waits for immediate response

---

## 2. File Naming Convention

### L2 API Routes (Customer-Facing)

```
backend/app/api/aos_{domain}.py
```

| Domain | File |
|--------|------|
| Activity | `aos_activity.py` |
| Incidents | `aos_incidents.py` |
| Policies | `aos_policies.py` |
| Logs | `aos_logs.py` |
| Analytics | `aos_analytics.py` |
| Overview | `aos_overview.py` |
| Accounts | `aos_accounts.py` |
| Integrations | `aos_cus_integrations.py` |
| API Keys | `aos_api_key.py` |

### L4 Domain Facades

```
backend/app/services/{domain}_facade.py
```

| Domain | File |
|--------|------|
| Activity | `activity_facade.py` |
| Incidents | `incidents_facade.py` |
| Policies | `policies_facade.py` |
| Logs | `logs_facade.py` |
| Analytics | `analytics_facade.py` |
| Overview | `overview_facade.py` |
| Accounts | `accounts_facade.py` |
| Integrations | `integrations_facade.py` |
| API Keys | `api_keys_facade.py` |

---

## 3. L4 Facade Template

### File Header

```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: ai-console
# Temporal:
#   Trigger: api
#   Execution: async (DB operations)
# Role: {Domain} domain facade - unified entry point for {domain} data
# Callers: L2 {domain} API (aos_{domain}.py)
# Allowed Imports: L4 (services), L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: {Domain} Domain Architecture
```

### Structure

```python
"""
{Domain} Domain Facade (L4)

Unified facade for {domain} data access.

Provides:
- list_{items}() - List with pagination
- get_{item}() - Single item detail
- ... other operations

All operations are tenant-scoped for isolation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


# =============================================================================
# Result Types (Dataclasses - NOT Pydantic)
# =============================================================================


@dataclass
class ItemSummaryResult:
    """Summary for list view."""
    id: str
    name: str
    status: str
    created_at: datetime


@dataclass
class ItemListResult:
    """Paginated list response."""
    items: list[ItemSummaryResult]
    total: int
    has_more: bool


@dataclass
class ItemDetailResult:
    """Full detail response."""
    id: str
    name: str
    status: str
    # ... all fields
    created_at: datetime
    updated_at: Optional[datetime]


# =============================================================================
# Facade Class
# =============================================================================


class DomainFacade:
    """
    Unified facade for {domain} data access.

    All operations are tenant-scoped for isolation.
    """

    async def list_items(
        self,
        session: AsyncSession,
        tenant_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> ItemListResult:
        """List items for tenant with pagination."""
        # Build query with tenant isolation
        query = select(Model).where(Model.tenant_id == tenant_id)

        # Apply filters
        if status:
            query = query.where(Model.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        rows = result.scalars().all()

        # Map to result types
        items = [
            ItemSummaryResult(
                id=str(row.id),
                name=row.name,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]

        return ItemListResult(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    async def get_item(
        self,
        session: AsyncSession,
        tenant_id: str,
        item_id: str,
    ) -> Optional[ItemDetailResult]:
        """Get single item detail."""
        query = select(Model).where(
            Model.tenant_id == tenant_id,
            Model.id == item_id,
        )
        result = await session.execute(query)
        row = result.scalar_one_or_none()

        if not row:
            return None

        return ItemDetailResult(
            id=str(row.id),
            name=row.name,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


# =============================================================================
# Singleton Factory
# =============================================================================


_facade_instance: DomainFacade | None = None


def get_domain_facade() -> DomainFacade:
    """Get the singleton DomainFacade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = DomainFacade()
    return _facade_instance


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    # Facade
    "DomainFacade",
    "get_domain_facade",
    # Result types
    "ItemSummaryResult",
    "ItemListResult",
    "ItemDetailResult",
]
```

---

## 4. L2 API Route Template

### File Header

```python
# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: {Domain} domain API - customer-facing endpoints
# Callers: Customer Console frontend, SDK
# Allowed Imports: L4 ({domain}_facade), L6 (schemas)
# Forbidden Imports: L1, L3, L5
# Reference: {Domain} Domain Architecture
```

### Structure

```python
"""
{Domain} API (L2)

Customer-facing endpoints for {domain} data.
All requests are tenant-scoped via auth_context.

Endpoints:
- GET /api/v1/{domain}           → List (O2)
- GET /api/v1/{domain}/{id}      → Detail (O3)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.schemas.response import wrap_dict, wrap_list
from app.services.{domain}_facade import get_{domain}_facade

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/{domain}", tags=["{domain}"])


# =============================================================================
# Helper: Get tenant from auth context
# =============================================================================


def get_tenant_id(request: Request) -> str:
    """Extract tenant_id from auth_context."""
    auth_context = get_auth_context(request)
    if not auth_context or not auth_context.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")
    return str(auth_context.tenant_id)


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", summary="List items (O2)")
async def list_items(
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_async_session_dep),
):
    """List items for the tenant. Delegates to L4 Facade."""
    tenant_id = get_tenant_id(request)

    try:
        facade = get_{domain}_facade()
        result = await facade.list_items(
            session=session,
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
            status=status,
        )

        return wrap_list(
            [
                {
                    "id": item.id,
                    "name": item.name,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                }
                for item in result.items
            ],
            total=result.total,
        )

    except Exception as e:
        logger.exception(f"Failed to list items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}", summary="Get item detail (O3)")
async def get_item(
    request: Request,
    item_id: str,
    session: AsyncSession = Depends(get_async_session_dep),
):
    """Get item detail. Delegates to L4 Facade."""
    tenant_id = get_tenant_id(request)

    try:
        facade = get_{domain}_facade()
        result = await facade.get_item(
            session=session,
            tenant_id=tenant_id,
            item_id=item_id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Item not found")

        return wrap_dict({
            "id": result.id,
            "name": result.name,
            "status": result.status,
            "created_at": result.created_at.isoformat(),
            "updated_at": result.updated_at.isoformat() if result.updated_at else None,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 5. Key Rules

### Import Rules

| Layer | Can Import | Cannot Import |
|-------|------------|---------------|
| L2 (API) | L4 facade, L6 schemas | L1, L3, L5, direct models |
| L4 (Facade) | L6 models, other L4 services | L1, L2, L3, L5 |

### Facade Rules

1. **Singleton Pattern**: Use `get_{domain}_facade()` factory function
2. **Tenant Isolation**: Every operation takes `tenant_id` parameter
3. **Typed Results**: Return dataclasses, never ORM models
4. **Session Management**: L2 creates session, passes to facade
5. **No HTTP Concepts**: Facade knows nothing about HTTP/REST

### Response Wrapping

```python
# List endpoints - use wrap_list()
return wrap_list(items, total=count)

# Detail endpoints - use wrap_dict()
return wrap_dict({"id": "...", "name": "..."})
```

### Error Handling Pattern

```python
try:
    facade = get_{domain}_facade()
    result = await facade.some_operation(...)

    if not result:
        raise HTTPException(status_code=404, detail="Not found")

    return wrap_dict(result_to_dict(result))

except HTTPException:
    raise  # Re-raise HTTP exceptions as-is
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception(f"Failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. Router Registration

In `backend/app/main.py`:

```python
# Include API routers
from .api.aos_{domain} import router as {domain}_router

# ... other imports ...

# Registration
app.include_router({domain}_router)
```

---

## 7. Architecture Documentation

Each domain should have architecture documentation in:

```
docs/architecture/{domain}/
├── {DOMAIN}_ARCHITECTURE.md      # Full architecture doc
└── {DOMAIN}_DOMAIN_AUDIT.md      # Implementation audit
```

The architecture doc should include an **L4 Facade Section**:

```markdown
## 3. L4 Domain Facade

**File:** `backend/app/services/{domain}_facade.py`
**Getter:** `get_{domain}_facade()` (singleton)

**Pattern:**
\`\`\`python
from app.services.{domain}_facade import get_{domain}_facade

facade = get_{domain}_facade()
result = await facade.list_items(session, tenant_id, ...)
\`\`\`

**Operations Provided:**
- `list_items()` - List with pagination
- `get_item()` - Single item detail
- ... other operations

**Facade Rules:**
- L2 routes call facade methods, never direct SQL
- Facade returns typed dataclass results
- Facade handles tenant isolation internally
```

---

## 8. Checklist for New Facades

- [ ] Create `backend/app/services/{domain}_facade.py`
- [ ] Define result dataclasses (Summary, List, Detail)
- [ ] Implement facade class with tenant-scoped methods
- [ ] Add singleton factory `get_{domain}_facade()`
- [ ] Add `__all__` exports
- [ ] Create `backend/app/api/aos_{domain}.py`
- [ ] Add file headers with AUDIENCE and layer info
- [ ] Import facade with `get_{domain}_facade()`
- [ ] Use `wrap_dict()` / `wrap_list()` for responses
- [ ] Register router in `main.py`
- [ ] Update architecture documentation

---

## Related PINs

- PIN-411: Unified Facades Consolidation
- PIN-436: Guardrail Violations Baseline
- W4_FACADE_ARCHITECTURE.md: Facade architecture reference
