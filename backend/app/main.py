# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: external (HTTP)
#   Execution: sync (request-response)
# Role: FastAPI application entry point, route registration, middleware setup
# Callers: uvicorn, gunicorn, docker entrypoint
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5 (no direct worker imports)
# Reference: Core Application

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .auth import verify_api_key
from .auth.rbac_middleware import RBACMiddleware
from .contracts.decisions import backfill_run_id_for_request
from .db import Agent, Memory, Provenance, Run, engine, init_db
from .logging_config import log_provenance, log_request, setup_logging
from .metrics import (
    generate_metrics,
    get_content_type,
    nova_runs_failed_total,
    nova_runs_queued,
    nova_runs_total,
    nova_skill_attempts_total,
    nova_skill_duration_seconds,
    nova_worker_pool_size,
)
from .middleware.tenant import TenantMiddleware
from .models.logs_records import (
    SystemCausedBy,
    SystemComponent,
    SystemEventType,
    SystemRecord,
    SystemSeverity,
)
from .planners import PlannerProtocol, get_planner
from .skills import get_skill, get_skill_manifest, list_skills
from .utils.budget_tracker import BudgetTracker, enforce_budget
from .utils.concurrent_runs import ConcurrentRunsLimiter
from .utils.idempotency import check_idempotency
from .utils.input_sanitizer import sanitize_goal
from .utils.rate_limiter import RateLimiter

# =============================================================================
# Global Utilities (Phase 2A: Deferred initialization)
# =============================================================================
# STRUCTURAL NOTE: These globals are initialized in lifespan(), not at import.
# This prevents DB connections and resource allocation during module import.
# All usage is guarded by lifespan startup completing before requests are served.

rate_limiter: Optional[RateLimiter] = None
concurrent_limiter: Optional[ConcurrentRunsLimiter] = None
budget_tracker: Optional[BudgetTracker] = None
planner: Optional[PlannerProtocol] = None

# Initialize logging (safe at import - no external resources)
logger = setup_logging()


# =============================================================================
# System Record Capture Helper (PIN-413)
# =============================================================================
def _create_system_record(
    component: str,
    event_type: str,
    severity: str,
    summary: str,
    details: Optional[dict] = None,
    caused_by: Optional[str] = None,
    correlation_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
):
    """
    Create an immutable system record for the Logs domain (PIN-413).

    This captures system-level events that affect trust:
    - API/Worker startup and shutdown
    - Deployments
    - Migrations
    - Auth changes

    Records are WRITE-ONCE (no UPDATE, no DELETE - enforced by DB trigger).
    """
    try:
        record = SystemRecord(
            tenant_id=tenant_id,  # NULL for system-wide events
            component=component,
            event_type=event_type,
            severity=severity,
            summary=summary,
            details=details,
            caused_by=caused_by,
            correlation_id=correlation_id,
        )

        with Session(engine) as session:
            session.add(record)
            session.commit()

        logger.info(
            "system_record_created",
            extra={
                "record_id": record.id,
                "component": component,
                "event_type": event_type,
                "severity": severity,
            },
        )
    except Exception as e:
        # System record creation failure should not crash the app
        # This is observability, not execution-critical
        logger.error("system_record_creation_failed", extra={"error": str(e)})


# ---------- API Schemas ----------
class CreateAgentRequest(BaseModel):
    name: str


class CreateAgentResponse(BaseModel):
    agent_id: str
    name: str
    status: str
    created_at: str


class GoalRequest(BaseModel):
    goal: str
    idempotency_key: Optional[str] = Field(default=None, description="Optional key for idempotent submissions")


class GoalResponse(BaseModel):
    run_id: str
    status: str
    message: str


class RunResponse(BaseModel):
    run_id: str
    agent_id: str
    goal: str
    status: str
    attempts: int
    error_message: Optional[str]
    plan: Optional[dict]
    tool_calls: Optional[List[dict]]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[float]


class MemoryResponse(BaseModel):
    id: str
    text: str
    meta: Optional[str]
    created_at: str


class ProvenanceResponse(BaseModel):
    id: str
    run_id: Optional[str]
    agent_id: str
    goal: str
    status: str
    plan: dict
    tool_calls: List[dict]
    attempts: int
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[float]


# ---------- Queue Depth Background Task ----------
async def update_queue_depth():
    """Periodically update the queue depth metric."""
    while True:
        try:
            with Session(engine) as session:
                count = session.exec(select(Run).where(Run.status.in_(["queued", "retry"]))).all()
                nova_runs_queued.set(len(count))
        except Exception as e:
            logger.warning(f"Failed to update queue depth: {e}")
        await asyncio.sleep(10)  # Update every 10 seconds


# =============================================================================
# PIN-411: Deferred Lessons Reactivation Scheduler
# =============================================================================


async def reactivate_deferred_lessons():
    """
    Periodically check for and reactivate deferred lessons.

    Lessons can be deferred to "snooze" them for a period.
    When the deferred_until time passes, they should be
    reactivated back to pending status.

    Runs every 60 seconds to balance responsiveness and efficiency.
    """
    from .services.lessons_learned_engine import get_lessons_learned_engine

    while True:
        try:
            engine = get_lessons_learned_engine()
            reactivated = engine.reactivate_expired_deferred_lessons()
            if reactivated > 0:
                logger.info(
                    "deferred_lessons_reactivated",
                    extra={"count": reactivated},
                )
        except Exception as e:
            logger.warning(f"Failed to reactivate deferred lessons: {e}")
        await asyncio.sleep(60)  # Check every 60 seconds


# =============================================================================
# PIN-411 GOV-POL-003: Panel Invariant Monitor Scheduler
# =============================================================================


async def run_panel_invariant_checks():
    """
    GOV-POL-003: Panel invariants are operator-monitored.

    Periodically check panel-backing queries for silent governance failures.
    Zero results trigger out-of-band alerts, NEVER UI blocking.

    Alert Types:
    - EMPTY_PANEL: Panel returning zero unexpectedly
    - STALE_PANEL: Data older than freshness SLA
    - FILTER_BREAK: Query returns error / no match

    Runs every 5 minutes to balance alerting latency and efficiency.
    This is CONSTITUTIONAL - silent failures must be detected.
    """
    from .services.panel_invariant_monitor import get_panel_monitor

    while True:
        try:
            monitor = get_panel_monitor()
            metrics = monitor.get_metrics()

            # Log metrics for operator visibility
            logger.info(
                "GOV-POL-003_PANEL_INVARIANT_CHECK",
                extra={
                    "panels_monitored": metrics["panels_monitored"],
                    "panels_healthy": metrics["panels_healthy"],
                    "panels_unhealthy": metrics["panels_unhealthy"],
                    "alerts_last_hour": metrics["alerts_last_hour"],
                },
            )

            # If any panels are unhealthy, log warning
            unhealthy = monitor.get_unhealthy_panels()
            if unhealthy:
                for panel in unhealthy:
                    logger.warning(
                        "GOV-POL-003_PANEL_UNHEALTHY",
                        extra={
                            "panel_id": panel.panel_id,
                            "result_count": panel.result_count,
                            "zero_duration_minutes": panel.zero_duration_minutes,
                            "alert_type": panel.alert_type.value if panel.alert_type else None,
                        },
                    )

        except Exception as e:
            logger.warning(f"GOV-POL-003_PANEL_CHECK_ERROR: {e}")

        await asyncio.sleep(300)  # Check every 5 minutes


# =============================================================================
# Runtime Route Validation (PIN-108)
# =============================================================================


