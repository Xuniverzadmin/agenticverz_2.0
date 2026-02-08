# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: evidence, planes (via driver)
#   Writes: none
# Role: Retrieval Facade - Centralized access to mediated data retrieval
# Callers: L2 retrieval.py API, SDK
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-094 (Mediated Data Retrieval API)

"""
Retrieval Facade (L4 Domain Logic)

This facade provides the external interface for mediated data retrieval operations.
All retrieval APIs MUST use this facade instead of directly importing
the RetrievalMediator.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes retrieval mediation logic
- Provides unified access to data retrieval with policy enforcement
- Single point for audit emission

Wrapped Services:
- RetrievalMediator: Central choke point for data access (GAP-065)

L2 API Routes (GAP-094):
- POST /api/v1/retrieval/access (mediated data access)
Plane registry + evidence administration is founder-scoped and routed through
L4 operations (see `app.hoc.api.fdr.ops.retrieval_admin`).

Usage:
    from app.hoc.cus.hoc_spine.services.retrieval_facade import get_retrieval_facade

    facade = get_retrieval_facade()

    # Mediated data access
    result = await facade.access_data(
        tenant_id="...",
        run_id="...",
        plane_id="documents",
        action="query",
        payload={"query": "..."},
    )

    # List available planes
    planes = await facade.list_planes(tenant_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.retrieval.facade")


@dataclass
class AccessResult:
    """Result of a mediated data access."""
    success: bool
    data: Any
    evidence_id: str
    connector_id: str
    tokens_consumed: int
    query_hash: str
    timestamp: str
    tenant_id: str
    run_id: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "evidence_id": self.evidence_id,
            "connector_id": self.connector_id,
            "tokens_consumed": self.tokens_consumed,
            "query_hash": self.query_hash,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "error": self.error,
        }


@dataclass
class PlaneInfo:
    """Information about a knowledge plane."""
    id: str
    name: str
    connector_type: str
    status: str
    tenant_id: str
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "connector_type": self.connector_type,
            "status": self.status,
            "tenant_id": self.tenant_id,
            "capabilities": self.capabilities,
        }


@dataclass
class EvidenceInfo:
    """Evidence record information."""
    id: str
    tenant_id: str
    run_id: str
    plane_id: str
    connector_id: str
    query_hash: str
    doc_ids: List[str]
    token_count: int
    policy_snapshot_id: Optional[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "plane_id": self.plane_id,
            "connector_id": self.connector_id,
            "query_hash": self.query_hash,
            "doc_ids": self.doc_ids,
            "token_count": self.token_count,
            "policy_snapshot_id": self.policy_snapshot_id,
            "timestamp": self.timestamp,
        }


class RetrievalFacade:
    """
    Facade for mediated data retrieval operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    the retrieval mediator.

    Layer: L4 (Domain Logic)
    Callers: retrieval.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade with lazy-loaded services."""
        self._mediator = None

    @property
    def mediator(self):
        """Lazy-load RetrievalMediator."""
        if self._mediator is None:
            try:
                from app.hoc.cus.hoc_spine.services.retrieval_mediator import (
                    get_retrieval_mediator,
                )
                self._mediator = get_retrieval_mediator()
            except ImportError:
                logger.warning("RetrievalMediator not available")
        return self._mediator

    # =========================================================================
    # Data Access Operations (GAP-094)
    # =========================================================================

    async def access_data(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
        payload: Dict[str, Any],
    ) -> AccessResult:
        """
        Mediated access to external data.

        All data access from LLM-controlled code MUST go through this method.
        Implements deny-by-default policy enforcement.

        Args:
            tenant_id: Tenant ID
            run_id: Run context for this access
            plane_id: Knowledge plane to access (e.g., "documents", "database")
            action: Action to perform (query, retrieve, search, list)
            payload: Action-specific payload

        Returns:
            AccessResult with data and evidence
        """
        logger.info(
            "facade.access_data",
            extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
                "plane_id": plane_id,
                "action": action,
            }
        )

        try:
            if self.mediator is None:
                return AccessResult(
                    success=False,
                    data=None,
                    evidence_id="none",
                    connector_id="none",
                    tokens_consumed=0,
                    query_hash="",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    tenant_id=tenant_id,
                    run_id=run_id,
                    error="RetrievalMediator not configured",
                )

            result = await self.mediator.access(
                tenant_id=tenant_id,
                run_id=run_id,
                plane_id=plane_id,
                action=action,
                payload=payload,
                requesting_tenant_id=tenant_id,
            )

            return AccessResult(
                success=result.success,
                data=result.data,
                evidence_id=result.evidence_id,
                connector_id=result.connector_id,
                tokens_consumed=result.tokens_consumed,
                query_hash=result.query_hash,
                timestamp=result.timestamp,
                tenant_id=result.tenant_id,
                run_id=result.run_id,
            )

        except Exception as e:
            logger.error(
                "facade.access_data failed",
                extra={
                    "error": str(e),
                    "tenant_id": tenant_id,
                    "run_id": run_id,
                    "plane_id": plane_id,
                }
            )
            return AccessResult(
                success=False,
                data=None,
                evidence_id="none",
                connector_id="none",
                tokens_consumed=0,
                query_hash="",
                timestamp=datetime.now(timezone.utc).isoformat(),
                tenant_id=tenant_id,
                run_id=run_id,
                error=str(e),
            )

    # =========================================================================
    # Plane Operations (GAP-094)
    # =========================================================================

    async def list_planes(
        self,
        tenant_id: str,
        connector_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[PlaneInfo]:
        """
        List available knowledge planes for a tenant.

        Args:
            tenant_id: Tenant ID
            connector_type: Optional filter by connector type
            status: Optional filter by status

        Returns:
            List of PlaneInfo
        """
        logger.debug(
            "facade.list_planes",
            extra={"tenant_id": tenant_id, "connector_type": connector_type}
        )

        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            get_async_session_context,
        )
        from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState

        driver = KnowledgePlaneRegistryDriver()
        async with get_async_session_context() as session:
            records = await driver.list_by_tenant(
                session,
                tenant_id=tenant_id,
                plane_type=str(connector_type) if connector_type else None,
            )

        results: List[PlaneInfo] = []
        for record in records:
            state = KnowledgePlaneLifecycleState(record.lifecycle_state_value).name.lower()
            plane = PlaneInfo(
                id=record.plane_id,
                name=record.plane_name,
                connector_type=record.connector_type,
                status=state,
                tenant_id=record.tenant_id,
                capabilities=list(record.config.get("capabilities", [])) if isinstance(record.config, dict) else [],
            )
            if status and plane.status != status:
                continue
            results.append(plane)

        return results

    async def register_plane(
        self,
        tenant_id: str,
        name: str,
        connector_type: str,
        connector_id: str,
        capabilities: Optional[List[str]] = None,
    ) -> PlaneInfo:
        raise NotImplementedError(
            "Plane registration is a governance/admin operation. Use hoc_spine operations via "
            "app.hoc.api.fdr.ops.retrieval_admin (knowledge.planes.register)."
        )

    async def get_plane(
        self,
        plane_id: str,
        tenant_id: str,
    ) -> Optional[PlaneInfo]:
        """
        Get a specific plane.

        Args:
            plane_id: Plane ID
            tenant_id: Tenant ID for authorization

        Returns:
            PlaneInfo or None if not found
        """
        from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import (
            KnowledgePlaneRegistryDriver,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            get_async_session_context,
        )
        from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState

        driver = KnowledgePlaneRegistryDriver()
        async with get_async_session_context() as session:
            record = await driver.get_by_id(session, tenant_id=tenant_id, plane_id=str(plane_id))

        if record is None:
            return None

        state = KnowledgePlaneLifecycleState(record.lifecycle_state_value).name.lower()
        capabilities = list(record.config.get("capabilities", [])) if isinstance(record.config, dict) else []
        return PlaneInfo(
            id=record.plane_id,
            name=record.plane_name,
            connector_type=record.connector_type,
            status=state,
            tenant_id=record.tenant_id,
            capabilities=capabilities,
        )

    # =========================================================================
    # Evidence Operations (GAP-094)
    # =========================================================================

    async def list_evidence(
        self,
        tenant_id: str,
        run_id: Optional[str] = None,
        plane_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvidenceInfo]:
        """
        List evidence records for a tenant.

        Args:
            tenant_id: Tenant ID
            run_id: Optional filter by run
            plane_id: Optional filter by plane
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of EvidenceInfo
        """
        logger.debug(
            "facade.list_evidence",
            extra={"tenant_id": tenant_id, "run_id": run_id}
        )

        from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import (
            RetrievalEvidenceDriver,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            get_async_session_context,
        )

        driver = RetrievalEvidenceDriver()
        async with get_async_session_context() as session:
            records = await driver.list(
                session,
                tenant_id=tenant_id,
                run_id=str(run_id) if run_id else None,
                plane_id=str(plane_id) if plane_id else None,
                limit=limit,
                offset=offset,
            )

        results: List[EvidenceInfo] = []
        for record in records:
            results.append(
                EvidenceInfo(
                    id=record.id,
                    tenant_id=record.tenant_id,
                    run_id=record.run_id,
                    plane_id=record.plane_id,
                    connector_id=record.connector_id,
                    query_hash=record.query_hash,
                    doc_ids=record.doc_ids,
                    token_count=record.token_count,
                    policy_snapshot_id=record.policy_snapshot_id,
                    timestamp=record.requested_at.isoformat(),
                )
            )
        return results

    async def get_evidence(
        self,
        evidence_id: str,
        tenant_id: str,
    ) -> Optional[EvidenceInfo]:
        """
        Get a specific evidence record.

        Args:
            evidence_id: Evidence ID
            tenant_id: Tenant ID for authorization

        Returns:
            EvidenceInfo or None if not found
        """
        from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import (
            RetrievalEvidenceDriver,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            get_async_session_context,
        )

        driver = RetrievalEvidenceDriver()
        async with get_async_session_context() as session:
            record = await driver.get_by_id(session, tenant_id=tenant_id, evidence_id=str(evidence_id))

        if record is None:
            return None

        return EvidenceInfo(
            id=record.id,
            tenant_id=record.tenant_id,
            run_id=record.run_id,
            plane_id=record.plane_id,
            connector_id=record.connector_id,
            query_hash=record.query_hash,
            doc_ids=record.doc_ids,
            token_count=record.token_count,
            policy_snapshot_id=record.policy_snapshot_id,
            timestamp=record.requested_at.isoformat(),
        )

    async def record_evidence(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        connector_id: str,
        action: str,
        query_hash: str,
        doc_ids: List[str],
        token_count: int,
        policy_snapshot_id: Optional[str] = None,
    ) -> EvidenceInfo:
        """
        Record evidence of a data access (internal use).

        Args:
            tenant_id: Tenant ID
            run_id: Run ID
            plane_id: Plane ID
            connector_id: Connector ID
            query_hash: Hash of the query
            doc_ids: List of accessed document IDs
            token_count: Tokens consumed
            policy_snapshot_id: Optional policy snapshot ID

        Returns:
            EvidenceInfo for the recorded evidence
        """
        from app.hoc.cus.hoc_spine.drivers.retrieval_evidence_driver import (
            RetrievalEvidenceDriver,
        )
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            get_async_session_context,
        )

        now = datetime.now(timezone.utc)
        driver = RetrievalEvidenceDriver()

        async with get_async_session_context() as session:
            async with session.begin():
                record = await driver.append(
                    session,
                    tenant_id=tenant_id,
                    run_id=run_id,
                    plane_id=plane_id,
                    connector_id=connector_id,
                    action=action,
                    query_hash=query_hash,
                    doc_ids=doc_ids,
                    token_count=token_count,
                    policy_snapshot_id=policy_snapshot_id,
                    requested_at=now,
                    completed_at=now,
                    duration_ms=0,
                )

        logger.info("facade.evidence_recorded", extra={"evidence_id": record.id, "run_id": run_id})
        return EvidenceInfo(
            id=record.id,
            tenant_id=record.tenant_id,
            run_id=record.run_id,
            plane_id=record.plane_id,
            connector_id=record.connector_id,
            query_hash=record.query_hash,
            doc_ids=record.doc_ids,
            token_count=record.token_count,
            policy_snapshot_id=record.policy_snapshot_id,
            timestamp=record.requested_at.isoformat(),
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[RetrievalFacade] = None


def get_retrieval_facade() -> RetrievalFacade:
    """
    Get the retrieval facade instance.

    This is the recommended way to access retrieval operations
    from L2 APIs and the SDK.

    Returns:
        RetrievalFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = RetrievalFacade()
    return _facade_instance
