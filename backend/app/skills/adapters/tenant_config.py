# Per-Tenant LLM Configuration (M11)
# Layer: L3 — Boundary Adapter
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: async
# Role: Tenant LLM configuration adapter
# Callers: llm_invoke skills
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: PIN-254 Phase B Fix
"""
Per-tenant LLM model configuration for cost optimization and rate limiting.

B05 FIX: Model selection policy moved to L4 LLMPolicyEngine.
This adapter provides tenant configuration data but delegates
policy decisions to L4.

Allows tenants to:
- Override default model (e.g., use gpt-4o-mini instead of Claude)
- Set per-tenant rate limits
- Set per-tenant budget limits
- Configure model preferences

Configuration can come from:
1. Environment variables (TENANT_{ID}_LLM_MODEL, etc.)
2. Vault secrets (agenticverz/tenants/{id}/llm)
3. Database (tenant_llm_configs table)

Environment Variables:
- TENANT_LLM_CONFIG_SOURCE: env|vault|database (default: env)
- DEFAULT_LLM_MODEL: Default model for all tenants
- DEFAULT_TENANT_RATE_LIMIT: Default requests per minute (default: 60)
- DEFAULT_TENANT_BUDGET_CENTS: Default monthly budget in cents (default: 100000)
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("nova.adapters.tenant_config")


@dataclass
class TenantLLMConfig:
    """LLM configuration for a specific tenant."""

    tenant_id: str

    # Model selection
    preferred_model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "gpt-4o-mini"
    allowed_models: List[str] = field(
        default_factory=lambda: [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "gpt-4o",
            "gpt-4o-mini",
        ]
    )

    # Rate limits
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000

    # Budget limits (in cents)
    monthly_budget_cents: int = 100000  # $1000 default
    max_cost_per_request_cents: float = 50.0

    # Feature flags
    allow_expensive_models: bool = False  # gpt-4, claude-opus
    use_fallback_on_budget_exceeded: bool = True

    def get_effective_model(self, requested_model: Optional[str] = None) -> str:
        """
        Get effective model based on tenant config and request.

        B05 FIX: Delegates to L4 LLMPolicyEngine.get_effective_model().
        L3 no longer contains model selection policy logic.
        """
        from app.services.llm_policy_engine import get_effective_model

        return get_effective_model(
            requested_model=requested_model,
            preferred_model=self.preferred_model,
            fallback_model=self.fallback_model,
            allowed_models=self.allowed_models,
        )

    def is_model_allowed(self, model: str) -> bool:
        """Check if model is allowed for this tenant."""
        return model in self.allowed_models


# =============================================================================
# Configuration Cache
# =============================================================================

_tenant_configs: Dict[str, TenantLLMConfig] = {}
_default_config: Optional[TenantLLMConfig] = None


def _load_config_from_env(tenant_id: str) -> Optional[TenantLLMConfig]:
    """Load tenant config from environment variables."""
    prefix = f"TENANT_{tenant_id.upper().replace('-', '_')}_"

    # Check if any tenant-specific env vars exist
    preferred_model = os.getenv(f"{prefix}LLM_MODEL")
    if not preferred_model:
        return None

    return TenantLLMConfig(
        tenant_id=tenant_id,
        preferred_model=preferred_model,
        fallback_model=os.getenv(f"{prefix}LLM_FALLBACK_MODEL", "gpt-4o-mini"),
        requests_per_minute=int(os.getenv(f"{prefix}RATE_LIMIT", "60")),
        monthly_budget_cents=int(os.getenv(f"{prefix}BUDGET_CENTS", "100000")),
        max_cost_per_request_cents=float(os.getenv(f"{prefix}MAX_COST_PER_REQUEST", "50")),
        allow_expensive_models=os.getenv(f"{prefix}ALLOW_EXPENSIVE", "").lower() == "true",
    )


async def _load_config_from_vault(tenant_id: str) -> Optional[TenantLLMConfig]:
    """Load tenant config from Vault."""
    try:
        import httpx

        vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        vault_token = os.getenv("VAULT_TOKEN", "")

        if not vault_token:
            return None

        path = f"agenticverz/data/tenants/{tenant_id}/llm"
        url = f"{vault_addr}/v1/{path}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={"X-Vault-Token": vault_token})

            if response.status_code != 200:
                return None

            data = response.json().get("data", {}).get("data", {})

            return TenantLLMConfig(
                tenant_id=tenant_id,
                preferred_model=data.get("preferred_model", "claude-sonnet-4-20250514"),
                fallback_model=data.get("fallback_model", "gpt-4o-mini"),
                requests_per_minute=int(data.get("requests_per_minute", 60)),
                monthly_budget_cents=int(data.get("monthly_budget_cents", 100000)),
                max_cost_per_request_cents=float(data.get("max_cost_per_request_cents", 50)),
                allow_expensive_models=data.get("allow_expensive_models", False),
            )

    except Exception as e:
        logger.debug(f"Could not load tenant config from Vault: {e}")
        return None


def get_default_config() -> TenantLLMConfig:
    """Get default tenant config."""
    global _default_config

    if _default_config is None:
        _default_config = TenantLLMConfig(
            tenant_id="default",
            preferred_model=os.getenv("DEFAULT_LLM_MODEL", "claude-sonnet-4-20250514"),
            fallback_model=os.getenv("DEFAULT_LLM_FALLBACK_MODEL", "gpt-4o-mini"),
            requests_per_minute=int(os.getenv("DEFAULT_TENANT_RATE_LIMIT", "60")),
            monthly_budget_cents=int(os.getenv("DEFAULT_TENANT_BUDGET_CENTS", "100000")),
        )

    return _default_config


async def get_tenant_config(tenant_id: Optional[str] = None) -> TenantLLMConfig:
    """
    Get LLM configuration for a tenant.

    Args:
        tenant_id: Tenant identifier (uses "default" if not provided)

    Returns:
        TenantLLMConfig for the tenant
    """
    if not tenant_id:
        return get_default_config()

    # Check cache
    if tenant_id in _tenant_configs:
        return _tenant_configs[tenant_id]

    # Try loading from configured source
    config_source = os.getenv("TENANT_LLM_CONFIG_SOURCE", "env").lower()

    config = None

    if config_source == "env":
        config = _load_config_from_env(tenant_id)
    elif config_source == "vault":
        config = await _load_config_from_vault(tenant_id)
    # Database source would go here

    if config is None:
        # Use default config with tenant_id
        config = TenantLLMConfig(
            tenant_id=tenant_id,
            preferred_model=get_default_config().preferred_model,
            fallback_model=get_default_config().fallback_model,
            requests_per_minute=get_default_config().requests_per_minute,
            monthly_budget_cents=get_default_config().monthly_budget_cents,
        )

    # Cache it
    _tenant_configs[tenant_id] = config
    logger.debug(f"Loaded config for tenant {tenant_id}: model={config.preferred_model}")

    return config


def reset_config_cache():
    """Reset config cache. For testing."""
    global _tenant_configs, _default_config
    _tenant_configs.clear()
    _default_config = None


# =============================================================================
# Tenant Model Selector
# =============================================================================


async def get_model_for_tenant(
    tenant_id: Optional[str] = None, requested_model: Optional[str] = None, task_type: str = "default"
) -> str:
    """
    Get the appropriate model for a tenant and task.

    B05 FIX: Delegates to L4 LLMPolicyEngine.get_model_for_task().
    L3 no longer contains task-based model selection policy logic.

    Args:
        tenant_id: Tenant identifier
        requested_model: Model explicitly requested by the caller
        task_type: Type of task (planning, execution, etc.) for model selection

    Returns:
        Model identifier to use
    """
    from app.services.llm_policy_engine import get_model_for_task

    config = await get_tenant_config(tenant_id)

    return get_model_for_task(
        task_type=task_type,
        requested_model=requested_model,
        tenant_allowed_models=config.allowed_models,
        allow_expensive=config.allow_expensive_models,
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TenantLLMConfig",
    "get_tenant_config",
    "get_default_config",
    "get_model_for_tenant",
    "reset_config_cache",
]
