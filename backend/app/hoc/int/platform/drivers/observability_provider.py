# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: import-time, runtime
#   Execution: sync
# Role: Phase-8 Observability Provider (protocol + mock)
# Callers: emitters, query handlers
# Allowed Imports: L4 (events), L6 (logging)
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-399 Phase-8 (Observability Unification)

"""
Phase-8 Observability Provider

Implements OBSERVE-004: Failure to emit must not block execution.
Implements OBSERVE-005: Mock provider must be interface-compatible with real provider.

The provider is the single interface for emitting and querying events.
All emit operations are non-blocking and fail silently (logged locally).
"""

from datetime import datetime
from typing import Protocol, Optional, runtime_checkable
import logging
import threading

from app.observability.events import UnifiedEvent


logger = logging.getLogger(__name__)


@runtime_checkable
class ObservabilityProvider(Protocol):
    """
    Phase-8 Observability Provider Protocol.

    This is the interface for all observability operations.
    Both mock and real implementations must satisfy this protocol.

    OBSERVE-004: emit() MUST NOT block execution on failure.
    OBSERVE-005: Mock must be interface-compatible with real.
    """

    def emit(self, event: UnifiedEvent) -> None:
        """
        Emit an event to the observability store.

        MUST NOT block execution on failure.
        MUST NOT raise exceptions to caller.

        Args:
            event: The unified event to emit
        """
        ...

    def query(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        event_types: Optional[list[str]] = None,
        event_sources: Optional[list[str]] = None,
    ) -> list[UnifiedEvent]:
        """
        Query events for a tenant within a time range.

        Returns events ordered by (timestamp, event_id).

        Args:
            tenant_id: The tenant to query (OBSERVE-003: all events are tenant-scoped)
            start: Start of the time range (inclusive)
            end: End of the time range (inclusive)
            event_types: Optional filter for specific event types
            event_sources: Optional filter for specific event sources

        Returns:
            List of events matching the criteria, ordered by (timestamp, event_id)
        """
        ...


class MockObservabilityProvider:
    """
    Mock implementation of ObservabilityProvider for testing.

    Requirements per design:
    - In-memory store
    - Deterministic ordering
    - No external dependencies
    - No async background jobs
    - Thread-safe for concurrent emit
    """

    def __init__(self) -> None:
        """Initialize the mock provider with empty event store."""
        self._events: list[UnifiedEvent] = []
        self._lock = threading.Lock()

    def emit(self, event: UnifiedEvent) -> None:
        """
        Emit an event to the in-memory store.

        Thread-safe and non-blocking. Errors are logged, not raised.
        Implements OBSERVE-004.

        Args:
            event: The unified event to emit
        """
        try:
            with self._lock:
                self._events.append(event)
        except Exception as e:
            # OBSERVE-004: Failure to emit must not block execution
            logger.error(f"Observability emit failed: {e}")
            # Operation continues - never propagate

    def query(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        event_types: Optional[list[str]] = None,
        event_sources: Optional[list[str]] = None,
    ) -> list[UnifiedEvent]:
        """
        Query events for a tenant within a time range.

        Returns events ordered by (timestamp, event_id).

        Args:
            tenant_id: The tenant to query
            start: Start of the time range (inclusive)
            end: End of the time range (inclusive)
            event_types: Optional filter for specific event types
            event_sources: Optional filter for specific event sources

        Returns:
            List of events matching the criteria
        """
        with self._lock:
            filtered = []

            for event in self._events:
                # OBSERVE-003: All events are tenant-scoped
                if event.tenant_id != tenant_id:
                    continue

                # Time range filter
                if event.timestamp < start or event.timestamp > end:
                    continue

                # Event type filter
                if event_types is not None and event.event_type not in event_types:
                    continue

                # Event source filter
                if event_sources is not None:
                    source_value = event.event_source.value
                    if source_value not in event_sources:
                        continue

                filtered.append(event)

            # Order by (timestamp, event_id)
            filtered.sort(key=lambda e: (e.timestamp, e.event_id))

            return filtered

    def get_all_events(self) -> list[UnifiedEvent]:
        """
        Get all events in the store (for testing).

        Returns:
            All events in order of emission
        """
        with self._lock:
            return list(self._events)

    def get_events_by_tenant(self, tenant_id: str) -> list[UnifiedEvent]:
        """
        Get all events for a specific tenant (for testing).

        Args:
            tenant_id: The tenant to filter by

        Returns:
            All events for the tenant in order of emission
        """
        with self._lock:
            return [e for e in self._events if e.tenant_id == tenant_id]

    def count(self) -> int:
        """
        Get the total number of events in the store.

        Returns:
            Event count
        """
        with self._lock:
            return len(self._events)

    def reset(self) -> None:
        """
        Clear all events from the store.

        Used for test isolation.
        """
        with self._lock:
            self._events.clear()


# =============================================================================
# GLOBAL PROVIDER INSTANCE
# =============================================================================

# Default to mock provider
_provider: ObservabilityProvider = MockObservabilityProvider()


def get_observability_provider() -> ObservabilityProvider:
    """
    Get the current observability provider.

    Returns:
        The active observability provider instance
    """
    return _provider


def set_observability_provider(provider: ObservabilityProvider) -> None:
    """
    Set the observability provider.

    Used for testing or switching to real provider.

    Args:
        provider: The provider instance to use
    """
    global _provider
    _provider = provider


__all__ = [
    "ObservabilityProvider",
    "MockObservabilityProvider",
    "get_observability_provider",
    "set_observability_provider",
]
