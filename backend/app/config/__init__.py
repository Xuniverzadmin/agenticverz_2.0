# Configuration module
"""
Runtime configuration and feature flags.

Usage:
    from app.config import get_feature_flag, is_flag_enabled

    if is_flag_enabled("failure_catalog_runtime_integration"):
        # Use enriched error handling
        pass
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.config")

_FLAGS_PATH = Path(__file__).parent / "feature_flags.json"
_flags_cache: Optional[Dict[str, Any]] = None


def _load_flags() -> Dict[str, Any]:
    """Load feature flags from JSON file."""
    global _flags_cache
    if _flags_cache is not None:
        return _flags_cache

    if not _FLAGS_PATH.exists():
        logger.warning(f"Feature flags file not found at {_FLAGS_PATH}")
        _flags_cache = {"flags": {}, "environments": {}}
        return _flags_cache

    try:
        with open(_FLAGS_PATH, "r") as f:
            _flags_cache = json.load(f)
        logger.info(f"Loaded feature flags v{_flags_cache.get('version', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to load feature flags: {e}")
        _flags_cache = {"flags": {}, "environments": {}}

    return _flags_cache


def get_environment() -> str:
    """Get current environment from ENV var or default to development."""
    return os.environ.get("AOS_ENV", "development").lower()


def get_feature_flag(flag_name: str) -> Dict[str, Any]:
    """
    Get full feature flag configuration.

    Args:
        flag_name: Name of the flag

    Returns:
        Flag configuration dict or empty dict if not found
    """
    flags = _load_flags()
    return flags.get("flags", {}).get(flag_name, {})


def is_flag_enabled(flag_name: str, environment: Optional[str] = None) -> bool:
    """
    Check if a feature flag is enabled.

    Checks environment-specific override first, then falls back to flag default.

    Args:
        flag_name: Name of the flag
        environment: Override environment (default: from AOS_ENV)

    Returns:
        True if flag is enabled, False otherwise
    """
    flags = _load_flags()
    env = environment or get_environment()

    # Check environment-specific override
    env_flags = flags.get("environments", {}).get(env, {})
    if flag_name in env_flags:
        return env_flags[flag_name]

    # Fall back to flag default
    flag_config = flags.get("flags", {}).get(flag_name, {})
    return flag_config.get("enabled", False)


def requires_m4_signoff(flag_name: str) -> bool:
    """Check if a flag requires M4 signoff before enabling."""
    flag_config = get_feature_flag(flag_name)
    return flag_config.get("requires_m4_signoff", True)


def reload_flags() -> None:
    """Force reload of feature flags from disk."""
    global _flags_cache
    _flags_cache = None
    _load_flags()
