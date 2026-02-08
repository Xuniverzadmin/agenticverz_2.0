# Layer: L4 — HOC Spine (Service)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (aos_sdk.access calls)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: external data (via connectors)
#   Writes: none
# Role: Unified mediation layer for all external data access
# Callers: L2 API routes, skill execution
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-065

"""
Module: retrieval_mediator
Purpose: All external data access must route through this layer.

This is the CENTRAL CHOKE POINT for data retrieval.
Any data access from LLM-controlled code MUST go through here.

Imports (Dependencies):
    - None (interfaces defined here, implementations injected)

Exports (Provides):
    - RetrievalMediator: Main mediation class
    - MediatedResult: Result of a mediated access
    - MediationDeniedError: Raised when access denied
    - get_retrieval_mediator(): Factory to get singleton

Wiring Points:
    - Called from: L2 API route /api/v1/mediation/access
    - Calls: PolicyEngine (injected), ConnectorRegistry (injected)

Invariant: Deny-by-default. All access blocked unless explicitly allowed.

Acceptance Criteria:
    - [x] AC-065-01: All data access routes through mediator
    - [x] AC-065-02: Deny-by-default enforced
    - [x] AC-065-03: Evidence emitted for every access
    - [x] AC-065-04: Policy check before connector
    - [x] AC-065-05: Tenant isolation enforced
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger("nova.services.mediation.retrieval_mediator")


class MediationAction(str, Enum):
    """Allowed mediation actions."""
    QUERY = "query"
    RETRIEVE = "retrieve"
    SEARCH = "search"
    LIST = "list"


@dataclass
class MediatedResult:
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


@dataclass
class PolicyCheckResult:
    """Result of policy check."""
    allowed: bool
    reason: str
    blocking_policy_id: Optional[str] = None
    snapshot_id: Optional[str] = None


@dataclass
class EvidenceRecord:
    """Evidence record for a mediated access."""
    id: str
    tenant_id: str
    run_id: str
    plane_id: str
    connector_id: str
    action: str
    query_hash: str
    doc_ids: List[str]
    token_count: int
    policy_snapshot_id: Optional[str]
    requested_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]


class MediationDeniedError(Exception):
    """Raised when mediation denies access."""

    def __init__(
        self,
        reason: str,
        policy_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ):
        self.reason = reason
        self.policy_id = policy_id
        self.tenant_id = tenant_id
        self.run_id = run_id
        super().__init__(f"Access denied: {reason}")


@runtime_checkable
class Connector(Protocol):
    """Protocol for connectors."""
    id: str

    async def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute connector action."""
        ...


@runtime_checkable
class ConnectorRegistry(Protocol):
    """Protocol for connector registry."""

    async def resolve(
        self,
        tenant_id: str,
        plane_id: str,
    ) -> Optional[Connector]:
        """Resolve connector for plane."""
        ...


@runtime_checkable
class PolicyChecker(Protocol):
    """Protocol for policy checking."""

    async def check_access(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
    ) -> PolicyCheckResult:
        """Check if access is allowed."""
        ...


@runtime_checkable
class EvidenceService(Protocol):
    """Protocol for evidence recording."""

    async def record(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        connector_id: str,
        action: str,
        query_hash: str,
        doc_ids: List[str],
        token_count: int,
        policy_snapshot_id: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
        duration_ms: Optional[int],
    ) -> EvidenceRecord:
        """Record evidence of data access."""
        ...


