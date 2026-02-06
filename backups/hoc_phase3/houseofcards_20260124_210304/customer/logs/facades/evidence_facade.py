# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: Evidence Facade - Centralized access to evidence and export operations
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: L2 evidence.py API, SDK
# Allowed Imports: L4 evidence services, L6 (models, db)
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-104 (Evidence Chain API), GAP-105 (Evidence Export API)


"""
Evidence Facade (L4 Domain Logic)

This facade provides the external interface for evidence chain and export operations.
All evidence APIs MUST use this facade instead of directly importing
internal evidence modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes evidence chain management
- Provides unified access to evidence export
- Single point for audit emission

L2 API Routes (GAP-104, GAP-105):
- GET /api/v1/evidence/chains (list evidence chains)
- GET /api/v1/evidence/chains/{id} (get evidence chain)
- POST /api/v1/evidence/chains (create evidence chain)
- GET /api/v1/evidence/chains/{id}/verify (verify chain integrity)
- POST /api/v1/evidence/export (export evidence)
- GET /api/v1/evidence/exports/{id} (get export status)

Usage:
    from app.services.evidence.facade import get_evidence_facade

    facade = get_evidence_facade()

    # List evidence chains
    chains = await facade.list_chains(tenant_id="...")

    # Export evidence
    export = await facade.create_export(tenant_id="...", chain_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
import hashlib
import json

logger = logging.getLogger("nova.services.evidence.facade")


class EvidenceType(str, Enum):
    """Evidence types."""
    EXECUTION = "execution"  # Run execution evidence
    RETRIEVAL = "retrieval"  # Data retrieval evidence
    POLICY = "policy"  # Policy decision evidence
    COST = "cost"  # Cost event evidence
    INCIDENT = "incident"  # Incident evidence


class ExportFormat(str, Enum):
    """Export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class ExportStatus(str, Enum):
    """Export status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvidenceLink:
    """A link in an evidence chain."""
    id: str
    evidence_type: str
    timestamp: str
    hash: str
    previous_hash: Optional[str]
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "evidence_type": self.evidence_type,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "data": self.data,
        }


@dataclass
class EvidenceChain:
    """An evidence chain."""
    id: str
    tenant_id: str
    run_id: Optional[str]
    created_at: str
    root_hash: str
    link_count: int
    links: List[EvidenceLink] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "root_hash": self.root_hash,
            "link_count": self.link_count,
            "links": [l.to_dict() for l in self.links],
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """Result of chain verification."""
    valid: bool
    chain_id: str
    links_verified: int
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "chain_id": self.chain_id,
            "links_verified": self.links_verified,
            "errors": self.errors,
        }


@dataclass
class EvidenceExport:
    """Evidence export request."""
    id: str
    tenant_id: str
    chain_id: str
    format: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "chain_id": self.chain_id,
            "format": self.format,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "download_url": self.download_url,
            "error": self.error,
        }


class EvidenceFacade:
    """
    Facade for evidence chain and export operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    evidence services.

    Layer: L4 (Domain Logic)
    Callers: evidence.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade."""
        # In-memory stores for demo (would be database in production)
        self._chains: Dict[str, EvidenceChain] = {}
        self._exports: Dict[str, EvidenceExport] = {}

    # =========================================================================
    # Evidence Chain Operations (GAP-104)
    # =========================================================================

    async def list_chains(
        self,
        tenant_id: str,
        run_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvidenceChain]:
        """
        List evidence chains.

        Args:
            tenant_id: Tenant ID
            run_id: Optional filter by run
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of EvidenceChain
        """
        results = []
        for chain in self._chains.values():
            if chain.tenant_id != tenant_id:
                continue
            if run_id and chain.run_id != run_id:
                continue
            results.append(chain)

        # Sort by created_at descending
        results.sort(key=lambda c: c.created_at, reverse=True)

        return results[offset:offset + limit]

    async def get_chain(
        self,
        chain_id: str,
        tenant_id: str,
    ) -> Optional[EvidenceChain]:
        """
        Get a specific evidence chain.

        Args:
            chain_id: Chain ID
            tenant_id: Tenant ID for authorization

        Returns:
            EvidenceChain or None if not found
        """
        chain = self._chains.get(chain_id)
        if chain and chain.tenant_id == tenant_id:
            return chain
        return None

    async def create_chain(
        self,
        tenant_id: str,
        run_id: Optional[str] = None,
        initial_evidence: Optional[Dict[str, Any]] = None,
    ) -> EvidenceChain:
        """
        Create a new evidence chain.

        Args:
            tenant_id: Tenant ID
            run_id: Optional associated run ID
            initial_evidence: Optional initial evidence data

        Returns:
            Created EvidenceChain
        """
        logger.info(
            "facade.create_chain",
            extra={"tenant_id": tenant_id, "run_id": run_id}
        )

        now = datetime.now(timezone.utc)
        chain_id = str(uuid.uuid4())

        # Create initial link if evidence provided
        links = []
        if initial_evidence:
            link = self._create_link(
                evidence_type=initial_evidence.get("type", "execution"),
                data=initial_evidence,
                previous_hash=None,
            )
            links.append(link)

        root_hash = links[0].hash if links else self._hash_data({"chain_id": chain_id})

        chain = EvidenceChain(
            id=chain_id,
            tenant_id=tenant_id,
            run_id=run_id,
            created_at=now.isoformat(),
            root_hash=root_hash,
            link_count=len(links),
            links=links,
        )

        self._chains[chain_id] = chain
        return chain

    async def add_evidence(
        self,
        chain_id: str,
        tenant_id: str,
        evidence_type: str,
        data: Dict[str, Any],
    ) -> Optional[EvidenceChain]:
        """
        Add evidence to a chain.

        Args:
            chain_id: Chain ID
            tenant_id: Tenant ID for authorization
            evidence_type: Type of evidence
            data: Evidence data

        Returns:
            Updated EvidenceChain or None if not found
        """
        chain = self._chains.get(chain_id)
        if not chain or chain.tenant_id != tenant_id:
            return None

        # Get previous hash
        previous_hash = chain.links[-1].hash if chain.links else chain.root_hash

        # Create new link
        link = self._create_link(
            evidence_type=evidence_type,
            data=data,
            previous_hash=previous_hash,
        )

        chain.links.append(link)
        chain.link_count = len(chain.links)

        logger.info(
            "facade.add_evidence",
            extra={"chain_id": chain_id, "link_id": link.id}
        )

        return chain

    async def verify_chain(
        self,
        chain_id: str,
        tenant_id: str,
    ) -> VerificationResult:
        """
        Verify chain integrity.

        Args:
            chain_id: Chain ID
            tenant_id: Tenant ID for authorization

        Returns:
            VerificationResult with verification outcome
        """
        chain = self._chains.get(chain_id)
        if not chain or chain.tenant_id != tenant_id:
            return VerificationResult(
                valid=False,
                chain_id=chain_id,
                links_verified=0,
                errors=["Chain not found"],
            )

        errors = []
        links_verified = 0

        # Verify each link
        for i, link in enumerate(chain.links):
            # Verify previous hash linkage
            expected_prev = chain.root_hash if i == 0 else chain.links[i - 1].hash
            if link.previous_hash != expected_prev:
                errors.append(f"Link {link.id}: previous_hash mismatch")
                continue

            # Verify link hash
            computed_hash = self._hash_data({
                "id": link.id,
                "evidence_type": link.evidence_type,
                "timestamp": link.timestamp,
                "previous_hash": link.previous_hash,
                "data": link.data,
            })
            if link.hash != computed_hash:
                errors.append(f"Link {link.id}: hash mismatch")
                continue

            links_verified += 1

        return VerificationResult(
            valid=len(errors) == 0,
            chain_id=chain_id,
            links_verified=links_verified,
            errors=errors,
        )

    def _create_link(
        self,
        evidence_type: str,
        data: Dict[str, Any],
        previous_hash: Optional[str],
    ) -> EvidenceLink:
        """Create a new evidence link."""
        now = datetime.now(timezone.utc)
        link_id = str(uuid.uuid4())

        link_data = {
            "id": link_id,
            "evidence_type": evidence_type,
            "timestamp": now.isoformat(),
            "previous_hash": previous_hash,
            "data": data,
        }

        return EvidenceLink(
            id=link_id,
            evidence_type=evidence_type,
            timestamp=now.isoformat(),
            hash=self._hash_data(link_data),
            previous_hash=previous_hash,
            data=data,
        )

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create deterministic hash of data."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    # =========================================================================
    # Evidence Export Operations (GAP-105)
    # =========================================================================

    async def create_export(
        self,
        tenant_id: str,
        chain_id: str,
        format: str = "json",
    ) -> EvidenceExport:
        """
        Create evidence export request.

        Args:
            tenant_id: Tenant ID
            chain_id: Chain ID to export
            format: Export format (json, csv, pdf)

        Returns:
            EvidenceExport with export status
        """
        logger.info(
            "facade.create_export",
            extra={"tenant_id": tenant_id, "chain_id": chain_id, "format": format}
        )

        # Verify chain exists
        chain = self._chains.get(chain_id)
        if not chain or chain.tenant_id != tenant_id:
            export = EvidenceExport(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                chain_id=chain_id,
                format=format,
                status=ExportStatus.FAILED.value,
                created_at=datetime.now(timezone.utc).isoformat(),
                error="Chain not found",
            )
            self._exports[export.id] = export
            return export

        now = datetime.now(timezone.utc)
        export_id = str(uuid.uuid4())

        # Simulate export (in production, would queue async job)
        export = EvidenceExport(
            id=export_id,
            tenant_id=tenant_id,
            chain_id=chain_id,
            format=format,
            status=ExportStatus.COMPLETED.value,
            created_at=now.isoformat(),
            completed_at=now.isoformat(),
            download_url=f"/api/v1/evidence/exports/{export_id}/download",
        )

        self._exports[export_id] = export
        return export

    async def get_export(
        self,
        export_id: str,
        tenant_id: str,
    ) -> Optional[EvidenceExport]:
        """
        Get export status.

        Args:
            export_id: Export ID
            tenant_id: Tenant ID for authorization

        Returns:
            EvidenceExport or None if not found
        """
        export = self._exports.get(export_id)
        if export and export.tenant_id == tenant_id:
            return export
        return None

    async def list_exports(
        self,
        tenant_id: str,
        chain_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EvidenceExport]:
        """
        List exports.

        Args:
            tenant_id: Tenant ID
            chain_id: Optional filter by chain
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of EvidenceExport
        """
        results = []
        for export in self._exports.values():
            if export.tenant_id != tenant_id:
                continue
            if chain_id and export.chain_id != chain_id:
                continue
            results.append(export)

        # Sort by created_at descending
        results.sort(key=lambda e: e.created_at, reverse=True)

        return results[offset:offset + limit]


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[EvidenceFacade] = None


def get_evidence_facade() -> EvidenceFacade:
    """
    Get the evidence facade instance.

    This is the recommended way to access evidence operations
    from L2 APIs and the SDK.

    Returns:
        EvidenceFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = EvidenceFacade()
    return _facade_instance
