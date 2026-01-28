# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Storage for audit expectations and acknowledgments (RAC)
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Callers: ROK (L5), Facades (L4), AuditReconciler
# Allowed Imports: L6, models
# Forbidden Imports: L1, L2, L3, sqlalchemy
# Reference: PIN-454, Sweep-03
# Migrated from: app/services/audit/store.py

"""
Audit Store

Provides storage for audit expectations and acknowledgments.

Storage Strategy:
- MEMORY: In-memory dictionary (dev/test only - NOT crash-safe)
- REDIS: Redis-backed store (staging/prod - crash-safe, cross-process)

Durability Modes:
- AOS_MODE=local → MEMORY allowed
- AOS_MODE=test/prod → REDIS required (startup fails without it)

The store is designed to be:
1. Fast for writes (acks happen in hot path)
2. Durable in production (Redis backing mandatory)
3. TTL-managed (old data expires automatically)

Redis keys:
- rac:expectations:{run_id} -> JSON list of expectations
- rac:acks:{run_id} -> JSON list of acks
- TTL: 1 hour (runs should complete within this time)
"""

import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional
from uuid import UUID

# L5 schema import (migrated to HOC per SWEEP-04)
from app.hoc.cus.general.L5_schemas.rac_models import (
    AuditExpectation,
    AuditStatus,
    DomainAck,
)

logger = logging.getLogger("nova.hoc.cus.general.audit_store")

# TTL for Redis keys (1 hour)
REDIS_TTL_SECONDS = 3600

# Environment configuration
AUDIT_REDIS_ENABLED = os.getenv("AUDIT_REDIS_ENABLED", "false").lower() == "true"
RAC_ENABLED = os.getenv("RAC_ENABLED", "false").lower() == "true"
AOS_MODE = os.getenv("AOS_MODE", "local").lower()  # local, test, prod


class StoreDurabilityMode(str, Enum):
    """Durability mode for the audit store."""

    MEMORY = "MEMORY"  # In-memory only (dev/test, NOT crash-safe)
    REDIS = "REDIS"  # Redis-backed (staging/prod, crash-safe)


class RACDurabilityError(Exception):
    """Raised when RAC requires durable storage but none is available."""

    pass


def _determine_durability_mode(redis_client) -> StoreDurabilityMode:
    """
    Determine the durability mode based on environment and Redis availability.

    Rules:
    - AOS_MODE=local → MEMORY allowed (dev)
    - AOS_MODE=test/prod + RAC_ENABLED + no Redis → ERROR
    - AOS_MODE=test/prod + RAC_ENABLED + Redis → REDIS
    """
    has_redis = redis_client is not None and AUDIT_REDIS_ENABLED

    if AOS_MODE == "local":
        # Local dev mode: in-memory is acceptable
        return StoreDurabilityMode.REDIS if has_redis else StoreDurabilityMode.MEMORY

    # Non-local modes (test, prod): require Redis when RAC is enabled
    if RAC_ENABLED and not has_redis:
        raise RACDurabilityError(
            f"RAC_ENABLED=true requires durable storage in AOS_MODE={AOS_MODE}. "
            f"Set AUDIT_REDIS_ENABLED=true and provide a Redis client, "
            f"or set AOS_MODE=local for development."
        )

    return StoreDurabilityMode.REDIS if has_redis else StoreDurabilityMode.MEMORY


