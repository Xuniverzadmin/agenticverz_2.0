# Layer: L5 — Domain Engine
# NOTE: Renamed cb_sync_wrapper.py → cb_sync_wrapper_engine.py (2026-01-31) per BANNED_NAMING rule
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via circuit_breaker (L6)
#   Writes: none
# Role: Circuit breaker sync wrapper (thread-safe async bridge)
# Callers: sync middleware, legacy code
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470

# CostSim Circuit Breaker Sync Wrapper
"""
Thread-safe sync wrapper for async circuit breaker functions.

This module provides sync-compatible wrappers that safely execute
async circuit breaker functions from sync contexts, including when
an event loop is already running.

Why this exists:
- The async circuit breaker functions use asyncpg which requires an event loop
- Some callers may be sync (e.g., middleware, legacy code)
- Calling asyncio.run() from a running event loop raises RuntimeError
- The naive workaround of returning True (disabled) is too conservative
  and causes false-positive V2 disables

Usage:
    from app.costsim.cb_sync_wrapper import is_v2_disabled_sync, get_state_sync

    # Safe from any context (sync or async)
    if is_v2_disabled_sync():
        return use_v1_only()
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from typing import Optional

logger = logging.getLogger("nova.costsim.cb_sync_wrapper")

# Thread pool for running async functions from sync contexts
_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    """Get or create the shared thread pool executor."""
    global _executor
    if _executor is None:
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="cb_sync_")
    return _executor


def _run_async_in_thread(coro, timeout: float = 5.0):
    """
    Run an async coroutine in a separate thread with its own event loop.

    This is safe to call from any context, including:
    - Sync functions with no event loop
    - Sync functions called from within an async context
    - The main thread of an async application

    Args:
        coro: The coroutine to run
        timeout: Maximum time to wait for result

    Returns:
        The result of the coroutine

    Raises:
        TimeoutError: If the operation times out
        Exception: Any exception raised by the coroutine
    """

    def run_in_new_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    executor = _get_executor()
    future = executor.submit(run_in_new_loop)
    return future.result(timeout=timeout)


def is_v2_disabled_sync(timeout: float = 5.0) -> bool:
    """
    Sync wrapper for is_v2_disabled().

    Safe to call from any context. Runs the async function in a
    separate thread with its own event loop.

    Args:
        timeout: Maximum time to wait for DB query

    Returns:
        True if V2 is disabled, False otherwise

    Note:
        On error, returns False (V2 enabled) to avoid false-positive
        disables. This is the opposite of the previous conservative
        approach which returned True on error.
    """
    try:
        # Import here to avoid circular imports
        from app.costsim.circuit_breaker_async import is_v2_disabled

        # Check if we're in an event loop
        try:
            loop = asyncio.get_running_loop()
            # We're in a running loop - use thread pool
            return bool(_run_async_in_thread(is_v2_disabled(), timeout))
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(is_v2_disabled())

    except concurrent.futures.TimeoutError:
        logger.error("is_v2_disabled_sync timed out, returning False (enabled)")
        return False
    except Exception as e:
        logger.error(f"is_v2_disabled_sync error: {e}, returning False (enabled)")
        return False


def get_state_sync(timeout: float = 5.0):
    """
    Sync wrapper for get_state().

    Safe to call from any context.

    Args:
        timeout: Maximum time to wait for DB query

    Returns:
        CircuitBreakerState or None on error
    """
    try:
        from app.costsim.circuit_breaker_async import get_state

        try:
            loop = asyncio.get_running_loop()
            return _run_async_in_thread(get_state(), timeout)
        except RuntimeError:
            return asyncio.run(get_state())

    except concurrent.futures.TimeoutError:
        logger.error("get_state_sync timed out")
        return None
    except Exception as e:
        logger.error(f"get_state_sync error: {e}")
        return None


def shutdown_executor():
    """Shutdown the thread pool executor gracefully."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None
