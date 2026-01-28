"""
Customer Integration Telemetry Middleware

PURPOSE:
    Middleware for automatically capturing telemetry from LLM calls.
    Can be used as decorators, context managers, or call wrappers.

SEMANTIC:
    Phase 3 scope: VISIBILITY ONLY, NO CONTROL.

    Middleware captures and reports telemetry:
    - Does NOT block calls
    - Does NOT throttle
    - Does NOT enforce limits

    Control/enforcement is Phase 5.

USAGE PATTERNS:

    1. Decorator pattern:
        @cus_telemetry(model="gpt-4o")
        def my_llm_function(prompt):
            return openai.chat.completions.create(...)

    2. Context manager pattern:
        with cus_track("gpt-4o") as tracker:
            response = openai.chat.completions.create(...)
            tracker.set_usage(response.usage)

    3. Wrapper pattern:
        response = cus_wrap(
            lambda: openai.chat.completions.create(...),
            model="gpt-4o",
        )

    4. Global middleware (patches SDK clients):
        cus_install_middleware()  # Call once at startup
        # All subsequent SDK calls are automatically tracked

Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
"""

import functools
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from .aos_sdk_cus_cost import calculate_cost
from .aos_sdk_cus_reporter import (
    CusPolicyResult,
    CusReporter,
    CusUsageRecord,
    generate_call_id,
)
from .aos_sdk_cus_token_counter import extract_usage

logger = logging.getLogger(__name__)

# Type variables
F = TypeVar("F", bound=Callable[..., Any])

# =============================================================================
# GLOBAL STATE
# =============================================================================

# Global reporter instance (initialized via configure())
_global_reporter: Optional[CusReporter] = None
_middleware_installed: bool = False


def configure(
    integration_key: Optional[str] = None,
    base_url: Optional[str] = None,
    auto_report: bool = True,
    batch_telemetry: bool = True,
    batch_size: int = 50,
    batch_interval: float = 5.0,
) -> CusReporter:
    """Configure global telemetry middleware.

    Call this once at application startup to enable automatic telemetry.

    Args:
        integration_key: AOS integration key (or CUS_INTEGRATION_KEY env var)
        base_url: AOS API base URL
        auto_report: Whether to auto-report telemetry
        batch_telemetry: Whether to batch telemetry
        batch_size: Max batch size
        batch_interval: Batch flush interval

    Returns:
        Configured CusReporter instance
    """
    global _global_reporter

    key = integration_key or os.getenv("CUS_INTEGRATION_KEY")
    url = base_url or os.getenv("AOS_BASE_URL", "http://127.0.0.1:8000")

    _global_reporter = CusReporter(
        integration_key=key,
        base_url=url,
    )

    if batch_telemetry:
        _global_reporter.enable_batching(
            max_size=batch_size,
            flush_interval_seconds=batch_interval,
        )

    logger.info("CUS telemetry middleware configured")
    return _global_reporter


def get_reporter() -> Optional[CusReporter]:
    """Get the global reporter instance."""
    return _global_reporter


def shutdown():
    """Shutdown and flush the global reporter."""
    global _global_reporter
    if _global_reporter:
        _global_reporter.close()
        _global_reporter = None
        logger.info("CUS telemetry middleware shutdown")


# =============================================================================
# TELEMETRY TRACKER
# =============================================================================


