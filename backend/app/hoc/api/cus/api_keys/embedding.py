# Layer: L2 — Product APIs
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Embedding API endpoints (quota management, embedding operations)
# Callers: SDK, Console UI
# Allowed Imports: L3, L4, L5, L6
# Forbidden Imports: L1
# Reference: PIN-047, PIN-082

# Embedding API Endpoints
"""
API endpoints for embedding operations and quota management.
PIN-047: P2 - Quota Status API Endpoint
PIN-082: IAEC v3.0 - Instruction-Aware Embedding Composer
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import verify_api_key
from ..schemas.response import wrap_dict
from ..memory.embedding_metrics import (
    EMBEDDING_DAILY_QUOTA,
    VECTOR_SEARCH_ENABLED,
    VECTOR_SEARCH_FALLBACK,
    get_embedding_quota_status,
)

router = APIRouter(prefix="/embedding", tags=["embedding"])


class EmbeddingQuotaResponse(BaseModel):
    """Response schema for embedding quota status."""

    daily_quota: int
    current_count: int
    remaining: int
    exceeded: bool
    reset_at: str  # ISO format timestamp of next reset (midnight UTC)
    vector_search_enabled: bool
    fallback_enabled: bool


class EmbeddingConfigResponse(BaseModel):
    """Response schema for embedding configuration."""

    provider: str
    model: str
    backup_provider: Optional[str]
    backup_model: Optional[str]
    dimensions: int
    daily_quota: int
    vector_search_enabled: bool
    fallback_to_keyword: bool
    provider_fallback_enabled: bool


@router.get("/quota", response_model=EmbeddingQuotaResponse)
async def get_embedding_quota(
    _api_key: str = Depends(verify_api_key),
) -> EmbeddingQuotaResponse:
    """
    Get current embedding quota status.

    Returns:
        - daily_quota: Maximum embeddings per day (0 = unlimited)
        - current_count: Number of embeddings used today
        - remaining: Embeddings remaining (-1 if unlimited)
        - exceeded: Whether quota has been exceeded
        - reset_at: When quota resets (midnight UTC)
        - vector_search_enabled: Whether vector search is active
        - fallback_enabled: Whether keyword fallback is enabled
    """
    status = get_embedding_quota_status()

    # Calculate next reset time (midnight UTC tomorrow)
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now.hour >= 0:
        from datetime import timedelta

        tomorrow = tomorrow + timedelta(days=1)

    return EmbeddingQuotaResponse(
        daily_quota=status["daily_quota"],
        current_count=status["current_count"],
        remaining=status["remaining"],
        exceeded=status["exceeded"],
        reset_at=tomorrow.isoformat(),
        vector_search_enabled=VECTOR_SEARCH_ENABLED,
        fallback_enabled=VECTOR_SEARCH_FALLBACK,
    )


@router.get("/config", response_model=EmbeddingConfigResponse)
async def get_embedding_config(
    _api_key: str = Depends(verify_api_key),
) -> EmbeddingConfigResponse:
    """
    Get embedding configuration.

    Returns current embedding provider settings including backup provider.
    """
    import os

    provider = os.getenv("EMBEDDING_PROVIDER", "openai")
    backup_provider = os.getenv("EMBEDDING_BACKUP_PROVIDER", "voyage")
    fallback_enabled = os.getenv("EMBEDDING_FALLBACK_ENABLED", "true").lower() == "true"

    # Get model for each provider
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    backup_model = os.getenv("VOYAGE_MODEL", "voyage-3-lite") if backup_provider == "voyage" else None

    return EmbeddingConfigResponse(
        provider=provider,
        model=model,
        backup_provider=backup_provider if fallback_enabled else None,
        backup_model=backup_model if fallback_enabled else None,
        dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
        daily_quota=EMBEDDING_DAILY_QUOTA,
        vector_search_enabled=VECTOR_SEARCH_ENABLED,
        fallback_to_keyword=VECTOR_SEARCH_FALLBACK,
        provider_fallback_enabled=fallback_enabled,
    )


@router.get("/health")
async def embedding_health() -> dict:
    """
    Quick health check for embedding subsystem.

    No authentication required - used for monitoring.
    """
    status = get_embedding_quota_status()

    return wrap_dict({
        "status": "healthy" if not status["exceeded"] else "degraded",
        "reason": "quota_exceeded" if status["exceeded"] else None,
        "vector_search": VECTOR_SEARCH_ENABLED,
        "quota_remaining": status["remaining"],
    })


@router.get("/cache/stats")
async def embedding_cache_stats(
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Get embedding cache statistics.

    Returns cache configuration and entry count.
    """
    from ..memory.embedding_cache import get_embedding_cache

    cache = get_embedding_cache()
    return await cache.stats()


