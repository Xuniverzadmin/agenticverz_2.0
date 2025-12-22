# CostSim Leader Election via PostgreSQL Advisory Locks
"""
Leader election using PostgreSQL advisory locks.

This module provides a simple leader election mechanism for scenarios where
only one instance should run a task (e.g., daily canary runs). Uses
pg_try_advisory_lock() which is session-scoped and automatically released
when the connection closes.

Usage:
    from app.costsim.leader import try_acquire_leader_lock, LeaderContext

    # Simple check
    async with AsyncSessionLocal() as session:
        if await try_acquire_leader_lock(session, LOCK_CANARY_RUNNER):
            # We are the leader - run the task
            await run_canary()
            # Lock is released when session closes

    # Or with context manager for cleaner code
    async with LeaderContext(LOCK_CANARY_RUNNER) as is_leader:
        if is_leader:
            await run_canary()

Lock IDs:
    - LOCK_CANARY_RUNNER (7001): Daily canary execution
    - LOCK_ALERT_WORKER (7002): Alert queue processor
    - LOCK_PROVENANCE_ARCHIVER (7003): Provenance data archival

Note:
    Advisory locks are session-scoped. They are automatically released when:
    - The session/connection is closed
    - The transaction is rolled back (for xact-level locks)
    - Explicitly released with pg_advisory_unlock()

    For long-running processes, ensure the connection stays alive or
    use heartbeat mechanisms.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import AsyncSessionLocal

logger = logging.getLogger("nova.costsim.leader")


# Lock IDs - must be unique across the application
# Using 7xxx range to avoid conflicts with other subsystems
LOCK_CANARY_RUNNER = 7001
LOCK_ALERT_WORKER = 7002
LOCK_PROVENANCE_ARCHIVER = 7003
LOCK_BASELINE_BACKFILL = 7004


async def try_acquire_leader_lock(
    session: AsyncSession,
    lock_id: int,
) -> bool:
    """
    Try to acquire an advisory lock (non-blocking).

    Uses pg_try_advisory_lock() which returns immediately with true/false.
    Lock is held until the session is closed.

    Args:
        session: Async database session
        lock_id: Unique lock identifier (use constants above)

    Returns:
        True if lock acquired (we are the leader), False otherwise
    """
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:lock_id)"),
        {"lock_id": lock_id},
    )
    row = result.fetchone()
    acquired = row[0] if row else False

    if acquired:
        logger.info(f"Acquired leader lock: lock_id={lock_id}")
    else:
        logger.debug(f"Failed to acquire leader lock (another instance holds it): lock_id={lock_id}")

    return acquired


async def release_leader_lock(
    session: AsyncSession,
    lock_id: int,
) -> bool:
    """
    Explicitly release an advisory lock.

    Usually not needed since locks are released when session closes,
    but useful for releasing early in long-running sessions.

    Args:
        session: Async database session
        lock_id: Lock identifier to release

    Returns:
        True if lock was released, False if we didn't hold it
    """
    result = await session.execute(
        text("SELECT pg_advisory_unlock(:lock_id)"),
        {"lock_id": lock_id},
    )
    row = result.fetchone()
    released = row[0] if row else False

    if released:
        logger.info(f"Released leader lock: lock_id={lock_id}")
    else:
        logger.debug(f"Could not release lock (we don't hold it): lock_id={lock_id}")

    return released


async def is_lock_held(
    session: AsyncSession,
    lock_id: int,
) -> bool:
    """
    Check if a lock is currently held by any session.

    Note: This is informational only. The lock state could change
    immediately after this check returns.

    Args:
        session: Async database session
        lock_id: Lock identifier to check

    Returns:
        True if lock is held by any session
    """
    result = await session.execute(
        text(
            """
            SELECT COUNT(*) > 0
            FROM pg_locks
            WHERE locktype = 'advisory'
              AND objid = :lock_id
              AND granted = true
        """
        ),
        {"lock_id": lock_id},
    )
    row = result.fetchone()
    return row[0] if row else False


class LeaderContext:
    """
    Async context manager for leader election.

    Acquires a leader lock on entry, releases on exit. The context
    variable indicates whether we successfully became the leader.

    Usage:
        async with LeaderContext(LOCK_CANARY_RUNNER) as is_leader:
            if is_leader:
                # We won the election
                await run_canary()
            else:
                # Another instance is the leader
                logger.info("Not the leader, skipping")

    The lock is held for the duration of the context and automatically
    released when the context exits (via session close).
    """

    def __init__(
        self,
        lock_id: int,
        session: Optional[AsyncSession] = None,
        timeout_seconds: float = 5.0,
    ):
        """
        Initialize leader context.

        Args:
            lock_id: Advisory lock ID
            session: Optional existing session (creates new if None)
            timeout_seconds: Timeout for lock acquisition attempt
        """
        self.lock_id = lock_id
        self._external_session = session
        self._own_session: Optional[AsyncSession] = None
        self._is_leader = False
        self._timeout = timeout_seconds

    async def __aenter__(self) -> bool:
        """Enter context and attempt to acquire leadership."""
        try:
            if self._external_session:
                # Use provided session
                self._is_leader = await asyncio.wait_for(
                    try_acquire_leader_lock(self._external_session, self.lock_id),
                    timeout=self._timeout,
                )
            else:
                # Create our own session
                self._own_session = AsyncSessionLocal()
                self._is_leader = await asyncio.wait_for(
                    try_acquire_leader_lock(self._own_session, self.lock_id),
                    timeout=self._timeout,
                )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout acquiring leader lock: lock_id={self.lock_id}")
            self._is_leader = False
        except Exception as e:
            logger.error(f"Error acquiring leader lock: {e}")
            self._is_leader = False

        return self._is_leader

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and release leadership."""
        if self._own_session:
            # Closing the session releases the advisory lock
            try:
                await self._own_session.close()
            except Exception as e:
                logger.error(f"Error closing leader session: {e}")
            self._own_session = None

        self._is_leader = False

    @property
    def is_leader(self) -> bool:
        """Check if we currently hold leadership."""
        return self._is_leader


