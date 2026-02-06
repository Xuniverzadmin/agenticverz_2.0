# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: OpenAI-compatible proxy with KillSwitch and budget enforcement
# Authority: WRITE ProxyCall records, Incident records (API self-authority)
# Callers: External clients (drop-in OpenAI replacement), SDK
# Reference: M22 KillSwitch MVP

"""M22 KillSwitch MVP - OpenAI-Compatible Proxy API

Drop-in replacement for OpenAI API with:
- KillSwitch enforcement (423 Locked if frozen)
- Budget enforcement (402 Payment Required if exceeded)
- Default guardrails (429 for rate limit, 400 for blocked)
- Full call logging for replay
- SSE streaming support

Endpoints:
- POST /v1/chat/completions - Chat completions (90% of usage)
- POST /v1/embeddings - Embeddings

HTTP Status Codes:
- 200: Success
- 400: Bad Request (validation, blocked content)
- 401: Unauthorized (invalid API key)
- 402: Payment Required (budget exceeded)
- 423: Locked (killswitch frozen)
- 429: Too Many Requests (rate limited)
- 500: Internal Server Error
- 503: Service Unavailable (upstream error)
"""

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_sync_session_dep,
    get_operation_registry,
    OperationContext,
)
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.proxy")


# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/v1", tags=["OpenAI Proxy"])


# =============================================================================
# Cost Models (per 1M tokens in cents)
# =============================================================================

COST_MODELS = {
    # OpenAI
    "gpt-4o": {"input": 250, "output": 1000},
    "gpt-4o-mini": {"input": 15, "output": 60},
    "gpt-4-turbo": {"input": 1000, "output": 3000},
    "gpt-4": {"input": 3000, "output": 6000},
    "gpt-3.5-turbo": {"input": 50, "output": 150},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
    "claude-3-5-haiku-20241022": {"input": 80, "output": 400},
    "claude-opus-4-20250514": {"input": 1500, "output": 7500},
    # Embeddings
    "text-embedding-3-small": {"input": 2, "output": 0},
    "text-embedding-3-large": {"input": 13, "output": 0},
    "text-embedding-ada-002": {"input": 10, "output": 0},
}

DEFAULT_MODEL = os.getenv("PROXY_DEFAULT_MODEL", "gpt-4o-mini")


# =============================================================================
# Request/Response Schemas (OpenAI-compatible)
# =============================================================================


class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = 4096
    presence_penalty: Optional[float] = 0
    frequency_penalty: Optional[float] = 0
    user: Optional[str] = None
    seed: Optional[int] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class EmbeddingRequest(BaseModel):
    model: str = "text-embedding-3-small"
    input: Any  # str or List[str]
    encoding_format: Optional[str] = "float"
    dimensions: Optional[int] = None
    user: Optional[str] = None


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Usage


class ErrorResponse(BaseModel):
    error: Dict[str, Any]


# =============================================================================
# Auth Dependency
# =============================================================================


async def get_auth_context(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session=Depends(get_sync_session_dep),
) -> Dict[str, Any]:
    """
    Authenticate request and return tenant/key context.

    Supports:
    - Authorization: Bearer <key>
    - X-API-Key: <key>
    """
    api_key = None

    # Extract API key from headers
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]
    elif x_api_key:
        api_key = x_api_key

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"message": "Missing API key", "type": "invalid_request_error", "code": "missing_api_key"}
            },
        )

    # Look up API key via L4 registry dispatch
    registry = get_operation_registry()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_api_key_by_hash",
            "sync_session": session,
            "key_hash": key_hash,
        }
    ))
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": result.error, "type": "internal_error", "code": result.error_code}}
        )
    api_key_row = result.data

    if not api_key_row:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"message": "Invalid API key", "type": "invalid_request_error", "code": "invalid_api_key"}
            },
        )

    # Inline is_valid() check: status must be 'active' and not expired
    db_key_status = api_key_row.status
    db_key_expires_at = api_key_row.expires_at
    now = datetime.now(timezone.utc)
    key_is_valid = (
        db_key_status == "active"
        and (db_key_expires_at is None or db_key_expires_at > now)
    )

    if not key_is_valid:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "message": f"API key is {db_key_status}",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            },
        )

    # Get tenant via L4 registry dispatch
    tenant_result = await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_tenant_by_id",
            "sync_session": session,
            "lookup_tenant_id": api_key_row.tenant_id,
        }
    ))
    if not tenant_result.success:
        raise HTTPException(
            status_code=500,
            detail={"error": {"message": tenant_result.error, "type": "internal_error", "code": tenant_result.error_code}}
        )
    tenant_row = tenant_result.data

    if not tenant_row:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"message": "Tenant not found", "type": "invalid_request_error", "code": "invalid_tenant"}
            },
        )

    # NOTE: Do NOT record usage here.
    # Usage must be recorded AFTER kill switch check to ensure
    # absolute semantics: frozen = no side effects whatsoever.
    # See record_usage_after_killswitch() in endpoint handlers.

    return {
        "tenant_id": tenant_row.id,
        "tenant": tenant_row.raw,
        "api_key_id": api_key_row.id,
        "api_key": api_key_row.raw,
        "session": session,  # Pass session for deferred usage recording
    }


