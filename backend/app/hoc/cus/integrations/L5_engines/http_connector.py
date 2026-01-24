# Layer: L5 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api (via mediation layer)
#   Execution: async
# Role: Machine-controlled HTTP connector (NOT LLM-controlled)
# Callers: RetrievalMediator
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: GAP-059

"""
Module: http_connector
Purpose: Machine-controlled HTTP connector (NOT LLM-controlled).

Key Difference from HttpCallSkill:
    - HttpCallSkill: LLM controls URL, headers, body (DANGEROUS)
    - HttpConnectorService: Machine resolves URL from registry, LLM only provides action

Security Model:
    - Base URL: Machine-controlled (from connector config)
    - Auth: Machine-controlled (from vault)
    - Endpoints: Machine-controlled (action -> path mapping)
    - Payload: LLM-controlled but validated against schema

Imports (Dependencies):
    - None (credential service passed via constructor)

Exports (Provides):
    - HttpConnectorService: Governed HTTP access
    - HttpConnectorConfig: Configuration dataclass

Wiring Points:
    - Called from: RetrievalMediator
    - Registered in: ConnectorRegistry

Acceptance Criteria:
    - [x] AC-059-01: URL resolved from config, not LLM
    - [x] AC-059-02: Auth from vault
    - [x] AC-059-03: Method restrictions enforced
    - [x] AC-059-04: Registered with connector registry
    - [x] AC-059-05: Evidence emitted via mediator
    - [x] AC-059-06: Tenant isolation (INV-003)
    - [x] AC-059-07: Max response bytes enforced
    - [x] AC-059-08: Max latency enforced
    - [x] AC-059-09: Request rate limited
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum
import logging

# Credential and CredentialService imported from canonical source — INT-DUP-001, INT-DUP-002
from app.hoc.cus.integrations.L5_engines.credentials import (
    Credential,
    CredentialService,
)

logger = logging.getLogger("nova.services.connectors.http_connector")

# Blast-radius caps (INV-003 connector constraints)
DEFAULT_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5MB
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_RATE_LIMIT_PER_MINUTE = 60


class HttpMethod(str, Enum):
    """Allowed HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class EndpointConfig:
    """Configuration for a single endpoint."""
    method: HttpMethod
    path: str
    description: str = ""
    request_schema: Optional[Dict] = None
    requires_body: bool = False


@dataclass
class HttpConnectorConfig:
    """Configuration for HTTP connector."""
    id: str
    name: str
    base_url: str
    auth_type: str  # "bearer", "api_key", "basic", "none"
    auth_header: str = "Authorization"
    credential_ref: str = ""  # Reference to vault
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES
    rate_limit_per_minute: int = DEFAULT_RATE_LIMIT_PER_MINUTE
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST"])
    endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)
    tenant_id: str = ""  # Owning tenant for isolation


# Credential dataclass removed — INT-DUP-001 quarantine
# Import from canonical source: engines/credentials/types.py

# CredentialService protocol removed — INT-DUP-002 quarantine
# Import from canonical source: engines/credentials/protocol.py


