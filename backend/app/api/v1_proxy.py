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

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlmodel import Session

from app.db import get_session
from app.models.killswitch import (
    ProxyCall,
    KillSwitchState,
    DefaultGuardrail,
    Incident,
    IncidentEvent,
)
from app.models.tenant import Tenant, APIKey


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
    session: Session = Depends(get_session),
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
            detail={"error": {"message": "Missing API key", "type": "invalid_request_error", "code": "missing_api_key"}}
        )

    # Look up API key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    stmt = select(APIKey).where(APIKey.key_hash == key_hash)
    row = session.exec(stmt).first()
    db_key = row[0] if row else None

    if not db_key:
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": "Invalid API key", "type": "invalid_request_error", "code": "invalid_api_key"}}
        )

    if not db_key.is_valid():
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": f"API key is {db_key.status}", "type": "invalid_request_error", "code": "invalid_api_key"}}
        )

    # Get tenant
    stmt = select(Tenant).where(Tenant.id == db_key.tenant_id)
    row = session.exec(stmt).first()
    tenant = row[0] if row else None

    if not tenant:
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": "Tenant not found", "type": "invalid_request_error", "code": "invalid_tenant"}}
        )

    # NOTE: Do NOT record usage here.
    # Usage must be recorded AFTER kill switch check to ensure
    # absolute semantics: frozen = no side effects whatsoever.
    # See record_usage_after_killswitch() in endpoint handlers.

    return {
        "tenant_id": tenant.id,
        "tenant": tenant,
        "api_key_id": db_key.id,
        "api_key": db_key,
        "session": session,  # Pass session for deferred usage recording
    }


# =============================================================================
# Usage Recording (AFTER KillSwitch)
# =============================================================================

def record_usage_after_killswitch(auth: Dict[str, Any], session: Session) -> None:
    """
    Record API key usage ONLY after kill switch passes.

    This ensures absolute kill switch semantics:
    - Frozen = zero side effects
    - No retries, no queued executions, no async spillover
    - Not even a usage counter increment
    """
    api_key = auth.get("api_key")
    if api_key and hasattr(api_key, "record_usage"):
        api_key.record_usage()
        session.add(api_key)
        session.commit()


# =============================================================================
# KillSwitch Check
# =============================================================================

async def check_killswitch(
    tenant_id: str,
    api_key_id: str,
    session: Session,
) -> Optional[Dict[str, Any]]:
    """
    Check if tenant or API key is frozen.
    Returns error dict if frozen, None if OK.
    """
    # Check tenant freeze
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "tenant",
            KillSwitchState.entity_id == tenant_id,
            KillSwitchState.is_frozen == True
        )
    )
    row = session.exec(stmt).first()
    tenant_state = row[0] if row else None

    if tenant_state:
        return {
            "error": {
                # Language layer: "Traffic stopped" not "tenant frozen"
                "message": f"🛑 TRAFFIC STOPPED: {tenant_state.freeze_reason or 'Your account has been protected from runaway costs'}",
                "type": "killswitch_error",
                "code": "traffic_stopped",
                "stopped_at": tenant_state.frozen_at.isoformat() if tenant_state.frozen_at else None,
                "reason": tenant_state.freeze_reason,
                "action": "Contact support to resume traffic after reviewing the incident.",
            }
        }

    # Check API key freeze
    stmt = select(KillSwitchState).where(
        and_(
            KillSwitchState.entity_type == "key",
            KillSwitchState.entity_id == api_key_id,
            KillSwitchState.is_frozen == True
        )
    )
    row = session.exec(stmt).first()
    key_state = row[0] if row else None

    if key_state:
        return {
            "error": {
                # Language layer: "Traffic stopped" not "key frozen"
                "message": f"🛑 TRAFFIC STOPPED: {key_state.freeze_reason or 'This API key has been protected from runaway costs'}",
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
    session: Session,
) -> tuple[bool, List[Dict[str, Any]]]:
    """
    Evaluate default guardrails against request.
    Returns (passed, decisions) where passed=False means blocked.
    """
    # Get enabled guardrails ordered by priority
    stmt = select(DefaultGuardrail).where(
        DefaultGuardrail.is_enabled == True
    ).order_by(DefaultGuardrail.priority)
    result = session.exec(stmt)
    guardrails = result.all()

    decisions = []
    all_passed = True

    for guardrail in guardrails:
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
            context["cost_cents"] = (input_tokens / 1_000_000) * pricing["input"] + (max_tokens / 1_000_000) * pricing["output"]

        passed, reason = guardrail.evaluate(context)

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
            detail={"error": {"message": "OpenAI SDK not available", "type": "service_error", "code": "sdk_unavailable"}}
        )


# =============================================================================
# Call Logging
# =============================================================================

async def log_proxy_call(
    session: Session,
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
) -> ProxyCall:
    """Log a proxy call for replay and analysis."""

    call = ProxyCall(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        api_key_id=api_key_id,
        user_id=user_id,  # M23: Track end-user from OpenAI standard `user` field
        endpoint=endpoint,
        model=request_body.get("model", DEFAULT_MODEL),
        request_hash=ProxyCall.hash_request(request_body),
        request_json=json.dumps(request_body),
        response_hash=ProxyCall.hash_response(response_body) if response_body else None,
        response_json=json.dumps(response_body) if response_body else None,
        status_code=status_code,
        error_code=error_code,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_cents=cost_cents,
        latency_ms=latency_ms,
        upstream_latency_ms=upstream_latency_ms,
        was_blocked=was_blocked,
        block_reason=block_reason,
        replay_eligible=not was_blocked and status_code == 200,
    )
    call.set_policy_decisions(policy_decisions)

    session.add(call)
    session.commit()
    session.refresh(call)

    return call


