# capability_id: CAP-001
# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: startup
#   Execution: sync (blocking until ready)
# Role: Initialize EventReactor at application startup
# Callers: main.py lifespan
# Allowed Imports: L4 (events), L6 (logging)
# Forbidden Imports: L1, L2, L3
# Reference: GAP-046

"""
Module: reactor_initializer
Purpose: Ensures EventReactor is initialized at startup and blocks if failed.

Imports (Dependencies):
    - app.events.subscribers: get_event_reactor, EventReactor
    - app.events.audit_handlers: register_audit_handlers
    - app.services.governance.profile: get_governance_config

Exports (Provides):
    - initialize_event_reactor(): EventReactor — initialized reactor
    - get_reactor_status(): ReactorStatus — health check

Wiring Points:
    - Called from: main.py:lifespan_startup()
    - Calls: get_event_reactor(), register_audit_handlers(), reactor.start()

Acceptance Criteria:
    - [x] AC-046-01: EventReactor initializes at startup
    - [x] AC-046-02: Audit handlers are registered
    - [x] AC-046-03: Heartbeat thread starts
    - [x] AC-046-04: Health endpoint includes reactor status
    - [x] AC-046-05: Boot fails if reactor fails
    - [x] AC-046-06: No orphan — wired to main.py
"""

from typing import Optional
import logging

logger = logging.getLogger("nova.events.reactor_initializer")

_reactor = None
_initialized = False


def initialize_event_reactor():
    """
    Initialize the EventReactor at startup.

    MUST be called in main.py lifespan before accepting requests.
    Raises RuntimeError if initialization fails (boot-fail policy).

    Returns:
        EventReactor instance or None if disabled
    """
    global _reactor, _initialized

    from app.hoc.cus.hoc_spine.authority.profile_policy_mode import get_governance_config

    config = get_governance_config()

    if not config.event_reactor_enabled:
        logger.warning("event_reactor.disabled_by_profile", extra={
            "profile": config.profile.value,
        })
        _initialized = True
        return None

    try:
        from app.events.subscribers import get_event_reactor
        from app.events.audit_handlers import register_audit_handlers

        _reactor = get_event_reactor()
        register_audit_handlers(_reactor)

        # Start reactor in background thread to process events
        _reactor.start_background()

        _initialized = True

        logger.info("event_reactor.initialized", extra={
            "background_thread_started": True,
            "audit_handlers_registered": True,
            "profile": config.profile.value,
        })

        return _reactor

    except Exception as e:
        logger.error("event_reactor.initialization_failed", extra={"error": str(e)})
        raise RuntimeError(f"BOOT FAILURE: EventReactor initialization failed: {e}")


def get_reactor_status() -> dict:
    """Health check for EventReactor."""
    if not _initialized:
        return {"status": "not_initialized", "healthy": False, "heartbeat_active": False}

    if _reactor is None:
        return {"status": "disabled", "healthy": True, "heartbeat_active": False}

    # Check if reactor has health check methods
    is_running = True
    heartbeat_active = False

    if hasattr(_reactor, 'is_running'):
        is_running = _reactor.is_running()

    if hasattr(_reactor, 'heartbeat_active'):
        heartbeat_active = _reactor.heartbeat_active()
    elif hasattr(_reactor, '_heartbeat_thread'):
        heartbeat_active = _reactor._heartbeat_thread is not None and _reactor._heartbeat_thread.is_alive()

    return {
        "status": "running" if is_running else "stopped",
        "healthy": is_running,
        "heartbeat_active": heartbeat_active,
    }


def shutdown_event_reactor() -> None:
    """Shutdown the EventReactor gracefully."""
    global _reactor, _initialized

    if _reactor is not None:
        try:
            # Stop the reactor (handles background thread cleanup)
            if hasattr(_reactor, 'stop'):
                _reactor.stop(timeout=5.0)
            logger.info("event_reactor.shutdown_complete")
        except Exception as e:
            logger.error("event_reactor.shutdown_error", extra={"error": str(e)})

    _reactor = None
    _initialized = False
