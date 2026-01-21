#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Test script for EventReactor cross-domain verification
# Reference: PIN-454 Phase 5

"""
EventReactor Cross-Domain Test

Tests the EventReactor by:
1. Starting the reactor in background
2. Publishing events for each domain
3. Verifying handlers receive and process events

Domains tested:
- Activity: run.started, run.completed, run.failed
- Incidents: incident.created, incident.resolved
- Policy: policy.evaluated, threshold.exceeded
- Logs: trace.started, trace.completed
- Audit: audit.reconciliation.missing, audit.reconciliation.drift

Usage:
    python scripts/test_event_reactor.py
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test results tracking
test_results: Dict[str, Dict[str, Any]] = {}
received_events: List[Dict[str, Any]] = []


def log(msg: str, level: str = "INFO") -> None:
    """Simple logger."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {msg}")


def test_redis_connection() -> bool:
    """Test Redis connectivity."""
    log("Testing Redis connection...")

    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        log("REDIS_URL not set", "ERROR")
        return False

    try:
        import redis
        client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        client.ping()
        log("Redis connection OK ✓")
        return True
    except Exception as e:
        log(f"Redis connection failed: {e}", "ERROR")
        return False


def create_test_handlers(reactor: Any) -> None:
    """Register test handlers for all domains."""

    # Activity domain handlers
    @reactor.on("run.started")
    def handle_run_started(payload: Dict[str, Any]) -> None:
        log(f"  → [Activity] run.started: run_id={payload.get('run_id')}")
        received_events.append({"event": "run.started", "payload": payload})

    @reactor.on("run.completed")
    def handle_run_completed(payload: Dict[str, Any]) -> None:
        log(f"  → [Activity] run.completed: run_id={payload.get('run_id')}, status={payload.get('status')}")
        received_events.append({"event": "run.completed", "payload": payload})

    @reactor.on("run.failed")
    def handle_run_failed(payload: Dict[str, Any]) -> None:
        log(f"  → [Activity] run.failed: run_id={payload.get('run_id')}, error={payload.get('error_code')}")
        received_events.append({"event": "run.failed", "payload": payload})

    # Incident domain handlers
    @reactor.on("incident.created")
    def handle_incident_created(payload: Dict[str, Any]) -> None:
        log(f"  → [Incidents] incident.created: incident_id={payload.get('incident_id')}")
        received_events.append({"event": "incident.created", "payload": payload})

    @reactor.on("incident.resolved")
    def handle_incident_resolved(payload: Dict[str, Any]) -> None:
        log(f"  → [Incidents] incident.resolved: incident_id={payload.get('incident_id')}")
        received_events.append({"event": "incident.resolved", "payload": payload})

    # Policy domain handlers
    @reactor.on("policy.evaluated")
    def handle_policy_evaluated(payload: Dict[str, Any]) -> None:
        log(f"  → [Policy] policy.evaluated: run_id={payload.get('run_id')}, decision={payload.get('decision')}")
        received_events.append({"event": "policy.evaluated", "payload": payload})

    @reactor.on("threshold.exceeded")
    def handle_threshold_exceeded(payload: Dict[str, Any]) -> None:
        log(f"  → [Policy] threshold.exceeded: run_id={payload.get('run_id')}, metric={payload.get('metric')}")
        received_events.append({"event": "threshold.exceeded", "payload": payload})

    # Logs domain handlers
    @reactor.on("trace.started")
    def handle_trace_started(payload: Dict[str, Any]) -> None:
        log(f"  → [Logs] trace.started: trace_id={payload.get('trace_id')}")
        received_events.append({"event": "trace.started", "payload": payload})

    @reactor.on("trace.completed")
    def handle_trace_completed(payload: Dict[str, Any]) -> None:
        log(f"  → [Logs] trace.completed: trace_id={payload.get('trace_id')}, steps={payload.get('step_count')}")
        received_events.append({"event": "trace.completed", "payload": payload})

    # Audit domain handlers (RAC)
    @reactor.on("audit.reconciliation.missing")
    def handle_audit_missing(payload: Dict[str, Any]) -> None:
        log(f"  → [Audit] reconciliation.missing: run_id={payload.get('run_id')}")
        received_events.append({"event": "audit.reconciliation.missing", "payload": payload})

    @reactor.on("audit.reconciliation.drift")
    def handle_audit_drift(payload: Dict[str, Any]) -> None:
        log(f"  → [Audit] reconciliation.drift: run_id={payload.get('run_id')}")
        received_events.append({"event": "audit.reconciliation.drift", "payload": payload})

    # Wildcard handler for debugging
    @reactor.on("*")
    def handle_all(payload: Dict[str, Any]) -> None:
        # Just count, don't log (too verbose)
        pass

    log(f"Registered {reactor.stats.handlers_registered} handlers")


