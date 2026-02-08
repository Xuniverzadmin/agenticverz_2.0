# Layer: L4 — HOC Spine (Engine)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker (mediated retrieval)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: knowledge_plane_registry (SSOT)
#   Writes: none
# Role: Resolve mediated retrieval plane_id -> connector binding (Phase 4)
# Callers: hoc_spine RetrievalMediator wiring
# Allowed Imports: hoc_spine drivers, hoc_spine orchestrator session context, app.models facts
# Forbidden Imports: L2 routes

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import KnowledgePlaneRegistryDriver
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_async_session_context
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState


@dataclass(frozen=True)
class UnsupportedConnector:
    """
    Placeholder connector used when a plane is ACTIVE but no runtime connector
    implementation exists yet for its connector binding.
    """

    id: str
    connector_type: str
    connector_id: str

    async def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError(
            "Connector runtime not implemented for this knowledge plane. "
            f"connector_type={self.connector_type} connector_id={self.connector_id}"
        )


class DbKnowledgePlaneConnectorRegistry:
    """
    ConnectorRegistry backed by the canonical knowledge_plane_registry SSOT.

    Contract:
    - Only ACTIVE governed planes are resolvable.
    - Connector identity is derived from the registry binding.
    """

    def __init__(self, driver: Optional[KnowledgePlaneRegistryDriver] = None) -> None:
        self._driver = driver or KnowledgePlaneRegistryDriver()

    async def resolve(self, tenant_id: str, plane_id: str) -> Optional[UnsupportedConnector]:
        async with get_async_session_context() as session:
            record = await self._driver.get_by_id(session, tenant_id=tenant_id, plane_id=plane_id)

        if record is None:
            return None

        if KnowledgePlaneLifecycleState(record.lifecycle_state_value) != KnowledgePlaneLifecycleState.ACTIVE:
            return None

        # Phase 4: resolve only to a binding. Actual runtime connector implementations land later.
        return UnsupportedConnector(
            id=record.connector_id,
            connector_type=record.connector_type,
            connector_id=record.connector_id,
        )


_connector_registry: Optional[DbKnowledgePlaneConnectorRegistry] = None


def get_db_knowledge_plane_connector_registry() -> DbKnowledgePlaneConnectorRegistry:
    global _connector_registry
    if _connector_registry is None:
        _connector_registry = DbKnowledgePlaneConnectorRegistry()
    return _connector_registry


__all__ = [
    "DbKnowledgePlaneConnectorRegistry",
    "UnsupportedConnector",
    "get_db_knowledge_plane_connector_registry",
]

