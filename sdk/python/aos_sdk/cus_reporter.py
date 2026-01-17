"""
Customer LLM Usage Reporter

PURPOSE:
    SDK module for reporting LLM usage telemetry to AOS. This enables
    customers to track and govern their LLM provider usage through AOS
    while using their own API keys.

SEMANTIC:
    This is the DATA PLANE reporter - it captures facts about LLM calls
    and sends them to AOS for aggregation, visibility, and enforcement.

USAGE:
    from aos_sdk.cus_reporter import CusReporter, CusUsageRecord

    # Initialize with integration credentials
    reporter = CusReporter(
        integration_key="tenant-id:integration-id:secret",
        base_url="https://api.aos.example.com"
    )

    # Report a single LLM call
    reporter.report(CusUsageRecord(
        call_id="call-123",
        provider="openai",
        model="gpt-4",
        tokens_in=100,
        tokens_out=50,
        cost_cents=5,
        latency_ms=250,
    ))

    # Or use the context manager for automatic reporting
    with reporter.track_call("openai", "gpt-4") as tracker:
        # Make your LLM call here
        response = openai.chat.completions.create(...)
        tracker.set_tokens(response.usage.prompt_tokens, response.usage.completion_tokens)
        tracker.set_cost(calculate_cost(response.usage))

BATCH REPORTING:
    # For high-volume usage, batch reports for efficiency
    reporter.enable_batching(max_size=50, flush_interval_seconds=5.0)

    # Reports are automatically batched and flushed
    reporter.report(record1)
    reporter.report(record2)

    # Force flush remaining records
    reporter.flush()

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
import os
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import httpx

    _USE_HTTPX = True
except ImportError:
    import requests  # type: ignore

    _USE_HTTPX = False


logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class CusPolicyResult(str, Enum):
    """Policy enforcement result for LLM calls."""

    ALLOWED = "allowed"
    WARNED = "warned"
    BLOCKED = "blocked"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CusUsageRecord:
    """Single LLM usage telemetry record.

    Attributes:
        call_id: Unique identifier for this call (idempotency key)
        provider: LLM provider (openai, anthropic, etc.)
        model: Model used
        tokens_in: Input/prompt tokens
        tokens_out: Output/completion tokens
        cost_cents: Calculated cost in cents
        latency_ms: Request latency in milliseconds
        session_id: Optional session grouping
        agent_id: Optional agent identifier
        policy_result: Policy enforcement result
        error_code: Error code if call failed
        error_message: Error message if call failed
        metadata: Additional context
    """

    call_id: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_cents: int
    latency_ms: Optional[int] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    policy_result: CusPolicyResult = CusPolicyResult.ALLOWED
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        data = {
            "call_id": self.call_id,
            "provider": self.provider,
            "model": self.model,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_cents": self.cost_cents,
            "policy_result": self.policy_result.value,
            "metadata": self.metadata,
        }
        if self.latency_ms is not None:
            data["latency_ms"] = self.latency_ms
        if self.session_id:
            data["session_id"] = self.session_id
        if self.agent_id:
            data["agent_id"] = self.agent_id
        if self.error_code:
            data["error_code"] = self.error_code
        if self.error_message:
            data["error_message"] = self.error_message
        return data


@dataclass
class CusLimitsStatus:
    """Current usage vs limits status."""

    budget_limit_cents: int
    budget_used_cents: int
    budget_percent: float
    token_limit_month: int
    tokens_used_month: int
    token_percent: float
    rate_limit_rpm: int
    current_rpm: int
    rate_percent: float


# =============================================================================
# CALL TRACKER
# =============================================================================


class CusCallTracker:
    """Context manager for tracking a single LLM call.

    Automatically measures latency and reports telemetry on exit.

    Usage:
        with reporter.track_call("openai", "gpt-4") as tracker:
            response = openai.chat.completions.create(...)
            tracker.set_tokens(response.usage.prompt_tokens, response.usage.completion_tokens)
            tracker.set_cost(calculate_cost(response.usage))
    """

    def __init__(
        self,
        reporter: "CusReporter",
        provider: str,
        model: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self._reporter = reporter
        self._provider = provider
        self._model = model
        self._session_id = session_id
        self._agent_id = agent_id
        self._call_id = f"call-{uuid.uuid4().hex[:16]}"
        self._start_time: Optional[float] = None
        self._tokens_in = 0
        self._tokens_out = 0
        self._cost_cents = 0
        self._error_code: Optional[str] = None
        self._error_message: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        self._policy_result = CusPolicyResult.ALLOWED

    def set_tokens(self, tokens_in: int, tokens_out: int) -> "CusCallTracker":
        """Set token counts."""
        self._tokens_in = tokens_in
        self._tokens_out = tokens_out
        return self

    def set_cost(self, cost_cents: int) -> "CusCallTracker":
        """Set cost in cents."""
        self._cost_cents = cost_cents
        return self

    def set_error(self, code: str, message: str) -> "CusCallTracker":
        """Set error information."""
        self._error_code = code
        self._error_message = message
        return self

    def set_metadata(self, **kwargs) -> "CusCallTracker":
        """Add metadata."""
        self._metadata.update(kwargs)
        return self

    def set_policy_result(self, result: CusPolicyResult) -> "CusCallTracker":
        """Set policy enforcement result."""
        self._policy_result = result
        return self

    def __enter__(self) -> "CusCallTracker":
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate latency
        latency_ms = None
        if self._start_time:
            latency_ms = int((time.perf_counter() - self._start_time) * 1000)

        # Set error if exception occurred
        if exc_type is not None:
            self._error_code = exc_type.__name__
            self._error_message = str(exc_val)[:500]

        # Create and report record
        record = CusUsageRecord(
            call_id=self._call_id,
            provider=self._provider,
            model=self._model,
            tokens_in=self._tokens_in,
            tokens_out=self._tokens_out,
            cost_cents=self._cost_cents,
            latency_ms=latency_ms,
            session_id=self._session_id,
            agent_id=self._agent_id,
            policy_result=self._policy_result,
            error_code=self._error_code,
            error_message=self._error_message,
            metadata=self._metadata,
        )

        try:
            self._reporter.report(record)
        except Exception as e:
            logger.warning(f"Failed to report telemetry: {e}")

        # Don't suppress the original exception
        return False


# =============================================================================
# REPORTER
# =============================================================================


class CusReporter:
    """Customer LLM Usage Reporter.

    Reports telemetry data to AOS for aggregation and governance.

    Args:
        integration_key: Integration authentication key (tenant:integration:secret)
        base_url: AOS API base URL
        timeout: Request timeout in seconds
        on_error: Optional error callback

    Environment Variables:
        CUS_INTEGRATION_KEY: Integration key (fallback)
        AOS_BASE_URL: Base URL (fallback)
    """

    def __init__(
        self,
        integration_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 10,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        self._integration_key = integration_key or os.getenv("CUS_INTEGRATION_KEY")
        self._base_url = (
            base_url or os.getenv("AOS_BASE_URL", "http://127.0.0.1:8000")
        ).rstrip("/")
        self._timeout = timeout
        self._on_error = on_error

        # Parse integration key to get tenant/integration IDs
        self._tenant_id: Optional[str] = None
        self._integration_id: Optional[str] = None
        if self._integration_key:
            parts = self._integration_key.split(":")
            if len(parts) >= 2:
                self._tenant_id = parts[0]
                self._integration_id = parts[1]

        # Batching configuration
        self._batching_enabled = False
        self._batch_max_size = 50
        self._batch_flush_interval = 5.0
        self._batch: List[CusUsageRecord] = []
        self._batch_lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None

        # HTTP client setup
        headers = {"Content-Type": "application/json"}
        if self._integration_key:
            headers["X-CUS-Integration-Key"] = self._integration_key

        if _USE_HTTPX:
            self._client = httpx.Client(headers=headers, timeout=timeout)
        else:
            self._session = requests.Session()
            self._session.headers.update(headers)

    @property
    def integration_id(self) -> Optional[str]:
        """Get the integration ID."""
        return self._integration_id

    @property
    def tenant_id(self) -> Optional[str]:
        """Get the tenant ID."""
        return self._tenant_id

    # =========================================================================
    # BATCHING
    # =========================================================================

    def enable_batching(
        self,
        max_size: int = 50,
        flush_interval_seconds: float = 5.0,
    ) -> "CusReporter":
        """Enable batching for efficient telemetry submission.

        Args:
            max_size: Maximum batch size before auto-flush
            flush_interval_seconds: Maximum time between flushes

        Returns:
            Self for chaining
        """
        self._batching_enabled = True
        self._batch_max_size = max_size
        self._batch_flush_interval = flush_interval_seconds
        return self

    def disable_batching(self) -> "CusReporter":
        """Disable batching and flush any pending records."""
        self.flush()
        self._batching_enabled = False
        return self

    def flush(self) -> Dict[str, Any]:
        """Flush any pending batched records.

        Returns:
            Batch submission result
        """
        with self._batch_lock:
            if not self._batch:
                return {"accepted": 0, "duplicates": 0, "errors": 0, "total": 0}

            records = self._batch.copy()
            self._batch.clear()

            # Cancel pending timer
            if self._flush_timer:
                self._flush_timer.cancel()
                self._flush_timer = None

        return self._send_batch(records)

    def _schedule_flush(self):
        """Schedule an automatic flush."""
        if self._flush_timer is None:
            self._flush_timer = threading.Timer(
                self._batch_flush_interval,
                self._auto_flush,
            )
            self._flush_timer.daemon = True
            self._flush_timer.start()

    def _auto_flush(self):
        """Auto-flush callback."""
        try:
            self.flush()
        except Exception as e:
            logger.warning(f"Auto-flush failed: {e}")
            if self._on_error:
                self._on_error(e)

    # =========================================================================
    # REPORTING
    # =========================================================================

    def report(self, record: CusUsageRecord) -> Optional[Dict[str, Any]]:
        """Report a single LLM usage record.

        If batching is enabled, adds to batch and returns None.
        Otherwise sends immediately and returns API response.

        Args:
            record: Usage record to report

        Returns:
            API response if sent immediately, None if batched
        """
        if self._batching_enabled:
            with self._batch_lock:
                self._batch.append(record)
                if len(self._batch) >= self._batch_max_size:
                    records = self._batch.copy()
                    self._batch.clear()
                    if self._flush_timer:
                        self._flush_timer.cancel()
                        self._flush_timer = None
                else:
                    self._schedule_flush()
                    return None

            return self._send_batch(records)
        else:
            return self._send_single(record)

    def _send_single(self, record: CusUsageRecord) -> Dict[str, Any]:
        """Send a single record to the API."""
        url = f"{self._base_url}/api/v1/telemetry/llm-usage"
        payload = record.to_dict()

        # Add integration_id if not in record
        if "integration_id" not in payload and self._integration_id:
            payload["integration_id"] = self._integration_id

        try:
            if _USE_HTTPX:
                resp = self._client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            else:
                resp = self._session.post(url, json=payload, timeout=self._timeout)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to send telemetry: {e}")
            if self._on_error:
                self._on_error(e)
            raise

    def _send_batch(self, records: List[CusUsageRecord]) -> Dict[str, Any]:
        """Send a batch of records to the API."""
        if not records:
            return {"accepted": 0, "duplicates": 0, "errors": 0, "total": 0}

        url = f"{self._base_url}/api/v1/telemetry/llm-usage/batch"
        payload = {"records": [r.to_dict() for r in records]}

        # Add integration_id to records if needed
        for rec in payload["records"]:
            if "integration_id" not in rec and self._integration_id:
                rec["integration_id"] = self._integration_id

        try:
            if _USE_HTTPX:
                resp = self._client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            else:
                resp = self._session.post(url, json=payload, timeout=self._timeout)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to send batch telemetry: {e}")
            if self._on_error:
                self._on_error(e)
            raise

    # =========================================================================
    # TRACKING
    # =========================================================================

    def track_call(
        self,
        provider: str,
        model: str,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> CusCallTracker:
        """Create a call tracker context manager.

        Args:
            provider: LLM provider
            model: Model being used
            session_id: Optional session grouping
            agent_id: Optional agent identifier

        Returns:
            CusCallTracker context manager
        """
        return CusCallTracker(
            reporter=self,
            provider=provider,
            model=model,
            session_id=session_id,
            agent_id=agent_id,
        )

    # =========================================================================
    # LIMITS CHECKING
    # =========================================================================

    def check_limits(self) -> CusLimitsStatus:
        """Check current usage against limits.

        Returns:
            CusLimitsStatus with current usage percentages
        """
        url = f"{self._base_url}/api/v1/integrations/{self._integration_id}/limits"

        try:
            if _USE_HTTPX:
                resp = self._client.get(url)
                resp.raise_for_status()
                data = resp.json().get("data", {})
            else:
                resp = self._session.get(url, timeout=self._timeout)
                resp.raise_for_status()
                data = resp.json().get("data", {})

            return CusLimitsStatus(
                budget_limit_cents=data.get("budget_limit_cents", 0),
                budget_used_cents=data.get("budget_used_cents", 0),
                budget_percent=data.get("budget_percent", 0.0),
                token_limit_month=data.get("token_limit_month", 0),
                tokens_used_month=data.get("tokens_used_month", 0),
                token_percent=data.get("token_percent", 0.0),
                rate_limit_rpm=data.get("rate_limit_rpm", 0),
                current_rpm=data.get("current_rpm", 0),
                rate_percent=data.get("rate_percent", 0.0),
            )
        except Exception as e:
            logger.error(f"Failed to check limits: {e}")
            if self._on_error:
                self._on_error(e)
            raise

    def is_within_limits(self, warn_threshold: float = 80.0) -> bool:
        """Check if current usage is within limits.

        Args:
            warn_threshold: Percentage at which to warn (default 80%)

        Returns:
            True if all limits are under threshold
        """
        try:
            status = self.check_limits()
            return (
                status.budget_percent < warn_threshold
                and status.token_percent < warn_threshold
                and status.rate_percent < warn_threshold
            )
        except Exception:
            # If we can't check, assume within limits
            return True

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def close(self):
        """Close the reporter and flush any pending records."""
        self.flush()
        if _USE_HTTPX:
            self._client.close()
        else:
            self._session.close()

    def __enter__(self) -> "CusReporter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def generate_call_id() -> str:
    """Generate a unique call ID for telemetry."""
    return f"call-{uuid.uuid4().hex[:16]}"


def calculate_openai_cost(model: str, tokens_in: int, tokens_out: int) -> int:
    """Calculate cost in cents for OpenAI models.

    This is a simplified calculation - actual pricing may vary.

    Args:
        model: Model name
        tokens_in: Input tokens
        tokens_out: Output tokens

    Returns:
        Cost in cents
    """
    # Simplified pricing (per 1K tokens)
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    # Find best matching model
    model_lower = model.lower()
    rates = pricing.get("gpt-4o-mini")  # Default
    for key, rates_val in pricing.items():
        if key in model_lower:
            rates = rates_val
            break

    # Calculate cost in cents
    input_cost = (tokens_in / 1000) * rates["input"]
    output_cost = (tokens_out / 1000) * rates["output"]
    return int((input_cost + output_cost) * 100)


def calculate_anthropic_cost(model: str, tokens_in: int, tokens_out: int) -> int:
    """Calculate cost in cents for Anthropic models.

    This is a simplified calculation - actual pricing may vary.

    Args:
        model: Model name
        tokens_in: Input tokens
        tokens_out: Output tokens

    Returns:
        Cost in cents
    """
    # Simplified pricing (per 1K tokens)
    pricing = {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
        "claude-sonnet-4": {"input": 0.003, "output": 0.015},
        "claude-opus-4": {"input": 0.015, "output": 0.075},
    }

    # Find best matching model
    model_lower = model.lower()
    rates = pricing.get("claude-3-sonnet")  # Default
    for key, rates_val in pricing.items():
        if key in model_lower:
            rates = rates_val
            break

    # Calculate cost in cents
    input_cost = (tokens_in / 1000) * rates["input"]
    output_cost = (tokens_out / 1000) * rates["output"]
    return int((input_cost + output_cost) * 100)
