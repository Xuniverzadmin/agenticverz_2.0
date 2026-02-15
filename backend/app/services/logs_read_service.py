# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async (delegates to L6)
# Role: Logs/Traces domain read operations (L4)
# Callers: customer_logs_adapter.py (L3)
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
#
# GOVERNANCE NOTE:
# This L4 service provides READ operations for the Logs/Traces domain.
# All log/trace reads must go through this service.
# The L3 adapter should NOT import L6 directly.

"""
Logs Read Service (L4)

This service provides all READ operations for the Logs/Traces domain.
It sits between L3 (CustomerLogsAdapter) and L6 (PostgresTraceStore).

L3 (Adapter) → L4 (this service) → L6 (PostgresTraceStore)

Responsibilities:
- Query traces with tenant isolation
- Get trace details
- Get trace counts
- Search traces with filters
- No write operations (writes go through runtime)

Reference: PIN-281 (L3 Adapter Closure - PHASE 1)
"""

from typing import List, Optional

# L6 imports (allowed)
from app.hoc.cus.logs.L5_schemas import TraceRecord, TraceSummary
from app.hoc.cus.logs.L6_drivers.pg_store import PostgresTraceStore, get_postgres_trace_store


class LogsReadService:
    """
    L4 service for logs/trace read operations.

    Provides tenant-scoped, bounded reads for the Logs domain.
    All L3 adapters must use this service for log reads.
    """

    def __init__(self, store: Optional[PostgresTraceStore] = None):
        """Initialize with trace store (lazy loaded if not provided)."""
        self._store = store
        self._store_loaded = store is not None

    async def _get_store(self) -> PostgresTraceStore:
        """Get the L6 PostgresTraceStore (lazy loaded)."""
        if not self._store_loaded:
            self._store = get_postgres_trace_store()
            self._store_loaded = True
        return self._store

    async def search_traces(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceSummary]:
        """
        Search traces for a tenant with optional filters.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            agent_id: Optional agent filter
            status: Optional status filter
            from_date: Optional start date (ISO format)
            to_date: Optional end date (ISO format)
            limit: Page size (max 100)
            offset: Pagination offset

        Returns:
            List of TraceSummary objects
        """
        # Enforce pagination limits
        limit = min(limit, 100)

        store = await self._get_store()
        return await store.search_traces(
            tenant_id=tenant_id,
            agent_id=agent_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )

    async def get_trace(
        self,
        trace_id: str,
        tenant_id: str,
    ) -> Optional[TraceRecord]:
        """
        Get a single trace by ID with tenant isolation.

        Args:
            trace_id: Trace ID or run ID
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            TraceRecord if found and belongs to tenant, None otherwise
        """
        store = await self._get_store()
        return await store.get_trace(
            trace_id=trace_id,
            tenant_id=tenant_id,
        )

    async def get_trace_count(
        self,
        tenant_id: str,
    ) -> int:
        """
        Get total trace count for a tenant.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            Total count of traces
        """
        store = await self._get_store()
        return await store.get_trace_count(tenant_id=tenant_id)

    async def get_trace_by_root_hash(
        self,
        root_hash: str,
        tenant_id: str,
    ) -> Optional[TraceRecord]:
        """
        Get trace by deterministic root hash with tenant isolation.

        Args:
            root_hash: Deterministic root hash
            tenant_id: Tenant ID (required, enforces isolation)

        Returns:
            TraceRecord if found and belongs to tenant, None otherwise
        """
        store = await self._get_store()
        return await store.get_trace_by_root_hash(
            root_hash=root_hash,
            tenant_id=tenant_id,
        )

    async def list_traces(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceSummary]:
        """
        List traces for a tenant.

        Args:
            tenant_id: Tenant ID (required, enforces isolation)
            limit: Page size (max 100)
            offset: Pagination offset

        Returns:
            List of TraceSummary objects
        """
        # Enforce pagination limits
        limit = min(limit, 100)

        store = await self._get_store()
        return await store.list_traces(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )


# Singleton instance
_logs_read_service: Optional[LogsReadService] = None


def get_logs_read_service() -> LogsReadService:
    """
    Factory function to get LogsReadService instance.

    This is the ONLY way L3 should obtain a logs read service.
    """
    global _logs_read_service
    if _logs_read_service is None:
        _logs_read_service = LogsReadService()
    return _logs_read_service


__all__ = [
    "LogsReadService",
    "get_logs_read_service",
]
