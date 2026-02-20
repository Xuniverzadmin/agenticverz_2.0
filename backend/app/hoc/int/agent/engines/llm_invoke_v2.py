# capability_id: CAP-008
# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: LLM Invoke Skill v2 (M3)
# llm_invoke_v2.py
"""
LLM Invoke Skill v2 (M3)

Invokes language models with:
- Adapter pattern for multiple providers
- Deterministic seeding support (when model supports it)
- Error contract enforcement
- Cost tracking and token counting

See: app/skills/contracts/llm_invoke.contract.yaml
See: app/specs/error_contract.md
"""

import hashlib
import json
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Path setup
_backend = Path(__file__).parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.hoc.int.worker.runtime.core import SkillDescriptor, StructuredOutcome

logger = logging.getLogger("nova.skills.llm_invoke_v2")


# =============================================================================
# Error Category Enum
# =============================================================================


class ErrorCategory(str, Enum):
    """Error categories from error_contract.md"""

    TRANSIENT = "TRANSIENT"
    RATE_LIMIT = "RATE_LIMIT"
    CLIENT_ERROR = "CLIENT_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    AUTH_FAIL = "AUTH_FAIL"
    VALIDATION = "VALIDATION"
    TIMEOUT = "TIMEOUT"
    PERMANENT = "PERMANENT"


# =============================================================================
# Error Mappings
# =============================================================================


@dataclass(frozen=True)
class ErrorMapping:
    """Mapping from error type to error info."""

    code: str
    category: ErrorCategory
    retryable: bool


LLM_ERROR_MAP: Dict[str, ErrorMapping] = {
    "rate_limited": ErrorMapping("ERR_LLM_RATE_LIMITED", ErrorCategory.RATE_LIMIT, True),
    "overloaded": ErrorMapping("ERR_LLM_OVERLOADED", ErrorCategory.TRANSIENT, True),
    "timeout": ErrorMapping("ERR_LLM_TIMEOUT", ErrorCategory.TIMEOUT, True),
    "invalid_prompt": ErrorMapping("ERR_LLM_INVALID_PROMPT", ErrorCategory.VALIDATION, False),
    "content_blocked": ErrorMapping("ERR_LLM_CONTENT_BLOCKED", ErrorCategory.PERMANENT, False),
    "auth_failed": ErrorMapping("ERR_LLM_AUTH_FAILED", ErrorCategory.AUTH_FAIL, False),
    "context_too_long": ErrorMapping("ERR_LLM_CONTEXT_TOO_LONG", ErrorCategory.VALIDATION, False),
    "invalid_model": ErrorMapping("ERR_LLM_INVALID_MODEL", ErrorCategory.VALIDATION, False),
}


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class Message:
    """Chat message."""

    role: str  # system, user, assistant
    content: str


@dataclass
class LLMConfig:
    """LLM invocation configuration."""

    model: Optional[str] = None
    temperature: float = 0.0
    max_tokens: int = 1024
    seed: Optional[int] = None
    system_prompt: Optional[str] = None
    stop_sequences: Optional[List[str]] = None
    timeout_ms: int = 60000


@dataclass
class LLMResponse:
    """LLM response."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    finish_reason: str  # end_turn, max_tokens, stop_sequence
    latency_ms: int
    seed: Optional[int] = None


# =============================================================================
# Cost Model
# =============================================================================

COST_PER_MTOK = {
    "claude-3-5-sonnet-20241022": {"input": 300, "output": 1500},
    "claude-sonnet-4-20250514": {"input": 300, "output": 1500},
    "claude-3-haiku-20240307": {"input": 25, "output": 125},
    "gpt-4o": {"input": 250, "output": 1000},
    "gpt-4o-mini": {"input": 15, "output": 60},
    "stub": {"input": 0, "output": 0},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in cents."""
    costs = COST_PER_MTOK.get(model, {"input": 100, "output": 500})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost


# =============================================================================
# Canonical JSON Utilities
# =============================================================================