def validate_route_order(app: FastAPI) -> list:
    """
    Runtime validation of route ordering.
    Detects if parameter routes shadow static routes.

    Only flags as problematic when, at the FIRST segment where routes differ,
    the earlier route has a parameter (less specific) and the later has static (more specific).
    """
    from typing import Dict, List

    issues = []
    routes_by_method: Dict[str, List[tuple]] = {}

    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method not in routes_by_method:
                    routes_by_method[method] = []
                endpoint_name = getattr(route.endpoint, "__name__", str(route.endpoint))
                routes_by_method[method].append((route.path, endpoint_name))

    def check_route_pair(path1: str, path2: str) -> bool:
        """Returns True if path1 (earlier) problematically shadows path2 (later)."""
        parts1 = path1.strip("/").split("/")
        parts2 = path2.strip("/").split("/")
        if len(parts1) != len(parts2):
            return False

        # Find first position where one route is more specific
        for p1, p2 in zip(parts1, parts2):
            is_param1 = "{" in p1
            is_param2 = "{" in p2

            if not is_param1 and not is_param2:
                if p1 != p2:
                    return False  # Paths diverge, no collision
                continue  # Same static segment

            if is_param1 and is_param2:
                continue  # Both params, no clear winner yet

            # One is static, one is param - this is the differentiator
            if is_param1 and not is_param2:
                # Earlier has param, later has static = PROBLEMATIC
                return True
            else:
                # Earlier has static (more specific) = CORRECT order
                return False

        return False  # Identical or no issues

    for method, routes in routes_by_method.items():
        for i, (path1, name1) in enumerate(routes):
            for path2, name2 in routes[i + 1 :]:
                if check_route_pair(path1, path2):
                    issues.append(f"{method} {path1} ({name1}) may shadow {path2} ({name2})")

    return issues


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - start background tasks and initialize services."""
    # ==========================================================================
    # Phase 2A: Deferred initialization of globals
    # ==========================================================================
    # These were previously initialized at import time. Now initialized here
    # to prevent DB connections and resource allocation during module import.
    global rate_limiter, concurrent_limiter, budget_tracker, planner

    # Initialize utilities
    rate_limiter = RateLimiter()
    concurrent_limiter = ConcurrentRunsLimiter()
    budget_tracker = BudgetTracker()

    # Initialize database
    init_db()

    # =========================================================================
    # GAP-067: SPINE Component Validation (FAIL-FAST)
    # =========================================================================
    # Validate required governance components are available at startup.
    # Missing SPINE components will crash the application (boot-fail policy).
    from .startup.boot_guard import validate_spine_components, SpineValidationError

    try:
        spine_result = validate_spine_components()
        logger.info("spine_components_validated", extra={
            "components_checked": spine_result.components_checked,
            "all_valid": spine_result.all_valid,
        })
    except SpineValidationError as e:
        logger.critical(f"STARTUP ABORTED - SPINE validation failed: {e}")
        raise

    # =========================================================================
    # GAP-046: EventReactor Initialization
    # =========================================================================
    # Initialize EventReactor before accepting requests.
    # Failure to initialize blocks startup (boot-fail policy).
    from .events.reactor_initializer import (
        initialize_event_reactor,
        get_reactor_status,
        shutdown_event_reactor,
    )

    try:
        event_reactor = initialize_event_reactor()
        app.state.event_reactor = event_reactor
        logger.info("event_reactor_initialized", extra=get_reactor_status())
    except RuntimeError as e:
        logger.critical(f"STARTUP ABORTED - EventReactor initialization failed: {e}")
        raise

    # PIN-413: Create immutable system record for API startup
    _create_system_record(
        component=SystemComponent.API.value,
        event_type=SystemEventType.STARTUP.value,
        severity=SystemSeverity.INFO.value,
        summary="API server started",
        details={
            "planner_backend": os.getenv("PLANNER_BACKEND", "stub"),
            "tenant_mode": os.getenv("TENANT_MODE", "single"),
            "skills_count": len(list_skills()),
        },
        caused_by=SystemCausedBy.SYSTEM.value,
    )

    # Initialize planner
    planner = get_planner()

    # Log startup with skills info
    logger.info(
        "NOVA Agent Manager started",
        extra={
            "planner_backend": os.getenv("PLANNER_BACKEND", "stub"),
            "skills_registered": [s["name"] for s in list_skills()],
        },
    )

    # Set worker pool size gauge
    nova_worker_pool_size.set(int(os.getenv("WORKER_CONCURRENCY", "0")))

    # M26: Validate required secrets at startup - FAIL FAST
    from .config.secrets import SecretValidationError, validate_required_secrets

    try:
        # Only hard-fail on DATABASE_URL and REDIS_URL
        # Billing secrets (OpenAI) warn but don't crash
        validate_required_secrets(include_billing=False, hard_fail=True)
        logger.info("startup_secrets_validated")
    except SecretValidationError as e:
        logger.critical(f"STARTUP ABORTED - Missing required secrets: {e}")
        raise

    # =========================================================================
    # PIN-454: Governance Profile Validation (FAIL-FAST)
    # =========================================================================
    # Validate governance feature flag combinations at startup.
    # Invalid combinations (e.g., RAC enforce without RAC enabled) will crash.
    from .services.governance.profile import (
        GovernanceConfigError,
        validate_governance_at_startup,
    )

    try:
        validate_governance_at_startup()
        logger.info("governance_profile_validated")
    except GovernanceConfigError as e:
        logger.critical(f"STARTUP ABORTED - Invalid governance configuration: {e}")
        raise

    # =========================================================================
    # SYSTEM MODE DECLARATIONS (Objective-1: Variable Truth Mapping)
    # =========================================================================

    # Event Publisher Mode
    event_publisher = os.getenv("EVENT_PUBLISHER", "logging").lower()
    logger.info(f"[BOOT] EVENT_PUBLISHER={event_publisher}")

    # Initialize event publisher at startup to fail-fast
    try:
        from .events.publisher import get_publisher

        _publisher = get_publisher()  # This will raise if misconfigured
    except Exception as e:
        logger.critical(f"[BOOT] EventPublisher initialization FAILED: {e}")
        raise

    # Tenant Mode (M21)
    tenant_mode = os.getenv("TENANT_MODE", "single").lower()
    if tenant_mode not in ("single", "multi"):
        raise RuntimeError(f"Invalid TENANT_MODE={tenant_mode}. Valid: single, multi")
    logger.info(f"[BOOT] TENANT_MODE={tenant_mode} (M21 router {'enabled' if tenant_mode == 'multi' else 'disabled'})")

    # CARE Scope (M17)
    care_scope = os.getenv("CARE_SCOPE", "worker_only").lower()
    if care_scope not in ("worker_only", "api_and_worker"):
        raise RuntimeError(f"Invalid CARE_SCOPE={care_scope}. Valid: worker_only, api_and_worker")
    logger.info(
        f"[BOOT] CARE_SCOPE={care_scope} (routing {'API+Worker' if care_scope == 'api_and_worker' else 'Worker only'})"
    )

    # =========================================================================
    # M7: Memory Features
    # =========================================================================
    memory_context_injection = os.getenv("MEMORY_CONTEXT_INJECTION", "false").lower() == "true"
    memory_post_update = os.getenv("MEMORY_POST_UPDATE", "false").lower() == "true"
    drift_detection_enabled = os.getenv("DRIFT_DETECTION_ENABLED", "false").lower() == "true"
    memory_fail_open_override = os.getenv("MEMORY_FAIL_OPEN_OVERRIDE", "false").lower() == "true"
    memory_features_enabled = memory_context_injection or memory_post_update or drift_detection_enabled
    logger.info(
        f"[BOOT] MEMORY_CONTEXT_INJECTION={memory_context_injection}, "
        f"MEMORY_POST_UPDATE={memory_post_update}, DRIFT_DETECTION_ENABLED={drift_detection_enabled}"
    )

    # Initialize M7 services - FAIL-FAST if memory features are enabled but modules unavailable
    try:
        from .auth.rbac_engine import init_rbac_engine
        from .db import get_session
        from .memory.memory_service import init_memory_service
        from .memory.update_rules import init_update_rules_engine

        # Initialize RBAC engine with DB session factory
        init_rbac_engine(db_session_factory=get_session)
        logger.info("rbac_engine_initialized")

        # Initialize update rules engine
        update_rules = init_update_rules_engine()
        logger.info("update_rules_engine_initialized")

        # Initialize memory service (with optional Redis)
        redis_client = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis

                redis_client = redis.from_url(redis_url)
                redis_client.ping()  # Test connection
                logger.info("redis_connected", extra={"url": redis_url.split("@")[-1]})
            except Exception as e:
                logger.warning(f"Redis connection failed, continuing without cache: {e}")
                redis_client = None

        init_memory_service(db_session_factory=get_session, redis_client=redis_client, update_rules=update_rules)
        logger.info("memory_service_initialized")

        # M8: Initialize Redis idempotency store for traces
        # NOTE: This MUST fail-open - missing Redis should NOT crash the server
        idempotency_store = None
        try:
            from .traces.idempotency import get_idempotency_store

            idempotency_store = await get_idempotency_store()
            logger.info(
                "idempotency_store_initialized",
                extra={"type": type(idempotency_store).__name__, "redis_available": bool(redis_url)},
            )
        except Exception:
            logger.warning("Idempotency store initialization failed (continuing without).", exc_info=True)
            idempotency_store = None

    except ImportError as e:
        if memory_features_enabled and not memory_fail_open_override:
            # FAIL-FAST: Memory features enabled but modules not available
            raise RuntimeError(
                f"Memory features enabled (MEMORY_CONTEXT_INJECTION={memory_context_injection}, "
                f"MEMORY_POST_UPDATE={memory_post_update}, DRIFT_DETECTION_ENABLED={drift_detection_enabled}) "
                f"but M7 modules failed to import: {e}. "
                f"Set MEMORY_FAIL_OPEN_OVERRIDE=true to bypass (NOT recommended)."
            ) from e
        else:
            logger.warning(f"M7 services not fully available: {e}")
    except Exception as e:
        if memory_features_enabled and not memory_fail_open_override:
            raise RuntimeError(f"Failed to initialize M7 services: {e}") from e
        else:
            logger.error(f"Failed to initialize M7 services: {e}")

    # =========================================================================
    # PB-S2: Orphan Run Recovery (Crash & Resume)
    # =========================================================================
    # Detect and mark runs that were orphaned due to previous system crash.
    # This MUST run before accepting new requests to ensure truth-grade state.
    try:
        from .services.orphan_recovery import recover_orphaned_runs

        recovery_result = await recover_orphaned_runs()
        if recovery_result.get("detected", 0) > 0:
            logger.warning(
                "pb_s2_orphan_recovery_complete",
                extra={
                    "detected": recovery_result["detected"],
                    "recovered": recovery_result["recovered"],
                    "failed": recovery_result["failed"],
                },
            )
        else:
            logger.info("pb_s2_no_orphaned_runs")
    except Exception as e:
        # Recovery failure should not block startup, but must be logged
        logger.error(f"pb_s2_orphan_recovery_error: {e}", exc_info=True)

    # =========================================================================
    # Phase R-3: Process pending budget enforcement decisions
    # L4 BudgetEnforcementEngine emits decision records for halted runs
    # that don't have corresponding decision records yet.
    # Reference: PIN-257 Phase R-3 (L5→L4 Violation Fix)
    # =========================================================================
    try:
        from .services.budget_enforcement_engine import process_pending_budget_decisions

        decisions_emitted = await process_pending_budget_decisions()
        if decisions_emitted > 0:
            logger.info(
                "phase_r3_budget_decisions_processed",
                extra={"decisions_emitted": decisions_emitted},
            )
        else:
            logger.debug("phase_r3_no_pending_budget_decisions")
    except Exception as e:
        # Decision emission failure should not block startup
        logger.error(f"phase_r3_budget_decision_error: {e}", exc_info=True)

    # Start queue depth updater
    task = asyncio.create_task(update_queue_depth())
    logger.info("queue_depth_updater_started")

    # PIN-411: Start deferred lessons reactivation scheduler
    lessons_task = asyncio.create_task(reactivate_deferred_lessons())
    logger.info("deferred_lessons_scheduler_started")

    # PIN-411 GOV-POL-003: Start panel invariant monitor scheduler
    panel_monitor_task = asyncio.create_task(run_panel_invariant_checks())
    logger.info("GOV-POL-003_panel_invariant_scheduler_started")

    # Runtime route validation (PIN-108)
    route_issues = validate_route_order(app)
    if route_issues:
        for issue in route_issues:
            logger.warning(f"ROUTE_VALIDATION: {issue}")
        logger.warning("route_validation_complete", extra={"issues": len(route_issues)})
    else:
        logger.info("route_validation_complete", extra={"issues": 0, "status": "pass"})

    # =========================================================================
    # CAP-006: Auth Gateway Initialization
    # =========================================================================
    # Initialize the auth gateway with dependencies (session store, API key service)
    try:
        from .auth.gateway_config import AUTH_GATEWAY_ENABLED, configure_auth_gateway

        if AUTH_GATEWAY_ENABLED:
            gateway = await configure_auth_gateway()
            app.state.auth_gateway = gateway
            logger.info("auth_gateway_initialized")
        else:
            logger.info("auth_gateway_skipped", extra={"reason": "AUTH_GATEWAY_ENABLED=false"})
    except Exception as e:
        logger.error(f"auth_gateway_init_error: {e}", exc_info=True)
        # Gateway init failure should not block startup in non-production
        if os.getenv("AUTH_GATEWAY_REQUIRED", "false").lower() == "true":
            raise

    # =========================================================================
    # PIN-443, PIN-444: OpenAPI Warm-Up with Assertion
    # =========================================================================
    # Pre-generate OpenAPI schema to avoid cold-start latency on first request.
    # Enabled via: WARM_OPENAPI_ON_STARTUP=true
    # PIN-444: Added hard assertion - fail startup if generation exceeds threshold
    if os.getenv("WARM_OPENAPI_ON_STARTUP", "false").lower() == "true":
        logger.info("[BOOT] Warming OpenAPI schema (WARM_OPENAPI_ON_STARTUP=true)")

        warmup_start = _openapi_time.perf_counter()
        app.openapi()  # Triggers custom_openapi() which logs timing
        warmup_duration = _openapi_time.perf_counter() - warmup_start

        # PIN-444: Hard assertion - if this fails, something is VERY wrong
        openapi_hard_fail = os.getenv("OPENAPI_HARD_FAIL_ON_SLOW", "false").lower() == "true"
        if warmup_duration > OPENAPI_TIMEOUT_THRESHOLD:
            msg = (
                f"[BOOT] OPENAPI WARM-UP EXCEEDED THRESHOLD: {warmup_duration:.2f}s > {OPENAPI_TIMEOUT_THRESHOLD}s. "
                f"Investigate response models for recursion/unions/default_factory."
            )
            logger.critical(msg)
            if openapi_hard_fail:
                raise RuntimeError(msg)

        logger.info("[BOOT] OpenAPI schema warmed in %.2fs", warmup_duration)

    yield

    # PIN-413: Create immutable system record for API shutdown
    _create_system_record(
        component=SystemComponent.API.value,
        event_type=SystemEventType.SHUTDOWN.value,
        severity=SystemSeverity.INFO.value,
        summary="API server shutting down",
        caused_by=SystemCausedBy.SYSTEM.value,
    )

    # GAP-046: Shutdown EventReactor
    try:
        shutdown_event_reactor()
        logger.info("event_reactor_shutdown")
    except Exception as e:
        logger.error(f"event_reactor_shutdown_error: {e}")

    # Cleanup on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("queue_depth_updater_stopped")

    # Cancel lessons scheduler
    lessons_task.cancel()
    try:
        await lessons_task
    except asyncio.CancelledError:
        pass
    logger.info("deferred_lessons_scheduler_stopped")

    # Cancel panel invariant monitor (GOV-POL-003)
    panel_monitor_task.cancel()
    try:
        await panel_monitor_task
    except asyncio.CancelledError:
        pass
    logger.info("GOV-POL-003_panel_invariant_scheduler_stopped")


# ---------- FastAPI App ----------
app = FastAPI(
    title="NOVA Agent Manager",
    description="AOS MVA - Agent Manager + Planner with async execution",
    version="0.2.0",
    lifespan=lifespan,
)


# ---------- OpenAPI Generation Tracing (PIN-443, PIN-444) ----------
# Explicit observability for schema generation - diagnoses cold-start hangs
# PIN-444: Added timeout detection, cache-free debug endpoint, startup assertion
import time as _openapi_time

from fastapi.openapi.utils import get_openapi as _fastapi_get_openapi

# Configurable timeout threshold (seconds) - fail loudly if exceeded
OPENAPI_TIMEOUT_THRESHOLD = float(os.getenv("OPENAPI_TIMEOUT_THRESHOLD", "10.0"))


def custom_openapi():
    """
    Custom OpenAPI generator with explicit tracing and timeout detection.

    PIN-443: Provides visibility into schema generation timing.
    PIN-444: Adds timeout detection - logs CRITICAL if generation exceeds threshold.

    FastAPI caches after first call, but first call can be slow (~2s for large schemas).
    If generation exceeds OPENAPI_TIMEOUT_THRESHOLD, something is wrong.
    """
    if app.openapi_schema:
        return app.openapi_schema

    logger.warning("OPENAPI: generation started")
    start = _openapi_time.perf_counter()

    schema = _fastapi_get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    duration_s = _openapi_time.perf_counter() - start
    duration_ms = duration_s * 1000

    if duration_s > OPENAPI_TIMEOUT_THRESHOLD:
        logger.critical(
            "OPENAPI: generation SLOW - possible schema graph issue",
            extra={
                "duration_ms": round(duration_ms, 2),
                "threshold_s": OPENAPI_TIMEOUT_THRESHOLD,
                "action": "investigate response models for recursion/unions/default_factory",
            },
        )
    else:
        logger.warning(
            "OPENAPI: generation completed in %.2fs",
            duration_s,
            extra={"duration_ms": round(duration_ms, 2)},
        )

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


# PIN-444: Debug endpoints - DISABLED IN PRODUCTION
# These endpoints expose operational debugging info. Safe for preprod/staging, not for prod.
_DEBUG_ENDPOINTS_ENABLED = os.getenv("AOS_MODE", "preprod").lower() != "prod"


# PIN-444: Debug endpoint for cache-free OpenAPI testing
# Use this to disambiguate "bad schema" vs "bad cache"
@app.get("/__debug/openapi_nocache", include_in_schema=False)
async def openapi_nocache():
    """
    Generate OpenAPI schema WITHOUT cache.

    PIN-444: Disambiguates schema graph problems from cache poisoning.
    DISABLED IN PRODUCTION (AOS_MODE=prod).

    If this hangs → schema graph problem (recursion, union explosion, default_factory)
    If this works but /openapi.json hangs → cache poisoning / stale state

    WARNING: This is slow (~2s) - only use for debugging.
    """
    if not _DEBUG_ENDPOINTS_ENABLED:
        return JSONResponse(status_code=404, content={"error": "not_found"})

    logger.warning("OPENAPI_DEBUG: cache-free generation requested")
    start = _openapi_time.perf_counter()

    # Force regeneration by clearing cache
    app.openapi_schema = None
    schema = app.openapi()

    duration_ms = (_openapi_time.perf_counter() - start) * 1000
    logger.warning(
        "OPENAPI_DEBUG: cache-free generation completed",
        extra={"duration_ms": round(duration_ms, 2)},
    )

    return {"status": "ok", "duration_ms": round(duration_ms, 2), "schema_routes": len(schema.get("paths", {}))}


# PIN-444: Debug endpoint to inspect schema for problematic patterns
@app.get("/__debug/openapi_inspect", include_in_schema=False)
async def openapi_inspect():
    """
    Inspect OpenAPI schema for problematic patterns.

    PIN-444: Quick diagnostic for schema health.
    DISABLED IN PRODUCTION (AOS_MODE=prod).
    """
    if not _DEBUG_ENDPOINTS_ENABLED:
        return JSONResponse(status_code=404, content={"error": "not_found"})

    if not app.openapi_schema:
        app.openapi()

    schema = app.openapi_schema
    components = schema.get("components", {}).get("schemas", {})

    # Count potentially problematic patterns
    recursive_refs = 0
    union_types = 0
    deep_nesting = 0

    for name, model_schema in components.items():
        # Check for recursive $ref patterns
        schema_str = str(model_schema)
        ref_count = schema_str.count("$ref")
        if ref_count > 3:
            recursive_refs += 1

        # Check for anyOf/oneOf (unions)
        if "anyOf" in model_schema or "oneOf" in model_schema:
            union_types += 1

        # Check for deep nesting (properties with nested objects)
        props = model_schema.get("properties", {})
        for prop_name, prop_schema in props.items():
            if isinstance(prop_schema, dict) and prop_schema.get("type") == "object":
                deep_nesting += 1

    return {
        "total_schemas": len(components),
        "paths_count": len(schema.get("paths", {})),
        "potential_issues": {
            "high_ref_count_models": recursive_refs,
            "union_types": union_types,
            "deep_nesting": deep_nesting,
        },
        "health": "ok" if (recursive_refs < 5 and union_types < 10) else "review_needed",
    }


# Include API routers
from .api.accounts import router as accounts_router  # ACCOUNTS: Unified facade (/api/v1/accounts/*)
from .api.activity import router as activity_router  # ACTIVITY Domain: Unified facade (/api/v1/activity/*)
from .api.analytics import router as analytics_router  # ANALYTICS Domain: Unified facade (/api/v1/analytics/*)
from .api.agents import router as agents_router  # M12 Multi-Agent System
from .api.authz_status import router as authz_status_router  # T5: Internal authz status
from .api.connectivity import router as connectivity_router  # CONNECTIVITY: Unified facade (/api/v1/connectivity/*)
from .api.cus_telemetry import router as cus_telemetry_router  # Customer LLM telemetry ingestion
from .api.cus_integrations import router as cus_integrations_router  # Customer LLM integration management
from .api.cus_enforcement import router as cus_enforcement_router  # Customer LLM enforcement checks
from .api.cost_guard import router as cost_guard_router  # /guard/costs/* - Customer cost visibility

# M26 Cost Intelligence - Token attribution, anomaly detection, budget enforcement
from .api.cost_intelligence import router as cost_intelligence_router

# M29 Category 4: Cost Intelligence Completion
from .api.cost_ops import router as cost_ops_router  # /ops/cost/* - Founder cost visibility
from .api.costsim import router as costsim_router
from .api.customer_visibility import router as customer_visibility_router  # Phase 4C-2 Customer Visibility
from .api.embedding import router as embedding_router  # PIN-047 Embedding Quota API

# M29 Category 6: Founder Action Paths
from .api.founder_actions import router as founder_actions_router  # /ops/actions/* - Founder actions

# CRM Contract Review (approve/reject workflow)
from .api.founder_contract_review import (
    router as founder_contract_review_router,  # /founder/contracts/* - Contract review
)
from .api.founder_explorer import router as explorer_router  # H3 Founder Explorer (cross-tenant READ-ONLY)

# PIN-399 Phase-4: Founder onboarding recovery (force-complete)
from .api.founder_onboarding import router as founder_onboarding_router

# PIN-333: Founder AUTO_EXECUTE Review (evidence-only, read-only)
from .api.founder_review import router as founder_review_router  # /founder/review/* - Evidence review
from .api.founder_timeline import router as founder_timeline_router  # Phase 4C-1 Founder Timeline

# M22.1 UI Console - Dual-console architecture (Customer + Operator)
from .api.guard import router as guard_router  # Customer Console (/guard/*)
from .api.guard_logs import router as guard_logs_router  # PIN-281: Customer Logs (/guard/logs/*)
from .api.guard_policies import router as guard_policies_router  # PIN-281: Customer Policies (/guard/policies/*)
from .api.health import router as health_router
from .api.incidents import router as incidents_router  # INCIDENTS Domain: Unified facade (/api/v1/incidents/*)

# M28: failures_router removed (PIN-145) - duplicates /ops/incidents/patterns
from .api.integration import router as integration_router  # M25 Pillar Integration Loop

# M29 Category 7: Legacy Route Handlers (410 Gone)
from .api.legacy_routes import router as legacy_routes_router  # 410 Gone for deprecated paths
from .api.logs import router as logs_router  # LOGS Domain: Unified facade (/api/v1/logs/*)
from .api.memory_pins import router as memory_pins_router
from .api.onboarding import router as onboarding_router  # M24 Customer Onboarding

# M28: operator_router removed (PIN-145) - redundant with /ops/*
from .api.ops import router as ops_router  # M24 Ops Console (founder intelligence)
from .api.overview import router as overview_router  # OVERVIEW Domain: Unified facade (/api/v1/overview/*)
from .api.platform import router as platform_router  # PIN-284 Platform Health (founder-only)
from .api.policies import router as policies_router  # POLICIES Domain: Unified facade (/api/v1/policies/*)
from .api.policy import router as policy_router
from .api.policy_layer import router as policy_layer_router  # M19 Policy Layer

# PIN-LIM: Limits Management Domain
from .api.policy_limits_crud import router as policy_limits_crud_router  # PIN-LIM-01: Policy limits CRUD
from .api.policy_rules_crud import router as policy_rules_crud_router  # PIN-LIM-02: Policy rules CRUD
from .api.limits.simulate import router as limits_simulate_router  # PIN-LIM-04: Limit simulation
from .api.limits.override import router as limits_override_router  # PIN-LIM-05: Limit overrides
from .api.rbac_api import router as rbac_router
from .api.recovery import router as recovery_router
from .api.recovery_ingest import router as recovery_ingest_router
from .api.replay import router as replay_router  # H1 Replay UX (READ-ONLY slice/timeline)
from .api.runtime import router as runtime_router
from .api.scenarios import router as scenarios_router  # H2 Scenario-based Cost Simulation (advisory)

# PIN-399: SDK handshake and registration endpoints
from .api.sdk import router as sdk_router

# PIN-409: Session context for frontend auth state
from .api.session_context import router as session_context_router

# Debug: Auth context visibility endpoint (AUTHORITY_CONTRACT.md)
from .api.debug_auth import router as debug_auth_router
from .api.status_history import router as status_history_router
from .api.tenants import router as tenants_router  # M21 - RE-ENABLED: PIN-399 Onboarding State Machine
from .api.traces import router as traces_router
from .api.v1_killswitch import router as v1_killswitch_router  # Kill switch, incidents, replay

# M22 KillSwitch MVP - OpenAI-compatible proxy with safety controls
from .api.v1_proxy import router as v1_proxy_router  # Drop-in OpenAI replacement
from .api.workers import router as workers_router  # Business Builder Worker v0.2
from .predictions.api import router as c2_predictions_router  # C2 Predictions (advisory only)

# PIN-411: Aurora Runtime Projections - REMOVED (all domains now have unified facades)
# Activity → /api/v1/activity/*, Incidents → /api/v1/incidents/*, Overview → /api/v1/overview/*
# Policies → /api/v1/policies/*, Logs → /api/v1/logs/*

app.include_router(health_router)
app.include_router(policy_router)
app.include_router(runtime_router)
app.include_router(status_history_router)
app.include_router(costsim_router)
app.include_router(memory_pins_router)
app.include_router(rbac_router)
app.include_router(traces_router, prefix="/api/v1")
app.include_router(replay_router, prefix="/api/v1")  # H1 Replay UX (READ-ONLY)
app.include_router(scenarios_router, prefix="/api/v1")  # H2 Scenarios (advisory simulation)
app.include_router(explorer_router, prefix="/api/v1")  # H3 Explorer (founder cross-tenant READ-ONLY)
# M28: failures_router removed (PIN-145)
app.include_router(recovery_router)  # M10 Recovery Suggestion Engine
app.include_router(recovery_ingest_router)  # M10 Recovery Ingest (idempotent)
app.include_router(agents_router)  # M12 Multi-Agent System
app.include_router(policy_layer_router, prefix="/api/v1")  # M19 Policy Layer
app.include_router(embedding_router, prefix="/api/v1")  # PIN-047 Embedding Quota
app.include_router(workers_router)  # Business Builder Worker v0.2
app.include_router(tenants_router)  # M21 - RE-ENABLED: PIN-399 Onboarding State Machine
app.include_router(sdk_router)  # PIN-399: SDK handshake and registration
app.include_router(session_context_router)  # PIN-409: Session context for frontend auth
app.include_router(debug_auth_router)  # Debug: Auth context visibility (AUTHORITY_CONTRACT.md)

# M22 KillSwitch MVP - OpenAI-compatible proxy (THE FRONT DOOR)
app.include_router(v1_proxy_router)  # /v1/chat/completions, /v1/embeddings, /v1/status
app.include_router(v1_killswitch_router)  # /v1/killswitch/*, /v1/policies/*, /v1/incidents/*, /v1/replay/*, /v1/demo/*

# M22.1 UI Console - Dual-console architecture
app.include_router(guard_router)  # /guard/* - Customer Console (trust + control)
app.include_router(guard_logs_router)  # PIN-281: /guard/logs/* - Customer Logs (L4→L3→L2)
app.include_router(guard_policies_router)  # PIN-281: /guard/policies/* - Customer Policy Constraints
app.include_router(activity_router)  # ACTIVITY Domain: /api/v1/activity/* (unified facade)
app.include_router(incidents_router)  # INCIDENTS Domain: /api/v1/incidents/* (unified facade)
app.include_router(overview_router)  # OVERVIEW Domain: /api/v1/overview/* (unified facade)
app.include_router(policies_router)  # POLICIES Domain: /api/v1/policies/* (unified facade)
app.include_router(analytics_router, prefix="/api/v1")  # ANALYTICS Domain: /api/v1/analytics/* (unified facade)

# PIN-LIM: Limits Management Domain routers
app.include_router(policy_limits_crud_router, prefix="/api/v1")  # PIN-LIM-01: Policy limits CRUD
app.include_router(policy_rules_crud_router, prefix="/api/v1")  # PIN-LIM-02: Policy rules CRUD
app.include_router(limits_simulate_router, prefix="/api/v1")  # PIN-LIM-04: Limit simulation
app.include_router(limits_override_router, prefix="/api/v1")  # PIN-LIM-05: Limit overrides

app.include_router(logs_router)  # LOGS Domain: /api/v1/logs/* (unified facade)
app.include_router(connectivity_router)  # CONNECTIVITY: /api/v1/connectivity/* (unified facade)
app.include_router(cus_telemetry_router, prefix="/api/v1")  # Customer LLM telemetry ingestion
app.include_router(cus_integrations_router, prefix="/api/v1")  # Customer LLM integration management
app.include_router(cus_enforcement_router, prefix="/api/v1")  # Customer LLM enforcement checks
app.include_router(accounts_router)  # ACCOUNTS: /api/v1/accounts/* (unified facade)
# M28: operator_router removed (PIN-145) - merged into /ops/*
app.include_router(ops_router)  # /ops/* - M24 Founder Intelligence Console
app.include_router(platform_router)  # /platform/* - PIN-284 Platform Health (founder-only)
app.include_router(founder_timeline_router)  # Phase 4C-1 Founder Timeline (decision records)
app.include_router(founder_review_router)  # PIN-333: /founder/review/* - AUTO_EXECUTE evidence review (FOPS auth)
app.include_router(
    founder_contract_review_router
)  # CRM: /founder/contracts/* - Contract approval/rejection (FOPS auth)
app.include_router(founder_onboarding_router)  # PIN-399 Phase-4: /founder/onboarding/* - Force-complete (FOPS auth)
app.include_router(customer_visibility_router)  # Phase 4C-2 Customer Visibility (predictability)
app.include_router(onboarding_router)  # /api/v1/auth/* - M24 Customer Onboarding
app.include_router(integration_router)  # /integration/* - M25 Pillar Integration Loop
app.include_router(cost_intelligence_router)  # /cost/* - M26 Cost Intelligence

# M29 Category 4: Cost Intelligence Completion - Domain-separated cost visibility
app.include_router(cost_ops_router)  # /ops/cost/* - Founder cost overview (FOPS auth)
app.include_router(cost_guard_router)  # /guard/costs/* - Customer cost summary (Console auth)

# T5: Authorization Status (internal visibility)
app.include_router(authz_status_router)  # /internal/authz/* - M28/M7 status

# C2 Prediction Plane (advisory only, no control influence)
app.include_router(c2_predictions_router)  # /api/v1/c2/predictions - C2 Prediction Plane
# M29 Category 6: Founder Action Paths
app.include_router(founder_actions_router)  # /ops/actions/* - Freeze, throttle, override (FOPS auth)
# M29 Category 7: Legacy Route Handlers (410 Gone for deprecated paths)
app.include_router(legacy_routes_router)  # /dashboard, /operator/*, /demo/*, /simulation/*

# Phase B Observability APIs (READ-ONLY) - PB-S3, PB-S4, PB-S5
from .api.feedback import router as feedback_router  # PB-S3 pattern_feedback
from .api.policy_proposals import router as policy_proposals_router  # PB-S4 policy_proposals
from .api.predictions import router as predictions_router  # PB-S5 prediction_events

app.include_router(feedback_router)  # /api/v1/feedback - Pattern feedback (read-only)
app.include_router(policy_proposals_router)  # /api/v1/policy-proposals - Policy proposals (read-only)
app.include_router(predictions_router)  # /api/v1/predictions - Predictions (read-only)

# Phase C Discovery Ledger (internal, founder/dev only)
from .api.discovery import router as discovery_router

app.include_router(discovery_router)  # /api/v1/discovery - Discovery Ledger (read-only)

# PIN-411: Aurora Runtime Projections - REMOVED (all domains now have unified facades)
# See unified facades: /api/v1/activity/*, /api/v1/incidents/*, /api/v1/overview/*,
# /api/v1/policies/*, /api/v1/logs/*, /api/v1/connectivity/*, /api/v1/accounts/*

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant context middleware (M6)
# Extracts tenant_id from X-Tenant-ID header and propagates through request lifecycle
app.add_middleware(TenantMiddleware)

# RBAC enforcement middleware (M7)
# Evaluates PolicyObject patterns for protected paths
app.add_middleware(RBACMiddleware)

# Auth Gateway middleware (CAP-006)
# Central authentication entry point - JWT XOR API Key, session revocation
# Must run BEFORE RBAC so auth context is available
from .auth.gateway_config import AUTH_GATEWAY_ENABLED, setup_auth_middleware

# Onboarding Gate middleware (PIN-399)
# Enforces onboarding state requirements per endpoint
# Must run AFTER Auth (needs tenant_id) but BEFORE RBAC
from .auth.onboarding_gate import OnboardingGateMiddleware

# Middleware execution order (Starlette runs in reverse of add order):
# 1. AuthGateway (authenticates, sets auth_context)
# 2. OnboardingGate (checks tenant.onboarding_state)
# 3. RBAC (checks permissions - only after COMPLETE state)
# 4. Tenant (propagates tenant context)
app.add_middleware(OnboardingGateMiddleware)

if AUTH_GATEWAY_ENABLED:
    setup_auth_middleware(app)

# Slow Request Diagnostic Middleware (PIN-443)
# Logs warnings for requests > 500ms - helps diagnose VPS hangs
# Enabled via: ENABLE_SLOW_REQUEST_LOGS=true
if os.getenv("ENABLE_SLOW_REQUEST_LOGS", "false").lower() == "true":
    from .middleware.slow_requests import SlowRequestMiddleware

    app.add_middleware(SlowRequestMiddleware, threshold_ms=500)
    logger.info("[BOOT] SlowRequestMiddleware enabled (threshold=500ms)")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ---------- Background task for run execution ----------
async def execute_run(run_id: str, slot_token: Optional[str] = None, concurrency_key: Optional[str] = None):
    """Execute a queued run in the background.

    Args:
        run_id: The run ID to execute
        slot_token: Optional concurrency slot token to release when done
        concurrency_key: Optional concurrency key (agent key) for slot release
    """
    try:
        await _execute_run_inner(run_id)
    finally:
        # Always release concurrency slot when done (if we have one)
        if slot_token and concurrency_key:
            concurrent_limiter.release(concurrency_key, slot_token)
            logger.debug("concurrency_slot_released", extra={"run_id": run_id, "concurrency_key": concurrency_key})


async def _execute_run_inner(run_id: str):
    """Inner execution logic for a run."""
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.status != "queued":
            return

        # Mark as running
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.attempts = 1
        session.add(run)
        session.commit()

        logger.info("run_started", extra={"run_id": run_id, "agent_id": run.agent_id, "goal": run.goal})
        planner_backend = os.getenv("PLANNER_BACKEND", "stub")
        nova_runs_total.labels(status="started", planner=planner_backend).inc()

    # Get tool manifest for planner context from skill registry
    tool_manifest = get_skill_manifest()

    # Generate plan using configured planner
    plan = planner.plan(
        agent_id=run.agent_id,
        goal=run.goal,
        context_summary=None,  # TODO: Add context from previous runs
        memory_snippets=None,  # TODO: Query relevant memories
        tool_manifest=tool_manifest,
    )

    # Normalize step format for execution
    for step in plan.get("steps", []):
        if "type" not in step:
            step["type"] = "invoke_skill"
        if "step_id" not in step:
            step["step_id"] = f"s{step.get('step_id', 1)}"
        elif isinstance(step["step_id"], int):
            step["step_id"] = f"s{step['step_id']}"

    logger.info(
        "plan_generated",
        extra={
            "run_id": run_id,
            "agent_id": run.agent_id,
            "planner": plan.get("planner", "unknown"),
            "step_count": len(plan.get("steps", [])),
        },
    )

    # Execute steps using skill registry
    tool_calls = []
    final_status = "succeeded"
    error_message = None

    for step in plan["steps"]:
        if step["type"] == "invoke_skill":
            skill_name = step.get("skill", "http_call")
            skill_entry = get_skill(skill_name)

            if not skill_entry:
                # Skill not found - log error and continue
                logger.warning("skill_not_found", extra={"skill": skill_name, "run_id": run_id})
                tool_call = {
                    "step_id": step["step_id"],
                    "skill": skill_name,
                    "request": step.get("params", {}),
                    "response": {"status": "error", "error": f"Skill '{skill_name}' not found"},
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                tool_calls.append(tool_call)
                final_status = "failed"
                error_message = f"Skill '{skill_name}' not found"
                continue

            # Instantiate skill with appropriate config
            skill_cls = skill_entry["class"]
            if skill_name == "calendar_write":
                skill_instance = skill_cls(provider=os.getenv("CALENDAR_PROVIDER", "mock"))
            else:
                skill_instance = skill_cls(allow_external=True)

            # Execute skill with metrics tracking
            import time as _time

            _skill_start = _time.time()
            nova_skill_attempts_total.labels(skill=skill_name).inc()
            result = await skill_instance.execute(step.get("params", {}))
            _skill_duration = _time.time() - _skill_start
            nova_skill_duration_seconds.labels(skill=skill_name).observe(_skill_duration)

            tool_call = {
                "step_id": step["step_id"],
                "skill": skill_name,
                "skill_version": result.get("skill_version"),
                "request": step.get("params", {}),
                "response": result.get("result", {}),
                "side_effects": result.get("side_effects", {}),
                "duration": result.get("duration"),
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            tool_calls.append(tool_call)

            # Log skill execution
            log_request(
                logger=logger,
                agent_id=run.agent_id,
                goal=run.goal,
                skill=skill_name,
                status=result.get("result", {}).get("status", "unknown"),
                run_id=run_id,
                duration_ms=result.get("duration", 0) * 1000,
                extra_data={
                    "skill_version": result.get("skill_version"),
                    "side_effects": result.get("side_effects", {}),
                },
            )

            # Check if skill failed
            skill_status = result.get("result", {}).get("status", "")
            if skill_status == "error" or skill_status == "failed":
                final_status = "failed"
                error_message = result.get("result", {}).get("message", "Skill execution failed")

            # Store result as memory
            with Session(engine) as session:
                memory = Memory(
                    agent_id=run.agent_id,
                    memory_type="skill_result",
                    text=f"Skill result: {json.dumps(result.get('result', {}))}",
                    meta=json.dumps(
                        {
                            "goal": run.goal,
                            "skill": skill_name,
                            "skill_version": result.get("skill_version"),
                            "status": skill_status,
                            "run_id": run_id,
                            "side_effects": result.get("side_effects", {}),
                        }
                    ),
                )
                session.add(memory)
                session.commit()

    # Update run with results
    completed_at = datetime.now(timezone.utc)
    with Session(engine) as session:
        run = session.get(Run, run_id)
        assert run is not None
        run.status = final_status
        assert run is not None
        run.plan_json = json.dumps(plan)
        assert run is not None
        run.tool_calls_json = json.dumps(tool_calls)
        run.error_message = error_message
        run.completed_at = completed_at
        assert run is not None
        if run.started_at:
            # Ensure started_at is timezone-aware before subtraction
            started_at_aware = (
                run.started_at.replace(tzinfo=timezone.utc) if run.started_at.tzinfo is None else run.started_at
            )
            run.duration_ms = (completed_at - started_at_aware).total_seconds() * 1000
        else:
            run.duration_ms = None
        session.add(run)
        session.commit()

        # Create provenance record
        provenance = Provenance(
            run_id=run_id,
            agent_id=run.agent_id,
            goal=run.goal,
            status=final_status,
            plan_json=json.dumps(plan),
            tool_calls_json=json.dumps(tool_calls),
            error_message=error_message,
            attempts=run.attempts,
            started_at=run.started_at,
            completed_at=completed_at,
            duration_ms=run.duration_ms,
        )
        session.add(provenance)
        assert session is not None
        assert session is not None
        session.commit()

        # Log provenance
        log_provenance(
            logger=logger, run_id=run_id, agent_id=run.agent_id, goal=run.goal, plan=plan, tool_calls=tool_calls
        )

        logger.info(
            "run_completed",
            extra={
                "run_id": run_id,
                "agent_id": run.agent_id,
                "goal": run.goal,
                "status": final_status,
                "duration_ms": run.duration_ms,
            },
        )

        # Update run metrics
        planner_backend = os.getenv("PLANNER_BACKEND", "stub")
        if final_status == "succeeded":
            nova_runs_total.labels(status="succeeded", planner=planner_backend).inc()
        else:
            nova_runs_total.labels(status="failed", planner=planner_backend).inc()
            nova_runs_failed_total.inc()


# ---------- Endpoints ----------
@app.get("/health")
async def health_check():
    """Health check with DB validation."""
    try:
        with Session(engine) as session:
            session.exec(select(Agent).limit(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    api_key_set = bool(os.getenv("AOS_API_KEY"))

    # GAP-046: Include EventReactor status in health check
    from .events.reactor_initializer import get_reactor_status
    reactor_status = get_reactor_status()
    reactor_healthy = reactor_status.get("healthy", False)

    # GAP-069: Include governance state in health check
    from .services.governance.runtime_switch import get_governance_state
    governance_state = get_governance_state()

    all_healthy = (
        db_status == "connected"
        and api_key_set
        and reactor_healthy
        and governance_state.get("governance_active", True)
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "nova_agent_manager",
        "database": db_status,
        "api_key_configured": api_key_set,
        "event_reactor": reactor_status,  # GAP-046
        "governance": governance_state,   # GAP-069
    }


@app.get("/version")
async def version():
    """Version info."""
    return {
        "service": "nova_agent_manager",
        "version": "0.5.0",
        "api_version": "v1",
        "phase": "MVA-C",
        "features": [
            "async_runs",
            "retry_logic",
            "provenance",
            "pluggable_planners",
            "skill_registry",
            "worker_pool",
            "event_publisher",
        ],
        "planner_backend": os.getenv("PLANNER_BACKEND", "stub"),
        "event_publisher": os.getenv("EVENT_PUBLISHER", "logging"),
        "worker_concurrency": int(os.getenv("WORKER_CONCURRENCY", "0")),
        "skills": list_skills(),
    }


@app.get("/healthz")
async def healthz():
    """Kubernetes-style health check."""
    return {"ok": True, "service": "nova_agent_manager"}


@app.get("/openapi-download")
async def download_openapi():
    """Download OpenAPI spec as JSON file."""
    openapi_spec = app.openapi()
    return JSONResponse(content=openapi_spec, headers={"Content-Disposition": "attachment; filename=openapi.json"})


@app.get("/healthz/worker_pool")
async def worker_pool_health():
    """Worker pool health probe endpoint."""
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "0"))
    return {"worker_pool_configured": concurrency, "status": "standby" if concurrency == 0 else "active"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (multiprocess-aware)."""
    data = generate_metrics()
    return PlainTextResponse(data, media_type=get_content_type())