def publish_test_events() -> List[str]:
    """Publish test events for all domains."""
    import redis

    redis_url = os.getenv("REDIS_URL", "")
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    channel = "aos.events"

    # Generate test IDs
    run_id = str(uuid.uuid4())
    tenant_id = "test-tenant-001"
    incident_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    events_to_publish = [
        # Activity domain
        {
            "event_type": "run.started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "tenant_id": tenant_id,
                "agent_id": "test-agent",
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        # Logs domain (trace started)
        {
            "event_type": "trace.started",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "trace_id": trace_id,
                "run_id": run_id,
                "tenant_id": tenant_id,
            }
        },
        # Policy domain (evaluation)
        {
            "event_type": "policy.evaluated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "tenant_id": tenant_id,
                "policy_id": "policy-001",
                "decision": "ALLOWED",
                "violations": [],
            }
        },
        # Policy domain (threshold exceeded)
        {
            "event_type": "threshold.exceeded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "tenant_id": tenant_id,
                "metric": "cost",
                "current_value": 5.50,
                "threshold_value": 5.00,
                "percentage": 110.0,
            }
        },
        # Incident domain
        {
            "event_type": "incident.created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "incident_id": incident_id,
                "run_id": run_id,
                "tenant_id": tenant_id,
                "severity": "WARNING",
                "reason": "Budget threshold exceeded",
            }
        },
        # Activity domain (completed)
        {
            "event_type": "run.completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "tenant_id": tenant_id,
                "status": "succeeded",
                "duration_ms": 1500,
                "total_cost": 5.50,
            }
        },
        # Logs domain (trace completed)
        {
            "event_type": "trace.completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "trace_id": trace_id,
                "run_id": run_id,
                "step_count": 5,
                "status": "completed",
            }
        },
        # Incident domain (resolved)
        {
            "event_type": "incident.resolved",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "incident_id": incident_id,
                "run_id": run_id,
                "resolution": "Run completed successfully",
            }
        },
        # Audit domain (missing ack - simulated)
        {
            "event_type": "audit.reconciliation.missing",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "missing_actions": [("incidents", "create_incident")],
                "expected_count": 4,
                "acked_count": 3,
            }
        },
        # Audit domain (drift - simulated)
        {
            "event_type": "audit.reconciliation.drift",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": run_id,
                "drift_actions": [("logs", "extra_trace")],
            }
        },
        # Activity domain (failed run - separate)
        {
            "event_type": "run.failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test",
            "payload": {
                "run_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "error_code": "BUDGET_EXCEEDED",
                "error_message": "Run exceeded budget limit",
            }
        },
    ]

    published_types = []
    log(f"\nPublishing {len(events_to_publish)} test events...")

    for event in events_to_publish:
        message = json.dumps(event, default=str)
        subscriber_count = client.publish(channel, message)
        published_types.append(event["event_type"])
        log(f"  ← Published: {event['event_type']} (subscribers: {subscriber_count})")
        time.sleep(0.1)  # Small delay between events

    client.close()
    return published_types