def _canonical_json(obj: Any) -> str:
    """Produce canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content_hash(data: Any, length: int = 16) -> str:
    """Compute SHA256 hash of content."""
    if isinstance(data, bytes):
        content = data
    elif isinstance(data, str):
        content = data.encode("utf-8")
    else:
        content = _canonical_json(data).encode("utf-8")
    return hashlib.sha256(content).hexdigest()[:length]


def _generate_call_id(params: Dict[str, Any]) -> str:
    """Generate deterministic call ID from params."""
    return f"llm_{_content_hash(params, 12)}"


# =============================================================================
# Adapter Interface (Abstract Base Class)
# =============================================================================


class LLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.

    Implementations:
    - StubAdapter: Deterministic mock responses (for testing)
    - ClaudeAdapter: Anthropic Claude API
    - OpenAIAdapter: OpenAI API (future)
    """

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique adapter identifier."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this adapter."""
        ...

    @abstractmethod
    def supports_seeding(self) -> bool:
        """Whether this adapter supports deterministic seeding."""
        ...

    @abstractmethod
    async def invoke(
        self, prompt: Union[str, List[Message]], config: LLMConfig
    ) -> Union[LLMResponse, Tuple[str, str, bool]]:
        """
        Invoke the LLM.

        Args:
            prompt: Text prompt or list of messages
            config: LLM configuration

        Returns:
            LLMResponse on success, or (error_type, message, retryable) on error
        """
        ...

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: ~4 chars per token
        return len(text) // 4


# =============================================================================
# Stub Adapter (for testing)
# =============================================================================


class StubAdapter(LLMAdapter):
    """
    Stub adapter for deterministic testing.

    Returns predictable responses based on input hash.
    Supports seeding for fully deterministic outputs.
    """

    # Configurable responses for testing
    _mock_responses: Dict[str, Union[LLMResponse, Tuple[str, str, bool]]] = {}

    @property
    def adapter_id(self) -> str:
        return "stub"

    @property
    def default_model(self) -> str:
        return "stub"

    def supports_seeding(self) -> bool:
        return True

    @classmethod
    def set_response(cls, prompt_hash: str, response: Union[LLMResponse, Tuple[str, str, bool]]):
        """Set mock response for a prompt hash."""
        cls._mock_responses[prompt_hash] = response

    @classmethod
    def set_error(cls, prompt_hash: str, error_type: str, message: str = "Mock error"):
        """Set mock error for a prompt hash."""
        mapping = LLM_ERROR_MAP.get(error_type)
        if mapping:
            cls._mock_responses[prompt_hash] = (error_type, message, mapping.retryable)
        else:
            cls._mock_responses[prompt_hash] = (error_type, message, False)

    @classmethod
    def clear_responses(cls):
        """Clear all mock responses."""
        cls._mock_responses.clear()

    async def invoke(
        self, prompt: Union[str, List[Message]], config: LLMConfig
    ) -> Union[LLMResponse, Tuple[str, str, bool]]:
        """Generate deterministic stub response."""
        import time

        start = time.perf_counter()

        # Normalize prompt for hashing
        if isinstance(prompt, str):
            prompt_text = prompt
        else:
            prompt_text = "\n".join(f"{m.role}: {m.content}" for m in prompt)

        prompt_hash = _content_hash(prompt_text, 16)

        # Check for mock response
        if prompt_hash in self._mock_responses:
            response = self._mock_responses[prompt_hash]
            if isinstance(response, tuple):
                return response  # Error tuple
            return response

        # Generate deterministic response based on seed and prompt
        if config.seed is not None:
            response_seed = f"{config.seed}:{prompt_hash}"
            response_hash = hashlib.sha256(response_seed.encode()).hexdigest()[:8]
            content = f"Deterministic response [{response_hash}] for: {prompt_text[:50]}..."
        else:
            content = f"Stub response for: {prompt_text[:50]}..."

        input_tokens = self.estimate_tokens(prompt_text)
        output_tokens = self.estimate_tokens(content)
        latency = int((time.perf_counter() - start) * 1000) + 10  # Simulated

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model="stub",
            finish_reason="end_turn",
            latency_ms=latency,
            seed=config.seed,
        )


