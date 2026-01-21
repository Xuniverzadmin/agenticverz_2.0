"""
AOS SDK - Python SDK for the Agentic Operating System

The most predictable, reliable, deterministic SDK for building machine-native agents.

Core Classes:
    AOSClient: HTTP client for AOS API
    RuntimeContext: Deterministic runtime context (seed, time, RNG)
    Trace: Execution trace for replay and verification

Usage:
    from aos_sdk import AOSClient, RuntimeContext, Trace

    # Deterministic simulation
    ctx = RuntimeContext(seed=42, now="2025-12-06T12:00:00Z")
    client = AOSClient()
    result = client.simulate(plan, seed=ctx.seed)

    # Trace and replay
    trace = Trace(seed=42, plan=plan)
    trace.add_step(...)
    trace.finalize()
    trace.save("run.trace.json")
"""

from .client import AOSClient, AOSError, SafetyBlockedError

# Attribution Enforcement (Phase 3)
from .attribution import (
    ActorType,
    AttributionContext,
    AttributionError,
    AttributionErrorCode,
    EnforcementMode,
    create_human_attribution,
    create_service_attribution,
    create_system_attribution,
    get_enforcement_mode,
    is_legacy_override_enabled,
    validate_attribution,
)

# Customer Integrations - Phase 2: Telemetry Reporter
from .cus_reporter import (
    CusCallTracker,
    CusLimitsStatus,
    CusPolicyResult,
    CusReporter,
    CusUsageRecord,
    calculate_anthropic_cost,
    calculate_openai_cost,
    generate_call_id,
)

# Customer Integrations - Phase 3: Provider Adapters
from .cus_base import (
    CusBaseProvider,
    CusCallContext,
    CusProviderConfig,
    CusProviderError,
    CusProviderStatus,
)
from .cus_token_counter import (
    count_tokens,
    estimate_tokens,
    get_context_window,
    get_model_info,
    tiktoken_available,
)
from .cus_cost import (
    CusModelPricing,
    CusPricingTable,
    calculate_cost,
    calculate_cost_breakdown,
    estimate_cost,
    format_cost,
    get_model_pricing,
    get_pricing_version,
)
from .cus_openai import CusOpenAIProvider, create_openai_provider
from .cus_anthropic import CusAnthropicProvider, create_anthropic_provider
from .cus_middleware import (
    configure as cus_configure,
    cus_install_middleware,
    cus_telemetry,
    cus_track,
    cus_wrap,
    get_reporter as cus_get_reporter,
    shutdown as cus_shutdown,
)

from .runtime import RuntimeContext, canonical_json, freeze_time, hash_trace
from .trace import (
    TRACE_SCHEMA_VERSION,
    ReplayResult,
    Trace,
    TraceStep,
    create_trace_from_context,
    diff_traces,
    generate_idempotency_key,
    hash_data,
    is_idempotency_key_executed,
    mark_idempotency_key_executed,
    replay_step,
    reset_idempotency_state,
)

__version__ = "0.1.0"
__all__ = [
    # Client
    "AOSClient",
    "AOSError",
    "SafetyBlockedError",
    # Attribution Enforcement (Phase 3)
    "ActorType",
    "AttributionContext",
    "AttributionError",
    "AttributionErrorCode",
    "EnforcementMode",
    "create_human_attribution",
    "create_service_attribution",
    "create_system_attribution",
    "get_enforcement_mode",
    "is_legacy_override_enabled",
    "validate_attribution",
    # Customer Integrations - Phase 2: Telemetry Reporter
    "CusReporter",
    "CusUsageRecord",
    "CusCallTracker",
    "CusLimitsStatus",
    "CusPolicyResult",
    "calculate_openai_cost",
    "calculate_anthropic_cost",
    "generate_call_id",
    # Customer Integrations - Phase 3: Provider Base
    "CusBaseProvider",
    "CusCallContext",
    "CusProviderConfig",
    "CusProviderError",
    "CusProviderStatus",
    # Customer Integrations - Phase 3: Token Counting
    "count_tokens",
    "estimate_tokens",
    "get_context_window",
    "get_model_info",
    "tiktoken_available",
    # Customer Integrations - Phase 3: Cost Calculation
    "CusModelPricing",
    "CusPricingTable",
    "calculate_cost",
    "calculate_cost_breakdown",
    "estimate_cost",
    "format_cost",
    "get_model_pricing",
    "get_pricing_version",
    # Customer Integrations - Phase 3: Provider Adapters
    "CusOpenAIProvider",
    "create_openai_provider",
    "CusAnthropicProvider",
    "create_anthropic_provider",
    # Customer Integrations - Phase 3: Middleware
    "cus_configure",
    "cus_install_middleware",
    "cus_telemetry",
    "cus_track",
    "cus_wrap",
    "cus_get_reporter",
    "cus_shutdown",
    # Runtime
    "RuntimeContext",
    "canonical_json",
    "hash_trace",
    "freeze_time",
    # Trace
    "Trace",
    "TraceStep",
    "diff_traces",
    "hash_data",
    "create_trace_from_context",
    "TRACE_SCHEMA_VERSION",
    # Replay & Idempotency
    "ReplayResult",
    "replay_step",
    "generate_idempotency_key",
    "reset_idempotency_state",
    "mark_idempotency_key_executed",
    "is_idempotency_key_executed",
    # Version
    "__version__",
]