@asynccontextmanager
async def leader_election(
    lock_id: int,
    timeout_seconds: float = 5.0,
) -> AsyncGenerator[bool, None]:
    """
    Context manager for leader election.

    Alternative to LeaderContext class, using a function-based approach.

    Usage:
        async with leader_election(LOCK_CANARY_RUNNER) as is_leader:
            if is_leader:
                await run_canary()

    Args:
        lock_id: Advisory lock ID
        timeout_seconds: Timeout for lock acquisition

    Yields:
        True if we are the leader, False otherwise
    """
    session: Optional[AsyncSession] = None
    is_leader = False

    try:
        session = AsyncSessionLocal()
        try:
            is_leader = await asyncio.wait_for(
                try_acquire_leader_lock(session, lock_id),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout acquiring leader lock: lock_id={lock_id}")
            is_leader = False

        yield is_leader

    except Exception as e:
        logger.error(f"Error in leader election: {e}")
        yield False

    finally:
        if session:
            try:
                await session.close()
            except Exception as e:
                logger.error(f"Error closing leader session: {e}")


async def with_leader_lock(
    lock_id: int,
    callback,
    *args,
    timeout_seconds: float = 5.0,
    **kwargs,
):
    """
    Execute callback only if we can acquire leadership.

    Convenience function for fire-and-forget leader tasks.

    Args:
        lock_id: Advisory lock ID
        callback: Async function to execute if we become leader
        *args: Arguments for callback
        timeout_seconds: Lock acquisition timeout
        **kwargs: Keyword arguments for callback

    Returns:
        Result of callback if we were leader, None otherwise

    Example:
        # Run canary only if we're the leader
        result = await with_leader_lock(
            LOCK_CANARY_RUNNER,
            run_canary,
            samples=100,
        )
    """
    async with leader_election(lock_id, timeout_seconds) as is_leader:
        if is_leader:
            return await callback(*args, **kwargs)
        return None


# Convenience aliases for specific locks
async def with_canary_lock(callback, *args, **kwargs):
    """Execute callback with canary runner lock."""
    return await with_leader_lock(LOCK_CANARY_RUNNER, callback, *args, **kwargs)


async def with_alert_worker_lock(callback, *args, **kwargs):
    """Execute callback with alert worker lock."""
    return await with_leader_lock(LOCK_ALERT_WORKER, callback, *args, **kwargs)


async def with_archiver_lock(callback, *args, **kwargs):
    """Execute callback with provenance archiver lock."""
    return await with_leader_lock(LOCK_PROVENANCE_ARCHIVER, callback, *args, **kwargs)
