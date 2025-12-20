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
from .planners import get_planner
from .skills import get_skill, get_skill_manifest, list_skills
from .utils.budget_tracker import BudgetTracker, enforce_budget
from .utils.concurrent_runs import ConcurrentRunsLimiter
from .utils.idempotency import check_idempotency
from .utils.input_sanitizer import sanitize_goal
from .utils.rate_limiter import RateLimiter

# Initialize utilities
rate_limiter = RateLimiter()
concurrent_limiter = ConcurrentRunsLimiter()
budget_tracker = BudgetTracker()

# Initialize logging
logger = setup_logging()

# Initialize database on startup
init_db()

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
    # M7: Check if memory features are enabled
    memory_context_injection = os.getenv("MEMORY_CONTEXT_INJECTION", "false").lower() == "true"
    memory_post_update = os.getenv("MEMORY_POST_UPDATE", "false").lower() == "true"
    drift_detection_enabled = os.getenv("DRIFT_DETECTION_ENABLED", "false").lower() == "true"
    memory_fail_open_override = os.getenv("MEMORY_FAIL_OPEN_OVERRIDE", "false").lower() == "true"
    memory_features_enabled = memory_context_injection or memory_post_update or drift_detection_enabled

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

    # Start queue depth updater
    task = asyncio.create_task(update_queue_depth())
    logger.info("queue_depth_updater_started")

    # Runtime route validation (PIN-108)
    route_issues = validate_route_order(app)
    if route_issues:
        for issue in route_issues:
            logger.warning(f"ROUTE_VALIDATION: {issue}")
        logger.warning("route_validation_complete", extra={"issues": len(route_issues)})
    else:
        logger.info("route_validation_complete", extra={"issues": 0, "status": "pass"})

    yield
    # Cleanup on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("queue_depth_updater_stopped")


# ---------- FastAPI App ----------
app = FastAPI(
    title="NOVA Agent Manager",
    description="AOS MVA - Agent Manager + Planner with async execution",
    version="0.2.0",
    lifespan=lifespan,
)

# Include API routers
from .api.agents import router as agents_router  # M12 Multi-Agent System
from .api.costsim import router as costsim_router
from .api.embedding import router as embedding_router  # PIN-047 Embedding Quota API
from .api.failures import router as failures_router

# M22.1 UI Console - Dual-console architecture (Customer + Operator)
from .api.guard import router as guard_router  # Customer Console (/guard/*)
from .api.health import router as health_router
from .api.memory_pins import router as memory_pins_router
from .api.operator import router as operator_router  # Operator Console (/operator/*)
from .api.ops import router as ops_router  # M24 Ops Console (founder intelligence)
from .api.policy import router as policy_router
from .api.policy_layer import router as policy_layer_router  # M19 Policy Layer
from .api.rbac_api import router as rbac_router
from .api.recovery import router as recovery_router
from .api.recovery_ingest import router as recovery_ingest_router
from .api.runtime import router as runtime_router
from .api.status_history import router as status_history_router
from .api.traces import router as traces_router
from .api.v1_killswitch import router as v1_killswitch_router  # Kill switch, incidents, replay

# from .api.tenants import router as tenants_router  # M21 - DISABLED: Premature for beta stage
# M22 KillSwitch MVP - OpenAI-compatible proxy with safety controls
from .api.v1_proxy import router as v1_proxy_router  # Drop-in OpenAI replacement
from .api.workers import router as workers_router  # Business Builder Worker v0.2

app.include_router(health_router)
app.include_router(policy_router)
app.include_router(runtime_router)
app.include_router(status_history_router)
app.include_router(costsim_router)
app.include_router(memory_pins_router)
app.include_router(rbac_router)
app.include_router(traces_router, prefix="/api/v1")
app.include_router(failures_router)
app.include_router(recovery_router)  # M10 Recovery Suggestion Engine
app.include_router(recovery_ingest_router)  # M10 Recovery Ingest (idempotent)
app.include_router(agents_router)  # M12 Multi-Agent System
app.include_router(policy_layer_router, prefix="/api/v1")  # M19 Policy Layer
app.include_router(embedding_router, prefix="/api/v1")  # PIN-047 Embedding Quota
app.include_router(workers_router)  # Business Builder Worker v0.2
# app.include_router(tenants_router)  # M21 - DISABLED: Premature for beta stage

# M22 KillSwitch MVP - OpenAI-compatible proxy (THE FRONT DOOR)
app.include_router(v1_proxy_router)  # /v1/chat/completions, /v1/embeddings, /v1/status
app.include_router(v1_killswitch_router)  # /v1/killswitch/*, /v1/policies/*, /v1/incidents/*, /v1/replay/*, /v1/demo/*

# M22.1 UI Console - Dual-console architecture
app.include_router(guard_router)  # /guard/* - Customer Console (trust + control)
app.include_router(operator_router)  # /operator/* - Operator Console (truth + oversight)
app.include_router(ops_router)  # /ops/* - M24 Founder Intelligence Console

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
        run.status = final_status
        run.plan_json = json.dumps(plan)
        run.tool_calls_json = json.dumps(tool_calls)
        run.error_message = error_message
        run.completed_at = completed_at
        run.duration_ms = (completed_at - run.started_at).total_seconds() * 1000 if run.started_at else None
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

    return {
        "status": "healthy" if db_status == "connected" and api_key_set else "degraded",
        "service": "nova_agent_manager",
        "database": db_status,
        "api_key_configured": api_key_set,
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


# Set static worker pool size gauge on startup
nova_worker_pool_size.set(int(os.getenv("WORKER_CONCURRENCY", "0")))


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
    rate_key = f"tenant:{tenant_id or 'default'}"
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
    estimated_cost = int(os.getenv("DEFAULT_EST_COST_CENTS", "50"))
    budget_result = enforce_budget(agent_id, estimated_cost)
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
    """List runs for an agent."""
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
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

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
        if not agent:
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
class RerunRequest(BaseModel):
    run_id: str
    reason: Optional[str] = "manual_retry"


class RerunResponse(BaseModel):
    status: str
    run_id: str
    original_status: str
    reason: str


@app.post("/admin/rerun", response_model=RerunResponse)
async def rerun_failed_run(payload: RerunRequest, _: str = Depends(verify_api_key)):
    """
    Re-queue a failed or completed run for retry.
    Only allows re-running runs with status: failed, succeeded, or retry.
    """
    with Session(engine) as session:
        run = session.get(Run, payload.run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        # Only allow rerun of terminal or retry states
        allowed_states = ["failed", "succeeded", "retry"]
        if run.status not in allowed_states:
            raise HTTPException(
                status_code=400, detail=f"Cannot rerun run with status '{run.status}'. Allowed: {allowed_states}"
            )

        original_status = run.status

        # Reset run to queued state
        run.status = "queued"
        run.started_at = None
        run.completed_at = None
        run.error_message = None
        run.next_attempt_at = None
        # Keep attempts count for audit trail
        session.add(run)
        session.commit()

        logger.info(
            "run_requeued",
            extra={
                "run_id": payload.run_id,
                "original_status": original_status,
                "reason": payload.reason,
                "agent_id": run.agent_id,
            },
        )

        return RerunResponse(
            status="queued",
            run_id=payload.run_id,
            original_status=original_status,
            reason=payload.reason or "manual_retry",
        )


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