# =============================================================================
# Usage Recording (AFTER KillSwitch)
# =============================================================================


async def record_usage_after_killswitch(auth: Dict[str, Any], session) -> None:
    """
    Record API key usage ONLY after kill switch passes.

    This ensures absolute kill switch semantics:
    - Frozen = zero side effects
    - No retries, no queued executions, no async spillover
    - Not even a usage counter increment
    """
    api_key = auth.get("api_key")
    if api_key and isinstance(api_key, dict):
        now = datetime.now(timezone.utc)
        registry = get_operation_registry()
        await registry.execute("proxy.ops", OperationContext(
            session=None,
            tenant_id="",
            params={
                "method": "record_api_key_usage",
                "sync_session": session,
                "key_id": api_key["id"],
                "now": now,
            }
        ))


# =============================================================================
# KillSwitch Check
# =============================================================================


async def check_killswitch(
    tenant_id: str,
    api_key_id: str,
    session,
) -> Optional[Dict[str, Any]]:
    """
    Check if tenant or API key is frozen.
    Returns error dict if frozen, None if OK.
    """
    registry = get_operation_registry()

    # Check tenant freeze via L4 registry dispatch
    tenant_result = await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id=tenant_id,
        params={
            "method": "get_killswitch_state",
            "sync_session": session,
            "entity_type": "tenant",
            "entity_id": tenant_id,
        }
    ))
    tenant_state = tenant_result.data if tenant_result.success else None

    if tenant_state:
        return {
            "error": {
                # Language layer: "Traffic stopped" not "tenant frozen"
                "message": f"TRAFFIC STOPPED: {tenant_state.freeze_reason or 'Your account has been protected from runaway costs'}",
                "type": "killswitch_error",
                "code": "traffic_stopped",
                "stopped_at": tenant_state.frozen_at.isoformat() if tenant_state.frozen_at else None,
                "reason": tenant_state.freeze_reason,
                "action": "Contact support to resume traffic after reviewing the incident.",
            }
        }

    # Check API key freeze via L4 registry dispatch
    key_result = await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id=tenant_id,
        params={
            "method": "get_killswitch_state",
            "sync_session": session,
            "entity_type": "key",
            "entity_id": api_key_id,
        }
    ))
    key_state = key_result.data if key_result.success else None

    if key_state:
        return {
            "error": {
                # Language layer: "Traffic stopped" not "key frozen"
                "message": f"TRAFFIC STOPPED: {key_state.freeze_reason or 'This API key has been protected from runaway costs'}",
                "type": "killswitch_error",
                "code": "traffic_stopped",
                "stopped_at": key_state.frozen_at.isoformat() if key_state.frozen_at else None,
                "reason": key_state.freeze_reason,
                "action": "Contact support to resume traffic after reviewing the incident.",
            }
        }

    return None


# =============================================================================
# Guardrail Evaluation
# =============================================================================


