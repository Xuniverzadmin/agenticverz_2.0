"""
Memory Update Tasks - M7 Implementation

Provides async and sync wrappers for applying memory update rules after
trace execution. Used by CostSim and other execution endpoints.

Features:
- Async apply_update_rules for non-blocking updates
- Sync apply_update_rules_sync for deterministic test scenarios
- Memory audit trail logging
- Prometheus metrics

Usage:
    # Async (default, non-blocking)
    asyncio.create_task(apply_update_rules(tenant, workflow, request_id, trace_input, trace_output))

    # Sync (for tests or deterministic scenarios)
    apply_update_rules_sync(tenant, workflow, request_id, trace_input, trace_output)
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger("nova.tasks.memory_update")

# =============================================================================
# Prometheus Metrics
# =============================================================================

MEMORY_UPDATES_TOTAL = Counter("memory_updates_total", "Total memory update operations", ["tenant_id", "status"])

MEMORY_UPDATE_LATENCY = Histogram(
    "memory_update_latency_seconds", "Memory update latency", buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)


# =============================================================================
# Update Rules Configuration
# =============================================================================


def _load_rules() -> List[Dict[str, Any]]:
    """
    Load update rules from configuration.

    Rules define how trace outputs should update memory:
    - target_key: Memory key pattern to update
    - source_path: JSON path in trace output to extract value
    - merge_strategy: How to merge with existing value
    - ttl_seconds: Optional TTL for the pin
    """
    # Default rules - can be extended via config file
    return [
        {
            "id": "costsim_history",
            "description": "Track cost simulation history",
            "target_key": "costsim:history:{tenant_id}",
            "source_paths": {
                "last_cost_cents": "estimated_cost_cents",
                "last_feasible": "feasible",
                "last_simulation_at": "_timestamp",
            },
            "merge_strategy": "deep_merge",
            "ttl_seconds": None,
        },
        {
            "id": "workflow_state",
            "description": "Update workflow execution state",
            "target_key": "workflow:{workflow_id}:state",
            "source_paths": {
                "last_execution_at": "_timestamp",
                "last_status": "status",
                "execution_count": "_increment:1",
            },
            "merge_strategy": "deep_merge",
            "ttl_seconds": None,
        },
        {
            "id": "agent_stats",
            "description": "Track agent execution statistics",
            "target_key": "agent:{agent_id}:stats",
            "source_paths": {
                "total_executions": "_increment:1",
                "last_execution_at": "_timestamp",
            },
            "merge_strategy": "increment",
            "ttl_seconds": None,
        },
    ]


def _extract_value(trace_output: Dict[str, Any], path: str) -> Any:
    """
    Extract value from trace output using dot-notation path.

    Special paths:
    - _timestamp: Current UTC timestamp
    - _increment:N: Returns N for increment operations
    """
    if path == "_timestamp":
        return datetime.now(timezone.utc).isoformat()

    if path.startswith("_increment:"):
        return int(path.split(":")[1])

    # Navigate dot-notation path
    value = trace_output
    for key in path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


async def _write_memory_audit(
    tenant_id: str, workflow_id: Optional[str], request_id: Optional[str], operation: str, details: Dict[str, Any]
) -> None:
    """Write audit record for memory update operation."""
    try:
        from app.memory.memory_service import get_memory_service

        memory_service = get_memory_service()
        if not memory_service:
            return

        audit_key = f"audit:memory_updates:{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "request_id": request_id,
            "operation": operation,
            "details": details,
        }

        # Append to audit log (using append merge strategy)
        await memory_service.set(
            tenant_id=tenant_id, key=audit_key, value=audit_entry, source="memory_update_task", agent_id=None
        )
    except Exception as e:
        logger.warning(f"Failed to write memory audit: {e}")


async def upsert_memory_pin(
    tenant_id: str, key: str, value: Any, source: str = "update_rule", ttl_seconds: Optional[int] = None
) -> bool:
    """
    Upsert a memory pin via the memory service.

    Returns True if successful, False otherwise.
    """
    try:
        from app.memory.memory_service import get_memory_service

        memory_service = get_memory_service()
        if not memory_service:
            logger.warning("Memory service not available for upsert")
            return False

        result = await memory_service.set(
            tenant_id=tenant_id, key=key, value=value, source=source, agent_id=None, ttl_seconds=ttl_seconds
        )

        return result.success

    except Exception as e:
        logger.error(f"Failed to upsert memory pin {key}: {e}")
        return False


async def apply_update_rules(
    tenant_id: str,
    workflow_id: Optional[str],
    request_id: Optional[str],
    trace_input: Dict[str, Any],
    trace_output: Dict[str, Any],
) -> int:
    """
    Evaluate deterministic rules and apply memory writes.

    Each rule is applied in order. Failures in one rule don't block others.

    Args:
        tenant_id: Tenant context
        workflow_id: Optional workflow ID for scoped updates
        request_id: Optional request ID for audit trail
        trace_input: Original trace input/request
        trace_output: Trace execution output

    Returns:
        Number of successful updates applied
    """
    import time

    start_time = time.time()

    rules = _load_rules()
    updates_applied = 0

    # Add context to trace_output for rule extraction
    enriched_output = {
        **trace_output,
        "_timestamp": datetime.now(timezone.utc).isoformat(),
        "_tenant_id": tenant_id,
        "_workflow_id": workflow_id,
        "_request_id": request_id,
    }

    for rule in rules:
        rule_id = rule.get("id", "unknown")

        try:
            # Build target key with substitutions
            target_key = rule["target_key"].format(
                tenant_id=tenant_id,
                workflow_id=workflow_id or "default",
                agent_id=trace_output.get("agent_id", "default"),
            )

            # Skip workflow-scoped rules if no workflow_id
            if "{workflow_id}" in rule["target_key"] and not workflow_id:
                continue

            # Extract values from source paths
            new_value = {}
            for dest_key, source_path in rule.get("source_paths", {}).items():
                extracted = _extract_value(enriched_output, source_path)
                if extracted is not None:
                    new_value[dest_key] = extracted

            if not new_value:
                continue

            # Apply the update
            ttl = rule.get("ttl_seconds")
            success = await upsert_memory_pin(
                tenant_id=tenant_id, key=target_key, value=new_value, source=f"rule:{rule_id}", ttl_seconds=ttl
            )

            if success:
                updates_applied += 1
                MEMORY_UPDATES_TOTAL.labels(tenant_id=tenant_id, status="success").inc()

                # Write audit record
                await _write_memory_audit(
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    request_id=request_id,
                    operation="update_rule_apply",
                    details={"rule": rule_id, "key": target_key, "value": new_value},
                )

                logger.debug(f"Applied rule {rule_id} to {target_key}")
            else:
                MEMORY_UPDATES_TOTAL.labels(tenant_id=tenant_id, status="failed").inc()

        except Exception as e:
            logger.warning(f"Rule {rule_id} failed: {e}")
            MEMORY_UPDATES_TOTAL.labels(tenant_id=tenant_id, status="error").inc()

    duration = time.time() - start_time
    MEMORY_UPDATE_LATENCY.observe(duration)

    logger.info(
        "memory_updates_complete",
        extra={
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "updates_applied": updates_applied,
            "duration_ms": duration * 1000,
        },
    )

    return updates_applied


def apply_update_rules_sync(
    tenant_id: str,
    workflow_id: Optional[str],
    request_id: Optional[str],
    trace_input: Dict[str, Any],
    trace_output: Dict[str, Any],
    timeout: int = 10,
) -> bool:
    """
    Synchronous wrapper to apply update rules and wait for completion.

    This is useful for integration tests that need deterministic immediate
    visibility of memory updates. It runs the async apply_update_rules in
    the event loop and waits until it completes or times out.

    Args:
        tenant_id: Tenant context
        workflow_id: Optional workflow ID
        request_id: Optional request ID
        trace_input: Original trace input
        trace_output: Trace execution output
        timeout: Maximum wait time in seconds

    Returns:
        True if updates completed successfully, False on timeout or error
    """
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    coro = apply_update_rules(tenant_id, workflow_id, request_id, trace_input, trace_output)

    if loop and loop.is_running():
        # Running inside an event loop (e.g., uvicorn)
        # Use run_until_complete via new loop in a thread
        result = {"ok": False, "updates": 0}

        def runner():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                updates = new_loop.run_until_complete(coro)
                result["ok"] = True
                result["updates"] = updates
            except Exception as e:
                logger.error(f"Sync update rules failed: {e}")
                result["ok"] = False
            finally:
                new_loop.close()

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        t.join(timeout)

        if t.is_alive():
            logger.error("apply_update_rules_sync timed out")
            return False

        return result.get("ok", False)
    else:
        # No running loop; run directly
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            updates = new_loop.run_until_complete(coro)
            return updates > 0 or True  # Return True even if 0 updates (no rules matched)
        except Exception as e:
            logger.error(f"Sync update rules failed: {e}")
            return False
        finally:
            new_loop.close()