@app.get("/skills")
async def get_skills():
    """List all registered skills."""
    return {"skills": list_skills(), "manifest": get_skill_manifest()}


@app.post("/agents", response_model=CreateAgentResponse, status_code=201)
async def create_agent(payload: CreateAgentRequest, _: str = Depends(verify_api_key)):
    """Create a new agent."""
    agent = Agent(name=payload.name)

    with Session(engine) as session:
        session.add(agent)
        session.commit()
        session.refresh(agent)

    logger.info("agent_created", extra={"agent_id": agent.id, "extra_data": {"name": agent.name}})

    return CreateAgentResponse(
        agent_id=agent.id, name=agent.name, status=agent.status, created_at=agent.created_at.isoformat()
    )


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str, _: str = Depends(verify_api_key)):
    """Get agent by ID."""
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        return {
            "agent_id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "created_at": agent.created_at.isoformat(),
        }


@app.post("/agents/{agent_id}/goals", response_model=GoalResponse, status_code=202)
async def post_goal(
    agent_id: str,
    payload: GoalRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    _: str = Depends(verify_api_key),
):
    """
    Submit a goal to an agent.
    Returns 202 Accepted with run_id. Poll /runs/{run_id} for status.

    Includes:
    - Idempotency checking (via idempotency_key in payload)
    - Rate limiting per tenant (100 requests/min)
    - Concurrent runs limiting per agent (max 5)
    - Budget pre-check before accepting
    """
    # Get tenant_id from request state (set by TenancyMiddleware)
    tenant_id = getattr(request.state, "tenant_id", None)

    # Phase 4B Extension: Generate request_id for causal binding
    # This ID links pre-run decisions (budget, policy) to the eventual run
    request_id = str(uuid.uuid4())[:16]

    # 1. Idempotency check
    if payload.idempotency_key:
        result = check_idempotency(payload.idempotency_key, tenant_id, agent_id)
        if result.exists and not result.is_expired:
            logger.info(
                "idempotent_request_returned",
                extra={
                    "idempotency_key": payload.idempotency_key,
                    "existing_run_id": result.run_id,
                    "tenant_id": tenant_id,
                },
            )
            return GoalResponse(
                run_id=result.run_id,
                status=result.status or "queued",
                message="Existing run returned (idempotent request).",
            )

    # 2. Input sanitization (prompt injection protection)
    sanitization = sanitize_goal(payload.goal)
    if not sanitization.is_safe:
        logger.warning(
            "goal_sanitization_blocked",
            extra={
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "reason": sanitization.blocked_reason,
                "patterns": sanitization.detected_patterns,
            },
        )
        raise HTTPException(status_code=400, detail=f"Goal rejected: {sanitization.blocked_reason}")

    # Use sanitized goal
    sanitized_goal = sanitization.sanitized

    if sanitization.warnings:
        logger.info(
            "goal_sanitization_warnings",
            extra={
                "agent_id": agent_id,
                "warnings": sanitization.warnings,
            },
        )

    # 3. Rate limit check (per tenant, 100 req/min)
    # AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required for rate limiting")
    rate_key = f"tenant:{tenant_id}"
    if not rate_limiter.allow(rate_key, rate_per_min=100):
        logger.warning("rate_limit_exceeded", extra={"tenant_id": tenant_id, "agent_id": agent_id})
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    # 4. Concurrent runs limit check (per agent, max 5)
    concurrency_key = f"agent:{agent_id}"
    slot_token = concurrent_limiter.acquire(concurrency_key, max_slots=5)
    if not slot_token:
        logger.warning("concurrency_limit_exceeded", extra={"agent_id": agent_id, "tenant_id": tenant_id})
        raise HTTPException(status_code=429, detail="Agent has too many concurrent runs. Try again later.")

    # 5. Budget pre-check with full enforcement
    # Pass request_id for causal binding (Phase 4B extension)
    estimated_cost = int(os.getenv("DEFAULT_EST_COST_CENTS", "50"))
    budget_result = enforce_budget(agent_id, estimated_cost, request_id=request_id)
    if not budget_result.allowed:
        # Release concurrency slot since we're rejecting
        concurrent_limiter.release(concurrency_key, slot_token)
        logger.warning(
            "budget_exceeded",
            extra={
                "agent_id": agent_id,
                "reason": budget_result.reason,
                "breach_type": budget_result.breach_type,
                "limit": budget_result.limit_cents,
                "current": budget_result.current_cents,
            },
        )
        raise HTTPException(status_code=402, detail=f"Budget exceeded: {budget_result.reason}")

    # Verify agent exists
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
            concurrent_limiter.release(concurrency_key, slot_token)
            raise HTTPException(status_code=404, detail="Agent not found")

        # Create run record with idempotency_key and tenant_id
        # Use sanitized_goal instead of raw payload.goal
        run = Run(
            agent_id=agent_id,
            goal=sanitized_goal,
            status="queued",
            idempotency_key=payload.idempotency_key,
            tenant_id=tenant_id,
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        run_id = run.id

        # Phase R-2: Generate plan at creation time (L4 domain logic)
        # Previously, plan generation happened in L5 runner.py, which violated
        # layer boundaries (L5 importing L4). Now L4 generates plans before
        # the run is queued for L5 execution.
        # Reference: PIN-257 Phase R-2 (L5→L4 Violation Fix)
        try:
            from app.services.plan_generation_engine import generate_plan_for_run

            plan_result = generate_plan_for_run(
                agent_id=agent_id,
                goal=sanitized_goal,
                run_id=run_id,
            )

            # Store generated plan in run record
            run.plan_json = plan_result.plan_json
            session.add(run)
            session.commit()

            logger.info(
                "plan_generated_at_creation",
                extra={
                    "run_id": run_id,
                    "step_count": len(plan_result.steps),
                    "memory_snippet_count": plan_result.memory_snippet_count,
                },
            )
        except Exception as e:
            # Plan generation failed - update run status and re-raise
            run.status = "failed"
            run.error_message = f"Plan generation failed: {str(e)}"
            session.add(run)
            session.commit()
            concurrent_limiter.release(concurrency_key, slot_token)
            raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

    # Phase 4B Extension: Backfill run_id for pre-run decisions
    # This binds budget/policy decisions made before run creation
    backfill_run_id_for_request(request_id, run_id)

    logger.info(
        "run_queued",
        extra={
            "run_id": run_id,
            "agent_id": agent_id,
            "goal": payload.goal,
            "tenant_id": tenant_id,
            "idempotency_key": payload.idempotency_key,
            "concurrency_slot": slot_token,
        },
    )

    # Schedule background execution
    # Note: The worker will release the concurrency slot when the run completes
    background_tasks.add_task(execute_run, run_id, slot_token, concurrency_key)

    return GoalResponse(
        run_id=run_id, status="queued", message="Goal accepted. Poll /agents/{agent_id}/runs/{run_id} for status."
    )


@app.get("/agents/{agent_id}/runs/{run_id}", response_model=RunResponse)
async def get_run(agent_id: str, run_id: str, _: str = Depends(verify_api_key)):
    """Get run status and results."""
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.agent_id != agent_id:
            raise HTTPException(status_code=404, detail="Run not found")

        return RunResponse(
            run_id=run.id,
            agent_id=run.agent_id,
            goal=run.goal,
            status=run.status,
            attempts=run.attempts,
            error_message=run.error_message,
            plan=json.loads(run.plan_json) if run.plan_json else None,
            tool_calls=json.loads(run.tool_calls_json) if run.tool_calls_json else None,
            created_at=run.created_at.isoformat(),
            started_at=run.started_at.isoformat() if run.started_at else None,
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            duration_ms=run.duration_ms,
        )


@app.get("/agents/{agent_id}/runs", response_model=List[RunResponse])
async def list_runs(agent_id: str, limit: int = 10, _: str = Depends(verify_api_key)):
    """List runs for an agent."""  # type: ignore[attr-defined]
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        statement = select(Run).where(Run.agent_id == agent_id).order_by(Run.created_at.desc()).limit(limit)
        runs = session.exec(statement).all()

        return [
            RunResponse(
                run_id=run.id,
                agent_id=run.agent_id,
                goal=run.goal,
                status=run.status,
                attempts=run.attempts,
                error_message=run.error_message,
                plan=json.loads(run.plan_json) if run.plan_json else None,
                tool_calls=json.loads(run.tool_calls_json) if run.tool_calls_json else None,
                created_at=run.created_at.isoformat(),
                started_at=run.started_at.isoformat() if run.started_at else None,
                completed_at=run.completed_at.isoformat() if run.completed_at else None,
                duration_ms=run.duration_ms,
            )
            for run in runs
        ]


@app.get("/agents/{agent_id}/recall", response_model=List[MemoryResponse])
async def recall_memory(agent_id: str, query: str, k: int = 5, _: str = Depends(verify_api_key)):
    """Recall memories for an agent."""
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:  # type: ignore[attr-defined]
            raise HTTPException(status_code=404, detail="Agent not found")  # type: ignore[attr-defined]

        statement = (
            select(Memory)
            .where(Memory.agent_id == agent_id)
            .where(Memory.text.ilike(f"%{query}%"))
            .order_by(Memory.created_at.desc())
            .limit(k)
        )
        results = session.exec(statement).all()

        return [MemoryResponse(id=m.id, text=m.text, meta=m.meta, created_at=m.created_at.isoformat()) for m in results]


@app.get("/agents/{agent_id}/provenance", response_model=List[ProvenanceResponse])
async def get_provenance(agent_id: str, limit: int = 10, _: str = Depends(verify_api_key)):
    """Get provenance records for an agent."""
    with Session(engine) as session:
        agent = session.get(Agent, agent_id)
        if not agent:  # type: ignore[attr-defined]
            raise HTTPException(status_code=404, detail="Agent not found")

        statement = (
            select(Provenance)
            .where(Provenance.agent_id == agent_id)
            .order_by(Provenance.created_at.desc())
            .limit(limit)
        )
        results = session.exec(statement).all()

        return [
            ProvenanceResponse(
                id=p.id,
                run_id=p.run_id,
                agent_id=p.agent_id,
                goal=p.goal,
                status=p.status,
                plan=json.loads(p.plan_json),
                tool_calls=json.loads(p.tool_calls_json),
                attempts=p.attempts,
                error_message=p.error_message,
                created_at=p.created_at.isoformat(),
                started_at=p.started_at.isoformat() if p.started_at else None,
                completed_at=p.completed_at.isoformat() if p.completed_at else None,
                duration_ms=p.duration_ms,
            )
            for p in results
        ]


@app.get("/agents/{agent_id}/provenance/{prov_id}", response_model=ProvenanceResponse)
async def get_provenance_by_id(agent_id: str, prov_id: str, _: str = Depends(verify_api_key)):
    """Get a specific provenance record."""
    with Session(engine) as session:
        provenance = session.get(Provenance, prov_id)
        if not provenance or provenance.agent_id != agent_id:
            raise HTTPException(status_code=404, detail="Provenance not found")

        return ProvenanceResponse(
            id=provenance.id,
            run_id=provenance.run_id,
            agent_id=provenance.agent_id,
            goal=provenance.goal,
            status=provenance.status,
            plan=json.loads(provenance.plan_json),
            tool_calls=json.loads(provenance.tool_calls_json),
            attempts=provenance.attempts,
            error_message=provenance.error_message,
            created_at=provenance.created_at.isoformat(),
            started_at=provenance.started_at.isoformat() if provenance.started_at else None,
            completed_at=provenance.completed_at.isoformat() if provenance.completed_at else None,
            duration_ms=provenance.duration_ms,
        )


# ---------- Admin Endpoints ----------


# PB-S1: Retry Request/Response Models (Migration 053)
class RetryRequest(BaseModel):
    """Request to retry a failed worker run (PB-S1 compliant)."""

    run_id: str = Field(..., description="ID of the failed run to retry")
    reason: Optional[str] = Field(default="manual_retry", description="Reason for retry")


class RetryResponse(BaseModel):
    """Response from retry operation (PB-S1 compliant)."""

    original_run_id: str = Field(..., description="ID of the original failed run (unchanged)")
    retry_run_id: str = Field(..., description="ID of the new retry run")
    attempt: int = Field(..., description="Attempt number of the retry")
    status: str = Field(..., description="Status of the retry run (queued)")
    original_status: str = Field(..., description="Status of the original run (unchanged)")
    reason: str


@app.post("/admin/retry", response_model=RetryResponse)
async def retry_failed_run(payload: RetryRequest, _: str = Depends(verify_api_key)):
    """
    Retry a failed worker run by creating a NEW execution (PB-S1 compliant).

    This endpoint:
    - Creates a NEW run with a new ID
    - Sets parent_run_id to link to the original failed run
    - Increments the attempt counter
    - NEVER modifies the original run (immutable)

    PB-S1 Guarantee: Original execution remains unchanged.

    PIN-337: Routes through ExecutionKernel for structural governance.
    """
    from sqlalchemy import select as sa_select

    from .db import get_async_session
    from .governance.kernel import ExecutionKernel, InvocationContext
    from .models.tenant import WorkerRun

    async with get_async_session() as session:
        # Fetch the original failed run
        result = await session.execute(sa_select(WorkerRun).where(WorkerRun.id == payload.run_id))
        original_run = result.scalar_one_or_none()

        if not original_run:
            raise HTTPException(status_code=404, detail="Run not found")

        # PIN-337: Create invocation context and record through kernel
        context = InvocationContext(
            subject="founder",  # Admin routes are founder-only
            tenant_id=original_run.tenant_id,
        )

        # PIN-337: Record invocation through kernel (emits envelope, records metrics)
        # Kernel is called at entry point - envelope emission is handled internally
        ExecutionKernel._emit_envelope(
            capability_id="CAP-019",
            execution_vector="HTTP_ADMIN",
            context=context,
            reason=payload.reason or "manual_retry",
        )
        ExecutionKernel._record_invocation_start(
            capability_id="CAP-019",
            execution_vector="HTTP_ADMIN",
            context=context,
            enforcement_mode=ExecutionKernel._ENFORCEMENT_CONFIG.get("CAP-019", "permissive"),
        )

        # Only allow retry of failed runs
        if original_run.status != "failed":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry run with status '{original_run.status}'. Only 'failed' runs can be retried.",
            )

        # Calculate attempt number by walking the chain
        attempt = original_run.attempt + 1

        # Check if already retried - walk to find the latest
        latest_run = original_run
        retry_check = await session.execute(
            sa_select(WorkerRun).where(WorkerRun.parent_run_id == original_run.id).order_by(WorkerRun.created_at.desc())
        )
        existing_retry = retry_check.scalar_one_or_none()
        if existing_retry:
            # There's already a retry - we should chain from the latest failed attempt
            if existing_retry.status == "failed":
                # Chain from the latest failed retry
                latest_run = existing_retry
                attempt = existing_retry.attempt + 1
            elif existing_retry.status in ("queued", "running"):
                raise HTTPException(
                    status_code=409,
                    detail=f"A retry is already in progress (run_id={existing_retry.id}, status={existing_retry.status})",
                )
            elif existing_retry.status == "completed":
                raise HTTPException(
                    status_code=409, detail=f"Run already succeeded in retry (run_id={existing_retry.id})"
                )

        # Create NEW retry run - original run is NEVER modified
        retry_run = WorkerRun(
            tenant_id=original_run.tenant_id,
            worker_id=original_run.worker_id,
            api_key_id=original_run.api_key_id,
            user_id=original_run.user_id,
            task=original_run.task,
            input_json=original_run.input_json,
            status="queued",
            # PB-S1: Retry linkage
            parent_run_id=latest_run.id,
            attempt=attempt,
            is_retry=True,
        )

        session.add(retry_run)
        await session.commit()
        await session.refresh(retry_run)

        logger.info(
            "pb_s1_retry_created",
            extra={
                "original_run_id": original_run.id,
                "retry_run_id": retry_run.id,
                "attempt": attempt,
                "reason": payload.reason,
                "tenant_id": original_run.tenant_id,
                "worker_id": original_run.worker_id,
            },
        )

        # PIN-337: Record completion
        ExecutionKernel._record_invocation_complete(
            capability_id="CAP-019",
            context=context,
            success=True,
            duration_ms=0,  # Not tracking precise timing in v1
        )

        return RetryResponse(
            original_run_id=original_run.id,
            retry_run_id=retry_run.id,
            attempt=attempt,
            status="queued",
            original_status=original_run.status,
            reason=payload.reason or "manual_retry",
        )


