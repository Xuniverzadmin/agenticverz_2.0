"""
Staging Webhook Receiver - FastAPI application.

Features:
- Receives webhooks at /webhook (and /webhook/<path>)
- Validates HMAC signatures (optional)
- Stores payloads to PostgreSQL
- Exposes replay, search, and export endpoints
- Configurable retention policy
- Prometheus metrics

Usage:
    DATABASE_URL=postgresql://user:pass@localhost/webhooks \
    WEBHOOK_TOKEN=secret \
    uvicorn app.main:app --host 0.0.0.0 --port 8080
"""

import hashlib
import hmac
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import (
    FastAPI,
    Request,
    Response,
    Header,
    HTTPException,
    Depends,
    Query,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from prometheus_client import (
    Counter,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

from .models import Webhook, get_engine, get_session_factory, init_db
from .rate_limiter import RedisRateLimiter

# Configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://nova:novapass@localhost:6432/nova_aos"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN", "")  # Empty = no auth
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")  # For HMAC validation
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))
MAX_BODY_SIZE = int(os.environ.get("MAX_BODY_SIZE", "1048576"))  # 1MB
RATE_LIMIT_RPM = int(
    os.environ.get("RATE_LIMIT_RPM", "100")
)  # Requests per minute per IP/tenant

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook_receiver")

# Prometheus metrics (using prometheus_client)
WEBHOOKS_RECEIVED = Counter(
    "webhooks_received_total", "Total webhooks received", ["path", "status"]
)
WEBHOOK_AUTH_FAILURES = Counter(
    "webhook_auth_failures_total", "Authentication failures"
)
WEBHOOK_SIGNATURE_FAILURES = Counter(
    "webhook_signature_failures_total", "Signature validation failures"
)
WEBHOOKS_BY_ALERTNAME = Counter(
    "webhooks_by_alertname_total", "Webhooks received by alertname", ["alertname"]
)
WEBHOOK_PROCESSING_TIME = Gauge(
    "webhook_processing_time_seconds", "Time to process webhook"
)

# Redis-backed rate limiter (distributed)
redis_rate_limiter: Optional[RedisRateLimiter] = None