# =============================================================================
# Adapter Registry
# =============================================================================

_adapters: Dict[str, LLMAdapter] = {"stub": StubAdapter()}


def register_adapter(adapter: LLMAdapter):
    """Register an LLM adapter."""
    _adapters[adapter.adapter_id] = adapter


def get_adapter(adapter_id: str) -> Optional[LLMAdapter]:
    """Get adapter by ID."""
    return _adapters.get(adapter_id)


def list_adapters() -> List[str]:
    """List registered adapter IDs."""
    return list(_adapters.keys())


# =============================================================================
# Skill Descriptor
# =============================================================================

LLM_INVOKE_DESCRIPTOR = SkillDescriptor(
    skill_id="skill.llm_invoke",
    name="LLM Invoke",
    version="2.0.0",
    description="Invoke language models with adapter pattern and seeding support",
    inputs_schema={
        "type": "object",
        "required": ["prompt"],
        "properties": {
            "prompt": {"oneOf": [{"type": "string"}, {"type": "array"}]},
            "model": {"type": "string"},
            "adapter": {"type": "string", "enum": ["claude", "openai", "stub"]},
            "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 100000},
            "seed": {"type": "integer"},
            "system_prompt": {"type": "string"},
            "stop_sequences": {"type": "array", "items": {"type": "string"}},
            "timeout_ms": {"type": "integer"},
        },
    },
    outputs_schema={
        "type": "object",
        "required": ["content", "input_tokens", "output_tokens", "content_hash"],
        "properties": {
            "content": {"type": "string"},
            "content_hash": {"type": "string"},
            "input_tokens": {"type": "integer"},
            "output_tokens": {"type": "integer"},
            "cost_cents": {"type": "number"},
            "model": {"type": "string"},
            "finish_reason": {"type": "string"},
            "latency_ms": {"type": "integer"},
            "seed": {"type": "integer"},
        },
    },
    stable_fields=["content_hash", "input_tokens", "output_tokens", "finish_reason", "seed"],
    idempotent=False,  # LLM calls are non-deterministic unless seeded
    cost_model={"base_cents": 0, "per_token_input_cents": 0.0003, "per_token_output_cents": 0.0015},
    failure_modes=[
        "ERR_LLM_RATE_LIMITED",
        "ERR_LLM_OVERLOADED",
        "ERR_LLM_TIMEOUT",
        "ERR_LLM_INVALID_PROMPT",
        "ERR_LLM_CONTENT_BLOCKED",
        "ERR_LLM_AUTH_FAILED",
        "ERR_LLM_CONTEXT_TOO_LONG",
        "ERR_LLM_INVALID_MODEL",
        "ERR_LLM_ADAPTER_NOT_FOUND",
    ],
    constraints={"max_prompt_tokens": 100000, "max_output_tokens": 100000, "rate_limit_rpm": 60},
)


# =============================================================================
# Main Execute Function
# =============================================================================


