# Voyage Embed Skill (M11)
# Generate embeddings using Voyage AI API

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from ..schemas.skill import VoyageEmbedInput, VoyageEmbedOutput
from .registry import skill

logger = logging.getLogger("nova.skills.voyage_embed")

# Voyage AI configuration
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
DEFAULT_MODEL = "voyage-3"
DEFAULT_TIMEOUT = 60.0


class VoyageEmbedConfig(BaseModel):
    """Configuration schema for voyage_embed skill."""

    allow_external: bool = True
    api_key: Optional[str] = None
    default_model: str = DEFAULT_MODEL
    timeout: float = DEFAULT_TIMEOUT


# Model dimensions
MODEL_DIMENSIONS = {
    "voyage-3": 1024,
    "voyage-3-lite": 512,
    "voyage-code-3": 1024,
    "voyage-finance-2": 1024,
}


@skill(
    "voyage_embed",
    input_schema=VoyageEmbedInput,
    output_schema=VoyageEmbedOutput,
    tags=["embedding", "vector", "voyage", "ai", "nlp"],
    default_config={"allow_external": True, "default_model": DEFAULT_MODEL, "timeout": DEFAULT_TIMEOUT},
)
class VoyageEmbedSkill:
    """Voyage AI embedding skill.

    Features:
    - Generate embeddings using Voyage AI models
    - Support for single text or batch input
    - Query vs document optimization via input_type
    - Multiple model support (voyage-3, voyage-3-lite, voyage-code-3)
    - External call control (can stub for testing)

    Environment Variables:
    - VOYAGE_API_KEY: Voyage AI API key

    Models:
    - voyage-3: General purpose (1024 dims)
    - voyage-3-lite: Lightweight (512 dims)
    - voyage-code-3: Code embeddings (1024 dims)
    - voyage-finance-2: Finance domain (1024 dims)

    Usage in workflow:
        {
            "skill": "voyage_embed",
            "params": {
                "input": "What is the capital of France?",
                "model": "voyage-3",
                "input_type": "query"
            }
        }
    """

    VERSION = "1.0.0"
    DESCRIPTION = "Generate embeddings using Voyage AI for semantic search and retrieval"

    def __init__(
        self,
        *,
        allow_external: bool = True,
        api_key: Optional[str] = None,
        default_model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.allow_external = allow_external
        self.api_key = api_key or VOYAGE_API_KEY
        self.default_model = default_model
        self.timeout = timeout

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute embedding generation.

        Args:
            params: Dict with input, model, input_type, truncation

        Returns:
            Structured result with embeddings, model, usage, dimensions
        """
        input_data = params.get("input", "")
        model = params.get("model", self.default_model)
        input_type = params.get("input_type")
        truncation = params.get("truncation", True)

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        # Normalize input to list
        if isinstance(input_data, str):
            input_list = [input_data]
        else:
            input_list = list(input_data)

        logger.info(
            "voyage_embed_execution_start",
            extra={
                "skill": "voyage_embed",
                "model": model,
                "input_count": len(input_list),
                "input_type": input_type,
            },
        )

        # Validate input
        if not input_list or (len(input_list) == 1 and not input_list[0]):
            duration = time.time() - start_time
            return {
                "skill": "voyage_embed",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "validation_error",
                    "message": "Input text is required",
                    "embeddings": [],
                    "model": model,
                    "usage": {"total_tokens": 0},
                    "dimensions": 0,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check stub mode
        if not self.allow_external:
            duration = time.time() - start_time
            dimensions = MODEL_DIMENSIONS.get(model, 1024)

            # Generate deterministic stub embeddings
            stub_embeddings = []
            for i, text in enumerate(input_list):
                # Use hash of text for deterministic stub
                import hashlib

                hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                stub_embedding = [(hash_val + j) % 1000 / 1000.0 for j in range(dimensions)]
                stub_embeddings.append(stub_embedding)

            logger.info("voyage_embed_stubbed", extra={"skill": "voyage_embed", "reason": "external_calls_disabled"})
            return {
                "skill": "voyage_embed",
                "skill_version": self.VERSION,
                "result": {
                    "status": "stubbed",
                    "embeddings": stub_embeddings,
                    "model": model,
                    "usage": {"total_tokens": sum(len(t.split()) for t in input_list)},
                    "dimensions": dimensions,
                },
                "duration": round(duration, 3),
                "side_effects": {"voyage_stubbed": True},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check API key
        if not self.api_key:
            duration = time.time() - start_time
            logger.error(
                "voyage_embed_failed", extra={"skill": "voyage_embed", "error": "VOYAGE_API_KEY not configured"}
            )
            return {
                "skill": "voyage_embed",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "configuration_error",
                    "message": "VOYAGE_API_KEY not configured",
                    "embeddings": [],
                    "model": model,
                    "usage": {"total_tokens": 0},
                    "dimensions": 0,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Build request payload
        payload: Dict[str, Any] = {
            "input": input_list,
            "model": model,
            "truncation": truncation,
        }

        if input_type:
            payload["input_type"] = input_type

        # Call Voyage AI API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    VOYAGE_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

                duration = time.time() - start_time
                completed_at = datetime.now(timezone.utc)

                if response.status_code == 200:
                    data = response.json()

                    # Extract embeddings
                    embeddings = [item["embedding"] for item in data.get("data", [])]
                    usage = data.get("usage", {"total_tokens": 0})
                    actual_model = data.get("model", model)
                    dimensions = len(embeddings[0]) if embeddings else 0

                    logger.info(
                        "voyage_embed_execution_end",
                        extra={
                            "skill": "voyage_embed",
                            "model": actual_model,
                            "input_count": len(input_list),
                            "total_tokens": usage.get("total_tokens", 0),
                            "duration": round(duration, 3),
                        },
                    )

                    return {
                        "skill": "voyage_embed",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "ok",
                            "embeddings": embeddings,
                            "model": actual_model,
                            "usage": usage,
                            "dimensions": dimensions,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {
                            "voyage_api_call": True,
                            "total_tokens": usage.get("total_tokens", 0),
                        },
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

                else:
                    error_body = response.text[:500]
                    logger.warning(
                        "voyage_embed_failed",
                        extra={
                            "skill": "voyage_embed",
                            "http_status": response.status_code,
                            "error": error_body,
                        },
                    )

                    return {
                        "skill": "voyage_embed",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "error",
                            "error": "api_error",
                            "message": f"Voyage API error ({response.status_code}): {error_body}",
                            "embeddings": [],
                            "model": model,
                            "usage": {"total_tokens": 0},
                            "dimensions": 0,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.warning("voyage_embed_timeout", extra={"skill": "voyage_embed", "timeout": self.timeout})
            return {
                "skill": "voyage_embed",
                "skill_version": self.VERSION,
                "result": {
                    "status": "timeout",
                    "error": "timeout",
                    "message": f"Request timed out after {self.timeout}s",
                    "embeddings": [],
                    "model": model,
                    "usage": {"total_tokens": 0},
                    "dimensions": 0,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except httpx.RequestError as e:
            duration = time.time() - start_time
            logger.error("voyage_embed_failed", extra={"skill": "voyage_embed", "error": str(e)[:200]})
            return {
                "skill": "voyage_embed",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "network_error",
                    "message": f"Network error: {str(e)[:200]}",
                    "embeddings": [],
                    "model": model,
                    "usage": {"total_tokens": 0},
                    "dimensions": 0,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        return VoyageEmbedInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        return VoyageEmbedOutput