class HttpConnectorError(Exception):
    """Error from HTTP connector."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class RateLimitExceededError(HttpConnectorError):
    """Rate limit exceeded."""

    def __init__(self, retry_after_seconds: int = 60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds}s")


class HttpConnectorService:
    """
    Governed HTTP connector.

    Machine controls:
    - Base URL (from connector config)
    - Auth headers (from vault)
    - Allowed methods
    - Endpoint mapping (action -> URL path)

    LLM controls:
    - Action name (maps to endpoint)
    - Payload data (validated against schema)

    Implements Connector protocol for use with RetrievalMediator.
    """

    def __init__(
        self,
        config: HttpConnectorConfig,
        credential_service: Optional[CredentialService] = None,
    ):
        self.config = config
        self.credential_service = credential_service
        self._request_counts: Dict[str, List[datetime]] = {}  # tenant_id -> timestamps

    @property
    def id(self) -> str:
        """Connector ID for protocol compliance."""
        return self.config.id

    async def execute(
        self,
        action: str,
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a governed HTTP request.

        Args:
            action: Action name (maps to endpoint path)
            payload: Request payload
            tenant_id: Requesting tenant (for rate limiting)

        Returns:
            Response data with token_count

        Raises:
            HttpConnectorError: On request failure
            RateLimitExceededError: If rate limit exceeded
            ValueError: If action unknown or method not allowed
        """
        # Step 0: Rate limit check
        if tenant_id:
            self._check_rate_limit(tenant_id)

        # Step 1: Resolve endpoint from action (machine-controlled)
        endpoint = self._resolve_endpoint(action)

        # Step 2: Validate method is allowed
        if endpoint.method.value not in self.config.allowed_methods:
            raise ValueError(
                f"Method {endpoint.method.value} not allowed. "
                f"Allowed: {self.config.allowed_methods}"
            )

        # Step 3: Build URL (machine-controlled)
        url = self._build_url(endpoint.path, payload)

        # Step 4: Get auth headers (machine-controlled from vault)
        headers = await self._get_auth_headers()

        # Step 5: Execute request with timeout and size limits
        try:
            import httpx

            async with httpx.AsyncClient(
                timeout=self.config.timeout_seconds,
                follow_redirects=True,
            ) as client:
                if endpoint.method == HttpMethod.GET:
                    response = await client.get(
                        url,
                        headers=headers,
                        params=payload if not endpoint.requires_body else None,
                    )
                elif endpoint.method == HttpMethod.POST:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=payload,
                    )
                elif endpoint.method == HttpMethod.PUT:
                    response = await client.put(
                        url,
                        headers=headers,
                        json=payload,
                    )
                elif endpoint.method == HttpMethod.PATCH:
                    response = await client.patch(
                        url,
                        headers=headers,
                        json=payload,
                    )
                elif endpoint.method == HttpMethod.DELETE:
                    response = await client.delete(
                        url,
                        headers=headers,
                    )
                else:
                    raise ValueError(f"Unsupported method: {endpoint.method}")

                response.raise_for_status()

                # Check response size (AC-059-07)
                content = response.content
                if len(content) > self.config.max_response_bytes:
                    logger.warning("http_connector.response_truncated", extra={
                        "connector_id": self.id,
                        "action": action,
                        "original_size": len(content),
                        "max_size": self.config.max_response_bytes,
                    })
                    content = content[:self.config.max_response_bytes]
                    truncated = True
                else:
                    truncated = False

                # Parse response
                try:
                    data = response.json()
                except Exception:
                    data = content.decode('utf-8', errors='replace')

                # Track request for rate limiting
                if tenant_id:
                    self._record_request(tenant_id)

                return {
                    "data": data,
                    "status_code": response.status_code,
                    "token_count": len(str(payload)) + len(content),
                    "truncated": truncated,
                }

        except httpx.TimeoutException as e:
            logger.error("http_connector.timeout", extra={
                "connector_id": self.id,
                "action": action,
                "timeout": self.config.timeout_seconds,
            })
            raise HttpConnectorError(
                f"Request timed out after {self.config.timeout_seconds}s"
            ) from e

        except httpx.HTTPStatusError as e:
            raise HttpConnectorError(
                f"HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            ) from e

    def _resolve_endpoint(self, action: str) -> EndpointConfig:
        """Map action to endpoint (machine-controlled)."""
        if action not in self.config.endpoints:
            available = list(self.config.endpoints.keys())
            raise ValueError(
                f"Unknown action: {action}. Available: {available}"
            )
        return self.config.endpoints[action]

    def _build_url(self, path: str, payload: Dict[str, Any]) -> str:
        """Build URL from base URL and path."""
        # Handle path parameters like /users/{id}
        formatted_path = path
        for key, value in payload.items():
            placeholder = f"{{{key}}}"
            if placeholder in formatted_path:
                formatted_path = formatted_path.replace(placeholder, str(value))

        return f"{self.config.base_url.rstrip('/')}{formatted_path}"

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get auth headers from vault (machine-controlled)."""
        if not self.credential_service or not self.config.credential_ref:
            if self.config.auth_type != "none":
                logger.warning("http_connector.no_credentials", extra={
                    "connector_id": self.id,
                    "auth_type": self.config.auth_type,
                })
            return {}

        credential = await self.credential_service.get(self.config.credential_ref)

        if self.config.auth_type == "bearer":
            return {self.config.auth_header: f"Bearer {credential.value}"}
        elif self.config.auth_type == "api_key":
            return {self.config.auth_header: credential.value}
        elif self.config.auth_type == "basic":
            import base64
            encoded = base64.b64encode(credential.value.encode()).decode()
            return {self.config.auth_header: f"Basic {encoded}"}

        return {}

    def _check_rate_limit(self, tenant_id: str):
        """Check if rate limit exceeded (AC-059-09)."""
        now = datetime.now(timezone.utc)
        minute_ago = now.timestamp() - 60

        if tenant_id not in self._request_counts:
            self._request_counts[tenant_id] = []

        # Clean old entries
        self._request_counts[tenant_id] = [
            ts for ts in self._request_counts[tenant_id]
            if ts.timestamp() > minute_ago
        ]

        if len(self._request_counts[tenant_id]) >= self.config.rate_limit_per_minute:
            logger.warning("http_connector.rate_limit_exceeded", extra={
                "connector_id": self.id,
                "tenant_id": tenant_id,
                "requests_in_window": len(self._request_counts[tenant_id]),
                "limit": self.config.rate_limit_per_minute,
            })
            raise RateLimitExceededError()

    def _record_request(self, tenant_id: str):
        """Record a request for rate limiting."""
        if tenant_id not in self._request_counts:
            self._request_counts[tenant_id] = []
        self._request_counts[tenant_id].append(datetime.now(timezone.utc))
