# Layer: L6 — Driver
# Product: system-wide
# Role: Worker discovery, status queries, capability registry
# Callers: L2 APIs, L5 workers
# Reference: PIN-242 (Baseline Freeze)
# capability_id: CAP-008

"""
Worker Registry Service (M21)

Provides:
- Dynamic worker discovery from database
- Worker status and capability queries
- Per-tenant worker configuration
- Worker availability checks
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.tenant import WorkerConfig, WorkerRegistry

logger = logging.getLogger("nova.services.worker_registry")


class WorkerRegistryError(Exception):
    """Base exception for worker registry errors."""

    pass


class WorkerNotFoundError(WorkerRegistryError):
    """Raised when a worker is not found."""

    pass


class WorkerUnavailableError(WorkerRegistryError):
    """Raised when a worker is not available."""

    pass


class WorkerRegistryService:
    """Service for worker registry operations."""

    def __init__(self, session: Session):
        self.session = session

    # ============== Worker Queries ==============

    def get_worker(self, worker_id: str) -> Optional[WorkerRegistry]:
        """Get a worker by ID."""
        return self.session.get(WorkerRegistry, worker_id)

    def get_worker_or_raise(self, worker_id: str) -> WorkerRegistry:
        """Get a worker by ID, raising if not found."""
        worker = self.get_worker(worker_id)
        if not worker:
            raise WorkerNotFoundError(f"Worker '{worker_id}' not found")
        return worker

    def list_workers(
        self,
        status: Optional[str] = None,
        public_only: bool = True,
    ) -> List[WorkerRegistry]:
        """List all workers, optionally filtered."""
        stmt = select(WorkerRegistry)
        if status:
            stmt = stmt.where(WorkerRegistry.status == status)
        if public_only:
            stmt = stmt.where(WorkerRegistry.is_public == True)
        stmt = stmt.order_by(WorkerRegistry.name)
        return list(self.session.exec(stmt))

    def list_available_workers(self) -> List[WorkerRegistry]:
        """List only available (runnable) workers."""
        return self.list_workers(status="available")

    def is_worker_available(self, worker_id: str) -> bool:
        """Check if a worker is available for execution."""
        worker = self.get_worker(worker_id)
        if not worker:
            return False
        return worker.status == "available"

    # ============== Worker Details ==============

    def get_worker_details(self, worker_id: str) -> Dict[str, Any]:
        """Get detailed worker information including schemas."""
        worker = self.get_worker_or_raise(worker_id)

        # Parse JSON fields
        moats = []
        if worker.moats_json:
            try:
                moats = json.loads(worker.moats_json)
            except json.JSONDecodeError:
                pass

        default_config = {}
        if worker.default_config_json:
            try:
                default_config = json.loads(worker.default_config_json)
            except json.JSONDecodeError:
                pass

        input_schema = {}
        if worker.input_schema_json:
            try:
                input_schema = json.loads(worker.input_schema_json)
            except json.JSONDecodeError:
                pass

        output_schema = {}
        if worker.output_schema_json:
            try:
                output_schema = json.loads(worker.output_schema_json)
            except json.JSONDecodeError:
                pass

        return {
            "id": worker.id,
            "name": worker.name,
            "description": worker.description,
            "version": worker.version,
            "status": worker.status,
            "is_public": worker.is_public,
            "moats": moats,
            "default_config": default_config,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "tokens_per_run_estimate": worker.tokens_per_run_estimate,
            "cost_per_run_cents": worker.cost_per_run_cents,
            "created_at": worker.created_at.isoformat() if worker.created_at else None,
            "updated_at": worker.updated_at.isoformat() if worker.updated_at else None,
        }

    def get_worker_summary(self, worker_id: str) -> Dict[str, Any]:
        """Get summary worker information (for listings)."""
        worker = self.get_worker_or_raise(worker_id)

        moats = []
        if worker.moats_json:
            try:
                moats = json.loads(worker.moats_json)
            except json.JSONDecodeError:
                pass

        return {
            "id": worker.id,
            "name": worker.name,
            "description": worker.description,
            "version": worker.version,
            "status": worker.status,
            "moats": moats,
            "tokens_per_run_estimate": worker.tokens_per_run_estimate,
            "cost_per_run_cents": worker.cost_per_run_cents,
        }

    def list_worker_summaries(
        self,
        status: Optional[str] = None,
        public_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """List worker summaries."""
        workers = self.list_workers(status=status, public_only=public_only)
        return [self.get_worker_summary(w.id) for w in workers]

    # ============== Worker Management ==============

    def register_worker(
        self,
        worker_id: str,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        status: str = "available",
        is_public: bool = True,
        moats: Optional[List[str]] = None,
        default_config: Optional[Dict] = None,
        input_schema: Optional[Dict] = None,
        output_schema: Optional[Dict] = None,
        tokens_per_run_estimate: Optional[int] = None,
        cost_per_run_cents: Optional[int] = None,
    ) -> WorkerRegistry:
        """Register a new worker."""
        existing = self.get_worker(worker_id)
        if existing:
            raise WorkerRegistryError(f"Worker '{worker_id}' already exists")

        worker = WorkerRegistry(
            id=worker_id,
            name=name,
            description=description,
            version=version,
            status=status,
            is_public=is_public,
            moats_json=json.dumps(moats) if moats else None,
            default_config_json=json.dumps(default_config) if default_config else None,
            input_schema_json=json.dumps(input_schema) if input_schema else None,
            output_schema_json=json.dumps(output_schema) if output_schema else None,
            tokens_per_run_estimate=tokens_per_run_estimate,
            cost_per_run_cents=cost_per_run_cents,
        )

        self.session.add(worker)
        self.session.commit()
        self.session.refresh(worker)

        logger.info("worker_registered", extra={"worker_id": worker_id})
        return worker

    def update_worker_status(self, worker_id: str, status: str) -> WorkerRegistry:
        """Update worker status."""
        worker = self.get_worker_or_raise(worker_id)
        worker.status = status
        self.session.add(worker)
        self.session.commit()
        self.session.refresh(worker)
        logger.info("worker_status_updated", extra={"worker_id": worker_id, "status": status})
        return worker

    def deprecate_worker(self, worker_id: str) -> WorkerRegistry:
        """Mark a worker as deprecated."""
        return self.update_worker_status(worker_id, "deprecated")

    # ============== Per-Tenant Configuration ==============

    def get_tenant_worker_config(
        self,
        tenant_id: str,
        worker_id: str,
    ) -> Optional[WorkerConfig]:
        """Get tenant-specific worker configuration."""
        stmt = select(WorkerConfig).where(
            WorkerConfig.tenant_id == tenant_id,
            WorkerConfig.worker_id == worker_id,
        )
        return self.session.exec(stmt).first()

    def set_tenant_worker_config(
        self,
        tenant_id: str,
        worker_id: str,
        enabled: bool = True,
        config: Optional[Dict] = None,
        brand: Optional[Dict] = None,
        max_runs_per_day: Optional[int] = None,
        max_tokens_per_run: Optional[int] = None,
    ) -> WorkerConfig:
        """Set or update tenant-specific worker configuration."""
        # Verify worker exists
        self.get_worker_or_raise(worker_id)

        existing = self.get_tenant_worker_config(tenant_id, worker_id)

        if existing:
            existing.enabled = enabled
            existing.config_json = json.dumps(config) if config else existing.config_json
            existing.brand_json = json.dumps(brand) if brand else existing.brand_json
            existing.max_runs_per_day = max_runs_per_day if max_runs_per_day is not None else existing.max_runs_per_day
            existing.max_tokens_per_run = (
                max_tokens_per_run if max_tokens_per_run is not None else existing.max_tokens_per_run
            )
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            config_obj = WorkerConfig(
                tenant_id=tenant_id,
                worker_id=worker_id,
                enabled=enabled,
                config_json=json.dumps(config) if config else None,
                brand_json=json.dumps(brand) if brand else None,
                max_runs_per_day=max_runs_per_day,
                max_tokens_per_run=max_tokens_per_run,
            )
            self.session.add(config_obj)
            self.session.commit()
            self.session.refresh(config_obj)
            return config_obj

    def list_tenant_worker_configs(self, tenant_id: str) -> List[WorkerConfig]:
        """List all worker configurations for a tenant."""
        stmt = select(WorkerConfig).where(WorkerConfig.tenant_id == tenant_id)
        return list(self.session.exec(stmt))

    def get_effective_worker_config(
        self,
        tenant_id: str,
        worker_id: str,
    ) -> Dict[str, Any]:
        """
        Get effective worker configuration, merging tenant overrides with defaults.
        """
        worker = self.get_worker_or_raise(worker_id)
        tenant_config = self.get_tenant_worker_config(tenant_id, worker_id)

        # Start with worker defaults
        default_config = {}
        if worker.default_config_json:
            try:
                default_config = json.loads(worker.default_config_json)
            except json.JSONDecodeError:
                pass

        default_brand = {}

        # Apply tenant overrides
        if tenant_config:
            if tenant_config.config_json:
                try:
                    tenant_overrides = json.loads(tenant_config.config_json)
                    default_config.update(tenant_overrides)
                except json.JSONDecodeError:
                    pass

            if tenant_config.brand_json:
                try:
                    default_brand = json.loads(tenant_config.brand_json)
                except json.JSONDecodeError:
                    pass

        return {
            "worker_id": worker_id,
            "enabled": tenant_config.enabled if tenant_config else True,
            "config": default_config,
            "brand": default_brand,
            "max_runs_per_day": tenant_config.max_runs_per_day if tenant_config else None,
            "max_tokens_per_run": tenant_config.max_tokens_per_run if tenant_config else None,
        }

    def is_worker_enabled_for_tenant(self, tenant_id: str, worker_id: str) -> bool:
        """Check if a worker is enabled for a tenant."""
        config = self.get_tenant_worker_config(tenant_id, worker_id)
        if config:
            return config.enabled
        # Default to enabled if no specific config
        return True

    # ============== Worker Capability Queries ==============

    def get_workers_for_tenant(
        self,
        tenant_id: str,
        include_disabled: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all workers available to a tenant with their effective configs.
        """
        workers = self.list_available_workers()
        result = []

        for worker in workers:
            effective = self.get_effective_worker_config(tenant_id, worker.id)

            if not include_disabled and not effective["enabled"]:
                continue

            moats = []
            if worker.moats_json:
                try:
                    moats = json.loads(worker.moats_json)
                except json.JSONDecodeError:
                    pass

            result.append(
                {
                    "id": worker.id,
                    "name": worker.name,
                    "description": worker.description,
                    "version": worker.version,
                    "status": worker.status,
                    "moats": moats,
                    "enabled": effective["enabled"],
                    "has_custom_config": bool(effective["config"]),
                    "has_custom_brand": bool(effective["brand"]),
                    "tokens_per_run_estimate": worker.tokens_per_run_estimate,
                    "cost_per_run_cents": worker.cost_per_run_cents,
                }
            )

        return result


# ============== Factory Function ==============


def get_worker_registry_service(session: Session) -> WorkerRegistryService:
    """Get a WorkerRegistryService instance."""
    return WorkerRegistryService(session)


__all__ = [
    "WorkerRegistryService",
    "WorkerRegistryError",
    "WorkerNotFoundError",
    "WorkerUnavailableError",
    "get_worker_registry_service",
]