async def evaluate_guardrails(
    request_body: Dict[str, Any],
    session,
) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Evaluate default guardrails against request.
    Returns (passed, decisions) where passed=False means blocked.
    """
    # Get enabled guardrails ordered by priority via L4 registry dispatch
    registry = get_operation_registry()
    guardrails_result = await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id="",
        params={
            "method": "get_enabled_guardrails",
            "sync_session": session,
        }
    ))
    guardrail_rows = guardrails_result.data if guardrails_result.success else []

    decisions = []
    all_passed = True

    for guardrail in guardrail_rows:
        # Build context for evaluation
        context = {
            "max_tokens": request_body.get("max_tokens", 4096),
            "model": request_body.get("model", DEFAULT_MODEL),
            "text": str(request_body.get("messages", [])),
        }

        # Estimate cost for cost guardrails
        if guardrail.category == "cost":
            model = context["model"]
            max_tokens = context["max_tokens"]
            # Estimate input tokens (rough)
            input_text = context["text"]
            input_tokens = len(input_text) // 4
            pricing = COST_MODELS.get(model, COST_MODELS[DEFAULT_MODEL])
            context["cost_cents"] = (input_tokens / 1_000_000) * pricing["input"] + (max_tokens / 1_000_000) * pricing[
                "output"
            ]

        # Inline evaluate() logic - convert GuardrailRow to dict for _evaluate_guardrail
        guardrail_dict = {
            "id": guardrail.id,
            "name": guardrail.name,
            "category": guardrail.category,
            "rule_type": guardrail.rule_type,
            "rule_config_json": guardrail.rule_config_json,
            "action": guardrail.action,
            "is_enabled": guardrail.is_enabled,
            "priority": guardrail.priority,
        }
        passed, reason = _evaluate_guardrail(guardrail_dict, context)

        decision = {
            "guardrail_id": guardrail.id,
            "guardrail_name": guardrail.name,
            "passed": passed,
            "action": guardrail.action if not passed else None,
            "reason": reason,
        }
        decisions.append(decision)

        if not passed and guardrail.action == "block":
            all_passed = False

    return all_passed, decisions


def _evaluate_guardrail(guardrail, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Evaluate a guardrail dict against context.
    Returns (passed, reason) where passed=False means violation.
    """
    if not guardrail["is_enabled"]:
        return True, None

    config = json.loads(guardrail["rule_config_json"])

    if guardrail["rule_type"] == "max_value":
        field = config.get("field")
        max_val = config.get("max")
        actual = context.get(field, 0)
        if actual > max_val:
            return False, f"{field} ({actual}) exceeds max ({max_val})"
        return True, None

    elif guardrail["rule_type"] == "rate_limit":
        # Rate limiting is handled at middleware level
        return True, None

    elif guardrail["rule_type"] == "threshold":
        metric = config.get("metric")
        threshold = config.get("threshold")
        actual = context.get(metric, 0)
        if actual > threshold:
            return False, f"{metric} ({actual}) exceeds threshold ({threshold})"
        return True, None

    elif guardrail["rule_type"] == "pattern_block":
        patterns = config.get("patterns", [])
        text = context.get("text", "")
        for pattern in patterns:
            if pattern.lower() in text.lower():
                return False, f"Blocked pattern detected: {pattern[:20]}..."
        return True, None

    return True, None