class AuditStore:
    """
    Storage for audit expectations and acknowledgments.

    Thread-safe store with configurable durability:
    - MEMORY mode: In-memory only (dev/test, NOT crash-safe)
    - REDIS mode: Redis-backed (staging/prod, crash-safe)

    Usage:
        store = get_audit_store()

        # Add expectations at run start
        store.add_expectations(run_id, expectations)

        # Add acks as domains complete
        store.add_ack(run_id, ack)

        # Get for reconciliation
        expectations = store.get_expectations(run_id)
        acks = store.get_acks(run_id)

    Durability:
        In production (AOS_MODE=test/prod), Redis is REQUIRED when RAC_ENABLED=true.
        This ensures expectations/acks survive worker crashes.
    """

    def __init__(self, redis_client=None):
        """
        Initialize the audit store.

        Args:
            redis_client: Optional Redis client for distributed storage

        Raises:
            RACDurabilityError: If RAC_ENABLED but no durable storage in prod
        """
        self._durability_mode = _determine_durability_mode(redis_client)
        self._expectations: Dict[str, List[AuditExpectation]] = {}
        self._acks: Dict[str, List[DomainAck]] = {}
        self._lock = Lock()
        self._redis = redis_client

        logger.info(
            "audit_store.initialized",
            extra={
                "durability_mode": self._durability_mode.value,
                "redis_available": redis_client is not None,
                "rac_enabled": RAC_ENABLED,
                "aos_mode": AOS_MODE,
            },
        )

    @property
    def durability_mode(self) -> StoreDurabilityMode:
        """Get the current durability mode."""
        return self._durability_mode

    @property
    def is_durable(self) -> bool:
        """Check if the store is using durable (Redis) storage."""
        return self._durability_mode == StoreDurabilityMode.REDIS

    # =========================================================================
    # Expectation Operations
    # =========================================================================

    def add_expectations(
        self,
        run_id: UUID,
        expectations: List[AuditExpectation],
    ) -> None:
        """
        Add expectations for a run.

        Called by ROK at T0 (run creation).

        Args:
            run_id: The run ID
            expectations: List of expectations to add
        """
        run_key = str(run_id)

        with self._lock:
            if run_key not in self._expectations:
                self._expectations[run_key] = []
            self._expectations[run_key].extend(expectations)

        logger.debug(
            "audit_store.add_expectations",
            extra={"run_id": run_key, "count": len(expectations)}
        )

        # Sync to Redis if enabled
        if self._redis and AUDIT_REDIS_ENABLED:
            self._sync_expectations_to_redis(run_key)

    def get_expectations(self, run_id: UUID) -> List[AuditExpectation]:
        """
        Get all expectations for a run.

        Args:
            run_id: The run ID

        Returns:
            List of expectations (may be empty)
        """
        run_key = str(run_id)

        with self._lock:
            return list(self._expectations.get(run_key, []))

    def update_expectation_status(
        self,
        run_id: UUID,
        domain: str,
        action: str,
        status: AuditStatus,
    ) -> bool:
        """
        Update the status of an expectation.

        Called when an ack is received to mark expectation as ACKED.

        Args:
            run_id: The run ID
            domain: Domain of the expectation
            action: Action of the expectation
            status: New status

        Returns:
            True if expectation was found and updated
        """
        run_key = str(run_id)

        with self._lock:
            expectations = self._expectations.get(run_key, [])
            for exp in expectations:
                if exp.domain.value == domain and exp.action.value == action:
                    exp.status = status
                    if status == AuditStatus.ACKED:
                        exp.acked_at = datetime.now(timezone.utc)
                    return True
        return False

    # =========================================================================
    # Acknowledgment Operations
    # =========================================================================

    def add_ack(self, run_id: UUID, ack: DomainAck) -> None:
        """
        Add an acknowledgment for a run.

        Called by facades after completing domain operations.

        Args:
            run_id: The run ID
            ack: The acknowledgment to add
        """
        run_key = str(run_id)

        with self._lock:
            if run_key not in self._acks:
                self._acks[run_key] = []
            self._acks[run_key].append(ack)

        logger.debug(
            "audit_store.add_ack",
            extra={
                "run_id": run_key,
                "domain": ack.domain.value,
                "action": ack.action.value,
                "success": ack.is_success,
            }
        )

        # Update corresponding expectation
        self.update_expectation_status(
            run_id,
            ack.domain.value,
            ack.action.value,
            AuditStatus.ACKED if ack.is_success else AuditStatus.FAILED,
        )

        # Sync to Redis if enabled
        if self._redis and AUDIT_REDIS_ENABLED:
            self._sync_acks_to_redis(run_key)

    def get_acks(self, run_id: UUID) -> List[DomainAck]:
        """
        Get all acknowledgments for a run.

        Args:
            run_id: The run ID

        Returns:
            List of acks (may be empty)
        """
        run_key = str(run_id)

        with self._lock:
            return list(self._acks.get(run_key, []))

    # =========================================================================
    # Cleanup Operations
    # =========================================================================

    def clear_run(self, run_id: UUID) -> None:
        """
        Clear all data for a run.

        Called after reconciliation is complete.

        Args:
            run_id: The run ID to clear
        """
        run_key = str(run_id)

        with self._lock:
            self._expectations.pop(run_key, None)
            self._acks.pop(run_key, None)

        logger.debug("audit_store.clear_run", extra={"run_id": run_key})

        # Clear from Redis if enabled
        if self._redis and AUDIT_REDIS_ENABLED:
            try:
                self._redis.delete(f"rac:expectations:{run_key}")
                self._redis.delete(f"rac:acks:{run_key}")
            except Exception as e:
                logger.warning(f"Failed to clear Redis keys: {e}")

    def get_pending_run_ids(self) -> List[str]:
        """
        Get all run IDs with pending expectations.

        Used by scheduler to find runs needing reconciliation.

        Returns:
            List of run IDs
        """
        with self._lock:
            return list(self._expectations.keys())

    # =========================================================================
    # Redis Sync (Optional)
    # =========================================================================

    def _sync_expectations_to_redis(self, run_key: str) -> None:
        """Sync expectations to Redis."""
        if not self._redis:
            return

        try:
            with self._lock:
                expectations = self._expectations.get(run_key, [])
                data = [exp.to_dict() for exp in expectations]

            self._redis.setex(
                f"rac:expectations:{run_key}",
                REDIS_TTL_SECONDS,
                json.dumps(data),
            )
        except Exception as e:
            logger.warning(f"Failed to sync expectations to Redis: {e}")

    def _sync_acks_to_redis(self, run_key: str) -> None:
        """Sync acks to Redis."""
        if not self._redis:
            return

        try:
            with self._lock:
                acks = self._acks.get(run_key, [])
                data = [ack.to_dict() for ack in acks]

            self._redis.setex(
                f"rac:acks:{run_key}",
                REDIS_TTL_SECONDS,
                json.dumps(data),
            )
        except Exception as e:
            logger.warning(f"Failed to sync acks to Redis: {e}")

    def load_from_redis(self, run_id: UUID) -> bool:
        """
        Load expectations and acks from Redis.

        Used for recovery or cross-process coordination.

        Args:
            run_id: The run ID to load

        Returns:
            True if data was found and loaded
        """
        if not self._redis:
            return False

        run_key = str(run_id)

        try:
            # Load expectations
            exp_data = self._redis.get(f"rac:expectations:{run_key}")
            if exp_data:
                expectations = [
                    AuditExpectation.from_dict(d)
                    for d in json.loads(exp_data)
                ]
                with self._lock:
                    self._expectations[run_key] = expectations

            # Load acks
            ack_data = self._redis.get(f"rac:acks:{run_key}")
            if ack_data:
                acks = [DomainAck.from_dict(d) for d in json.loads(ack_data)]
                with self._lock:
                    self._acks[run_key] = acks

            return bool(exp_data or ack_data)

        except Exception as e:
            logger.warning(f"Failed to load from Redis: {e}")
            return False


# =============================================================================
# Module-level singleton
# =============================================================================

_store_instance: Optional[AuditStore] = None


def get_audit_store(redis_client=None) -> AuditStore:
    """
    Get the audit store singleton.

    Args:
        redis_client: Optional Redis client (only used on first call)

    Returns:
        AuditStore instance
    """
    global _store_instance
    if _store_instance is None:
        _store_instance = AuditStore(redis_client=redis_client)
    return _store_instance
