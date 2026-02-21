# capability_id: CAP-012
# Layer: L4 — HOC Spine (Coordinator)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 coordinator — distributed locking primitives
# Callers: Schedulers, background jobs
# Allowed Imports: hoc_spine, hoc.cus.analytics.L6_drivers (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A6 Wiring
# artifact_class: CODE

"""
Leadership Coordinator (PIN-513 Batch 3A6 Wiring)

L4 coordinator that owns distributed locking primitives.
No business logic imports this directly.

Wires from analytics/L6_drivers/leader_driver.py:
- try_acquire_leader_lock(session, lock_id)
- release_leader_lock(session, lock_id)
- is_lock_held(session, lock_id)
- leader_election(lock_id, timeout_seconds)
- with_leader_lock(lock_id, callback, *args, timeout_seconds, **kwargs)
- with_canary_lock(callback, *args, **kwargs)
- with_alert_worker_lock(callback, *args, **kwargs)
- with_archiver_lock(callback, *args, **kwargs)
"""

import logging
from typing import Any, Callable

logger = logging.getLogger("nova.hoc_spine.coordinators.leadership")


class LeadershipCoordinator:
    """L4 coordinator: distributed locking primitives.

    Schedulers and background jobs use this coordinator
    to acquire advisory locks before executing.
    """

    async def try_acquire(
        self,
        session: Any,
        lock_id: int,
    ) -> bool:
        """Try to acquire an advisory lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import (
            try_acquire_leader_lock,
        )

        return await try_acquire_leader_lock(session=session, lock_id=lock_id)

    async def release(
        self,
        session: Any,
        lock_id: int,
    ) -> bool:
        """Release an advisory lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import (
            release_leader_lock,
        )

        return await release_leader_lock(session=session, lock_id=lock_id)

    async def is_held(
        self,
        session: Any,
        lock_id: int,
    ) -> bool:
        """Check if a lock is currently held."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import is_lock_held

        return await is_lock_held(session=session, lock_id=lock_id)

    async def with_lock(
        self,
        lock_id: int,
        callback: Callable,
        *args: Any,
        timeout_seconds: float = 5.0,
        **kwargs: Any,
    ) -> Any:
        """Execute callback under advisory lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import with_leader_lock

        return await with_leader_lock(
            lock_id, callback, *args, timeout_seconds=timeout_seconds, **kwargs
        )

    async def with_canary_lock(
        self,
        callback: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute callback under canary lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import with_canary_lock

        return await with_canary_lock(callback, *args, **kwargs)

    async def with_alert_worker_lock(
        self,
        callback: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute callback under alert worker lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import (
            with_alert_worker_lock,
        )

        return await with_alert_worker_lock(callback, *args, **kwargs)

    async def with_archiver_lock(
        self,
        callback: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute callback under archiver lock."""
        from app.hoc.cus.analytics.L6_drivers.leader_driver import with_archiver_lock

        return await with_archiver_lock(callback, *args, **kwargs)