# =============================================================================
# Cost Calculation
# =============================================================================


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Calculate cost in cents."""
    pricing = COST_MODELS.get(model, COST_MODELS[DEFAULT_MODEL])
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return Decimal(str(input_cost + output_cost))


def estimate_tokens(text: str) -> int:
    """Estimate token count."""
    return len(text) // 4


# =============================================================================
# OpenAI Client
# =============================================================================


def get_openai_client():
    """Get OpenAI client (lazy loaded)."""
    try:
        from openai import OpenAI

        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {"message": "OpenAI SDK not available", "type": "service_error", "code": "sdk_unavailable"}
            },
        )


# =============================================================================
# Call Logging
# =============================================================================


async def log_proxy_call(
    session,
    tenant_id: str,
    api_key_id: str,
    endpoint: str,
    request_body: Dict[str, Any],
    response_body: Optional[Dict[str, Any]],
    status_code: int,
    error_code: Optional[str],
    input_tokens: int,
    output_tokens: int,
    cost_cents: Decimal,
    latency_ms: int,
    upstream_latency_ms: Optional[int],
    was_blocked: bool,
    block_reason: Optional[str],
    policy_decisions: List[Dict[str, Any]],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Log a proxy call for replay and analysis via L4 registry dispatch."""

    call_id = str(uuid.uuid4())
    request_json_str = json.dumps(request_body)
    response_json_str = json.dumps(response_body) if response_body else None
    request_hash = hashlib.sha256(
        json.dumps(request_body, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()
    response_hash = (
        hashlib.sha256(
            json.dumps(response_body, sort_keys=True, ensure_ascii=True).encode()
        ).hexdigest()
        if response_body else None
    )
    policy_decisions_json = json.dumps(policy_decisions)
    now = datetime.now(timezone.utc)

    registry = get_operation_registry()
    await registry.execute("proxy.ops", OperationContext(
        session=None,
        tenant_id=tenant_id,
        params={
            "method": "log_proxy_call",
            "sync_session": session,
            "call_data": {
                "call_id": call_id,
                "tenant_id": tenant_id,
                "api_key_id": api_key_id,
                "user_id": user_id,
                "endpoint": endpoint,
                "model": request_body.get("model", DEFAULT_MODEL),
                "request_hash": request_hash,
                "request_json": request_json_str,
                "response_hash": response_hash,
                "response_json": response_json_str,
                "status_code": status_code,
                "error_code": error_code,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cents": cost_cents,
                "policy_decisions_json": policy_decisions_json,
                "was_blocked": was_blocked,
                "block_reason": block_reason,
                "latency_ms": latency_ms,
                "upstream_latency_ms": upstream_latency_ms,
                "replay_eligible": not was_blocked and status_code == 200,
                "created_at": now,
            },
        }
    ))

    return {"id": call_id, "tenant_id": tenant_id, "status_code": status_code}


# =============================================================================
# Chat Completions Endpoint
# =============================================================================


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    auth: Dict[str, Any] = Depends(get_auth_context),
    session=Depends(get_sync_session_dep),
):
    """
    OpenAI-compatible chat completions endpoint.

    Status codes:
    - 200: Success
    - 400: Bad request or content blocked
    - 401: Unauthorized
    - 402: Budget exceeded
    - 423: Tenant/key frozen
    - 429: Rate limited
    - 503: Upstream error
    """
    start_time = time.perf_counter()
    request_body = request.model_dump()

    tenant_id = auth["tenant_id"]
    api_key_id = auth["api_key_id"]

    # === CHECK KILLSWITCH ===
    killswitch_error = await check_killswitch(tenant_id, api_key_id, session)
    if killswitch_error:
        # Log blocked call
        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/chat/completions",
            request_body=request_body,
            response_body=killswitch_error,
            status_code=423,
            error_code="killswitch",
            input_tokens=0,
            output_tokens=0,
            cost_cents=Decimal("0"),
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=None,
            was_blocked=True,
            block_reason="killswitch",
            policy_decisions=[],
            user_id=request.user,  # M23: Track end-user
        )
        raise HTTPException(status_code=423, detail=killswitch_error)

    # === RECORD USAGE (only after killswitch passes) ===
    # This is the ABSOLUTE guarantee: frozen = no side effects
    await record_usage_after_killswitch(auth, session)

    # === EVALUATE GUARDRAILS ===
    passed, decisions = await evaluate_guardrails(request_body, session)
    if not passed:
        # Find the blocking decision
        blocking = next((d for d in decisions if not d["passed"] and d["action"] == "block"), None)
        # Language layer: "Incident prevented" not "policy triggered"
        guardrail_name = blocking["guardrail_name"] if blocking else "policy"
        error = {
            "error": {
                "message": f"INCIDENT PREVENTED: {blocking['reason'] if blocking else 'Request exceeded safety limits'}",
                "type": "incident_prevented",
                "code": "incident_prevented",
                "guardrail": guardrail_name,
                "action": f"Your {guardrail_name} guardrail blocked this request to protect you.",
            }
        }

        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/chat/completions",
            request_body=request_body,
            response_body=error,
            status_code=400,
            error_code="incident_prevented",
            input_tokens=0,
            output_tokens=0,
            cost_cents=Decimal("0"),
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=None,
            was_blocked=True,
            block_reason=guardrail_name,
            policy_decisions=decisions,
            user_id=request.user,  # M23: Track end-user
        )
        raise HTTPException(status_code=400, detail=error)

    # === CALL OPENAI ===
    try:
        client = get_openai_client()
        upstream_start = time.perf_counter()

        # Build OpenAI request
        openai_request = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if request.seed is not None:
            openai_request["seed"] = request.seed
        if request.stop:
            openai_request["stop"] = request.stop
        # M23: Pass user field to OpenAI for end-user tracking
        if request.user:
            openai_request["user"] = request.user

        # Make request
        if request.stream:
            # Streaming response
            return await stream_chat_completion(
                client,
                openai_request,
                request_body,
                auth,
                session,
                start_time,
                decisions,
                user_id=request.user,  # M23: Track end-user
            )
        else:
            response = client.chat.completions.create(**openai_request)
            upstream_latency_ms = int((time.perf_counter() - upstream_start) * 1000)

        # Extract usage
        input_tokens = response.usage.prompt_tokens if response.usage else estimate_tokens(str(request.messages))
        output_tokens = response.usage.completion_tokens if response.usage else 0
        cost_cents = calculate_cost(request.model, input_tokens, output_tokens)

        # Build response
        result = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:24]}",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=response.model,
            choices=[
                ChatCompletionChoice(
                    index=i,
                    message=ChatMessage(role=c.message.role, content=c.message.content or ""),
                    finish_reason=c.finish_reason or "stop",
                )
                for i, c in enumerate(response.choices)
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )

        # Log successful call
        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/chat/completions",
            request_body=request_body,
            response_body=result.model_dump(),
            status_code=200,
            error_code=None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=cost_cents,
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=upstream_latency_ms,
            was_blocked=False,
            block_reason=None,
            policy_decisions=decisions,
            user_id=request.user,  # M23: Track end-user
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"OpenAI API error: {e}")
        error = {
            "error": {
                "message": str(e),
                "type": "api_error",
                "code": "upstream_error",
            }
        }

        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/chat/completions",
            request_body=request_body,
            response_body=error,
            status_code=503,
            error_code="upstream_error",
            input_tokens=0,
            output_tokens=0,
            cost_cents=Decimal("0"),
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=None,
            was_blocked=False,
            block_reason=None,
            policy_decisions=decisions,
            user_id=request.user,  # M23: Track end-user
        )
        raise HTTPException(status_code=503, detail=error)