class RetrievalMediator:
    """
    Unified mediation layer for all external data access.

    Flow:
    1. Receive access request (plane_id, action, payload)
    2. Tenant isolation check
    3. Policy check (deny-by-default)
    4. Connector resolution (plane -> data source)
    5. Execute access through connector
    6. Emit retrieval evidence
    7. Return result

    All data access from LLM-controlled code MUST go through this layer.
    """

    def __init__(
        self,
        policy_checker: Optional[PolicyChecker] = None,
        connector_registry: Optional[ConnectorRegistry] = None,
        evidence_service: Optional[EvidenceService] = None,
    ):
        self.policy_checker = policy_checker
        self.connector_registry = connector_registry
        self.evidence_service = evidence_service
        self._default_deny = True  # INVARIANT: deny-by-default

    async def access(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
        payload: Dict[str, Any],
        requesting_tenant_id: Optional[str] = None,
    ) -> MediatedResult:
        """
        Mediated access to external data.

        Args:
            tenant_id: Tenant owning the data
            run_id: Run context for this access
            plane_id: Knowledge plane to access (e.g., "documents", "database")
            action: Action to perform (query, retrieve, etc.)
            payload: Action-specific payload
            requesting_tenant_id: Tenant making the request (for isolation check)

        Returns:
            MediatedResult with data and evidence

        Raises:
            MediationDeniedError: If access is denied
        """
        request_time = datetime.now(timezone.utc)
        query_hash = self._hash_payload(payload)

        # Step 0: Tenant isolation check (INV-003: CONN-INV-001)
        if requesting_tenant_id and requesting_tenant_id != tenant_id:
            logger.warning("mediation.tenant_isolation_violation", extra={
                "requesting_tenant_id": requesting_tenant_id,
                "target_tenant_id": tenant_id,
                "run_id": run_id,
                "plane_id": plane_id,
            })
            raise MediationDeniedError(
                reason="Cross-tenant access denied",
                tenant_id=tenant_id,
                run_id=run_id,
            )

        # Step 1: Policy check (deny-by-default)
        policy_result = await self._check_policy(
            tenant_id=tenant_id,
            run_id=run_id,
            plane_id=plane_id,
            action=action,
        )

        if not policy_result.allowed:
            logger.warning("mediation.denied", extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
                "plane_id": plane_id,
                "action": action,
                "reason": policy_result.reason,
                "policy_id": policy_result.blocking_policy_id,
            })
            raise MediationDeniedError(
                reason=policy_result.reason,
                policy_id=policy_result.blocking_policy_id,
                tenant_id=tenant_id,
                run_id=run_id,
            )

        # Step 2: Resolve connector
        connector = await self._resolve_connector(
            tenant_id=tenant_id,
            plane_id=plane_id,
        )

        if connector is None:
            raise MediationDeniedError(
                reason=f"No connector found for plane {plane_id}",
                tenant_id=tenant_id,
                run_id=run_id,
            )

        # Step 3: Execute through connector
        try:
            result = await connector.execute(action, payload)
        except Exception as e:
            logger.error("mediation.connector_error", extra={
                "plane_id": plane_id,
                "connector_id": connector.id,
                "error": str(e),
                "tenant_id": tenant_id,
                "run_id": run_id,
            })
            raise MediationDeniedError(
                reason=f"Connector error: {e}",
                tenant_id=tenant_id,
                run_id=run_id,
            )

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - request_time).total_seconds() * 1000)

        # Step 4: Emit evidence
        evidence = await self._record_evidence(
            tenant_id=tenant_id,
            run_id=run_id,
            plane_id=plane_id,
            connector_id=connector.id,
            action=action,
            query_hash=query_hash,
            doc_ids=result.get("doc_ids", []),
            token_count=result.get("token_count", 0),
            policy_snapshot_id=policy_result.snapshot_id,
            requested_at=request_time,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

        logger.info("mediation.success", extra={
            "tenant_id": tenant_id,
            "run_id": run_id,
            "plane_id": plane_id,
            "evidence_id": evidence.id if evidence else "none",
            "tokens": result.get("token_count", 0),
            "connector_id": connector.id,
        })

        return MediatedResult(
            success=True,
            data=result.get("data"),
            evidence_id=evidence.id if evidence else "unrecorded",
            connector_id=connector.id,
            tokens_consumed=result.get("token_count", 0),
            query_hash=query_hash,
            timestamp=request_time.isoformat(),
            tenant_id=tenant_id,
            run_id=run_id,
        )

    async def _check_policy(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        action: str,
    ) -> PolicyCheckResult:
        """
        Check if access is allowed by policy.

        INVARIANT: Deny-by-default.
        If no policy checker is configured, access is DENIED.
        """
        if self.policy_checker is None:
            if self._default_deny:
                return PolicyCheckResult(
                    allowed=False,
                    reason="No policy checker configured (deny-by-default)",
                )
            # Only for testing - should never happen in production
            logger.warning("mediation.no_policy_checker_allow", extra={
                "tenant_id": tenant_id,
                "plane_id": plane_id,
            })
            return PolicyCheckResult(allowed=True, reason="No policy checker")

        return await self.policy_checker.check_access(
            tenant_id=tenant_id,
            run_id=run_id,
            plane_id=plane_id,
            action=action,
        )

    async def _resolve_connector(
        self,
        tenant_id: str,
        plane_id: str,
    ) -> Optional[Connector]:
        """Resolve connector for the given plane."""
        if self.connector_registry is None:
            logger.warning("mediation.no_connector_registry", extra={
                "tenant_id": tenant_id,
                "plane_id": plane_id,
            })
            return None

        return await self.connector_registry.resolve(
            tenant_id=tenant_id,
            plane_id=plane_id,
        )

    async def _record_evidence(
        self,
        tenant_id: str,
        run_id: str,
        plane_id: str,
        connector_id: str,
        action: str,
        query_hash: str,
        doc_ids: List[str],
        token_count: int,
        policy_snapshot_id: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
        duration_ms: Optional[int],
    ) -> Optional[EvidenceRecord]:
        """Record evidence of data access."""
        if self.evidence_service is None:
            logger.warning("mediation.no_evidence_service", extra={
                "tenant_id": tenant_id,
                "run_id": run_id,
            })
            return None

        return await self.evidence_service.record(
            tenant_id=tenant_id,
            run_id=run_id,
            plane_id=plane_id,
            connector_id=connector_id,
            action=action,
            query_hash=query_hash,
            doc_ids=doc_ids,
            token_count=token_count,
            policy_snapshot_id=policy_snapshot_id,
            requested_at=requested_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        """Create deterministic hash of payload for audit."""
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]


# Singleton instance
_retrieval_mediator: Optional[RetrievalMediator] = None


def get_retrieval_mediator() -> RetrievalMediator:
    """
    Get or create the singleton RetrievalMediator.

    Default wiring (Phase 4):
    - Connector resolution is backed by the persisted knowledge plane registry (SSOT).
    - Evidence recording is backed by the retrieval_evidence table (append-only).
    - Policy checking is deny-by-default and allows only when the run's persisted
      policy snapshot includes an explicit plane allowlist (Phase 6).
    """
    global _retrieval_mediator

    if _retrieval_mediator is None:
        from app.hoc.cus.hoc_spine.services.knowledge_plane_connector_registry_engine import (
            get_db_knowledge_plane_connector_registry,
        )
        from app.hoc.cus.hoc_spine.services.retrieval_evidence_engine import (
            get_db_retrieval_evidence_service,
        )
        from app.hoc.cus.hoc_spine.services.retrieval_policy_checker_engine import (
            get_db_policy_snapshot_policy_checker,
        )

        _retrieval_mediator = RetrievalMediator(
            policy_checker=get_db_policy_snapshot_policy_checker(),
            connector_registry=get_db_knowledge_plane_connector_registry(),
            evidence_service=get_db_retrieval_evidence_service(),
        )
        logger.info(
            "retrieval_mediator.created",
            extra={
                "has_policy_checker": True,
                "has_connector_registry": True,
                "has_evidence_service": True,
            },
        )

    return _retrieval_mediator


def configure_retrieval_mediator(
    policy_checker: Optional[PolicyChecker] = None,
    connector_registry: Optional[ConnectorRegistry] = None,
    evidence_service: Optional[EvidenceService] = None,
) -> RetrievalMediator:
    """
    Configure the singleton RetrievalMediator with dependencies.

    Call this at startup to inject real implementations.
    """
    global _retrieval_mediator

    _retrieval_mediator = RetrievalMediator(
        policy_checker=policy_checker,
        connector_registry=connector_registry,
        evidence_service=evidence_service,
    )

    logger.info("retrieval_mediator.configured", extra={
        "has_policy_checker": policy_checker is not None,
        "has_connector_registry": connector_registry is not None,
        "has_evidence_service": evidence_service is not None,
    })

    return _retrieval_mediator