@router.delete("/cache")
async def clear_embedding_cache(
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Clear all embedding cache entries.

    Returns number of entries cleared.
    """
    from ..memory.embedding_cache import get_embedding_cache

    cache = get_embedding_cache()
    cleared = await cache.clear_all()
    return wrap_dict({"cleared": cleared})


# =============================================================================
# IAEC v3.0 - Instruction-Aware Embedding Composer
# =============================================================================


class IAECComposeRequest(BaseModel):
    """Request schema for IAEC composition (v3.0)."""

    instruction: str = "default"
    query: str
    context: Optional[str] = None
    mode: str = "weighted"  # "segmented", "weighted", or "hybrid"
    # Policy encoding (v3.0)
    policy_id: Optional[str] = None
    policy_version: int = 1
    policy_level: int = 0  # 0=global, 1=org, 2=team, 3=agent


class TemporalSignatureResponse(BaseModel):
    """Temporal signature for drift control."""

    epoch_hash: str
    model_family: str
    model_version: str
    iaec_version: str
    slot_structure_version: int


class PolicyEncodingResponse(BaseModel):
    """Policy slot encoding."""

    policy_id: Optional[str]
    policy_version: int
    hierarchy_level: int


class IAECComposeResponse(BaseModel):
    """Response schema for IAEC composition (v3.2)."""

    vector: list
    mode: str
    instruction: str
    weights: Optional[list] = None
    dimensions: int
    # Provenance tracking
    query_hash: Optional[str] = None
    instruction_hash: Optional[str] = None
    context_hash: Optional[str] = None
    provenance_hash: Optional[str] = None
    # Quality indicators
    mismatch_score: float = 0.0
    deep_mismatch_score: float = 0.0  # v3.0: embedding-based
    collapse_prevented: bool = False
    values_clamped: bool = False
    norm_coefficient: float = 1.0
    # v3.0: Temporal signature
    temporal_signature: Optional[TemporalSignatureResponse] = None
    # v3.0: Policy encoding
    policy_id: Optional[str] = None
    policy_encoding: Optional[PolicyEncodingResponse] = None
    # v3.0: Reversibility
    slot_basis_hash: Optional[str] = None
    integrity_verified: bool = False
    reconstruction_error: float = 0.0
    # Metadata
    created_at: Optional[str] = None
    iaec_version: str = "3.2.0"
    # v3.2: Whitening versioning for audit replay
    whitening_basis_id: Optional[str] = None
    whitening_version: Optional[str] = None


class IAECDecomposeRequest(BaseModel):
    """Request schema for IAEC decomposition."""

    vector: List[float]
    verify: bool = True


class IAECDecomposeResponse(BaseModel):
    """Response schema for IAEC decomposition (v3.0)."""

    instruction_slot: List[float]
    query_slot: List[float]
    context_slot: List[float]
    temporal_slot: List[float]
    policy_slot: List[float]
    is_valid: bool
    reconstruction_error: float
    temporal_compatible: bool
    source_mode: str


class IAECVerifyRequest(BaseModel):
    """Request for integrity verification."""

    vector: List[float]
    instruction: str
    query: str
    context: Optional[str] = None
    mode: str = "weighted"
    policy_id: Optional[str] = None


class IAECVerifyResponse(BaseModel):
    """Response for integrity verification."""

    passed: bool
    reconstruction_error: float
    temporal_match: bool
    policy_match: bool
    slot_norms_valid: bool
    provenance_match: bool
    details: Dict[str, Any]


@router.post("/compose", response_model=IAECComposeResponse)
async def compose_embedding(
    request: IAECComposeRequest,
    _api_key: str = Depends(verify_api_key),
) -> IAECComposeResponse:
    """
    Compose an instruction-aware embedding using IAEC v3.0.

    IAEC creates structured composite embeddings with 4 slots:
    - Instruction: what kind of task (summarize, extract, analyze, etc.)
    - Query: what the user wants
    - Context: what the system knows
    - Temporal + Policy: version/governance metadata (v3.0)

    Modes:
    - "segmented": Best for routing - splits vector into regions
    - "weighted": Best for search - uses learned weights per instruction
    - "hybrid": Returns weighted, stores segmented metadata

    v3.0 Features:
    - Reversible decomposition (weighted mode)
    - Temporal signature for drift control
    - Deep embedding-based mismatch detection
    - Policy slot encoding for governance
    - Slot integrity verification

    Supported instructions: summarize, extract, analyze, rewrite, qa,
    compare, classify, generate, route, default
    """
    from ..memory.iaec import get_iaec

    iaec = await get_iaec()
    result = await iaec.compose(
        instruction=request.instruction,
        query=request.query,
        context=request.context,
        mode=request.mode,
        policy_id=request.policy_id,
        policy_version=request.policy_version,
        policy_level=request.policy_level,
    )

    # Build temporal signature response
    temporal_sig = None
    if result.temporal_signature:
        temporal_sig = TemporalSignatureResponse(
            epoch_hash=result.temporal_signature.epoch_hash,
            model_family=result.temporal_signature.model_family,
            model_version=result.temporal_signature.model_version,
            iaec_version=result.temporal_signature.iaec_version,
            slot_structure_version=result.temporal_signature.slot_structure_version,
        )

    # Build policy encoding response
    policy_enc = None
    if result.policy_encoding:
        policy_enc = PolicyEncodingResponse(
            policy_id=result.policy_encoding.policy_id,
            policy_version=result.policy_encoding.policy_version,
            hierarchy_level=result.policy_encoding.hierarchy_level,
        )

    return IAECComposeResponse(
        vector=result.to_list(),
        mode=result.mode,
        instruction=result.instruction,
        weights=list(result.weights) if result.weights else None,
        dimensions=result.dimensions,
        # Provenance
        query_hash=result.query_hash,
        instruction_hash=result.instruction_hash,
        context_hash=result.context_hash,
        provenance_hash=result.provenance_hash,
        # Quality indicators
        mismatch_score=result.mismatch_score,
        deep_mismatch_score=result.deep_mismatch_score,
        collapse_prevented=result.collapse_prevented,
        values_clamped=result.values_clamped,
        norm_coefficient=result.norm_coefficient,
        # v3.0 features
        temporal_signature=temporal_sig,
        policy_id=result.policy_id,
        policy_encoding=policy_enc,
        slot_basis_hash=result.slot_basis_hash,
        integrity_verified=result.integrity_verified,
        reconstruction_error=result.reconstruction_error,
        # Metadata
        created_at=result.created_at,
        iaec_version=result.iaec_version,
        # v3.2: Whitening versioning for audit replay
        whitening_basis_id=result.whitening_basis_id,
        whitening_version=result.whitening_version,
    )


@router.post("/decompose", response_model=IAECDecomposeResponse)
async def decompose_embedding(
    request: IAECDecomposeRequest,
    _api_key: str = Depends(verify_api_key),
) -> IAECDecomposeResponse:
    """
    Decompose an IAEC embedding back into its constituent slots (v3.0).

    For segmented mode embeddings: Direct extraction from dimensional regions
    For raw vectors: Assumes segmented layout

    Note: For full reversibility of weighted mode embeddings, the original
    CompositeEmbedding with slot_basis must be preserved.

    Returns all 5 slots:
    - instruction_slot: Task type encoding
    - query_slot: User intent encoding
    - context_slot: System context encoding
    - temporal_slot: Version/epoch signature (32 dims)
    - policy_slot: Governance encoding (32 dims)
    """
    import numpy as np

    from ..memory.iaec import get_iaec

    iaec = await get_iaec()
    vec = np.array(request.vector, dtype=np.float32)
    result = iaec.decompose(vec, verify=request.verify)

    return IAECDecomposeResponse(
        instruction_slot=result.instruction_slot.tolist(),
        query_slot=result.query_slot.tolist(),
        context_slot=result.context_slot.tolist(),
        temporal_slot=result.temporal_slot.tolist(),
        policy_slot=result.policy_slot.tolist(),
        is_valid=result.is_valid,
        reconstruction_error=result.reconstruction_error,
        temporal_compatible=result.temporal_compatible,
        source_mode=result.source_mode,
    )


@router.get("/iaec/instructions")
async def get_iaec_instructions(
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Get available IAEC instruction types and their weights.
    """
    from ..memory.iaec import INSTRUCTION_PROMPTS, INSTRUCTION_WEIGHTS

    return wrap_dict({
        "instructions": [
            {
                "type": instr,
                "prompt": INSTRUCTION_PROMPTS.get(instr, ""),
                "weights": {
                    "instruction": w[0],
                    "query": w[1],
                    "context": w[2],
                },
            }
            for instr, w in INSTRUCTION_WEIGHTS.items()
        ]
    })


@router.get("/iaec/segment-info")
async def get_iaec_segment_info(
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Get IAEC v3.0 segmentation configuration.

    Returns slot layout, dimensions, and temporal signature info.
    """
    from ..memory.iaec import get_iaec

    iaec = await get_iaec()
    return iaec.get_segment_info()


@router.post("/iaec/check-mismatch")
async def check_mismatch(
    instruction: str,
    query: str,
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Check instruction-query semantic compatibility (v3.1).

    Uses both keyword-based and embedding-based detection.

    v3.1: Includes corrective_action with confidence for M18/M19 governance.

    Returns:
    - score: Keyword-based mismatch score (0-1)
    - deep_score: Embedding-based mismatch score (0-1)
    - suggested_instruction: Better instruction if mismatch detected
    - detection_method: "keyword", "embedding", or "none"
    - message: Human-readable guidance
    - corrective_action: Prescriptive action with confidence (v3.1)
    """
    from ..memory.iaec import check_instruction_query_match

    result = await check_instruction_query_match(instruction, query)

    response = {
        "instruction": result.instruction,
        "query": result.query,
        "score": result.score,
        "deep_score": result.deep_score,
        "suggested_instruction": result.suggested_instruction,
        "detection_method": result.detection_method,
        "message": result.message,
    }

    # v3.1: Include corrective action if available
    if result.corrective_action:
        response["corrective_action"] = result.corrective_action.to_dict()

    return wrap_dict(response)