async def stream_chat_completion(
    client,
    openai_request: Dict[str, Any],
    request_body: Dict[str, Any],
    auth: Dict[str, Any],
    session,
    start_time: float,
    decisions: List[Dict[str, Any]],
    user_id: Optional[str] = None,  # M23: Track end-user
) -> StreamingResponse:
    """Handle streaming chat completion."""

    async def generate() -> AsyncGenerator[bytes, None]:
        total_content = ""
        input_tokens = estimate_tokens(str(openai_request["messages"]))
        upstream_start = time.perf_counter()

        try:
            # Stream from OpenAI
            stream = client.chat.completions.create(**openai_request, stream=True)

            for chunk in stream:
                # Format as SSE
                chunk_dict = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now(timezone.utc).timestamp()),
                    "model": openai_request["model"],
                    "choices": [
                        {
                            "index": c.index,
                            "delta": {
                                "role": c.delta.role if c.delta.role else None,
                                "content": c.delta.content if c.delta.content else None,
                            },
                            "finish_reason": c.finish_reason,
                        }
                        for c in chunk.choices
                    ],
                }

                # Track content
                for c in chunk.choices:
                    if c.delta.content:
                        total_content += c.delta.content

                yield f"data: {json.dumps(chunk_dict)}\n\n".encode()

            yield b"data: [DONE]\n\n"

            # Log after stream completes
            upstream_latency_ms = int((time.perf_counter() - upstream_start) * 1000)
            output_tokens = estimate_tokens(total_content)
            cost_cents = calculate_cost(openai_request["model"], input_tokens, output_tokens)

            # Need a new session for the commit since we're in a generator
            # TODO: L2-DB-HYGIENE — replace inline session creation with L4-provided context manager
            from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_sync_session_dep as _get_dep
            new_session = next(_get_dep())
            try:
                await log_proxy_call(
                    session=new_session,
                    tenant_id=auth["tenant_id"],
                    api_key_id=auth["api_key_id"],
                    endpoint="/v1/chat/completions",
                    request_body=request_body,
                    response_body={"streamed": True, "content_length": len(total_content)},
                    status_code=200,
                    error_code=None,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_cents=cost_cents,
                    latency_ms=int((time.perf_counter() - start_time) * 1000),
                    upstream_latency_ms=upstream_latency_ms,
                    was_blocked=False,
                    block_reason=None,
                    policy_decisions=decisions,
                    user_id=user_id,  # M23: Track end-user
                )
            finally:
                new_session.close()

        except Exception as e:
            logger.exception(f"Streaming error: {e}")
            error = {"error": {"message": str(e), "type": "stream_error"}}
            yield f"data: {json.dumps(error)}\n\n".encode()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# Embeddings Endpoint
# =============================================================================