async def llm_invoke_execute(params: Dict[str, Any]) -> StructuredOutcome:
    """
    Execute LLM invocation with error contract enforcement.

    Args:
        params: Invocation parameters

    Returns:
        StructuredOutcome with response or error
    """
    call_id = _generate_call_id(params)

    # Extract parameters
    prompt = params.get("prompt")
    adapter_id = params.get("adapter", "stub")
    model = params.get("model")
    temperature = params.get("temperature", 0.0)
    max_tokens = params.get("max_tokens", 1024)
    seed = params.get("seed")
    system_prompt = params.get("system_prompt")
    stop_sequences = params.get("stop_sequences")
    timeout_ms = params.get("timeout_ms", 60000)

    # Validate prompt
    if not prompt:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_LLM_INVALID_PROMPT",
            message="Missing required parameter: prompt",
            category="VALIDATION",
            retryable=False,
        )

    # Get adapter
    adapter = get_adapter(adapter_id)
    if not adapter:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_LLM_ADAPTER_NOT_FOUND",
            message=f"Unknown adapter: {adapter_id}. Available: {list_adapters()}",
            category="VALIDATION",
            retryable=False,
            details={"adapter": adapter_id, "available": list_adapters()},
        )

    # Build config
    config = LLMConfig(
        model=model or adapter.default_model,
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        system_prompt=system_prompt,
        stop_sequences=stop_sequences,
        timeout_ms=timeout_ms,
    )

    # Convert prompt to messages if needed
    if isinstance(prompt, str):
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
    elif isinstance(prompt, list):
        messages = [Message(role=m.get("role", "user"), content=m.get("content", "")) for m in prompt]
    else:
        return StructuredOutcome.failure(
            call_id=call_id,
            code="ERR_LLM_INVALID_PROMPT",
            message="Prompt must be string or list of messages",
            category="VALIDATION",
            retryable=False,
        )

    # Invoke adapter
    try:
        result = await adapter.invoke(messages, config)

        if isinstance(result, tuple):
            # Error response
            error_type, message, retryable = result
            mapping = LLM_ERROR_MAP.get(error_type)
            if mapping:
                return StructuredOutcome.failure(
                    call_id=call_id,
                    code=mapping.code,
                    message=message,
                    category=mapping.category.value,
                    retryable=mapping.retryable,
                    details={"error_type": error_type},
                    meta={
                        "skill_id": LLM_INVOKE_DESCRIPTOR.skill_id,
                        "skill_version": LLM_INVOKE_DESCRIPTOR.version,
                        "adapter": adapter_id,
                    },
                )
            else:
                return StructuredOutcome.failure(
                    call_id=call_id,
                    code=f"ERR_LLM_{error_type.upper()}",
                    message=message,
                    category="PERMANENT",
                    retryable=retryable,
                    details={"error_type": error_type},
                )

        # Success
        content_hash = _content_hash(result.content)
        cost = estimate_cost(result.model, result.input_tokens, result.output_tokens)

        return StructuredOutcome.success(
            call_id=call_id,
            result={
                "content": result.content,
                "content_hash": content_hash,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost_cents": cost,
                "model": result.model,
                "finish_reason": result.finish_reason,
                "latency_ms": result.latency_ms,
                "seed": result.seed,
            },
            meta={
                "skill_id": LLM_INVOKE_DESCRIPTOR.skill_id,
                "skill_version": LLM_INVOKE_DESCRIPTOR.version,
                "adapter": adapter_id,
                "deterministic": seed is not None and adapter.supports_seeding(),
            },
        )

    except Exception as e:
        # Map exception to error
        error_str = str(e).lower()

        if "rate" in error_str or "429" in error_str:
            mapping = LLM_ERROR_MAP["rate_limited"]
        elif "timeout" in error_str:
            mapping = LLM_ERROR_MAP["timeout"]
        elif "auth" in error_str or "key" in error_str or "401" in error_str:
            mapping = LLM_ERROR_MAP["auth_failed"]
        elif "overloaded" in error_str or "503" in error_str:
            mapping = LLM_ERROR_MAP["overloaded"]
        else:
            # Default to transient
            mapping = ErrorMapping("ERR_LLM_UNKNOWN", ErrorCategory.TRANSIENT, True)

        return StructuredOutcome.failure(
            call_id=call_id,
            code=mapping.code,
            message=str(e),
            category=mapping.category.value,
            retryable=mapping.retryable,
            details={"exception_type": type(e).__name__},
            meta={
                "skill_id": LLM_INVOKE_DESCRIPTOR.skill_id,
                "skill_version": LLM_INVOKE_DESCRIPTOR.version,
                "adapter": adapter_id,
            },
        )


# Handler for registry
async def llm_invoke_handler(params: Dict[str, Any]) -> StructuredOutcome:
    """Handler function for skill registry."""
    return await llm_invoke_execute(params)


# =============================================================================
# Registration Helper
# =============================================================================


def register_llm_invoke(registry) -> None:
    """Register llm_invoke skill with registry."""
    registry.register(
        descriptor=LLM_INVOKE_DESCRIPTOR,
        handler=llm_invoke_handler,
        is_stub=False,
        tags=["llm", "ai", "generation", "m3"],
    )