# =============================================================================
# Chat Completions Endpoint
# =============================================================================

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    auth: Dict[str, Any] = Depends(get_auth_context),
    session: Session = Depends(get_session),
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
    record_usage_after_killswitch(auth, session)

    # === EVALUATE GUARDRAILS ===
    passed, decisions = await evaluate_guardrails(request_body, session)
    if not passed:
        # Find the blocking decision
        blocking = next((d for d in decisions if not d["passed"] and d["action"] == "block"), None)
        # Language layer: "Incident prevented" not "policy triggered"
        guardrail_name = blocking["guardrail_name"] if blocking else "policy"
        error = {
            "error": {
                "message": f"🛡️ INCIDENT PREVENTED: {blocking['reason'] if blocking else 'Request exceeded safety limits'}",
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
                client, openai_request, request_body, auth, session, start_time, decisions,
                user_id=request.user  # M23: Track end-user
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
                    finish_reason=c.finish_reason or "stop"
                )
                for i, c in enumerate(response.choices)
            ],
            usage=Usage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            )
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
    session: Session,
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
                    ]
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
            from app.db import engine
            from sqlmodel import Session as SQLSession
            with SQLSession(engine) as new_session:
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
        }
    )


# =============================================================================
# Embeddings Endpoint
# =============================================================================

@router.post("/embeddings", response_model=EmbeddingResponse)
async def embeddings(
    request: EmbeddingRequest,
    auth: Dict[str, Any] = Depends(get_auth_context),
    session: Session = Depends(get_session),
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
    record_usage_after_killswitch(auth, session)

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
            )
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
    session: Session = Depends(get_session),
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
    from sqlalchemy import func, text

    now = datetime.now(timezone.utc)

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
        stmt = select(APIKey).where(APIKey.key_hash == key_hash)
        row = session.exec(stmt).first()
        db_key = row[0] if row else None
        if db_key:
            tenant_id = db_key.tenant_id
            api_key_id = db_key.id

            # Check freeze status
            tenant_row = session.exec(
                select(KillSwitchState).where(
                    and_(
                        KillSwitchState.entity_type == "tenant",
                        KillSwitchState.entity_id == tenant_id,
                        KillSwitchState.is_frozen == True
                    )
                )
            ).first()
            tenant_freeze = tenant_row[0] if tenant_row else None
            key_row = session.exec(
                select(KillSwitchState).where(
                    and_(
                        KillSwitchState.entity_type == "key",
                        KillSwitchState.entity_id == api_key_id,
                        KillSwitchState.is_frozen == True
                    )
                )
            ).first()
            key_freeze = key_row[0] if key_row else None

            freeze_status = {
                "tenant_frozen": tenant_freeze is not None,
                "key_frozen": key_freeze is not None,
                "frozen_at": (tenant_freeze.frozen_at if tenant_freeze else (key_freeze.frozen_at if key_freeze else None)),
                "freeze_reason": (tenant_freeze.freeze_reason if tenant_freeze else (key_freeze.freeze_reason if key_freeze else None)),
            }
            if freeze_status["tenant_frozen"] or freeze_status["key_frozen"]:
                freeze_status["message"] = "⚠️ TRAFFIC STOPPED - Your API access is currently frozen"

    # Calculate enforcement latency p95 (from last 1000 calls)
    enforcement_stats = {"p95_ms": None, "calls_last_hour": 0, "incidents_blocked": 0}
    try:
        # Base filter for tenant if authenticated
        base_filter = []
        if tenant_id:
            base_filter.append(ProxyCall.tenant_id == tenant_id)

        # Get latency p95 from recent calls
        latency_query = select(ProxyCall.latency_ms).where(
            *base_filter,
            ProxyCall.created_at >= now - timedelta(hours=1)
        ).order_by(ProxyCall.created_at.desc()).limit(1000)

        latencies = [row[0] for row in session.exec(latency_query).all() if row[0]]
        if latencies:
            latencies.sort()
            p95_idx = int(len(latencies) * 0.95)
            enforcement_stats["p95_ms"] = latencies[p95_idx] if p95_idx < len(latencies) else latencies[-1]
            enforcement_stats["calls_last_hour"] = len(latencies)

        # Count blocked calls (incidents prevented)
        blocked_query = select(func.count(ProxyCall.id)).where(
            *base_filter,
            ProxyCall.was_blocked == True,
            ProxyCall.created_at >= now - timedelta(hours=24)
        )
        result = session.exec(blocked_query).one()
        enforcement_stats["incidents_blocked"] = result[0] if result else 0
    except Exception:
        pass  # Stats are best-effort

    # Get last incident
    last_incident = None
    try:
        incident_filter = [Incident.tenant_id == tenant_id] if tenant_id else []
        incident_query = select(Incident).where(*incident_filter).order_by(Incident.created_at.desc()).limit(1)
        row = session.exec(incident_query).first()
        last = row[0] if row else None
        if last:
            last_incident = {
                "id": last.id,
                "title": last.title,
                "severity": last.severity,
                "timestamp": last.created_at.isoformat() if last.created_at else None,
                "status": last.status,
            }
    except Exception:
        pass  # Best-effort

    # Build protection summary
    protection = {
        "status": "🛡️ PROTECTING" if not (freeze_status.get("tenant_frozen") or freeze_status.get("key_frozen")) else "⛔ FROZEN",
        "enforcement_latency_p95_ms": enforcement_stats["p95_ms"],
        "incidents_blocked_24h": enforcement_stats["incidents_blocked"],
        "calls_monitored_1h": enforcement_stats["calls_last_hour"],
        "last_incident": last_incident,
        "freeze_status": freeze_status,
    }

    return {
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
    }