# Database
engine = get_engine(DATABASE_URL)
SessionLocal = get_session_factory(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize DB and Redis on startup."""
    global redis_rate_limiter

    logger.info("Initializing webhook receiver database...")
    init_db(engine)
    logger.info("Database initialized")

    # Initialize Redis rate limiter
    logger.info(f"Initializing Redis rate limiter at {REDIS_URL}...")
    redis_rate_limiter = RedisRateLimiter(
        redis_url=REDIS_URL, default_rpm=RATE_LIMIT_RPM
    )
    connected = await redis_rate_limiter.init()
    if connected:
        logger.info("Redis rate limiter connected")
    else:
        logger.warning("Redis rate limiter failed to connect - will fail-open")

    yield

    # Cleanup
    logger.info("Shutting down webhook receiver")
    if redis_rate_limiter:
        await redis_rate_limiter.close()


app = FastAPI(
    title="AOS Webhook Receiver",
    description="Staging webhook capture service for AOS alerts and integrations",
    version="1.1.0",
    lifespan=lifespan,
)


# Helper functions for rate limiting
def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from request headers or default to 'public'."""
    return request.headers.get("X-Tenant-ID", "public")


def get_remote_ip(request: Request) -> str:
    """Extract client IP, handling X-Forwarded-For for proxies/ingress."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def get_request_id(request: Request) -> str:
    """Extract or generate request ID for log correlation."""
    # Check for existing request ID from headers
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = request.headers.get("X-Correlation-ID")
    if not request_id:
        # Generate one based on timestamp for correlation
        import uuid

        request_id = str(uuid.uuid4())[:8]
    return request_id


async def check_rate_limit(request: Request) -> bool:
    """Check rate limit using Redis-backed limiter."""
    if redis_rate_limiter is None:
        return True  # Not initialized, allow

    tenant_id = get_tenant_id(request)
    ip = get_remote_ip(request)
    request_id = get_request_id(request)

    allowed = await redis_rate_limiter.allow_request(
        tenant_id=tenant_id, ip=ip, rpm=RATE_LIMIT_RPM, request_id=request_id
    )

    if not allowed:
        logger.warning(
            f"Rate limit exceeded | "
            f"tenant_id={tenant_id} ip={ip} request_id={request_id}"
        )

    return allowed


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_token(x_token: Optional[str] = Header(None, alias="X-Webhook-Token")):
    """Verify authentication token if configured."""
    if WEBHOOK_TOKEN and x_token != WEBHOOK_TOKEN:
        WEBHOOK_AUTH_FAILURES.inc()
        raise HTTPException(status_code=403, detail="Invalid or missing token")
    return True


def verify_signature(body: bytes, signature: Optional[str]) -> Optional[bool]:
    """Verify HMAC signature if secret is configured."""
    if not WEBHOOK_SECRET:
        return None  # Not configured

    if not signature:
        return False

    # Support various signature formats
    # X-Hub-Signature-256: sha256=abc123...
    # X-Signature: abc123...
    if "=" in signature:
        algo, sig = signature.split("=", 1)
    else:
        algo, sig = "sha256", signature

    if algo == "sha256":
        expected = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    elif algo == "sha1":
        expected = hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha1,
        ).hexdigest()
    else:
        return False

    return hmac.compare_digest(sig, expected)


def extract_alert_fields(body: Any) -> dict:
    """Extract Alertmanager-specific fields from body."""
    result = {"alertname": None, "severity": None, "status": None}

    if not isinstance(body, (list, dict)):
        return result

    # Handle list of alerts (Alertmanager format)
    alerts = body if isinstance(body, list) else [body]

    for alert in alerts:
        if isinstance(alert, dict):
            labels = alert.get("labels", {})
            result["alertname"] = labels.get("alertname", result["alertname"])
            result["severity"] = labels.get("severity", result["severity"])
            result["status"] = alert.get("status", result["status"])
            break  # Just get first alert's info

    return result


# ========== Webhook Endpoints ==========


@app.post("/webhook")
@app.post("/webhook/{path:path}")
async def receive_webhook(
    request: Request,
    path: str = "",
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_hub_signature: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    # Check rate limit first (Redis-backed distributed limiter)
    if not await check_rate_limit(request):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    """
    Receive and store a webhook payload.

    Accepts any JSON or form data. Stores headers, body, and metadata
    for later replay and analysis.
    """
    # Read body
    body_bytes = await request.body()

    if len(body_bytes) > MAX_BODY_SIZE:
        raise HTTPException(status_code=413, detail="Payload too large")

    # Parse body
    content_type = request.headers.get("content-type", "")
    body_json = None
    body_raw = None

    if "application/json" in content_type:
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            body_raw = body_bytes.decode("utf-8", errors="replace")
    else:
        body_raw = body_bytes.decode("utf-8", errors="replace")

    # Verify signature
    signature = x_hub_signature or x_signature
    sig_valid = verify_signature(body_bytes, signature)

    if sig_valid is False and WEBHOOK_SECRET:
        WEBHOOK_SIGNATURE_FAILURES.inc()
        logger.warning(f"Invalid signature for webhook to /{path}")
        # Don't reject - just log and mark as invalid

    # Extract alert fields
    alert_fields = extract_alert_fields(body_json)

    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)

    # Store webhook
    webhook = Webhook(
        method=request.method,
        path=f"/webhook/{path}" if path else "/webhook",
        query_string=str(request.query_params) if request.query_params else None,
        content_type=content_type,
        headers=dict(request.headers),
        body_json=body_json,
        body_raw=body_raw,
        body_size=len(body_bytes),
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        signature_header=signature,
        signature_valid=sig_valid,
        alertname=alert_fields["alertname"],
        severity=alert_fields["severity"],
        status=alert_fields["status"],
        expires_at=expires_at,
    )

    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    # Update Prometheus metrics
    full_path = webhook.path
    WEBHOOKS_RECEIVED.labels(path=full_path, status="ok").inc()
    if alert_fields["alertname"]:
        WEBHOOKS_BY_ALERTNAME.labels(alertname=alert_fields["alertname"]).inc()

    logger.info(
        f"Webhook received: id={webhook.id}, path={webhook.path}, "
        f"alertname={alert_fields['alertname']}, size={len(body_bytes)}"
    )

    return {"status": "ok", "id": webhook.id}


# ========== Query Endpoints ==========


class WebhookListParams(BaseModel):
    """Query parameters for listing webhooks."""

    path: Optional[str] = None
    alertname: Optional[str] = None
    severity: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@app.get("/webhooks")
async def list_webhooks(
    path: Optional[str] = Query(None),
    alertname: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """List stored webhooks with optional filtering."""
    from sqlalchemy import desc

    query = db.query(Webhook)

    if path:
        query = query.filter(Webhook.path == path)
    if alertname:
        query = query.filter(Webhook.alertname == alertname)
    if severity:
        query = query.filter(Webhook.severity == severity)
    if since:
        query = query.filter(Webhook.received_at >= since)
    if until:
        query = query.filter(Webhook.received_at <= until)

    total = query.count()
    webhooks = (
        query.order_by(desc(Webhook.received_at)).offset(offset).limit(limit).all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "webhooks": [w.to_dict() for w in webhooks],
    }


@app.get("/webhooks/{webhook_id}")
async def get_webhook(
    webhook_id: int,
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """Get a specific webhook by ID."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook.to_dict()


@app.get("/webhooks/{webhook_id}/raw")
async def get_webhook_raw(
    webhook_id: int,
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """Get raw webhook body."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    if webhook.body_json:
        return Response(
            content=json.dumps(webhook.body_json, indent=2),
            media_type="application/json",
        )
    elif webhook.body_raw:
        return Response(content=webhook.body_raw, media_type="text/plain")
    else:
        return Response(content="", media_type="text/plain")


# ========== Replay Endpoints ==========


@app.post("/webhooks/{webhook_id}/replay")
async def replay_webhook(
    webhook_id: int,
    target_url: str = Query(..., description="URL to replay webhook to"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """Replay a webhook to a target URL."""
    import httpx

    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    async def do_replay():
        async with httpx.AsyncClient(timeout=30) as client:
            body = webhook.body_json or webhook.body_raw
            headers = {"Content-Type": webhook.content_type or "application/json"}

            response = await client.request(
                method=webhook.method,
                url=target_url,
                json=body if webhook.body_json else None,
                content=body if webhook.body_raw else None,
                headers=headers,
            )

            # Update replay count
            webhook.replayed = True
            webhook.replay_count += 1
            db.commit()

            logger.info(
                f"Replayed webhook {webhook_id} to {target_url}: "
                f"status={response.status_code}"
            )

    background_tasks.add_task(do_replay)

    return {
        "status": "replay_queued",
        "webhook_id": webhook_id,
        "target_url": target_url,
    }


# ========== Export Endpoints ==========


@app.get("/webhooks/export")
async def export_webhooks(
    format: str = Query("json", enum=["json", "ndjson"]),
    alertname: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """Export webhooks as JSON or NDJSON."""
    from sqlalchemy import desc

    query = db.query(Webhook)

    if alertname:
        query = query.filter(Webhook.alertname == alertname)
    if since:
        query = query.filter(Webhook.received_at >= since)
    if until:
        query = query.filter(Webhook.received_at <= until)

    webhooks = query.order_by(desc(Webhook.received_at)).all()

    if format == "ndjson":

        def generate():
            for w in webhooks:
                yield json.dumps(w.to_dict()) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")
    else:
        return JSONResponse([w.to_dict() for w in webhooks])


# ========== Stats & Health Endpoints ==========


@app.get("/stats")
async def get_stats(db=Depends(get_db)):
    """Get webhook statistics."""
    from sqlalchemy import func

    total = db.query(func.count(Webhook.id)).scalar()
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_count = (
        db.query(func.count(Webhook.id)).filter(Webhook.received_at >= today).scalar()
    )

    # Alertname counts
    alertname_counts = (
        db.query(Webhook.alertname, func.count(Webhook.id))
        .filter(Webhook.alertname.isnot(None))
        .group_by(Webhook.alertname)
        .all()
    )

    # Get rate limiter status
    rate_limiter_status = "not_connected"
    if redis_rate_limiter and redis_rate_limiter._connected:
        rate_limiter_status = "connected"

    return {
        "total_webhooks": total,
        "webhooks_today": today_count,
        "alertname_counts": dict(alertname_counts),
        "rate_limiter": rate_limiter_status,
    }


@app.get("/health")
async def health():
    """Health check endpoint (liveness probe)."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Track application startup time for uptime calculation
_app_start_time: Optional[datetime] = None


@app.get("/ready")
async def ready():
    """
    Readiness check endpoint.

    Checks Redis connectivity and reports degraded status if unavailable.
    Returns 200 in all cases (fail-open behavior) but includes status info.

    Response format when healthy:
    {
        "status": "ok",
        "redis": "ok",
        "version": "v1",
        "uptime_seconds": 12345
    }

    Response format when degraded:
    {
        "status": "degraded",
        "redis": "error" | "disconnected" | "not_initialized"
    }
    """
    global _app_start_time

    # Initialize start time on first call if not set
    if _app_start_time is None:
        _app_start_time = datetime.now(timezone.utc)

    redis_status = "ok"
    redis_degraded = False

    if redis_rate_limiter is None:
        redis_status = "not_initialized"
        redis_degraded = True
    elif not redis_rate_limiter._connected:
        redis_status = "disconnected"
        redis_degraded = True
    else:
        # Try a quick ping
        try:
            await redis_rate_limiter._client.ping()
        except Exception as e:
            redis_status = f"error: {str(e)[:50]}"
            redis_degraded = True

    # Calculate uptime
    uptime_seconds = int((datetime.now(timezone.utc) - _app_start_time).total_seconds())

    if redis_degraded:
        return {
            "status": "degraded",
            "redis": redis_status,
        }

    return {
        "status": "ok",
        "redis": "ok",
        "version": "v1",
        "uptime_seconds": uptime_seconds,
    }


@app.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.

    Uses prometheus_client to generate standard format metrics including:
    - webhooks_received_total (with path, status labels)
    - webhook_auth_failures_total
    - webhook_signature_failures_total
    - webhooks_by_alertname_total (with alertname label)
    - webhook_rate_limit_exceeded_total (from rate_limiter)
    - webhook_rate_limit_redis_errors_total (from rate_limiter)
    - webhook_rate_limit_redis_connected (from rate_limiter)
    """
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


# ========== Cleanup Endpoint ==========


@app.delete("/webhooks/expired")
async def cleanup_expired(
    db=Depends(get_db),
    _auth=Depends(verify_token),
):
    """Delete expired webhooks (based on retention policy)."""
    now = datetime.now(timezone.utc)
    deleted = db.query(Webhook).filter(Webhook.expires_at < now).delete()
    db.commit()

    logger.info(f"Deleted {deleted} expired webhooks")

    return {"deleted": deleted}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
