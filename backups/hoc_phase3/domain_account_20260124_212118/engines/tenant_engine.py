# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync (DB via driver)
# Role: Tenant domain engine - business logic for tenant operations
# Callers: L2 APIs, L5 workers
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, L5, L7 (at runtime)
# Reference: ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# This engine was extracted from tenant_service.py to enforce L4/L6 separation.
# All business logic (quota checks, plan logic, status validation) is here.
# All DB operations are delegated to TenantDriver (L6).

"""
Tenant Engine (L4)

Business logic for tenant operations.

Provides:
- Tenant creation with plan quotas
- Plan upgrades/downgrades
- Quota enforcement (runs per day, tokens per month, concurrent runs)
- API key management with limits
- Run lifecycle with quota checks
- Usage tracking

All DB operations are delegated to TenantDriver (L6).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any, List, Optional, Tuple

from app.hoc.cus.general.utils.time import utc_now
from app.hoc.cus.account.drivers.tenant_driver import TenantDriver, get_tenant_driver
from app.models.tenant import PLAN_QUOTAS, APIKey, Tenant, TenantMembership, WorkerRun

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger("nova.engines.tenant")


# =============================================================================
# Exceptions
# =============================================================================


class TenantEngineError(Exception):
    """Base exception for tenant engine errors."""
    pass


class QuotaExceededError(TenantEngineError):
    """Raised when a quota limit is exceeded."""

    def __init__(self, quota_name: str, limit: int, current: int):
        self.quota_name = quota_name
        self.limit = limit
        self.current = current
        super().__init__(f"{quota_name} quota exceeded: {current}/{limit}")


# =============================================================================
# Tenant Engine
# =============================================================================


class TenantEngine:
    """
    L4 Engine for tenant business logic.

    Handles:
    - Quota decisions
    - Plan logic
    - Status validation
    - Temporal logic (daily counter reset)

    Delegates all DB operations to TenantDriver (L6).
    """

    def __init__(self, session: Session, driver: TenantDriver | None = None):
        self.session = session
        self._driver = driver or get_tenant_driver(session)

    # ============== Tenant Operations ==============

    def create_tenant(
        self,
        name: str,
        slug: str,
        clerk_org_id: Optional[str] = None,
        plan: str = "free",
        billing_email: Optional[str] = None,
    ) -> Tenant:
        """Create a new tenant with plan quotas."""
        # Business logic: Check slug uniqueness
        existing = self._driver.fetch_tenant_by_slug(slug)
        if existing:
            raise TenantEngineError(f"Tenant with slug '{slug}' already exists")

        # Business logic: Apply plan quotas
        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])

        # Delegate to driver
        tenant = self._driver.insert_tenant(
            name=name,
            slug=slug,
            plan=plan,
            max_workers=quotas["max_workers"],
            max_runs_per_day=quotas["max_runs_per_day"],
            max_concurrent_runs=quotas["max_concurrent_runs"],
            max_tokens_per_month=quotas["max_tokens_per_month"],
            max_api_keys=quotas["max_api_keys"],
            clerk_org_id=clerk_org_id,
            billing_email=billing_email,
        )

        logger.info("tenant_created", extra={"tenant_id": tenant.id, "slug": slug})
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._driver.fetch_tenant_by_id(tenant_id)

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return self._driver.fetch_tenant_by_slug(slug)

    def update_plan(self, tenant_id: str, plan: str) -> Tenant:
        """Update tenant plan and quotas."""
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            raise TenantEngineError("Tenant not found")

        # Business logic: Apply plan quotas
        quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])

        # Delegate to driver
        tenant = self._driver.update_tenant_plan(
            tenant,
            plan=plan,
            max_workers=quotas["max_workers"],
            max_runs_per_day=quotas["max_runs_per_day"],
            max_concurrent_runs=quotas["max_concurrent_runs"],
            max_tokens_per_month=quotas["max_tokens_per_month"],
            max_api_keys=quotas["max_api_keys"],
        )

        logger.info("tenant_plan_updated", extra={"tenant_id": tenant_id, "plan": plan})
        return tenant

    def suspend(self, tenant_id: str, reason: str) -> Tenant:
        """Suspend a tenant."""
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            raise TenantEngineError("Tenant not found")

        # Delegate to driver
        tenant = self._driver.update_tenant_status(tenant, "suspended", reason)

        logger.warning("tenant_suspended", extra={"tenant_id": tenant_id, "reason": reason})
        return tenant

    def create_membership_with_default(
        self,
        tenant: Tenant,
        user_id: str,
        role: str = "owner",
        set_as_default: bool = True,
    ) -> TenantMembership:
        """Create a tenant membership and optionally set as user's default tenant."""
        membership = self._driver.insert_membership(
            tenant_id=tenant.id,
            user_id=user_id,
            role=role,
            set_as_default=set_as_default,
        )

        logger.info(
            "tenant_membership_created",
            extra={
                "tenant_id": tenant.id,
                "user_id": user_id,
                "role": role,
                "set_as_default": set_as_default,
            },
        )
        return membership

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
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            raise TenantEngineError("Tenant not found")

        # Business logic: Check key limit
        key_count = self._driver.count_active_api_keys(tenant_id)
        if key_count >= tenant.max_api_keys:
            raise QuotaExceededError("api_keys", tenant.max_api_keys, key_count)

        # Business logic: Generate key
        full_key, prefix, key_hash = APIKey.generate_key()

        # Business logic: Set expiry
        expires_at = None
        if expires_in_days:
            expires_at = utc_now() + timedelta(days=expires_in_days)

        # Delegate to driver
        api_key = self._driver.insert_api_key(
            tenant_id=tenant_id,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            user_id=user_id,
            permissions=permissions,
            allowed_workers=allowed_workers,
            expires_at=expires_at,
            rate_limit_rpm=rate_limit_rpm,
            max_concurrent_runs=max_concurrent_runs,
        )

        # Audit log
        self._driver.insert_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=api_key.id,
            new_value={"name": name, "prefix": prefix},
        )
        self.session.commit()

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
        return self._driver.fetch_api_keys(tenant_id, include_revoked=include_revoked)

    def revoke_api_key(
        self,
        key_id: str,
        reason: str = "Manual revocation",
        user_id: Optional[str] = None,
    ) -> APIKey:
        """Revoke an API key."""
        api_key = self._driver.fetch_api_key_by_id(key_id)
        if not api_key:
            raise TenantEngineError("API key not found")

        # Delegate to driver
        api_key = self._driver.update_api_key_revoked(api_key, reason)

        # Audit log
        self._driver.insert_audit_log(
            tenant_id=api_key.tenant_id,
            user_id=user_id,
            api_key_id=key_id,
            action="revoke_api_key",
            resource_type="api_key",
            resource_id=key_id,
            new_value={"reason": reason},
        )
        self.session.commit()

        logger.info("api_key_revoked", extra={"key_id": key_id, "reason": reason})
        return api_key

    # ============== Quota Enforcement ==============

    def check_run_quota(self, tenant_id: str) -> Tuple[bool, str]:
        """
        Check if tenant can create a new run.

        Business logic:
        - Tenant must be active
        - Daily run limit not exceeded
        - Concurrent run limit not exceeded

        Returns:
            (allowed, reason): Whether allowed and reason if not
        """
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        # Business logic: Check status
        if tenant.status != "active":
            return False, f"Tenant is {tenant.status}"

        # Business logic: Reset daily counter if needed
        self._maybe_reset_daily_counter(tenant)

        # Business logic: Check daily limit
        if tenant.runs_today >= tenant.max_runs_per_day:
            return False, f"Daily run limit ({tenant.max_runs_per_day}) exceeded"

        # Business logic: Check concurrent runs
        running_count = self._driver.count_running_runs(tenant_id)
        if running_count >= tenant.max_concurrent_runs:
            return False, f"Concurrent run limit ({tenant.max_concurrent_runs}) exceeded"

        return True, ""

    def check_token_quota(self, tenant_id: str, tokens_needed: int) -> Tuple[bool, str]:
        """
        Check if tenant has token budget for operation.

        Business logic:
        - Monthly token limit not exceeded

        Returns:
            (allowed, reason): Whether allowed and reason if not
        """
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            return False, "Tenant not found"

        # Business logic: Project token usage
        projected = tenant.tokens_this_month + tokens_needed
        if projected > tenant.max_tokens_per_month:
            return False, f"Monthly token limit ({tenant.max_tokens_per_month:,}) would be exceeded"

        return True, ""

    def increment_usage(self, tenant_id: str, tokens: int = 0) -> None:
        """Increment usage counters for a tenant."""
        tenant = self._driver.fetch_tenant_by_id(tenant_id)
        if not tenant:
            return

        # Business logic: Reset daily counter if needed
        self._maybe_reset_daily_counter(tenant)

        # Delegate to driver
        self._driver.increment_tenant_usage(tenant, tokens)

    def _maybe_reset_daily_counter(self, tenant: Tenant) -> None:
        """Reset daily run counter if new day (temporal logic)."""
        now = utc_now()
        if tenant.last_run_reset_at:
            if tenant.last_run_reset_at.date() < now.date():
                self._driver.update_tenant_usage(
                    tenant,
                    runs_today=0,
                    last_run_reset_at=now,
                )
        else:
            self._driver.update_tenant_usage(
                tenant,
                last_run_reset_at=now,
            )

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
    ) -> None:
        """Record a usage event for billing."""
        self._driver.insert_usage_record(
            tenant_id=tenant_id,
            meter_name=meter_name,
            amount=amount,
            unit=unit,
            worker_id=worker_id,
            api_key_id=api_key_id,
            metadata=metadata,
        )

    def get_usage_summary(
        self,
        tenant_id: str,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
    ) -> dict:
        """Get usage summary for a tenant."""
        now = utc_now()
        if not start_date:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not end_date:
            end_date = now

        records = self._driver.fetch_usage_records(tenant_id, start_date, end_date)

        # Business logic: Aggregate by meter
        summary: dict[str, dict[str, Any]] = {}
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
        # Business logic: Check quota
        allowed, reason = self.check_run_quota(tenant_id)
        if not allowed:
            raise QuotaExceededError("runs", 0, 0)  # Details in reason

        # Delegate to driver
        run = self._driver.insert_run(
            tenant_id=tenant_id,
            worker_id=worker_id,
            task=task,
            api_key_id=api_key_id,
            user_id=user_id,
            input_json=input_json,
        )

        # Business logic: Increment usage counter
        self.increment_usage(tenant_id)

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
        run = self._driver.fetch_run_by_id(run_id)
        if not run:
            raise TenantEngineError("Run not found")

        # Delegate to driver for update
        run = self._driver.update_run_completed(
            run,
            success=success,
            output_json=output_json,
            replay_token_json=replay_token_json,
            total_tokens=total_tokens,
            total_latency_ms=total_latency_ms,
            stages_completed=stages_completed,
            recoveries=recoveries,
            policy_violations=policy_violations,
            cost_cents=cost_cents,
            error=error,
        )

        # Business logic: Record token usage
        if total_tokens > 0:
            tenant = self._driver.fetch_tenant_by_id(run.tenant_id)
            if tenant:
                self._driver.update_tenant_usage(
                    tenant,
                    tokens_this_month=tenant.tokens_this_month + total_tokens,
                )

            self.record_usage(
                tenant_id=run.tenant_id,
                meter_name="tokens_used",
                amount=total_tokens,
                unit="tokens",
                worker_id=run.worker_id,
                api_key_id=run.api_key_id,
            )

        # Business logic: Record run completion
        self.record_usage(
            tenant_id=run.tenant_id,
            meter_name="worker_runs",
            amount=1,
            unit="count",
            worker_id=run.worker_id,
            api_key_id=run.api_key_id,
            metadata={"success": success, "cost_cents": cost_cents},
        )

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
        return self._driver.fetch_runs(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            status=status,
            worker_id=worker_id,
        )


# =============================================================================
# Factory Function
# =============================================================================


def get_tenant_engine(session: Session) -> TenantEngine:
    """Get a TenantEngine instance."""
    return TenantEngine(session)


__all__ = [
    "TenantEngine",
    "TenantEngineError",
    "QuotaExceededError",
    "get_tenant_engine",
]