@dataclass
class CusTelemetryTracker:
    """Tracks telemetry for a single LLM call.

    Used as a context manager to capture timing, tokens, and cost.
    """

    model: str
    provider: str = "unknown"
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        self.call_id = generate_call_id()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.tokens_in: int = 0
        self.tokens_out: int = 0
        self.cost_cents: int = 0
        self.error_code: Optional[str] = None
        self.error_message: Optional[str] = None
        self._reported: bool = False

    @property
    def latency_ms(self) -> Optional[int]:
        """Calculate latency in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return None

    def set_usage(
        self,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        cost_cents: Optional[int] = None,
    ) -> "CusTelemetryTracker":
        """Set usage metrics manually.

        Args:
            tokens_in: Input tokens
            tokens_out: Output tokens
            cost_cents: Cost in cents (calculated if not provided)

        Returns:
            Self for chaining
        """
        if tokens_in is not None:
            self.tokens_in = tokens_in
        if tokens_out is not None:
            self.tokens_out = tokens_out
        if cost_cents is not None:
            self.cost_cents = cost_cents
        elif self.tokens_in > 0 or self.tokens_out > 0:
            self.cost_cents = calculate_cost(self.model, self.tokens_in, self.tokens_out)
        return self

    def set_usage_from_response(
        self,
        response: Any,
        provider: Optional[str] = None,
    ) -> "CusTelemetryTracker":
        """Extract and set usage from a provider response.

        Args:
            response: Provider response object
            provider: Provider name (uses self.provider if not specified)

        Returns:
            Self for chaining
        """
        prov = provider or self.provider
        self.tokens_in, self.tokens_out = extract_usage(response, prov)
        self.cost_cents = calculate_cost(self.model, self.tokens_in, self.tokens_out)
        return self

    def set_error(self, error: Exception) -> "CusTelemetryTracker":
        """Set error information from an exception.

        Args:
            error: Exception that occurred

        Returns:
            Self for chaining
        """
        self.error_code = type(error).__name__
        self.error_message = str(error)[:500]
        return self

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
            policy_result=CusPolicyResult.ALLOWED,
            error_code=self.error_code,
            error_message=self.error_message,
            metadata=self.metadata or {},
        )

    def report(self, reporter: Optional[CusReporter] = None) -> bool:
        """Report telemetry.

        Args:
            reporter: Reporter to use (uses global if not specified)

        Returns:
            True if reported successfully
        """
        if self._reported:
            return True

        rep = reporter or _global_reporter
        if not rep:
            logger.warning("No reporter configured - telemetry not reported")
            return False

        try:
            rep.report(self.to_usage_record())
            self._reported = True
            return True
        except Exception as e:
            logger.warning(f"Failed to report telemetry: {e}")
            return False


# =============================================================================
# CONTEXT MANAGER
# =============================================================================


@contextmanager
def cus_track(
    model: str,
    provider: str = "unknown",
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    auto_report: bool = True,
    reporter: Optional[CusReporter] = None,
):
    """Context manager for tracking LLM call telemetry.

    Phase 3: Captures telemetry only, does NOT block.

    Usage:
        with cus_track("gpt-4o", provider="openai") as tracker:
            response = openai.chat.completions.create(...)
            tracker.set_usage_from_response(response, "openai")

    Args:
        model: Model being called
        provider: Provider name
        session_id: Optional session grouping
        agent_id: Optional agent identifier
        auto_report: Whether to auto-report on exit
        reporter: Reporter to use (uses global if not specified)

    Yields:
        CusTelemetryTracker instance
    """
    tracker = CusTelemetryTracker(
        model=model,
        provider=provider,
        session_id=session_id,
        agent_id=agent_id,
    )
    tracker.start_time = time.perf_counter()

    try:
        yield tracker
    except Exception as e:
        tracker.set_error(e)
        raise
    finally:
        tracker.end_time = time.perf_counter()
        if auto_report:
            tracker.report(reporter)


# =============================================================================
# DECORATOR
# =============================================================================


def cus_telemetry(
    model: str,
    provider: str = "unknown",
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    extract_response: bool = True,
    reporter: Optional[CusReporter] = None,
) -> Callable[[F], F]:
    """Decorator for automatic telemetry capture.

    Phase 3: Captures telemetry only, does NOT block.

    Usage:
        @cus_telemetry(model="gpt-4o", provider="openai")
        def my_chat_function(messages):
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )

    Args:
        model: Model being called
        provider: Provider name
        session_id: Optional session grouping
        agent_id: Optional agent identifier
        extract_response: Whether to auto-extract usage from response
        reporter: Reporter to use (uses global if not specified)

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with cus_track(
                model=model,
                provider=provider,
                session_id=session_id,
                agent_id=agent_id,
                auto_report=True,
                reporter=reporter,
            ) as tracker:
                response = func(*args, **kwargs)

                if extract_response and response is not None:
                    try:
                        tracker.set_usage_from_response(response, provider)
                    except Exception as e:
                        logger.debug(f"Could not extract usage from response: {e}")

                return response

        return wrapper  # type: ignore

    return decorator


