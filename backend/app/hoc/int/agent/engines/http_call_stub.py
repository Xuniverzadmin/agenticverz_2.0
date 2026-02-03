# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: HTTP Call Stub (M2)
# skills/stubs/http_call_stub.py
"""
HTTP Call Stub (M2)

Deterministic stub for http_call skill for testing.
Returns configurable mock responses based on URL patterns.

Features:
- Deterministic behavior (seeded randomness only if explicit)
- Configurable timeout & mock responses
- Side-effect logging
- Conforms to SkillDescriptor from runtime/core.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_runtime_path = str(Path(__file__).parent.parent.parent / "worker" / "runtime")

    sys.path.insert(0, _runtime_path)

from core import SkillDescriptor

# Descriptor for http_call stub
HTTP_CALL_STUB_DESCRIPTOR = SkillDescriptor(
    skill_id="skill.http_call",
    name="HTTP Call (Stub)",
    version="1.0.0-stub",
    inputs_schema_version="1.0",
    outputs_schema_version="1.0",
    stable_fields={"status": "DETERMINISTIC", "headers": "DETERMINISTIC", "body_hash": "DETERMINISTIC"},
    cost_model={"base_cents": 0, "per_kb_cents": 0},
    failure_modes=[
        {"code": "ERR_TIMEOUT", "category": "TRANSIENT", "typical_cause": "slow server"},
        {"code": "ERR_DNS_FAILURE", "category": "TRANSIENT", "typical_cause": "network issue"},
        {"code": "ERR_HTTP_4XX", "category": "PERMANENT", "typical_cause": "bad request"},
        {"code": "ERR_HTTP_5XX", "category": "TRANSIENT", "typical_cause": "server error"},
        {"code": "ERR_CONNECTION_REFUSED", "category": "TRANSIENT", "typical_cause": "server down"},
    ],
    constraints={
        "blocked_hosts": ["localhost", "127.0.0.1", "169.254.169.254"],
        "max_response_bytes": 10485760,
        "timeout_ms": 30000,
    },
)


@dataclass
class MockResponse:
    """Configurable mock response for http_call stub."""

    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    latency_ms: int = 50
    error: Optional[str] = None  # If set, simulates an error


@dataclass
class HttpCallStub:
    """
    HTTP Call stub with configurable responses.

    Usage:
        stub = HttpCallStub()
        stub.add_response("https://api.example.com/data", MockResponse(
            status=200,
            body={"key": "value"}
        ))
        result = await stub.execute({"url": "https://api.example.com/data"})
    """

    # URL pattern -> response mapping
    responses: Dict[str, MockResponse] = field(default_factory=dict)
    # Default response for unmatched URLs
    default_response: MockResponse = field(
        default_factory=lambda: MockResponse(status_code=200, body={"stub": True, "message": "Default stub response"})
    )
    # Record of calls for verification
    call_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_response(self, url_pattern: str, response: Union[MockResponse, Dict[str, Any]]) -> None:
        """Add a mock response for a URL pattern."""
        if isinstance(response, dict):
            response = MockResponse(
                status_code=response.get("status_code", 200),
                headers=response.get("headers", {}),
                body=response.get("body"),
                latency_ms=response.get("latency_ms", 50),
                error=response.get("error"),
            )
        self.responses[url_pattern] = response

    def add_error(self, url_pattern: str, error_code: str, message: str) -> None:
        """Add an error response for a URL pattern."""
        self.responses[url_pattern] = MockResponse(error=f"{error_code}:{message}")

    def _find_response(self, url: str) -> MockResponse:
        """Find matching response for URL."""
        # Exact match
        if url in self.responses:
            return self.responses[url]
        # Host-based match (pattern can be just the hostname)
        for pattern, response in self.responses.items():
            if pattern in url:
                return response
        return self.default_response

    def _compute_body_hash(self, body: Any) -> str:
        """Compute deterministic hash of response body."""
        body_str = json.dumps(body, sort_keys=True) if body else ""
        return hashlib.sha256(body_str.encode()).hexdigest()[:16]

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the stub with deterministic behavior.

        Args:
            inputs: Must contain 'url', optionally 'method', 'headers', 'body'

        Returns:
            Deterministic response based on URL pattern
        """
        url = inputs.get("url", "")
        method = inputs.get("method", "GET")
        request_headers = inputs.get("headers", {})
        request_body = inputs.get("body")

        # Record call
        self.call_history.append({"url": url, "method": method, "headers": request_headers, "body": request_body})

        # Find matching response
        response = self._find_response(url)

        # Check for simulated error
        if response.error:
            error_parts = response.error.split(":", 1)
            raise Exception(f"Simulated error: {response.error}")

        # Build deterministic response
        result = {
            "status_code": response.status_code,
            "headers": {"content-type": "application/json", "x-stub": "true", **response.headers},
            "body": response.body,
            "body_hash": self._compute_body_hash(response.body),
            "latency_ms": response.latency_ms,
            "url": url,
            "method": method,
        }

        return result

    def reset(self) -> None:
        """Reset call history."""
        self.call_history.clear()


# Global stub instance
_HTTP_CALL_STUB = HttpCallStub()


async def http_call_stub_handler(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler function for http_call stub.

    This is the function registered with the runtime.
    """
    return await _HTTP_CALL_STUB.execute(inputs)


def get_http_call_stub() -> HttpCallStub:
    """Get the global http_call stub instance for configuration."""
    return _HTTP_CALL_STUB


def configure_http_call_stub(stub: HttpCallStub) -> None:
    """Replace the global http_call stub instance."""
    global _HTTP_CALL_STUB
    _HTTP_CALL_STUB = stub
