# skills/stubs/llm_invoke_stub.py
"""
LLM Invoke Stub (M2)

Deterministic stub for llm_invoke skill for testing.
Returns seeded deterministic responses based on prompt hash.

Features:
- Deterministic token-level structure for replay tests
- Configurable responses based on prompt patterns
- Token cost estimation
- Conforms to SkillDescriptor from runtime/core.py
"""

from __future__ import annotations
import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

import sys
_runtime_path = str(Path(__file__).parent.parent.parent / "worker" / "runtime")
if _runtime_path not in sys.path:
    sys.path.insert(0, _runtime_path)

from core import SkillDescriptor


# Descriptor for llm_invoke stub
LLM_INVOKE_STUB_DESCRIPTOR = SkillDescriptor(
    skill_id="skill.llm_invoke",
    name="LLM Invoke (Stub)",
    version="1.0.0-stub",
    inputs_schema_version="1.0",
    outputs_schema_version="1.0",
    stable_fields={
        "model": "DETERMINISTIC",
        "prompt_hash": "DETERMINISTIC",
        "token_count": "DETERMINISTIC",
        "response_hash": "DETERMINISTIC"
    },
    cost_model={
        "base_cents": 1,
        "per_token_cents": 0.001
    },
    failure_modes=[
        {"code": "ERR_RATE_LIMITED", "category": "TRANSIENT", "typical_cause": "API rate limit"},
        {"code": "ERR_CONTEXT_LENGTH", "category": "PERMANENT", "typical_cause": "prompt too long"},
        {"code": "ERR_INVALID_MODEL", "category": "PERMANENT", "typical_cause": "model not available"},
        {"code": "ERR_CONTENT_FILTER", "category": "PERMANENT", "typical_cause": "content blocked"}
    ],
    constraints={
        "max_tokens": 4096,
        "models_allowed": ["stub-model", "claude-sonnet-stub"],
        "timeout_ms": 60000
    }
)


@dataclass
class MockLlmResponse:
    """Configurable mock LLM response."""
    content: str
    model: str = "stub-model"
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"
    error: Optional[str] = None


@dataclass
class LlmInvokeStub:
    """
    LLM Invoke stub with deterministic responses.

    Usage:
        stub = LlmInvokeStub()
        stub.add_response("analyze", MockLlmResponse(
            content="Analysis complete: The data shows positive trends.",
            output_tokens=10
        ))
        result = await stub.execute({"prompt": "Please analyze this data"})
    """
    # Prompt pattern -> response mapping
    responses: Dict[str, MockLlmResponse] = field(default_factory=dict)
    # Default response generator (seeded by prompt hash)
    default_model: str = "stub-model"
    # Call history for verification
    call_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_response(self, prompt_pattern: str, response: MockLlmResponse) -> None:
        """Add a mock response for a prompt pattern."""
        self.responses[prompt_pattern.lower()] = response

    def add_error(self, prompt_pattern: str, error_code: str, message: str) -> None:
        """Add an error response for a prompt pattern."""
        self.responses[prompt_pattern.lower()] = MockLlmResponse(
            content="",
            error=f"{error_code}:{message}"
        )

    def _compute_prompt_hash(self, prompt: str) -> str:
        """Compute deterministic hash of prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _find_response(self, prompt: str) -> Optional[MockLlmResponse]:
        """Find matching response for prompt."""
        prompt_lower = prompt.lower()
        # Check for pattern matches
        for pattern, response in self.responses.items():
            if pattern in prompt_lower:
                return response
        return None

    def _generate_deterministic_response(self, prompt: str) -> MockLlmResponse:
        """
        Generate a deterministic response based on prompt hash.

        This ensures the same prompt always produces the same response,
        which is required for replay tests.
        """
        prompt_hash = self._compute_prompt_hash(prompt)
        # Use hash to seed response content
        seed = int(prompt_hash[:8], 16)

        # Generate deterministic "thinking"
        thoughts = [
            "Analyzing the request...",
            "Processing the input...",
            "Generating response...",
            "Finalizing output..."
        ]
        thought = thoughts[seed % len(thoughts)]

        # Deterministic response structure
        response_content = f"[STUB] {thought} Based on prompt hash {prompt_hash[:8]}, here is a deterministic response for testing purposes."

        # Estimate tokens (deterministic based on lengths)
        input_tokens = len(prompt.split())
        output_tokens = len(response_content.split())

        return MockLlmResponse(
            content=response_content,
            model=self.default_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            finish_reason="stop"
        )

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the stub with deterministic behavior.

        Args:
            inputs: Must contain 'prompt', optionally 'model', 'max_tokens'

        Returns:
            Deterministic response based on prompt
        """
        prompt = inputs.get("prompt", "")
        model = inputs.get("model", self.default_model)
        max_tokens = inputs.get("max_tokens", 1024)

        prompt_hash = self._compute_prompt_hash(prompt)

        # Record call
        self.call_history.append({
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "prompt_hash": prompt_hash,
            "model": model,
            "max_tokens": max_tokens
        })

        # Find matching response or generate deterministic one
        response = self._find_response(prompt)
        if response is None:
            response = self._generate_deterministic_response(prompt)

        # Check for simulated error
        if response.error:
            raise Exception(f"Simulated LLM error: {response.error}")

        # Build deterministic response
        result = {
            "content": response.content,
            "model": response.model,
            "prompt_hash": prompt_hash,
            "response_hash": self._compute_prompt_hash(response.content),
            "usage": {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "total_tokens": response.input_tokens + response.output_tokens
            },
            "finish_reason": response.finish_reason,
            "cost_cents": max(1, int(
                (response.input_tokens + response.output_tokens) * 0.001
            ))
        }

        return result

    def reset(self) -> None:
        """Reset call history."""
        self.call_history.clear()


# Global stub instance
_LLM_INVOKE_STUB = LlmInvokeStub()


async def llm_invoke_stub_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for llm_invoke stub.

    This is the function registered with the runtime.
    """
    return await _LLM_INVOKE_STUB.execute(inputs)


def get_llm_invoke_stub() -> LlmInvokeStub:
    """Get the global llm_invoke stub instance for configuration."""
    return _LLM_INVOKE_STUB


def configure_llm_invoke_stub(stub: LlmInvokeStub) -> None:
    """Replace the global llm_invoke stub instance."""
    global _LLM_INVOKE_STUB
    _LLM_INVOKE_STUB = stub