# DEPRECATED: Legacy rerun endpoint (violates PB-S1)
class RerunRequest(BaseModel):
    run_id: str
    reason: Optional[str] = "manual_retry"


class RerunResponse(BaseModel):
    status: str
    run_id: str
    original_status: str
    reason: str
    warning: Optional[str] = None


@app.post("/admin/rerun", response_model=RerunResponse, deprecated=True)
async def rerun_failed_run(payload: RerunRequest, _: str = Depends(verify_api_key)):
    """
    REMOVED: This endpoint has been disabled to enforce PB-S1 truth guarantees.

    Use POST /admin/retry instead.

    PB-S1 Invariant: Retry creates NEW execution, never mutates original.
    This endpoint violated that invariant and has been hard-disabled.
    """
    # PB-S1 HARD-FAIL: This endpoint is permanently disabled
    # It previously mutated original runs, violating truth guarantees
    logger.error(
        "pb_s1_rerun_blocked",
        extra={
            "run_id": payload.run_id,
            "reason": payload.reason,
            "error": "Endpoint disabled - use /admin/retry",
        },
    )

    raise HTTPException(
        status_code=410,  # 410 Gone - resource no longer available
        detail={
            "error": "endpoint_removed",
            "message": "POST /admin/rerun has been permanently disabled (PB-S1 enforcement)",
            "reason": "This endpoint mutated original runs, violating truth guarantees",
            "action": "Use POST /admin/retry instead - it creates a NEW execution with parent linkage",
            "documentation": "See PIN-199 for PB-S1 implementation details",
        },
    )


assert datetime is not None
assert datetime is not None


@app.get("/admin/failed-runs")
async def list_failed_runs(limit: int = 50, _: str = Depends(verify_api_key)):
    """List recent failed runs for review."""
    with Session(engine) as session:
        statement = select(Run).where(Run.status == "failed").order_by(Run.completed_at.desc()).limit(limit)
        runs = session.exec(statement).all()

        return {
            "count": len(runs),
            "runs": [
                {
                    "run_id": r.id,
                    "agent_id": r.agent_id,
                    "goal": r.goal,
                    "attempts": r.attempts,
                    "error_message": r.error_message,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in runs
            ],
        }