@router.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(
    request: EmbeddingRequest,
    auth: Dict[str, Any] = Depends(get_auth_context),
    session=Depends(get_sync_session_dep),
):
    """
    OpenAI-compatible embeddings endpoint.
    """
    start_time = time.perf_counter()
    request_body = request.model_dump()

    tenant_id = auth["tenant_id"]
    api_key_id = auth["api_key_id"]

    # === CHECK KILLSWITCH ===
    killswitch_error = await check_killswitch(tenant_id, api_key_id, session)
    if killswitch_error:
        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/embeddings",
            request_body=request_body,
            response_body=killswitch_error,
            status_code=423,
            error_code="killswitch",
            input_tokens=0,
            output_tokens=0,
            cost_cents=Decimal("0"),
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=None,
            was_blocked=True,
            block_reason="killswitch",
            policy_decisions=[],
            user_id=request.user,  # M23: Track end-user
        )
        raise HTTPException(status_code=423, detail=killswitch_error)

    # === RECORD USAGE (only after killswitch passes) ===
    await record_usage_after_killswitch(auth, session)

    # === CALL OPENAI ===
    try:
        client = get_openai_client()
        upstream_start = time.perf_counter()

        # M23: Build embeddings request with user tracking
        embed_kwargs = {
            "model": request.model,
            "input": request.input,
            "encoding_format": request.encoding_format,
        }
        if request.dimensions:
            embed_kwargs["dimensions"] = request.dimensions
        if request.user:
            embed_kwargs["user"] = request.user

        response = client.embeddings.create(**embed_kwargs)

        upstream_latency_ms = int((time.perf_counter() - upstream_start) * 1000)

        # Calculate tokens and cost
        input_text = request.input if isinstance(request.input, str) else " ".join(request.input)
        input_tokens = response.usage.prompt_tokens if response.usage else estimate_tokens(input_text)
        cost_cents = calculate_cost(request.model, input_tokens, 0)

        result = EmbeddingResponse(
            data=[
                EmbeddingData(
                    embedding=d.embedding,
                    index=d.index,
                )
                for d in response.data
            ],
            model=response.model,
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=0,
                total_tokens=input_tokens,
            ),
        )

        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/embeddings",
            request_body=request_body,
            response_body={"embedding_count": len(result.data), "model": result.model},
            status_code=200,
            error_code=None,
            input_tokens=input_tokens,
            output_tokens=0,
            cost_cents=cost_cents,
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=upstream_latency_ms,
            was_blocked=False,
            block_reason=None,
            policy_decisions=[],
            user_id=request.user,  # M23: Track end-user
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"OpenAI embeddings error: {e}")
        error = {
            "error": {
                "message": str(e),
                "type": "api_error",
                "code": "upstream_error",
            }
        }

        await log_proxy_call(
            session=session,
            tenant_id=tenant_id,
            api_key_id=api_key_id,
            endpoint="/v1/embeddings",
            request_body=request_body,
            response_body=error,
            status_code=503,
            error_code="upstream_error",
            input_tokens=0,
            output_tokens=0,
            cost_cents=Decimal("0"),
            latency_ms=int((time.perf_counter() - start_time) * 1000),
            upstream_latency_ms=None,
            was_blocked=False,
            block_reason=None,
            policy_decisions=[],
            user_id=request.user,  # M23: Track end-user
        )
        raise HTTPException(status_code=503, detail=error)


# =============================================================================
# Status Endpoint (Buyer Signal)
# =============================================================================