# =============================================================================
# WRAPPER FUNCTION
# =============================================================================


def cus_wrap(
    func: Callable[[], Any],
    model: str,
    provider: str = "unknown",
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    reporter: Optional[CusReporter] = None,
) -> Any:
    """Wrap a single LLM call with telemetry.

    Phase 3: Captures telemetry only, does NOT block.

    Usage:
        response = cus_wrap(
            lambda: openai.chat.completions.create(model="gpt-4o", messages=messages),
            model="gpt-4o",
            provider="openai",
        )

    Args:
        func: Function that makes the LLM call
        model: Model being called
        provider: Provider name
        session_id: Optional session grouping
        agent_id: Optional agent identifier
        reporter: Reporter to use (uses global if not specified)

    Returns:
        Result from the wrapped function
    """
    with cus_track(
        model=model,
        provider=provider,
        session_id=session_id,
        agent_id=agent_id,
        auto_report=True,
        reporter=reporter,
    ) as tracker:
        response = func()

        if response is not None:
            try:
                tracker.set_usage_from_response(response, provider)
            except Exception:
                pass

        return response


# =============================================================================
# SDK PATCHING (EXPERIMENTAL)
# =============================================================================


def cus_install_middleware(
    patch_openai: bool = True,
    patch_anthropic: bool = True,
) -> bool:
    """Install telemetry middleware by patching SDK clients.

    EXPERIMENTAL: This modifies SDK client classes globally.

    Phase 3: Captures telemetry only, does NOT block.

    Args:
        patch_openai: Whether to patch OpenAI SDK
        patch_anthropic: Whether to patch Anthropic SDK

    Returns:
        True if any SDK was patched
    """
    global _middleware_installed

    if _middleware_installed:
        logger.warning("Middleware already installed")
        return True

    if not _global_reporter:
        logger.warning("Configure middleware first with configure()")
        return False

    patched = False

    if patch_openai:
        patched |= _patch_openai()

    if patch_anthropic:
        patched |= _patch_anthropic()

    _middleware_installed = patched
    return patched


def _patch_openai() -> bool:
    """Patch OpenAI SDK for automatic telemetry."""
    try:
        from openai.resources.chat import completions as chat_completions

        original_create = chat_completions.Completions.create

        def patched_create(self, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            with cus_track(model=model, provider="openai") as tracker:
                response = original_create(self, *args, **kwargs)
                tracker.set_usage_from_response(response, "openai")
                return response

        chat_completions.Completions.create = patched_create
        logger.info("OpenAI SDK patched for telemetry")
        return True

    except ImportError:
        logger.debug("OpenAI SDK not available for patching")
        return False
    except Exception as e:
        logger.warning(f"Failed to patch OpenAI SDK: {e}")
        return False


def _patch_anthropic() -> bool:
    """Patch Anthropic SDK for automatic telemetry."""
    try:
        from anthropic.resources import messages

        original_create = messages.Messages.create

        def patched_create(self, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            with cus_track(model=model, provider="anthropic") as tracker:
                response = original_create(self, *args, **kwargs)
                tracker.set_usage_from_response(response, "anthropic")
                return response

        messages.Messages.create = patched_create
        logger.info("Anthropic SDK patched for telemetry")
        return True

    except ImportError:
        logger.debug("Anthropic SDK not available for patching")
        return False
    except Exception as e:
        logger.warning(f"Failed to patch Anthropic SDK: {e}")
        return False


def cus_uninstall_middleware():
    """Uninstall telemetry middleware.

    Note: This cannot restore original SDK methods.
    Restart the application to fully remove middleware.
    """
    global _middleware_installed
    _middleware_installed = False
    shutdown()
    logger.info("Middleware marked as uninstalled (restart app to fully remove)")
