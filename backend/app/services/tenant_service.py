"""
Tenant Service (M21)

Provides:
- Tenant CRUD operations
- API key management (create, revoke, list)
- Quota enforcement (runs per day, tokens per month)
- Usage tracking and metering
- Plan management
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlmodel import Session, func, select

from ..models.tenant import (
    PLAN_QUOTAS,
    APIKey,
    AuditLog,
    Tenant,
    UsageRecord,
    WorkerRun,
)

logger = logging.getLogger("nova.services.tenant")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TenantServiceError(Exception):
    """Base exception for tenant service errors."""

    pass


class QuotaExceededError(TenantServiceError):
    """Raised when a quota limit is exceeded."""

    def __init__(self, quota_name: str, limit: int, current: int):
        self.quota_name = quota_name
        self.limit = limit
        self.current = current
        super().__init__(f"{quota_name} quota exceeded: {current}/{limit}")


class TenantService:
    """Service for tenant management."""

    def __init__(self, session: Session):
        self.session = session

    # ============== Tenant Operations ==============

    def create_tenant(
        self,
        name: str,
        slug: str,
        clerk_org_id: Optional[str] = None,
        plan: str = "free",
        billing_email: Optional[str] = None,
    ) -> Tenant:
        """Create a new tenant."""
        # Check slug uniqueness
        existing = self.session.exec(select(Tenant).where(Tenant.slug == slug)).first()
        if existing:
            raise TenantServiceError(f"Tenant with slug '{slug}' already exists")

        # Get plan quotas
        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])

        tenant = Tenant(
            name=name,
            slug=slug,
            clerk_org_id=clerk_org_id,
            plan=plan,
            billing_email=billing_email,
            max_workers=quotas["max_workers"],
            max_runs_per_day=quotas["max_runs_per_day"],
            max_concurrent_runs=quotas["max_concurrent_runs"],
            max_tokens_per_month=quotas["max_tokens_per_month"],
            max_api_keys=quotas["max_api_keys"],
        )

        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)

        logger.info("tenant_created", extra={"tenant_id": tenant.id, "slug": slug})
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.session.get(Tenant, tenant_id)

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return self.session.exec(select(Tenant).where(Tenant.slug == slug)).first()

    def update_tenant_plan(self, tenant_id: str, plan: str) -> Tenant:
        """Update tenant plan and quotas."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise TenantServiceError("Tenant not found")

        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])

        tenant.plan = plan
        tenant.max_workers = quotas["max_workers"]
        tenant.max_runs_per_day = quotas["max_runs_per_day"]
        tenant.max_concurrent_runs = quotas["max_concurrent_runs"]
        tenant.max_tokens_per_month = quotas["max_tokens_per_month"]
        tenant.max_api_keys = quotas["max_api_keys"]
        tenant.updated_at = utc_now()

        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)

        logger.info("tenant_plan_updated", extra={"tenant_id": tenant_id, "plan": plan})
        return tenant

    def suspend_tenant(self, tenant_id: str, reason: str) -> Tenant:
        """Suspend a tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise TenantServiceError("Tenant not found")

        tenant.status = "suspended"
        tenant.suspended_reason = reason
        tenant.updated_at = utc_now()

        self.session.add(tenant)
        self.session.commit()

        logger.warning("tenant_suspended", extra={"tenant_id": tenant_id, "reason": reason})
        return tenant

    # ============== API Key Operations ==============

    def create_api_key(
        self,
        tenant_id: str,
        name: str,
        user_id: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        allowed_workers: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_rpm: Optional[int] = None,
        max_concurrent_runs: Optional[int] = None,
    ) -> Tuple[str, APIKey]:
        """
        Create a new API key for a tenant.

        Returns:
            (full_key, APIKey): The full key (only shown once) and the key record
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            raise TenantServiceError("Tenant not found")

        # Check key limit
        key_count = self.session.exec(
            select(func.count(APIKey.id)).where(APIKey.tenant_id == tenant_id, APIKey.status == "active")
        ).one()

        if key_count >= tenant.max_api_keys:
            raise QuotaExceededError("api_keys", tenant.max_api_keys, key_count)

        # Generate key
        full_key, prefix, key_hash = APIKey.generate_key()

        # Set expiry
        expires_at = None
        if expires_in_days:
            expires_at = utc_now() + timedelta(days=expires_in_days)

        api_key = APIKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            key_prefix=prefix,
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

        # Audit log
        self._audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=api_key.id,
            new_value={"name": name, "prefix": prefix},
        )

        logger.info(
            "api_key_created",
            extra={
                "tenant_id": tenant_id,
                "key_id": api_key.id,
                "key_prefix": prefix,
            },
        )

        return full_key, api_key

    def list_api_keys(self, tenant_id: str, include_revoked: bool = False) -> List[APIKey]:
        """List API keys for a tenant."""
        stmt = select(APIKey).where(APIKey.tenant_id == tenant_id)
        if not include_revoked:
            stmt = stmt.where(APIKey.status == "active")
        return list(self.session.exec(stmt))

    def revoke_api_key(
        self,
        key_id: str,
        reason: str = "Manual revocation",
        user_id: Optional[str] = None,
    ) -> APIKey:
        """Revoke an API key."""
        api_key = self.session.get(APIKey, key_id)
        if not api_key:
            raise TenantServiceError("API key not found")

        api_key.status = "revoked"
        api_key.revoked_at = utc_now()
        api_key.revoked_reason = reason

        self.session.add(api_key)
        self.session.commit()

        # Audit log
        self._audit(
            tenant_id=api_key.tenant_id,
            user_id=user_id,
            api_key_id=key_id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=key_id,
            new_value={"reason": reason},
        )

        logger.info("api_key_revoked", extra={"key_id": key_id, "reason": reason})
        return api_key

    # ============== Quota Enforcement ==============

    def check_run_quota(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Check if tenant can create a new run.

        Returns:
            (allowed, reason): Whether allowed and reason if not
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        # Check status
        if tenant.status != "active":
            return False, f"Tenant is {tenant.status}"

        # Reset daily counter if needed
        self._maybe_reset_daily_counter(tenant)

        # Check daily limit
        if tenant.runs_today >= tenant.max_runs_per_day:
            return False, f"Daily run limit ({tenant.max_runs_per_day}) exceeded"

        # Check concurrent runs
        running_count = self.session.exec(
            select(func.count(WorkerRun.id)).where(
                WorkerRun.tenant_id == tenant_id, WorkerRun.status.in_(["queued", "running"])
            )
        ).one()

        if running_count >= tenant.max_concurrent_runs:
            return False, f"Concurrent run limit ({tenant.max_concurrent_runs}) exceeded"

        return True, ""

    def check_token_quota(self, tenant_id: str, tokens_needed: int) -> Tuple[bool, str]:
        """
        Check if tenant has token budget for operation.

        Returns:
            (allowed, reason): Whether allowed and reason if not
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        projected = tenant.tokens_this_month + tokens_needed
        if projected > tenant.max_tokens_per_month:
            return False, f"Monthly token limit ({tenant.max_tokens_per_month:,}) would be exceeded"

        return True, ""

    def increment_usage(self, tenant_id: str, tokens: int = 0) -> None:
        """Increment usage counters for a tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return

        self._maybe_reset_daily_counter(tenant)
        tenant.increment_usage(tokens)
        self.session.add(tenant)
        self.session.commit()

    def _maybe_reset_daily_counter(self, tenant: Tenant) -> None:
        """Reset daily run counter if new day."""
        now = utc_now()
        if tenant.last_run_reset_at:
            if tenant.last_run_reset_at.date() < now.date():
                tenant.runs_today = 0
                tenant.last_run_reset_at = now
                self.session.add(tenant)
                self.session.commit()
        else:
            tenant.last_run_reset_at = now
            self.session.add(tenant)
            self.session.commit()

    # ============== Usage Recording ==============

    def record_usage(
        self,
        tenant_id: str,
        meter_name: str,
        amount: int,
        unit: str = "count",
        worker_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UsageRecord:
        """Record a usage event for billing."""
        now = utc_now()
        # Period is the current hour
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

    def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get usage summary for a tenant."""
        now = utc_now()
        if not start_date:
            # Default to start of current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = now

        # Get usage records
        stmt = select(UsageRecord).where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.period_start >= start_date,
            UsageRecord.period_end <= end_date,
        )
        records = list(self.session.exec(stmt))

        # Aggregate by meter
        summary = {}
        for record in records:
            if record.meter_name not in summary:
                summary[record.meter_name] = {"total": 0, "unit": record.unit}
            summary[record.meter_name]["total"] += record.amount

        return {
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "meters": summary,
            "total_records": len(records),
        }

    # ============== Run Management ==============

    def create_run(
        self,
        tenant_id: str,
        worker_id: str,
        task: str,
        api_key_id: Optional[str] = None,
        user_id: Optional[str] = None,
        input_json: Optional[str] = None,
    ) -> WorkerRun:
        """Create a new worker run (with quota check)."""
        # Check quota
        allowed, reason = self.check_run_quota(tenant_id)
        if not allowed:
            raise QuotaExceededError("runs", 0, 0)  # Details in reason

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

        # Increment usage counter
        self.increment_usage(tenant_id)

        self.session.commit()
        self.session.refresh(run)

        return run

    def complete_run(
        self,
        run_id: str,
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
        """Mark a run as completed and record usage."""
        run = self.session.get(WorkerRun, run_id)
        if not run:
            raise TenantServiceError("Run not found")

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

        # Record token usage
        if total_tokens > 0:
            tenant = self.get_tenant(run.tenant_id)
            if tenant:
                tenant.tokens_this_month += total_tokens
                self.session.add(tenant)

            self.record_usage(
                tenant_id=run.tenant_id,
                meter_name="tokens_used",
                amount=total_tokens,
                unit="tokens",
                worker_id=run.worker_id,
                api_key_id=run.api_key_id,
            )

        # Record run completion
        self.record_usage(
            tenant_id=run.tenant_id,
            meter_name="worker_runs",
            amount=1,
            unit="count",
            worker_id=run.worker_id,
            api_key_id=run.api_key_id,
            metadata={"success": success, "cost_cents": cost_cents},
        )

        self.session.commit()
        self.session.refresh(run)

        return run

    def list_runs(
        self,
        tenant_id: str,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> List[WorkerRun]:
        """List runs for a tenant."""
        stmt = select(WorkerRun).where(WorkerRun.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(WorkerRun.status == status)
        if worker_id:
            stmt = stmt.where(WorkerRun.worker_id == worker_id)
        stmt = stmt.order_by(WorkerRun.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(stmt))

    # ============== Audit Logging ==============

    def _audit(
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
        """Create an audit log entry."""
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


# ============== Factory Function ==============


def get_tenant_service(session: Session) -> TenantService:
    """Get a TenantService instance."""
    return TenantService(session)


__all__ = [
    "TenantService",
    "TenantServiceError",
    "QuotaExceededError",
    "get_tenant_service",
]
