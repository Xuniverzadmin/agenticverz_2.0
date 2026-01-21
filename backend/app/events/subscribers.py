# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Backend event subscribers for cross-domain reactions
# Callers: Worker process (event reactor loop)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-454, FIX-003 (Phase 5)

"""
Event Reactor — Backend Event Subscriber System

Subscribes to Redis pub/sub channel and routes events to appropriate handlers.
Enables backend reactions to cross-domain events.

DESIGN CONSTRAINTS:
1. Layer L3 — Boundary Adapter (no business logic)
2. Handler registration via decorator
3. Fire-and-forget event dispatch (handlers may fail independently)
4. Prometheus metrics for observability
5. Graceful shutdown support

Usage:
    from app.events.subscribers import EventReactor, get_event_reactor

    reactor = get_event_reactor()

    @reactor.on("run.failed")
    def handle_run_failed(payload: dict) -> None:
        # Handle the event
        pass

    # Start the reactor (blocking)
    reactor.start()
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("nova.events.subscribers")

# Configuration
EVENT_REACTOR_ENABLED = os.getenv("EVENT_REACTOR_ENABLED", "false").lower() == "true"
AOS_EVENTS_CHANNEL = "aos.events"

# Heartbeat configuration
REACTOR_HEARTBEAT_INTERVAL_SECONDS = int(
    os.getenv("REACTOR_HEARTBEAT_INTERVAL_SECONDS", "30")
)
REACTOR_HEARTBEAT_MISS_THRESHOLD = int(
    os.getenv("REACTOR_HEARTBEAT_MISS_THRESHOLD", "3")
)  # Create incident after N missed heartbeats

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram

    EVENTS_RECEIVED = Counter(
        "aos_events_received_total",
        "Total events received by reactor",
        ["event_type"],
    )
    EVENTS_HANDLED = Counter(
        "aos_events_handled_total",
        "Total events handled successfully",
        ["event_type", "handler"],
    )
    EVENTS_FAILED = Counter(
        "aos_events_failed_total",
        "Total events that failed handling",
        ["event_type", "handler"],
    )
    HANDLER_DURATION = Histogram(
        "aos_event_handler_duration_seconds",
        "Duration of event handler execution",
        ["event_type", "handler"],
    )
    REACTOR_HEARTBEAT = Counter(
        "aos_reactor_heartbeat_total",
        "Total heartbeats emitted by reactor",
    )
    REACTOR_HEARTBEAT_MISSED = Counter(
        "aos_reactor_heartbeat_missed_total",
        "Total missed heartbeats (reactor unhealthy)",
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


class ReactorState(str, Enum):
    """Event reactor lifecycle states."""

    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"


@dataclass
class EventEnvelope:
    """
    Parsed event envelope from Redis pub/sub.

    Matches the format published by RedisPublisher:
    {
        "event_type": "INCIDENT_CREATED",
        "timestamp": "2025-01-09T12:32:11Z",
        "source": "aos",
        "payload": { ... }
    }
    """

    event_type: str
    timestamp: datetime
    source: str
    payload: Dict[str, Any]
    raw: str = ""

    @classmethod
    def from_message(cls, data: str) -> Optional["EventEnvelope"]:
        """Parse event envelope from Redis message."""
        try:
            parsed = json.loads(data)
            timestamp_str = parsed.get("timestamp", "")

            # Parse timestamp
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)

            return cls(
                event_type=parsed.get("event_type", "UNKNOWN"),
                timestamp=timestamp,
                source=parsed.get("source", "unknown"),
                payload=parsed.get("payload", {}),
                raw=data,
            )
        except json.JSONDecodeError as e:
            logger.error("event_parse_failed", extra={"error": str(e), "data": data[:200]})
            return None


@dataclass
class HandlerRegistration:
    """Registration info for an event handler."""

    event_type: str
    handler: Callable[[Dict[str, Any]], None]
    name: str
    priority: int = 0  # Higher priority handlers run first


@dataclass
class EventReactorStats:
    """Runtime statistics for the event reactor."""

    events_received: int = 0
    events_handled: int = 0
    events_failed: int = 0
    handlers_registered: int = 0
    last_event_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    start_time: Optional[datetime] = None
    # Heartbeat tracking
    heartbeats_emitted: int = 0
    heartbeats_missed: int = 0
    last_heartbeat_time: Optional[datetime] = None
    consecutive_missed_heartbeats: int = 0


class EventReactor:
    """
    Backend event subscriber for cross-domain reactions.

    Subscribes to Redis pub/sub channel and routes events
    to registered handlers.

    Layer: L3 (Boundary Adapter)

    Thread Safety:
    - Handler registration is NOT thread-safe (do at startup)
    - Event dispatch IS thread-safe
    - start() is blocking; use start_background() for async
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize event reactor.

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
        """
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")
        self._handlers: Dict[str, List[HandlerRegistration]] = {}
        self._wildcard_handlers: List[HandlerRegistration] = []
        self._state = ReactorState.STOPPED
        self._stats = EventReactorStats()
        self._stop_event = threading.Event()
        self._client: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        # Heartbeat monitoring
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._heartbeat_interval = REACTOR_HEARTBEAT_INTERVAL_SECONDS
        self._heartbeat_miss_threshold = REACTOR_HEARTBEAT_MISS_THRESHOLD
        self._on_unhealthy_callback: Optional[Callable[[int], None]] = None

    @property
    def state(self) -> ReactorState:
        """Current reactor state."""
        return self._state

    @property
    def stats(self) -> EventReactorStats:
        """Current reactor statistics."""
        if self._stats.start_time:
            self._stats.uptime_seconds = (
                datetime.now(timezone.utc) - self._stats.start_time
            ).total_seconds()
        return self._stats

    def on(
        self,
        event_type: str,
        priority: int = 0,
    ) -> Callable[[Callable[[Dict[str, Any]], None]], Callable[[Dict[str, Any]], None]]:
        """
        Decorator to register an event handler.

        Args:
            event_type: Event type to handle (e.g., "run.failed", "*" for all)
            priority: Handler priority (higher runs first)

        Returns:
            Decorator function

        Example:
            @reactor.on("run.failed")
            def handle_run_failed(payload: dict) -> None:
                logger.info(f"Run failed: {payload['run_id']}")
        """

        def decorator(
            fn: Callable[[Dict[str, Any]], None]
        ) -> Callable[[Dict[str, Any]], None]:
            self.register_handler(event_type, fn, priority=priority)
            return fn

        return decorator

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None],
        name: Optional[str] = None,
        priority: int = 0,
    ) -> None:
        """
        Register an event handler.

        Args:
            event_type: Event type to handle ("*" for all events)
            handler: Handler function (receives payload dict)
            name: Handler name for logging (defaults to function name)
            priority: Handler priority (higher runs first)
        """
        handler_name = name or handler.__name__
        registration = HandlerRegistration(
            event_type=event_type,
            handler=handler,
            name=handler_name,
            priority=priority,
        )

        if event_type == "*":
            self._wildcard_handlers.append(registration)
            self._wildcard_handlers.sort(key=lambda h: -h.priority)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(registration)
            self._handlers[event_type].sort(key=lambda h: -h.priority)

        self._stats.handlers_registered += 1
        logger.info(
            "event_handler_registered",
            extra={
                "event_type": event_type,
                "handler": handler_name,
                "priority": priority,
            },
        )

    def start(self) -> None:
        """
        Start the event reactor (blocking).

        Connects to Redis and begins listening for events.
        Blocks until stop() is called.

        Raises:
            RuntimeError: If Redis is not configured or connection fails
        """
        if self._state != ReactorState.STOPPED:
            logger.warning("event_reactor_already_running", extra={"state": self._state.value})
            return

        self._state = ReactorState.STARTING
        logger.info("event_reactor_starting")

        # Check Redis URL
        if not self._redis_url:
            self._state = ReactorState.STOPPED
            raise RuntimeError(
                "EVENT_REACTOR requires REDIS_URL to be set. "
                "Either set REDIS_URL or disable EVENT_REACTOR_ENABLED"
            )

        # Connect to Redis
        try:
            import redis

            self._client = redis.Redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self._client.ping()
            logger.info("event_reactor_redis_connected")
        except ImportError:
            self._state = ReactorState.STOPPED
            raise RuntimeError("redis package not installed. Install with: pip install redis")
        except Exception as e:
            self._state = ReactorState.STOPPED
            raise RuntimeError(f"Failed to connect to Redis: {e}")

        # Subscribe to events channel
        self._pubsub = self._client.pubsub()
        assert self._pubsub is not None  # Type narrowing for Pyright
        self._pubsub.subscribe(AOS_EVENTS_CHANNEL)

        self._state = ReactorState.RUNNING
        self._stats.start_time = datetime.now(timezone.utc)
        logger.info(
            "event_reactor_started",
            extra={
                "channel": AOS_EVENTS_CHANNEL,
                "handlers": self._stats.handlers_registered,
            },
        )

        # Start heartbeat monitoring thread
        self._start_heartbeat_thread()

        # Main event loop
        self._event_loop()

    def start_background(self) -> threading.Thread:
        """
        Start the event reactor in a background thread.

        Returns:
            Background thread running the reactor
        """
        self._thread = threading.Thread(target=self.start, daemon=True, name="EventReactor")
        self._thread.start()
        return self._thread

    def set_unhealthy_callback(
        self, callback: Callable[[int], None]
    ) -> None:
        """
        Set callback for when reactor becomes unhealthy.

        The callback receives the number of consecutive missed heartbeats.
        Use this to create system-level incidents.

        Args:
            callback: Function to call when unhealthy (receives miss count)
        """
        self._on_unhealthy_callback = callback

    def _start_heartbeat_thread(self) -> None:
        """Start the heartbeat monitoring thread."""
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="EventReactorHeartbeat",
        )
        self._heartbeat_thread.start()
        logger.info(
            "event_reactor_heartbeat_started",
            extra={
                "interval_seconds": self._heartbeat_interval,
                "miss_threshold": self._heartbeat_miss_threshold,
            },
        )

    def _heartbeat_loop(self) -> None:
        """
        Heartbeat monitoring loop.

        Publishes heartbeat events and checks for reactor health.
        If the reactor misses too many heartbeats, triggers unhealthy callback.
        """
        while not self._stop_event.is_set():
            try:
                # Wait for interval
                self._stop_event.wait(timeout=self._heartbeat_interval)
                if self._stop_event.is_set():
                    break

                # Check if reactor is processing events
                now = datetime.now(timezone.utc)
                last_event = self._stats.last_event_time

                # Emit heartbeat
                self._emit_heartbeat()

                # Check health: if no events for 2x heartbeat interval, mark unhealthy
                if last_event:
                    silence_duration = (now - last_event).total_seconds()
                    if silence_duration > self._heartbeat_interval * 2:
                        # Reactor might be stuck or no events flowing
                        self._stats.consecutive_missed_heartbeats += 1
                        self._stats.heartbeats_missed += 1

                        if METRICS_ENABLED:
                            REACTOR_HEARTBEAT_MISSED.inc()

                        logger.warning(
                            "event_reactor_heartbeat_check_failed",
                            extra={
                                "silence_duration_seconds": silence_duration,
                                "consecutive_misses": self._stats.consecutive_missed_heartbeats,
                            },
                        )

                        # Trigger unhealthy callback if threshold exceeded
                        if (
                            self._stats.consecutive_missed_heartbeats
                            >= self._heartbeat_miss_threshold
                        ):
                            self._trigger_unhealthy()
                    else:
                        # Reset consecutive misses on healthy heartbeat
                        self._stats.consecutive_missed_heartbeats = 0

            except Exception as e:
                logger.error("heartbeat_loop_error", extra={"error": str(e)})

    def _emit_heartbeat(self) -> None:
        """Emit a heartbeat event to Redis."""
        if not self._client:
            return

        try:
            heartbeat_event = json.dumps({
                "event_type": "reactor.heartbeat",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "event_reactor",
                "payload": {
                    "events_received": self._stats.events_received,
                    "events_handled": self._stats.events_handled,
                    "uptime_seconds": self.stats.uptime_seconds,
                    "handlers_registered": self._stats.handlers_registered,
                },
            })

            self._client.publish(AOS_EVENTS_CHANNEL, heartbeat_event)
            self._stats.heartbeats_emitted += 1
            self._stats.last_heartbeat_time = datetime.now(timezone.utc)

            if METRICS_ENABLED:
                REACTOR_HEARTBEAT.inc()

            logger.debug(
                "event_reactor_heartbeat_emitted",
                extra={"heartbeat_count": self._stats.heartbeats_emitted},
            )

        except Exception as e:
            logger.warning(f"Failed to emit heartbeat: {e}")

    def _trigger_unhealthy(self) -> None:
        """Trigger unhealthy callback when heartbeat threshold exceeded."""
        logger.error(
            "event_reactor_unhealthy",
            extra={
                "consecutive_missed_heartbeats": self._stats.consecutive_missed_heartbeats,
                "threshold": self._heartbeat_miss_threshold,
            },
        )

        if self._on_unhealthy_callback:
            try:
                self._on_unhealthy_callback(self._stats.consecutive_missed_heartbeats)
            except Exception as e:
                logger.error(f"Unhealthy callback failed: {e}")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the event reactor.

        Args:
            timeout: Seconds to wait for graceful shutdown
        """
        if self._state not in (ReactorState.RUNNING, ReactorState.STARTING):
            return

        logger.info("event_reactor_stopping")
        self._state = ReactorState.STOPPING
        self._stop_event.set()

        # Wait for heartbeat thread to finish
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=timeout / 2)

        # Wait for main thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout / 2)

        # Cleanup
        if self._pubsub:
            try:
                self._pubsub.unsubscribe()
                self._pubsub.close()
            except Exception:
                pass

        if self._client:
            try:
                self._client.close()
            except Exception:
                pass

        self._state = ReactorState.STOPPED
        logger.info(
            "event_reactor_stopped",
            extra={
                "events_received": self._stats.events_received,
                "events_handled": self._stats.events_handled,
                "events_failed": self._stats.events_failed,
                "heartbeats_emitted": self._stats.heartbeats_emitted,
                "heartbeats_missed": self._stats.heartbeats_missed,
            },
        )

    def _event_loop(self) -> None:
        """Main event processing loop."""
        while not self._stop_event.is_set():
            try:
                # Get message with timeout (allows checking stop event)
                message = self._pubsub.get_message(timeout=1.0)  # type: ignore[union-attr]

                if message is None:
                    continue

                if message["type"] != "message":
                    continue

                # Parse event
                data = message.get("data", "")
                if not data:
                    continue

                envelope = EventEnvelope.from_message(data)
                if envelope is None:
                    continue

                # Record metrics
                self._stats.events_received += 1
                self._stats.last_event_time = datetime.now(timezone.utc)

                if METRICS_ENABLED:
                    EVENTS_RECEIVED.labels(event_type=envelope.event_type).inc()

                # Dispatch to handlers
                self._dispatch_event(envelope)

            except Exception as e:
                logger.error("event_loop_error", extra={"error": str(e)})
                # Brief pause on error to avoid tight loop
                time.sleep(0.1)

    def _dispatch_event(self, envelope: EventEnvelope) -> None:
        """
        Dispatch event to registered handlers.

        Args:
            envelope: Parsed event envelope
        """
        # Get handlers for this event type + wildcard handlers
        handlers = list(self._handlers.get(envelope.event_type, []))
        handlers.extend(self._wildcard_handlers)
        handlers.sort(key=lambda h: -h.priority)

        if not handlers:
            logger.debug(
                "event_no_handlers",
                extra={"event_type": envelope.event_type},
            )
            return

        for registration in handlers:
            try:
                start_time = time.time()
                registration.handler(envelope.payload)
                duration = time.time() - start_time

                self._stats.events_handled += 1

                if METRICS_ENABLED:
                    EVENTS_HANDLED.labels(
                        event_type=envelope.event_type,
                        handler=registration.name,
                    ).inc()
                    HANDLER_DURATION.labels(
                        event_type=envelope.event_type,
                        handler=registration.name,
                    ).observe(duration)

                logger.debug(
                    "event_handled",
                    extra={
                        "event_type": envelope.event_type,
                        "handler": registration.name,
                        "duration_ms": int(duration * 1000),
                    },
                )

            except Exception as e:
                self._stats.events_failed += 1

                if METRICS_ENABLED:
                    EVENTS_FAILED.labels(
                        event_type=envelope.event_type,
                        handler=registration.name,
                    ).inc()

                logger.error(
                    "event_handler_failed",
                    extra={
                        "event_type": envelope.event_type,
                        "handler": registration.name,
                        "error": str(e),
                    },
                )


# Singleton instance
_reactor_instance: Optional[EventReactor] = None


def get_event_reactor() -> EventReactor:
    """
    Get or create EventReactor singleton.

    Returns:
        EventReactor instance
    """
    global _reactor_instance
    if _reactor_instance is None:
        _reactor_instance = EventReactor()
    return _reactor_instance


def reset_event_reactor() -> None:
    """Reset reactor instance (for testing)."""
    global _reactor_instance
    if _reactor_instance:
        _reactor_instance.stop()
    _reactor_instance = None
