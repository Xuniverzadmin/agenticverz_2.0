# skills/stubs/__init__.py
"""
Skill Stubs (M2)

Deterministic stub implementations for testing:
- http_call_stub: Mock HTTP responses
- llm_invoke_stub: Deterministic LLM responses
- json_transform_stub: Deterministic JSON transformations

These stubs conform to SkillDescriptor from runtime/core.py
and produce deterministic outputs for replay tests.
"""

from .http_call_stub import (
    HttpCallStub,
    http_call_stub_handler,
    HTTP_CALL_STUB_DESCRIPTOR
)
from .llm_invoke_stub import (
    LlmInvokeStub,
    llm_invoke_stub_handler,
    LLM_INVOKE_STUB_DESCRIPTOR
)
from .json_transform_stub import (
    JsonTransformStub,
    json_transform_stub_handler,
    JSON_TRANSFORM_STUB_DESCRIPTOR
)

__all__ = [
    "HttpCallStub",
    "http_call_stub_handler",
    "HTTP_CALL_STUB_DESCRIPTOR",
    "LlmInvokeStub",
    "llm_invoke_stub_handler",
    "LLM_INVOKE_STUB_DESCRIPTOR",
    "JsonTransformStub",
    "json_transform_stub_handler",
    "JSON_TRANSFORM_STUB_DESCRIPTOR",
]