def verify_results(published_types: List[str]) -> Dict[str, Any]:
    """Verify that all events were received."""
    log("\n" + "=" * 60)
    log("VERIFICATION RESULTS")
    log("=" * 60)

    received_types = [e["event"] for e in received_events]

    results = {
        "published": len(published_types),
        "received": len(received_events),
        "by_domain": {
            "activity": {"expected": 0, "received": 0, "events": []},
            "incidents": {"expected": 0, "received": 0, "events": []},
            "policy": {"expected": 0, "received": 0, "events": []},
            "logs": {"expected": 0, "received": 0, "events": []},
            "audit": {"expected": 0, "received": 0, "events": []},
        },
        "missing": [],
        "success": True,
    }

    # Categorize events by domain
    domain_map = {
        "run.started": "activity",
        "run.completed": "activity",
        "run.failed": "activity",
        "incident.created": "incidents",
        "incident.resolved": "incidents",
        "policy.evaluated": "policy",
        "threshold.exceeded": "policy",
        "trace.started": "logs",
        "trace.completed": "logs",
        "audit.reconciliation.missing": "audit",
        "audit.reconciliation.drift": "audit",
    }

    # Count expected
    for event_type in published_types:
        domain = domain_map.get(event_type, "unknown")
        if domain in results["by_domain"]:
            results["by_domain"][domain]["expected"] += 1

    # Count received
    for event_type in received_types:
        domain = domain_map.get(event_type, "unknown")
        if domain in results["by_domain"]:
            results["by_domain"][domain]["received"] += 1
            results["by_domain"][domain]["events"].append(event_type)

    # Check for missing events
    for event_type in published_types:
        if event_type not in received_types:
            results["missing"].append(event_type)
            results["success"] = False

    # Print results by domain
    log("\nBy Domain:")
    for domain, stats in results["by_domain"].items():
        status = "✓" if stats["received"] >= stats["expected"] else "✗"
        log(f"  {domain.upper():12} {status} {stats['received']}/{stats['expected']} events")
        if stats["events"]:
            for evt in stats["events"]:
                log(f"               • {evt}")

    log(f"\nTotal: {results['received']}/{results['published']} events received")

    if results["missing"]:
        log(f"\nMissing events: {results['missing']}", "WARNING")

    return results


def run_test() -> bool:
    """Run the full EventReactor test."""
    log("=" * 60)
    log("EventReactor Cross-Domain Test")
    log("PIN-454 Phase 5 Verification")
    log("=" * 60)

    # Step 1: Test Redis connection
    if not test_redis_connection():
        return False

    # Step 2: Import and create reactor
    log("\nInitializing EventReactor...")
    try:
        from app.events.subscribers import EventReactor, reset_event_reactor

        # Reset any existing instance
        reset_event_reactor()

        # Create new reactor
        reactor = EventReactor()
        log("EventReactor created ✓")
    except Exception as e:
        log(f"Failed to create EventReactor: {e}", "ERROR")
        return False

    # Step 3: Register handlers
    log("\nRegistering test handlers...")
    create_test_handlers(reactor)

    # Step 4: Start reactor in background
    log("\nStarting EventReactor in background...")
    try:
        thread = reactor.start_background()
        time.sleep(1)  # Wait for reactor to start

        if reactor.state.value != "RUNNING":
            log(f"Reactor not running, state: {reactor.state.value}", "ERROR")
            return False

        log(f"EventReactor running ✓ (state: {reactor.state.value})")
    except Exception as e:
        log(f"Failed to start EventReactor: {e}", "ERROR")
        return False

    # Step 5: Publish test events
    try:
        published_types = publish_test_events()
    except Exception as e:
        log(f"Failed to publish events: {e}", "ERROR")
        reactor.stop()
        return False

    # Step 6: Wait for events to be processed
    log("\nWaiting for events to be processed...")
    time.sleep(2)

    # Step 7: Verify results
    results = verify_results(published_types)

    # Step 8: Print reactor stats
    stats = reactor.stats
    log("\nReactor Stats:")
    log(f"  Events received: {stats.events_received}")
    log(f"  Events handled: {stats.events_handled}")
    log(f"  Events failed: {stats.events_failed}")
    log(f"  Handlers registered: {stats.handlers_registered}")
    log(f"  Uptime: {stats.uptime_seconds:.2f}s")

    # Step 9: Stop reactor
    log("\nStopping EventReactor...")
    reactor.stop(timeout=5.0)
    log(f"EventReactor stopped (state: {reactor.state.value})")

    # Final result
    log("\n" + "=" * 60)
    if results["success"]:
        log("TEST PASSED ✓", "INFO")
        log("All events received and processed across all domains")
    else:
        log("TEST FAILED ✗", "ERROR")
        log(f"Missing events: {results['missing']}")
    log("=" * 60)

    return results["success"]


def main() -> int:
    """Main entry point."""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    success = run_test()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
