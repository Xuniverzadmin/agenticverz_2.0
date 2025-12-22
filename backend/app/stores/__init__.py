# Store Factory Functions (M11)
"""
Unified factory functions for pluggable storage backends.

Provides environment-based switching between:
- In-memory stores (testing, single-worker)
- Redis stores (Upstash, multi-worker budget/idempotency)
- PostgreSQL stores (Neon, checkpoints/traces)
- R2 offload (Cloudflare R2, checkpoint archival)

All credentials are expected to be injected via environment variables
(populated from Vault: secret/data/user/<service>).

STRICT MODE (ENV=prod or ENV=production):
- Raises ConfigurationError instead of falling back to memory stores
- Ensures production deployments never silently degrade

Environment Variables:
- ENV: environment mode (prod|production enables strict mode)
- CHECKPOINT_STORE: postgres|memory (default: postgres if DATABASE_URL set)
- BUDGET_STORE: redis|memory (default: redis if REDIS_URL set)
- IDEMPOTENCY_STORE: redis|memory (default: redis if REDIS_URL set)
- DATABASE_URL: PostgreSQL connection string (from Vault: secret/data/user/neon)
- REDIS_URL: Redis connection string (from Vault: secret/data/user/upstash)
- R2_ENDPOINT: Cloudflare R2 endpoint (from Vault: secret/data/user/r2)
- R2_BUCKET: R2 bucket name
- R2_ACCESS_KEY_ID: R2 access key
- R2_SECRET_ACCESS_KEY: R2 secret key
"""

import logging
import os
from typing import Any, Optional, Protocol

logger = logging.getLogger("nova.stores")


# =============================================================================
# Configuration Error for Strict Mode
# =============================================================================


class StoreConfigurationError(Exception):
    """Raised when store configuration is invalid in strict mode (ENV=prod)."""

    pass


def _is_strict_mode() -> bool:
    """Check if we're in strict production mode."""
    env = os.getenv("ENV", "").lower()
    return env in ("prod", "production")


def _strict_fail(message: str) -> None:
    """Raise error in strict mode, or log warning in dev mode."""
    if _is_strict_mode():
        raise StoreConfigurationError(f"[STRICT MODE] {message}")
    logger.warning(message)


# =============================================================================
# Protocols for type hints
# =============================================================================


class BudgetStoreProtocol(Protocol):
    """Protocol for budget storage backends."""

    async def get_workflow_cost(self, run_id: str) -> int:
        ...

    async def add_workflow_cost(self, run_id: str, cost_cents: int) -> int:
        ...

    async def reset_workflow_cost(self, run_id: str) -> None:
        ...


class CheckpointStoreProtocol(Protocol):
    """Protocol for checkpoint storage backends."""

    def init_tables(self) -> None:
        ...

    async def ping(self) -> bool:
        ...

    async def save(self, run_id: str, next_step_index: int, **kwargs) -> str:
        ...

    async def load(self, run_id: str) -> Optional[Any]:
        ...

    async def delete(self, run_id: str) -> bool:
        ...


# =============================================================================
# Budget Store Factory
# =============================================================================

_budget_store_instance: Optional[BudgetStoreProtocol] = None


def get_budget_store(force_new: bool = False) -> BudgetStoreProtocol:
    """
    Get or create budget store based on environment configuration.

    Args:
        force_new: Force creation of new instance (for testing)

    Returns:
        BudgetStoreProtocol implementation (Redis or InMemory)

    Environment:
        BUDGET_STORE: 'redis' or 'memory' (auto-detected from REDIS_URL if not set)
        REDIS_URL: Redis connection string for RedisBudgetStore
    """
    global _budget_store_instance

    if _budget_store_instance is not None and not force_new:
        return _budget_store_instance

    store_type = os.getenv("BUDGET_STORE", "").lower()
    redis_url = os.getenv("REDIS_URL", "")

    # Auto-detect: use Redis if URL is available and not explicitly set to memory
    if store_type == "redis" or (store_type == "" and redis_url):
        if not redis_url:
            _strict_fail("BUDGET_STORE=redis but REDIS_URL not set, falling back to memory")
            store_type = "memory"
        else:
            try:
                from app.workflow.policies import RedisBudgetStore

                _budget_store_instance = RedisBudgetStore(redis_url=redis_url)
                logger.info(f"Using RedisBudgetStore (Upstash): {redis_url[:30]}...")
                return _budget_store_instance
            except ImportError as e:
                _strict_fail(f"Redis package not available: {e}, cannot use RedisBudgetStore")
                store_type = "memory"

    # Fallback to in-memory (blocked in strict mode)
    if _is_strict_mode() and store_type != "memory":
        raise StoreConfigurationError(
            "[STRICT MODE] Cannot use InMemoryBudgetStore in production. "
            "Set REDIS_URL or explicitly set BUDGET_STORE=memory to acknowledge."
        )

    from app.workflow.policies import InMemoryBudgetStore

    _budget_store_instance = InMemoryBudgetStore()
    logger.info("Using InMemoryBudgetStore (single-worker mode)")
    return _budget_store_instance


async def get_budget_store_async(force_new: bool = False) -> BudgetStoreProtocol:
    """Async version of get_budget_store (for consistency with async contexts)."""
    return get_budget_store(force_new=force_new)


