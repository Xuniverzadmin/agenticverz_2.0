"""
Centralized Secret Access Module
================================

INVARIANT: No script or module should call os.environ.get() for secrets directly.
           All secret access MUST go through this module.

This module provides:
1. Typed accessors for all secrets
2. Validation at access time (fail-fast)
3. Clear categorization (REQUIRED vs OPTIONAL)
4. Startup invariant checking

Usage:
    from app.config.secrets import Secrets

    # Get required secret (raises if missing)
    key = Secrets.openai_api_key()

    # Check if secret is available
    if Secrets.has_openai():
        key = Secrets.openai_api_key()

    # Startup validation
    from app.config.secrets import validate_required_secrets
    validate_required_secrets()  # Called at app startup
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("nova.secrets")


class SecretMissingError(Exception):
    """Raised when a required secret is not configured."""

    pass


class SecretValidationError(Exception):
    """Raised when secrets validation fails at startup."""

    pass


def _load_dotenv_if_exists() -> None:
    """Load .env file if it exists and python-dotenv is available."""
    try:
        from dotenv import load_dotenv

        # Check multiple locations
        env_paths = [
            Path("/root/agenticverz2.0/.env"),
            Path("/root/agenticverz2.0/backend/.env"),
            Path.cwd() / ".env",
        ]

        for env_path in env_paths:
            try:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.debug(f"Loaded environment from {env_path}")
                    return
            except PermissionError:
                # Path exists but not accessible (e.g., running in container)
                continue

    except ImportError:
        pass  # python-dotenv not installed, rely on environment


# Load .env on module import
_load_dotenv_if_exists()


class Secrets:
    """
    Centralized secret accessor.

    Categories:
    - REQUIRED: App cannot function without these
    - BILLING: Required for cost/billing features (M26)
    - EXTERNAL: Third-party integrations
    - OPTIONAL: Has sensible defaults
    """

    # =========================================================================
    # REQUIRED SECRETS - App crashes without these
    # =========================================================================

    @staticmethod
    def database_url() -> str:
        """PostgreSQL connection string. REQUIRED."""
        val = os.environ.get("DATABASE_URL")
        if not val:
            raise SecretMissingError("DATABASE_URL is required. " "Set it in .env or environment.")
        return val

    @staticmethod
    def redis_url() -> str:
        """Redis connection string. REQUIRED for queue operations."""
        val = os.environ.get("REDIS_URL")
        if not val:
            raise SecretMissingError("REDIS_URL is required. " "Set it in .env or environment.")
        return val

    @staticmethod
    def aos_api_key() -> str:
        """Internal API key for service authentication. REQUIRED."""
        val = os.environ.get("AOS_API_KEY")
        if not val:
            raise SecretMissingError(
                "AOS_API_KEY is required. " 'Generate with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return val

    # =========================================================================
    # BILLING SECRETS - Required for M26 cost features
    # =========================================================================

    @staticmethod
    def openai_api_key() -> str:
        """OpenAI API key. REQUIRED for LLM operations."""
        val = os.environ.get("OPENAI_API_KEY")
        if not val:
            raise SecretMissingError(
                "OPENAI_API_KEY is required for LLM operations. " "Get one at https://platform.openai.com/api-keys"
            )
        return val

    @staticmethod
    def has_openai() -> bool:
        """Check if OpenAI key is configured."""
        return bool(os.environ.get("OPENAI_API_KEY"))

    @staticmethod
    def anthropic_api_key() -> str:
        """Anthropic API key. REQUIRED for Claude operations."""
        val = os.environ.get("ANTHROPIC_API_KEY")
        if not val:
            raise SecretMissingError(
                "ANTHROPIC_API_KEY is required for Claude operations. " "Get one at https://console.anthropic.com/"
            )
        return val

    @staticmethod
    def has_anthropic() -> bool:
        """Check if Anthropic key is configured."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    @staticmethod
    def voyage_api_key() -> str:
        """Voyage AI API key for embeddings."""
        val = os.environ.get("VOYAGE_API_KEY")
        if not val:
            raise SecretMissingError(
                "VOYAGE_API_KEY is required for embeddings. " "Get one at https://www.voyageai.com/"
            )
        return val

    @staticmethod
    def has_voyage() -> bool:
        """Check if Voyage key is configured."""
        return bool(os.environ.get("VOYAGE_API_KEY"))

    # =========================================================================
    # EXTERNAL INTEGRATION SECRETS
    # =========================================================================

    @staticmethod
    def vault_token() -> str:
        """HashiCorp Vault token for secrets management."""
        val = os.environ.get("VAULT_TOKEN") or os.environ.get("VAULT_ROOT_TOKEN")
        if not val:
            raise SecretMissingError("VAULT_TOKEN or VAULT_ROOT_TOKEN is required for Vault access.")
        return val

    @staticmethod
    def has_vault() -> bool:
        """Check if Vault is configured."""
        return bool(os.environ.get("VAULT_TOKEN") or os.environ.get("VAULT_ROOT_TOKEN"))

    @staticmethod
    def vault_addr() -> str:
        """Vault server address."""
        return os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")

    @staticmethod
    def r2_access_key() -> str:
        """Cloudflare R2 access key."""
        val = os.environ.get("R2_ACCESS_KEY_ID")
        if not val:
            raise SecretMissingError("R2_ACCESS_KEY_ID is required for R2 storage.")
        return val

    @staticmethod
    def r2_secret_key() -> str:
        """Cloudflare R2 secret key."""
        val = os.environ.get("R2_SECRET_ACCESS_KEY")
        if not val:
            raise SecretMissingError("R2_SECRET_ACCESS_KEY is required for R2 storage.")
        return val

    @staticmethod
    def has_r2() -> bool:
        """Check if R2 is configured."""
        return bool(os.environ.get("R2_ACCESS_KEY_ID") and os.environ.get("R2_SECRET_ACCESS_KEY"))

    @staticmethod
    def slack_webhook_url() -> Optional[str]:
        """Slack webhook for notifications. Optional."""
        return os.environ.get("SLACK_WEBHOOK_URL")

    @staticmethod
    def has_slack() -> bool:
        """Check if Slack is configured."""
        return bool(os.environ.get("SLACK_WEBHOOK_URL"))

    @staticmethod
    def posthog_api_key() -> Optional[str]:
        """PostHog API key for analytics. Optional."""
        return os.environ.get("POSTHOG_API_KEY")

    @staticmethod
    def has_posthog() -> bool:
        """Check if PostHog is configured."""
        return bool(os.environ.get("POSTHOG_API_KEY"))

    @staticmethod
    def resend_api_key() -> Optional[str]:
        """Resend API key for email. Optional."""
        return os.environ.get("RESEND_API_KEY")

    @staticmethod
    def has_resend() -> bool:
        """Check if Resend is configured."""
        return bool(os.environ.get("RESEND_API_KEY"))

    # =========================================================================
    # AUTH SECRETS
    # =========================================================================

    @staticmethod
    def google_client_id() -> str:
        """Google OAuth client ID."""
        val = os.environ.get("GOOGLE_CLIENT_ID")
        if not val:
            raise SecretMissingError("GOOGLE_CLIENT_ID is required for Google OAuth.")
        return val

    @staticmethod
    def google_client_secret() -> str:
        """Google OAuth client secret."""
        val = os.environ.get("GOOGLE_CLIENT_SECRET")
        if not val:
            raise SecretMissingError("GOOGLE_CLIENT_SECRET is required for Google OAuth.")
        return val

    @staticmethod
    def has_google_oauth() -> bool:
        """Check if Google OAuth is configured."""
        return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))

    @staticmethod
    def azure_client_id() -> str:
        """Azure AD client ID."""
        val = os.environ.get("AZURE_CLIENT_ID")
        if not val:
            raise SecretMissingError("AZURE_CLIENT_ID is required for Azure AD.")
        return val

    @staticmethod
    def azure_tenant_id() -> str:
        """Azure AD tenant ID."""
        val = os.environ.get("AZURE_TENANT_ID")
        if not val:
            raise SecretMissingError("AZURE_TENANT_ID is required for Azure AD.")
        return val

    @staticmethod
    def has_azure_ad() -> bool:
        """Check if Azure AD is configured."""
        return bool(os.environ.get("AZURE_CLIENT_ID") and os.environ.get("AZURE_TENANT_ID"))

    # =========================================================================
    # OPTIONAL SECRETS WITH DEFAULTS
    # =========================================================================

    @staticmethod
    def aos_env() -> str:
        """Environment name. Defaults to 'development'."""
        return os.environ.get("AOS_ENV", "development").lower()

    @staticmethod
    def is_production() -> bool:
        """Check if running in production."""
        return Secrets.aos_env() in ("production", "prod")

    @staticmethod
    def log_level() -> str:
        """Logging level. Defaults to INFO."""
        return os.environ.get("LOG_LEVEL", "INFO").upper()


