"""
Customer Integration Base Provider

PURPOSE:
    Abstract base class for LLM provider adapters. Provider adapters wrap
    native SDK clients (OpenAI, Anthropic, etc.) to automatically capture
    telemetry for visibility and governance.

SEMANTIC:
    Phase 3 scope: VISIBILITY ONLY, NO CONTROL.

    Providers capture and report telemetry:
    1. Intercept LLM calls
    2. Execute the actual LLM call via native SDK
    3. Capture telemetry (tokens, cost, latency)
    4. Report telemetry to AOS

    No blocking, no throttling, no policy decisions.
    Enforcement is Phase 5.

USAGE:
    # Don't use CusBaseProvider directly - use provider-specific classes
    from aos_sdk.cus_anthropic import CusAnthropicProvider
    from aos_sdk.cus_openai import CusOpenAIProvider

    # Create a governed Anthropic client
    provider = CusAnthropicProvider(
        api_key="your-anthropic-key",
        integration_key="tenant:integration:secret",
    )

    # Use like normal Anthropic client - telemetry captured automatically
    response = provider.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hello"}],
    )

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from .cus_reporter import (
    CusPolicyResult,
    CusReporter,
    CusUsageRecord,
    generate_call_id,
)

logger = logging.getLogger(__name__)

# Type variable for the wrapped client
T = TypeVar("T")


# =============================================================================
# ENUMS
# =============================================================================


class CusProviderStatus(str, Enum):
    """Provider health status."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CusCallContext:
    """Context for a single LLM call.

    Captures all information needed for telemetry reporting.
    """

    call_id: str
    provider: str
    model: str
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_cents: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    policy_result: CusPolicyResult = CusPolicyResult.ALLOWED
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def latency_ms(self) -> Optional[int]:
        """Calculate latency in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

    def to_usage_record(self) -> CusUsageRecord:
        """Convert to CusUsageRecord for reporting."""
        return CusUsageRecord(
            call_id=self.call_id,
            provider=self.provider,
            model=self.model,
            tokens_in=self.tokens_in,
            tokens_out=self.tokens_out,
            cost_cents=self.cost_cents,
            latency_ms=self.latency_ms,
            session_id=self.session_id,
            agent_id=self.agent_id,
            policy_result=self.policy_result,
            error_code=self.error_code,
            error_message=self.error_message,
            metadata=self.metadata,
        )


@dataclass
class CusProviderConfig:
    """Configuration for a provider adapter.

    Attributes:
        integration_key: AOS integration authentication key
        base_url: AOS API base URL for telemetry reporting
        auto_report: Whether to automatically report telemetry
        batch_telemetry: Whether to batch telemetry reports
        batch_size: Max batch size before auto-flush
        batch_interval: Max seconds between batch flushes
        session_id: Optional session ID for grouping calls
        agent_id: Optional agent ID for attribution
        on_call_complete: Optional callback after each call
    """

    integration_key: Optional[str] = None
    base_url: str = "http://127.0.0.1:8000"
    auto_report: bool = True
    batch_telemetry: bool = True
    batch_size: int = 50
    batch_interval: float = 5.0
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    on_call_complete: Optional[Callable[["CusCallContext"], None]] = None


# =============================================================================
# EXCEPTIONS
# =============================================================================


class CusProviderError(Exception):
    """Base exception for provider errors."""

    pass


# =============================================================================
# BASE PROVIDER
# =============================================================================


class CusBaseProvider(ABC, Generic[T]):
    """Abstract base class for LLM provider adapters.

    Phase 3: VISIBILITY ONLY - captures and reports telemetry.
    No blocking, no throttling, no policy enforcement.

    Subclasses must implement:
    - _create_client(): Create the native SDK client
    - _get_provider_name(): Return provider name (e.g., "anthropic")
    - _extract_usage(): Extract token counts from response
    - _calculate_cost(): Calculate cost from usage

    The base class handles:
    - Telemetry reporting via CusReporter
    - Call context management
    - Error tracking
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[CusProviderConfig] = None,
        **client_kwargs,
    ):
        """Initialize the provider adapter.

        Args:
            api_key: API key for the LLM provider
            config: Provider configuration (uses defaults if not provided)
            **client_kwargs: Additional arguments passed to native SDK client
        """
        self._api_key = api_key
        self._config = config or CusProviderConfig()
        self._client_kwargs = client_kwargs

        # Create native client
        self._client: T = self._create_client(api_key, **client_kwargs)

        # Create telemetry reporter
        self._reporter: Optional[CusReporter] = None
        if self._config.auto_report and self._config.integration_key:
            self._reporter = CusReporter(
                integration_key=self._config.integration_key,
                base_url=self._config.base_url,
            )
            if self._config.batch_telemetry:
                self._reporter.enable_batching(
                    max_size=self._config.batch_size,
                    flush_interval_seconds=self._config.batch_interval,
                )

        # Provider status
        self._status = CusProviderStatus.READY
        self._last_error: Optional[str] = None
        self._call_count: int = 0
        self._error_count: int = 0

    # =========================================================================
    # ABSTRACT METHODS (must be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    def _create_client(self, api_key: str, **kwargs) -> T:
        """Create the native SDK client.

        Args:
            api_key: API key for the provider
            **kwargs: Additional client configuration

        Returns:
            Native SDK client instance
        """
        pass

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'openai')."""
        pass

    @abstractmethod
    def _extract_usage(self, response: Any) -> tuple[int, int]:
        """Extract token counts from response.

        Args:
            response: Native SDK response object

        Returns:
            Tuple of (tokens_in, tokens_out)
        """
        pass

    @abstractmethod
    def _calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> int:
        """Calculate cost in cents for a call.

        Args:
            model: Model name
            tokens_in: Input tokens
            tokens_out: Output tokens

        Returns:
            Cost in cents
        """
        pass

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def client(self) -> T:
        """Access the underlying native SDK client."""
        return self._client

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return self._get_provider_name()

    @property
    def status(self) -> CusProviderStatus:
        """Get current provider status."""
        return self._status

    @property
    def is_ready(self) -> bool:
        """Check if provider is ready for calls."""
        return self._status == CusProviderStatus.READY

    @property
    def call_count(self) -> int:
        """Get total number of calls made."""
        return self._call_count

    @property
    def error_count(self) -> int:
        """Get total number of errors."""
        return self._error_count

    @property
    def error_rate(self) -> float:
        """Get error rate as percentage."""
        if self._call_count == 0:
            return 0.0
        return (self._error_count / self._call_count) * 100

    # =========================================================================
    # CALL EXECUTION
    # =========================================================================

    def _create_call_context(self, model: str, **kwargs) -> CusCallContext:
        """Create a call context for tracking."""
        return CusCallContext(
            call_id=generate_call_id(),
            provider=self.provider_name,
            model=model,
            session_id=self._config.session_id,
            agent_id=self._config.agent_id,
            metadata=kwargs.get("metadata", {}),
        )

    def _report_call(self, ctx: CusCallContext) -> None:
        """Report call telemetry."""
        if self._reporter and self._config.auto_report:
            try:
                self._reporter.report(ctx.to_usage_record())
            except Exception as e:
                logger.warning(f"Failed to report telemetry: {e}")

        # Call completion callback if configured
        if self._config.on_call_complete:
            try:
                self._config.on_call_complete(ctx)
            except Exception as e:
                logger.warning(f"Call completion callback failed: {e}")

    def _execute_with_telemetry(
        self,
        model: str,
        execute_fn: Callable[[], Any],
        **kwargs,
    ) -> Any:
        """Execute an LLM call with telemetry capture.

        Phase 3: Captures telemetry only, does NOT block or enforce limits.

        Args:
            model: Model being called
            execute_fn: Function that executes the actual API call
            **kwargs: Additional context for telemetry

        Returns:
            Response from the LLM API
        """
        ctx = self._create_call_context(model, **kwargs)
        self._call_count += 1

        # Execute the call
        ctx.start_time = time.perf_counter()
        try:
            response = execute_fn()
            ctx.end_time = time.perf_counter()

            # Extract usage from response
            ctx.tokens_in, ctx.tokens_out = self._extract_usage(response)
            ctx.cost_cents = self._calculate_cost(model, ctx.tokens_in, ctx.tokens_out)

            # Update status
            self._status = CusProviderStatus.READY
            self._last_error = None

            return response

        except Exception as e:
            ctx.end_time = time.perf_counter()
            ctx.error_code = type(e).__name__
            ctx.error_message = str(e)[:500]
            self._error_count += 1

            # Update status based on error rate
            if self.error_rate > 50:
                self._status = CusProviderStatus.UNAVAILABLE
            elif self.error_rate > 10:
                self._status = CusProviderStatus.DEGRADED
            self._last_error = str(e)

            raise

        finally:
            # Always report telemetry (visibility, not control)
            self._report_call(ctx)

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    def flush(self) -> None:
        """Flush any pending telemetry reports."""
        if self._reporter:
            self._reporter.flush()

    def close(self) -> None:
        """Close the provider and release resources."""
        self.flush()
        if self._reporter:
            self._reporter.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics.

        Returns:
            Dict with call counts, error rates, and status.
        """
        return {
            "provider": self.provider_name,
            "status": self._status.value,
            "call_count": self._call_count,
            "error_count": self._error_count,
            "error_rate": self.error_rate,
            "last_error": self._last_error,
        }