# =============================================================================
# Checkpoint Store Factory
# =============================================================================

_checkpoint_store_instance: Optional[CheckpointStoreProtocol] = None


def get_checkpoint_store(force_new: bool = False) -> CheckpointStoreProtocol:
    """
    Get or create checkpoint store based on environment configuration.

    Args:
        force_new: Force creation of new instance (for testing)

    Returns:
        CheckpointStoreProtocol implementation (Postgres or InMemory)

    Environment:
        CHECKPOINT_STORE: 'postgres' or 'memory' (auto-detected from DATABASE_URL if not set)
        DATABASE_URL: PostgreSQL connection string for CheckpointStore
    """
    global _checkpoint_store_instance

    if _checkpoint_store_instance is not None and not force_new:
        return _checkpoint_store_instance

    store_type = os.getenv("CHECKPOINT_STORE", "").lower()
    database_url = os.getenv("DATABASE_URL", "")

    # Auto-detect: use Postgres if URL is available and not explicitly set to memory
    if store_type == "postgres" or (store_type == "" and database_url):
        if not database_url:
            _strict_fail("CHECKPOINT_STORE=postgres but DATABASE_URL not set, falling back to memory")
            store_type = "memory"
        else:
            try:
                from app.workflow.checkpoint import CheckpointStore

                _checkpoint_store_instance = CheckpointStore(engine_url=database_url)
                logger.info("Using PostgresCheckpointStore (Neon)")
                return _checkpoint_store_instance
            except Exception as e:
                _strict_fail(f"Failed to init CheckpointStore: {e}, cannot use PostgresCheckpointStore")
                store_type = "memory"

    # Fallback to in-memory (blocked in strict mode)
    if _is_strict_mode() and store_type != "memory":
        raise StoreConfigurationError(
            "[STRICT MODE] Cannot use InMemoryCheckpointStore in production. "
            "Set DATABASE_URL or explicitly set CHECKPOINT_STORE=memory to acknowledge."
        )

    from app.workflow.checkpoint import InMemoryCheckpointStore

    _checkpoint_store_instance = InMemoryCheckpointStore()
    logger.info("Using InMemoryCheckpointStore (testing mode)")
    return _checkpoint_store_instance


async def get_checkpoint_store_async(force_new: bool = False) -> CheckpointStoreProtocol:
    """Async version of get_checkpoint_store (for consistency with async contexts)."""
    return get_checkpoint_store(force_new=force_new)


# =============================================================================
# Idempotency Store Factory (re-export from traces)
# =============================================================================


async def get_idempotency_store():
    """
    Get or create idempotency store based on environment configuration.

    Re-exports the existing factory from app.traces.idempotency which already
    has proper REDIS_URL-based auto-detection.

    Environment:
        REDIS_URL: Redis connection string (auto-detects to Redis if set)
    """
    from app.traces.idempotency import get_idempotency_store as _get_idempotency_store

    return await _get_idempotency_store()


# =============================================================================
# R2 Offload Client Factory
# =============================================================================

_r2_client_instance = None


def get_r2_client():
    """
    Get or create Cloudflare R2 client for checkpoint offload.

    Returns:
        boto3 S3 client configured for R2, or None if not configured

    Environment:
        R2_ENDPOINT: Cloudflare R2 endpoint URL
        R2_BUCKET: R2 bucket name
        R2_ACCESS_KEY_ID: R2 access key
        R2_SECRET_ACCESS_KEY: R2 secret key
    """
    global _r2_client_instance

    if _r2_client_instance is not None:
        return _r2_client_instance

    r2_endpoint = os.getenv("R2_ENDPOINT", "")
    r2_access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")

    if not all([r2_endpoint, r2_access_key, r2_secret_key]):
        logger.debug("R2 not configured (missing R2_ENDPOINT, R2_ACCESS_KEY_ID, or R2_SECRET_ACCESS_KEY)")
        return None

    try:
        import boto3

        _r2_client_instance = boto3.client(
            "s3",
            endpoint_url=r2_endpoint,
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
        )
        logger.info(f"R2 client initialized: {r2_endpoint}")
        return _r2_client_instance
    except ImportError:
        logger.warning("boto3 not installed, R2 offload disabled")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize R2 client: {e}")
        return None


def get_r2_bucket() -> Optional[str]:
    """Get R2 bucket name from environment."""
    return os.getenv("R2_BUCKET", "")


# =============================================================================
# Store Reset (for testing)
# =============================================================================


def reset_all_stores():
    """Reset all cached store instances. For testing only."""
    global _budget_store_instance, _checkpoint_store_instance, _r2_client_instance
    _budget_store_instance = None
    _checkpoint_store_instance = None
    _r2_client_instance = None
    logger.debug("All store instances reset")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "get_budget_store",
    "get_budget_store_async",
    "get_checkpoint_store",
    "get_checkpoint_store_async",
    "get_idempotency_store",
    "get_r2_client",
    "get_r2_bucket",
    "reset_all_stores",
    "BudgetStoreProtocol",
    "CheckpointStoreProtocol",
    "StoreConfigurationError",
]