# =============================================================================
# STARTUP VALIDATION
# =============================================================================

# Secrets required for app to start
REQUIRED_FOR_STARTUP = [
    ("DATABASE_URL", "PostgreSQL database connection"),
    ("REDIS_URL", "Redis for queues and caching"),
]

# Secrets required for billing/cost features (M26)
REQUIRED_FOR_BILLING = [
    ("OPENAI_API_KEY", "OpenAI API for LLM operations"),
]

# Secrets that should warn if missing
WARN_IF_MISSING = [
    ("ANTHROPIC_API_KEY", "Anthropic Claude API"),
    ("VAULT_TOKEN", "HashiCorp Vault"),
    ("VOYAGE_API_KEY", "Voyage AI embeddings"),
]


def validate_required_secrets(include_billing: bool = True, hard_fail: bool = True) -> Tuple[bool, List[str]]:
    """
    Validate that all required secrets are present.

    Call this at application startup.

    Args:
        include_billing: Also check billing-required secrets
        hard_fail: Raise exception if validation fails

    Returns:
        Tuple of (success, list of missing secrets)

    Raises:
        SecretValidationError: If hard_fail=True and secrets are missing
    """
    missing = []
    warnings = []

    # Check startup requirements
    for env_var, description in REQUIRED_FOR_STARTUP:
        if not os.environ.get(env_var):
            missing.append(f"{env_var} ({description})")

    # Check billing requirements
    if include_billing:
        for env_var, description in REQUIRED_FOR_BILLING:
            if not os.environ.get(env_var):
                missing.append(f"{env_var} ({description})")

    # Check warnings
    for env_var, description in WARN_IF_MISSING:
        if not os.environ.get(env_var):
            warnings.append(f"{env_var} ({description})")

    # Log warnings
    for w in warnings:
        logger.warning(f"Secret not configured: {w}")

    # Handle missing required
    if missing:
        msg = "Required secrets missing:\n" + "\n".join(f"  - {m}" for m in missing)
        logger.error(msg)

        if hard_fail:
            raise SecretValidationError(msg)

        return False, missing

    logger.info("All required secrets validated successfully")
    return True, []


def get_secret_status() -> dict:
    """
    Get status of all known secrets for diagnostics.

    Returns dict with secret names and their status (configured/missing).
    Never returns actual values.
    """
    all_secrets = (
        REQUIRED_FOR_STARTUP
        + REQUIRED_FOR_BILLING
        + WARN_IF_MISSING
        + [
            ("R2_ACCESS_KEY_ID", "Cloudflare R2"),
            ("SLACK_WEBHOOK_URL", "Slack notifications"),
            ("POSTHOG_API_KEY", "PostHog analytics"),
            ("RESEND_API_KEY", "Resend email"),
            ("GOOGLE_CLIENT_ID", "Google OAuth"),
            ("AZURE_CLIENT_ID", "Azure AD"),
        ]
    )

    return {
        env_var: {
            "status": "configured" if os.environ.get(env_var) else "missing",
            "description": description,
            "required": env_var in [s[0] for s in REQUIRED_FOR_STARTUP + REQUIRED_FOR_BILLING],
        }
        for env_var, description in all_secrets
    }
