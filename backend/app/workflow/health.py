# Workflow Engine Health Endpoints (M4 Hardening)
"""
Health and readiness endpoints for workflow engine.

Provides:
1. /workflow/healthz - Liveness check (always returns OK if process is alive)
2. /workflow/readyz - Readiness check (verifies checkpoint store and golden writer)
3. /workflow/status - Detailed status with metrics

Design Principles:
- Fail-fast: Return 503 immediately if not ready
- Lightweight: No expensive operations in health checks
- Observable: Include diagnostic info for debugging
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import logging
import os

logger = logging.getLogger("nova.workflow.health")

# Optional FastAPI imports (for when used as HTTP endpoints)
try:
    from fastapi import APIRouter
    from fastapi import status as http_status
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    http_status = None
    JSONResponse = None


# Global references to engine components (set during app startup)
_checkpoint_store: Optional[Any] = None
_golden_recorder: Optional[Any] = None
_policy_enforcer: Optional[Any] = None
_last_checkpoint_time: Optional[datetime] = None
_workflow_engine_enabled: bool = False


def configure_health(
    checkpoint_store: Any = None,
    golden_recorder: Any = None,
    policy_enforcer: Any = None,
    enabled: bool = False,
) -> None:
    """
    Configure health check dependencies.

    Called during app startup to inject workflow engine components.

    Args:
        checkpoint_store: CheckpointStore instance
        golden_recorder: GoldenRecorder instance
        policy_enforcer: PolicyEnforcer instance
        enabled: Whether workflow engine is enabled
    """
    global _checkpoint_store, _golden_recorder, _policy_enforcer, _workflow_engine_enabled
    _checkpoint_store = checkpoint_store
    _golden_recorder = golden_recorder
    _policy_enforcer = policy_enforcer
    _workflow_engine_enabled = enabled


def record_checkpoint_activity() -> None:
    """Record that a checkpoint operation occurred (for health tracking)."""
    global _last_checkpoint_time
    _last_checkpoint_time = datetime.now(timezone.utc)


# ============== Core Health Functions ==============
# These work without FastAPI for testing

async def healthz() -> Dict[str, Any]:
    """
    Liveness probe - returns OK if process is running.

    Use for Kubernetes liveness probes.
    Always returns 200 if the service is alive.
    """
    return {
        "status": "ok",
        "service": "workflow_engine",
        "ts": datetime.now(timezone.utc).isoformat(),
    }


async def readyz():
    """
    Readiness probe - checks if workflow engine is ready to accept work.

    Use for Kubernetes readiness probes.
    Returns 200 if ready, 503 if not ready.

    Checks:
    - Workflow engine enabled flag
    - Checkpoint store connectivity (actual DB ping)
    - Golden directory writability (if configured)
    """
    checks = {
        "engine_enabled": _workflow_engine_enabled,
        "checkpoint_store": False,
        "golden_writer": True,  # Default true if not configured
    }

    # Check checkpoint store with actual DB ping
    if _checkpoint_store:
        try:
            # Use ping() for actual DB connectivity check
            if hasattr(_checkpoint_store, 'ping'):
                checks["checkpoint_store"] = await _checkpoint_store.ping()
            else:
                # Fallback for stores without ping (in-memory)
                checks["checkpoint_store"] = hasattr(_checkpoint_store, 'load')
        except Exception as e:
            logger.warning(f"Checkpoint store health check failed: {e}")
            checks["checkpoint_store"] = False
    else:
        # No store configured - mark as not ready
        checks["checkpoint_store"] = False

    # Check golden writer if configured
    if _golden_recorder:
        try:
            if hasattr(_golden_recorder, 'dir'):
                # File-based recorder - check directory exists and is writable
                golden_dir = _golden_recorder.dir
                dir_exists = os.path.isdir(golden_dir)
                dir_writable = os.access(golden_dir, os.W_OK)
                # Also try to create a temp file to verify actual write access
                if dir_exists and dir_writable:
                    import tempfile
                    try:
                        with tempfile.NamedTemporaryFile(dir=golden_dir, delete=True) as tf:
                            tf.write(b"health_check")
                        checks["golden_writer"] = True
                    except Exception:
                        checks["golden_writer"] = False
                else:
                    checks["golden_writer"] = False
            else:
                # In-memory recorder - always OK
                checks["golden_writer"] = True
        except Exception as e:
            logger.warning(f"Golden writer health check failed: {e}")
            checks["golden_writer"] = False

    # Determine overall readiness
    ready = all(checks.values())

    response_data = {
        "ready": ready,
        "checks": checks,
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    # Return JSONResponse if FastAPI available, otherwise dict with status
    if FASTAPI_AVAILABLE and JSONResponse is not None:
        if not ready:
            logger.warning("Workflow engine not ready", extra={"checks": checks})
            return JSONResponse(
                status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response_data,
            )
        return JSONResponse(status_code=http_status.HTTP_200_OK, content=response_data)
    else:
        # For testing without FastAPI, return a mock response
        class MockResponse:
            def __init__(self, status_code: int, body: bytes):
                self.status_code = status_code
                self.body = body

        import json
        if not ready:
            return MockResponse(503, json.dumps(response_data).encode())
        return MockResponse(200, json.dumps(response_data).encode())


async def workflow_status() -> Dict[str, Any]:
    """
    Detailed workflow engine status.

    Includes:
    - Engine configuration
    - Policy settings
    - Last checkpoint time
    - Component health
    """
    status_data = {
        "service": "workflow_engine",
        "enabled": _workflow_engine_enabled,
        "ts": datetime.now(timezone.utc).isoformat(),
        "components": {
            "checkpoint_store": _checkpoint_store is not None,
            "golden_recorder": _golden_recorder is not None,
            "policy_enforcer": _policy_enforcer is not None,
        },
        "last_checkpoint_at": _last_checkpoint_time.isoformat() if _last_checkpoint_time else None,
    }

    # Add policy configuration if available
    if _policy_enforcer:
        status_data["policy"] = {
            "step_ceiling_cents": _policy_enforcer.step_ceiling,
            "workflow_ceiling_cents": _policy_enforcer.workflow_ceiling,
            "emergency_stop_enabled": _policy_enforcer.EMERGENCY_STOP_ENABLED,
        }

    # Add environment flags
    status_data["environment"] = {
        "DISABLE_EXTERNAL_CALLS": os.getenv("DISABLE_EXTERNAL_CALLS", "false"),
        "GOLDEN_SECRET_SET": bool(os.getenv("GOLDEN_SECRET")),
        "WORKFLOW_EMERGENCY_STOP": os.getenv("WORKFLOW_EMERGENCY_STOP", "false"),
    }

    return status_data


async def workflow_config() -> Dict[str, Any]:
    """
    Return workflow engine configuration (non-sensitive).

    Useful for debugging and verifying deployment configuration.
    """
    return {
        "engine": {
            "enabled": _workflow_engine_enabled,
            "checkpoint_store_type": type(_checkpoint_store).__name__ if _checkpoint_store else None,
            "golden_recorder_type": type(_golden_recorder).__name__ if _golden_recorder else None,
        },
        "policy": {
            "step_ceiling_cents": _policy_enforcer.step_ceiling if _policy_enforcer else None,
            "workflow_ceiling_cents": _policy_enforcer.workflow_ceiling if _policy_enforcer else None,
        },
        "environment": {
            "DEFAULT_STEP_CEILING_CENTS": os.getenv("DEFAULT_STEP_CEILING_CENTS", "100"),
            "DEFAULT_WORKFLOW_CEILING_CENTS": os.getenv("DEFAULT_WORKFLOW_CEILING_CENTS", "1000"),
        },
    }


# ============== FastAPI Router ==============
# Only created if FastAPI is available

router = None

if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/workflow", tags=["workflow-health"])

    @router.get("/healthz")
    async def _healthz_endpoint():
        return await healthz()

    @router.get("/readyz")
    async def _readyz_endpoint():
        return await readyz()

    @router.get("/status")
    async def _status_endpoint():
        return await workflow_status()

    @router.get("/config")
    async def _config_endpoint():
        return await workflow_config()