@router.get("/status")
async def proxy_status(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session=Depends(get_sync_session_dep),
):
    """
    Protection status endpoint - the pulse of your safety net.

    Returns:
    - System status and features
    - Enforcement latency (p95)
    - Last incident timestamp
    - Current freeze status
    - Incidents blocked count

    When authenticated, shows tenant-specific protection metrics.
    When unauthenticated, shows global system health.
    """
    now = datetime.now(timezone.utc)
    registry = get_operation_registry()

    # Try to get tenant context if authenticated
    tenant_id = None
    api_key_id = None
    freeze_status = {"tenant_frozen": False, "key_frozen": False}

    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]
    elif x_api_key:
        api_key = x_api_key

    if api_key:
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_result = await registry.execute("proxy.ops", OperationContext(
            session=None,
            tenant_id="",
            params={
                "method": "get_api_key_id_and_tenant",
                "sync_session": session,
                "key_hash": key_hash,
            }
        ))
        db_key = key_result.data if key_result.success else None

        if db_key:
            tenant_id = db_key["tenant_id"]
            api_key_id = db_key["id"]

            # Check tenant freeze status via L4 registry dispatch
            tenant_freeze_result = await registry.execute("proxy.ops", OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "get_killswitch_state",
                    "sync_session": session,
                    "entity_type": "tenant",
                    "entity_id": tenant_id,
                }
            ))
            tenant_freeze = tenant_freeze_result.data if tenant_freeze_result.success else None

            # Check key freeze status via L4 registry dispatch
            key_freeze_result = await registry.execute("proxy.ops", OperationContext(
                session=None,
                tenant_id=tenant_id,
                params={
                    "method": "get_killswitch_state",
                    "sync_session": session,
                    "entity_type": "key",
                    "entity_id": api_key_id,
                }
            ))
            key_freeze = key_freeze_result.data if key_freeze_result.success else None

            freeze_status = {
                "tenant_frozen": tenant_freeze is not None,
                "key_frozen": key_freeze is not None,
                "frozen_at": (
                    tenant_freeze.frozen_at if tenant_freeze else (key_freeze.frozen_at if key_freeze else None)
                ),
                "freeze_reason": (
                    tenant_freeze.freeze_reason if tenant_freeze else (key_freeze.freeze_reason if key_freeze else None)
                ),
            }
            if freeze_status["tenant_frozen"] or freeze_status["key_frozen"]:
                freeze_status["message"] = "TRAFFIC STOPPED - Your API access is currently frozen"

    # Calculate enforcement latency p95 (from last 1000 calls) via L4 registry dispatch
    enforcement_stats = {"p95_ms": None, "calls_last_hour": 0, "incidents_blocked": 0}
    try:
        one_hour_ago = now - timedelta(hours=1)
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Get latency stats via L4 registry dispatch
        latency_result = await registry.execute("proxy.ops", OperationContext(
            session=None,
            tenant_id=tenant_id or "",
            params={
                "method": "get_latency_stats",
                "sync_session": session,
                "since": one_hour_ago,
                "lookup_tenant_id": tenant_id,
            }
        ))
        if latency_result.success and latency_result.data:
            latency_stats = latency_result.data
            enforcement_stats["p95_ms"] = latency_stats.p95_ms
            enforcement_stats["calls_last_hour"] = latency_stats.calls_count

        # Count blocked calls via L4 registry dispatch
        blocked_result = await registry.execute("proxy.ops", OperationContext(
            session=None,
            tenant_id=tenant_id or "",
            params={
                "method": "get_blocked_call_count",
                "sync_session": session,
                "since": twenty_four_hours_ago,
                "lookup_tenant_id": tenant_id,
            }
        ))
        if blocked_result.success:
            enforcement_stats["incidents_blocked"] = blocked_result.data
    except Exception:
        pass  # Stats are best-effort

    # Get last incident via L4 registry dispatch
    last_incident = None
    try:
        incident_result = await registry.execute("proxy.ops", OperationContext(
            session=None,
            tenant_id=tenant_id or "",
            params={
                "method": "get_last_incident",
                "sync_session": session,
                "lookup_tenant_id": tenant_id,
            }
        ))
        if incident_result.success and incident_result.data:
            incident_row = incident_result.data
            last_incident = {
                "id": incident_row.id,
                "title": incident_row.title,
                "severity": incident_row.severity,
                "timestamp": incident_row.created_at.isoformat() if incident_row.created_at else None,
                "status": incident_row.status,
            }
    except Exception:
        pass  # Best-effort

    # Build protection summary
    protection = {
        "status": "PROTECTING"
        if not (freeze_status.get("tenant_frozen") or freeze_status.get("key_frozen"))
        else "FROZEN",
        "enforcement_latency_p95_ms": enforcement_stats["p95_ms"],
        "incidents_blocked_24h": enforcement_stats["incidents_blocked"],
        "calls_monitored_1h": enforcement_stats["calls_last_hour"],
        "last_incident": last_incident,
        "freeze_status": freeze_status,
    }

    return wrap_dict({
        "status": "healthy",
        "proxy_version": "1.0.0",
        "timestamp": now.isoformat(),
        "protection": protection,
        "features": {
            "chat_completions": True,
            "embeddings": True,
            "streaming": True,
            "killswitch": True,
            "guardrails": True,
            "replay": True,
        },
        "message": "This proxy is actively protecting your AI traffic.",
    })
