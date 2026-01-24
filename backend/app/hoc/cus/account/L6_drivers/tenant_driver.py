# Layer: L6 — Platform Substrate
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async/sync (DB reads/writes)
# Role: Tenant domain driver - pure data access for tenant operations
# Callers: tenant_engine.py (L4)
# Allowed Imports: L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This driver was extracted from tenant_service.py to enforce L4/L6 separation.
# All DB operations are now in this L6 driver.
# Business logic belongs in the engine (L4), not here.

"""
Tenant Driver (L6)

Pure data access layer for tenant operations.

Provides:
- Tenant CRUD
- Membership CRUD
- API key CRUD
- Usage record CRUD
- Run CRUD
- Audit logging

All methods are pure data access - no business logic.
Returns snapshot dataclasses or ORM models for mutations.
Business logic belongs in the engine (L4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Optional, cast

from sqlmodel import Session, func, select

from app.hoc.cus.general.L5_utils.time import utc_now
from app.models.tenant import (
    APIKey,
    AuditLog,
    Tenant,
    TenantMembership,
    UsageRecord,
    User,
    WorkerRun,
)


# =============================================================================
# Snapshot Dataclasses
# =============================================================================


@dataclass
class TenantCoreSnapshot:
    """Core tenant data for engine operations."""
    id: str
    name: str
    slug: str
    status: str
    plan: str
    max_workers: int
    max_runs_per_day: int
    max_concurrent_runs: int
    max_tokens_per_month: int
    max_api_keys: int
    runs_today: int
    runs_this_month: int
    tokens_this_month: int
    last_run_reset_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class RunCountSnapshot:
    """Running count for quota checks."""
    count: int


@dataclass
class APIKeySnapshot:
    """API key data snapshot."""
    id: str
    tenant_id: str
    user_id: Optional[str]
    name: str
    key_prefix: str
    status: str
    permissions: List[str]
    allowed_workers: Optional[List[str]]
    rate_limit_rpm: Optional[int]
    max_concurrent_runs: Optional[int]
    expires_at: Optional[datetime]
    created_at: datetime


@dataclass
class UsageRecordSnapshot:
    """Usage record data."""
    id: str
    tenant_id: str
    meter_name: str
    amount: int
    unit: str
    period_start: datetime
    period_end: datetime


@dataclass
class RunSnapshot:
    """Worker run snapshot."""
    id: str
    tenant_id: str
    worker_id: str
    task: str
    status: str
    success: Optional[bool]
    total_tokens: int
    total_latency_ms: int
    cost_cents: int
    created_at: datetime
    completed_at: Optional[datetime]


# =============================================================================
# Tenant Driver
# =============================================================================


class TenantDriver:
    """
    L6 Driver for tenant data access.

    All methods are pure data access - no business logic.
    Returns snapshots or ORM models for mutations.
    """

    def __init__(self, session: Session):
        self.session = session

    # ============== Tenant Operations ==============

    def fetch_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Fetch tenant by ID (returns ORM model for mutations)."""
        return self.session.get(Tenant, tenant_id)

    def fetch_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Fetch tenant by slug."""
        return self.session.exec(select(Tenant).where(Tenant.slug == slug)).first()

    def fetch_tenant_snapshot(self, tenant_id: str) -> Optional[TenantCoreSnapshot]:
        """Fetch tenant as snapshot."""
        tenant = self.fetch_tenant_by_id(tenant_id)
        if not tenant:
            return None
        return TenantCoreSnapshot(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
            plan=tenant.plan,
            max_workers=tenant.max_workers,
            max_runs_per_day=tenant.max_runs_per_day,
            max_concurrent_runs=tenant.max_concurrent_runs,
            max_tokens_per_month=tenant.max_tokens_per_month,
            max_api_keys=tenant.max_api_keys,
            runs_today=tenant.runs_today,
            runs_this_month=tenant.runs_this_month,
            tokens_this_month=tenant.tokens_this_month,
            last_run_reset_at=tenant.last_run_reset_at,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

    def insert_tenant(
        self,
        name: str,
        slug: str,
        plan: str,
        max_workers: int,
        max_runs_per_day: int,
        max_concurrent_runs: int,
        max_tokens_per_month: int,
        max_api_keys: int,
        clerk_org_id: Optional[str] = None,
        billing_email: Optional[str] = None,
    ) -> Tenant:
        """Insert a new tenant."""
        tenant = Tenant(
            name=name,
            slug=slug,
            clerk_org_id=clerk_org_id,
            plan=plan,
            billing_email=billing_email,
            max_workers=max_workers,
            max_runs_per_day=max_runs_per_day,
            max_concurrent_runs=max_concurrent_runs,
            max_tokens_per_month=max_tokens_per_month,
            max_api_keys=max_api_keys,
        )
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def update_tenant_plan(
        self,
        tenant: Tenant,
        plan: str,
        max_workers: int,
        max_runs_per_day: int,
        max_concurrent_runs: int,
        max_tokens_per_month: int,
        max_api_keys: int,
    ) -> Tenant:
        """Update tenant plan and quotas."""
        tenant.plan = plan
        tenant.max_workers = max_workers
        tenant.max_runs_per_day = max_runs_per_day
        tenant.max_concurrent_runs = max_concurrent_runs
        tenant.max_tokens_per_month = max_tokens_per_month
        tenant.max_api_keys = max_api_keys
        tenant.updated_at = utc_now()
        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)
        return tenant

    def update_tenant_status(
        self,
        tenant: Tenant,
        status: str,
        suspended_reason: Optional[str] = None,
    ) -> Tenant:
        """Update tenant status."""
        tenant.status = status
        if suspended_reason:
            tenant.suspended_reason = suspended_reason
        tenant.updated_at = utc_now()
        self.session.add(tenant)
        self.session.commit()
        return tenant

    def update_tenant_usage(
        self,
        tenant: Tenant,
        runs_today: Optional[int] = None,
        runs_this_month: Optional[int] = None,
        tokens_this_month: Optional[int] = None,
        last_run_reset_at: Optional[datetime] = None,
    ) -> Tenant:
        """Update tenant usage counters."""
        if runs_today is not None:
            tenant.runs_today = runs_today
        if runs_this_month is not None:
            tenant.runs_this_month = runs_this_month
        if tokens_this_month is not None:
            tenant.tokens_this_month = tokens_this_month
        if last_run_reset_at is not None:
            tenant.last_run_reset_at = last_run_reset_at
        self.session.add(tenant)
        self.session.commit()
        return tenant

    def increment_tenant_usage(self, tenant: Tenant, tokens: int = 0) -> None:
        """Increment usage counters."""
        tenant.increment_usage(tokens)
        self.session.add(tenant)
        self.session.commit()

    # ============== Membership Operations ==============

    def insert_membership(
        self,
        tenant_id: str,
        user_id: str,
        role: str = "owner",
        set_as_default: bool = True,
    ) -> TenantMembership:
        """Insert a new membership."""
        membership = TenantMembership(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(membership)

        if set_as_default:
            user = self.session.get(User, user_id)
            if user:
                user.default_tenant_id = tenant_id
                self.session.add(user)

        self.session.commit()
        return membership

    # ============== API Key Operations ==============

    def count_active_api_keys(self, tenant_id: str) -> int:
        """Count active API keys for tenant."""
        count = self.session.exec(
            select(func.count(APIKey.id)).where(
                APIKey.tenant_id == tenant_id,
                APIKey.status == "active"
            )
        ).one()
        return count or 0

    def insert_api_key(
        self,
        tenant_id: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        user_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        allowed_workers: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
        rate_limit_rpm: Optional[int] = None,
        max_concurrent_runs: Optional[int] = None,
    ) -> APIKey:
        """Insert a new API key."""
        api_key = APIKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            permissions_json=json.dumps(permissions or ["run:*", "read:*"]),
            allowed_workers_json=json.dumps(allowed_workers) if allowed_workers else None,
            rate_limit_rpm=rate_limit_rpm,
            max_concurrent_runs=max_concurrent_runs,
            expires_at=expires_at,
        )
        self.session.add(api_key)
        self.session.commit()
        self.session.refresh(api_key)
        return api_key

    def fetch_api_keys(
        self,
        tenant_id: str,
        include_revoked: bool = False,
    ) -> List[APIKey]:
        """Fetch API keys for tenant."""
        stmt = select(APIKey).where(APIKey.tenant_id == tenant_id)
        if not include_revoked:
            stmt = stmt.where(APIKey.status == "active")
        return list(self.session.exec(stmt))

    def fetch_api_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """Fetch API key by ID."""
        return self.session.get(APIKey, key_id)

    def update_api_key_revoked(
        self,
        api_key: APIKey,
        reason: str,
    ) -> APIKey:
        """Mark API key as revoked."""
        api_key.status = "revoked"
        api_key.revoked_at = utc_now()
        api_key.revoked_reason = reason
        self.session.add(api_key)
        self.session.commit()
        return api_key

    # ============== Run Count Operations ==============

    def count_running_runs(self, tenant_id: str) -> int:
        """Count queued or running runs for tenant."""
        count = self.session.exec(
            select(func.count(WorkerRun.id)).where(
                WorkerRun.tenant_id == tenant_id,
                cast(Any, WorkerRun.status).in_(["queued", "running"])
            )
        ).one()
        return count or 0

    # ============== Run Operations ==============

    def insert_run(
        self,
        tenant_id: str,
        worker_id: str,
        task: str,
        api_key_id: Optional[str] = None,
        user_id: Optional[str] = None,
        input_json: Optional[str] = None,
    ) -> WorkerRun:
        """Insert a new worker run."""
        run = WorkerRun(
            tenant_id=tenant_id,
            worker_id=worker_id,
            task=task,
            api_key_id=api_key_id,
            user_id=user_id,
            input_json=input_json,
            status="queued",
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def fetch_run_by_id(self, run_id: str) -> Optional[WorkerRun]:
        """Fetch run by ID."""
        return self.session.get(WorkerRun, run_id)

    def update_run_completed(
        self,
        run: WorkerRun,
        success: bool,
        output_json: Optional[str] = None,
        replay_token_json: Optional[str] = None,
        total_tokens: int = 0,
        total_latency_ms: int = 0,
        stages_completed: int = 0,
        recoveries: int = 0,
        policy_violations: int = 0,
        cost_cents: int = 0,
        error: Optional[str] = None,
    ) -> WorkerRun:
        """Update run as completed."""
        run.status = "completed" if success else "failed"
        run.success = success
        run.output_json = output_json
        run.replay_token_json = replay_token_json
        run.total_tokens = total_tokens
        run.total_latency_ms = total_latency_ms
        run.stages_completed = stages_completed
        run.recoveries = recoveries
        run.policy_violations = policy_violations
        run.cost_cents = cost_cents
        run.error = error
        run.completed_at = utc_now()
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def fetch_runs(
        self,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> List[WorkerRun]:
        """Fetch runs for tenant."""
        stmt = select(WorkerRun).where(WorkerRun.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(WorkerRun.status == status)
        if worker_id:
            stmt = stmt.where(WorkerRun.worker_id == worker_id)
        stmt = stmt.order_by(cast(Any, WorkerRun.created_at).desc()).offset(offset).limit(limit)
        return list(self.session.exec(stmt))

    # ============== Usage Recording ==============

    def insert_usage_record(
        self,
        tenant_id: str,
        meter_name: str,
        amount: int,
        unit: str = "count",
        worker_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        """Insert a usage record."""
        now = utc_now()
        period_start = now.replace(minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(hours=1)

        record = UsageRecord(
            tenant_id=tenant_id,
            meter_name=meter_name,
            amount=amount,
            unit=unit,
            period_start=period_start,
            period_end=period_end,
            worker_id=worker_id,
            api_key_id=api_key_id,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def fetch_usage_records(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[UsageRecord]:
        """Fetch usage records for period."""
        stmt = select(UsageRecord).where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.period_start >= start_date,
            UsageRecord.period_end <= end_date,
        )
        return list(self.session.exec(stmt))

    # ============== Audit Logging ==============

    def insert_audit_log(
        self,
        action: str,
        resource_type: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Insert an audit log entry."""
        log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            api_key_id=api_key_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value_json=json.dumps(old_value) if old_value else None,
            new_value_json=json.dumps(new_value) if new_value else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        self.session.add(log)
        # Don't commit here - let caller control transaction


# =============================================================================
# Factory Function
# =============================================================================


def get_tenant_driver(session: Session) -> TenantDriver:
    """Get a TenantDriver instance."""
    return TenantDriver(session)


__all__ = [
    "TenantDriver",
    "get_tenant_driver",
    # Snapshots
    "TenantCoreSnapshot",
    "RunCountSnapshot",
    "APIKeySnapshot",
    "UsageRecordSnapshot",
    "RunSnapshot",
]
