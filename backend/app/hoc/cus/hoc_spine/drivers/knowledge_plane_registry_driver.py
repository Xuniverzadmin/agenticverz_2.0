# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: DB I/O for governed knowledge plane registry (SSOT)
# Callers: hoc_spine lifecycle / handlers (transaction owned by L4)
# Allowed Imports: sqlmodel/sqlalchemy only
# Forbidden Imports: hoc_spine orchestrator, L2 routes
# Reference: DRIVER_ENGINE_PATTERN_LOCKED.md

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.knowledge_plane_registry import KnowledgePlaneRegistry


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgePlaneRegistryDriver:
    """Pure DB access for knowledge_plane_registry."""

    async def get_by_id(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        plane_id: str,
    ) -> Optional[KnowledgePlaneRegistry]:
        stmt = select(KnowledgePlaneRegistry).where(
            KnowledgePlaneRegistry.tenant_id == tenant_id,
            KnowledgePlaneRegistry.plane_id == plane_id,
        )
        result = await session.exec(stmt)
        return result.first()

    async def get_by_key(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        plane_type: str,
        plane_name: str,
    ) -> Optional[KnowledgePlaneRegistry]:
        stmt = select(KnowledgePlaneRegistry).where(
            KnowledgePlaneRegistry.tenant_id == tenant_id,
            KnowledgePlaneRegistry.plane_type == plane_type,
            KnowledgePlaneRegistry.plane_name == plane_name,
        )
        result = await session.exec(stmt)
        return result.first()

    async def list_by_tenant(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        plane_type: Optional[str] = None,
    ) -> List[KnowledgePlaneRegistry]:
        stmt = select(KnowledgePlaneRegistry).where(KnowledgePlaneRegistry.tenant_id == tenant_id)
        if plane_type is not None:
            stmt = stmt.where(KnowledgePlaneRegistry.plane_type == plane_type)
        result = await session.exec(stmt)
        return list(result.all())

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        plane_type: str,
        plane_name: str,
        connector_type: str,
        connector_id: str,
        config: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> KnowledgePlaneRegistry:
        record = KnowledgePlaneRegistry(
            tenant_id=tenant_id,
            plane_type=plane_type,
            plane_name=plane_name,
            connector_type=connector_type,
            connector_id=connector_id,
            config=config or {},
            created_by=created_by,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(record)
        # Flush so callers can see plane_id and uniqueness violations without committing.
        try:
            await session.flush()
        except IntegrityError:
            raise
        return record

    async def set_lifecycle_state_value(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        plane_id: str,
        lifecycle_state_value: int,
    ) -> KnowledgePlaneRegistry:
        record = await self.get_by_id(session, tenant_id=tenant_id, plane_id=plane_id)
        if record is None:
            raise ValueError("Plane not found")
        record.lifecycle_state_value = lifecycle_state_value
        record.updated_at = utc_now()
        session.add(record)
        await session.flush()
        return record


__all__ = ["KnowledgePlaneRegistryDriver"]

