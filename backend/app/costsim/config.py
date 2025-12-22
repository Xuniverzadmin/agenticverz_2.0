# CostSim V2 Configuration (M6)
"""
Feature flags and configuration for CostSim V2 sandbox.

Environment Variables:
- COSTSIM_V2_SANDBOX: Enable V2 sandbox path (default: false)
- COSTSIM_V2_AUTO_DISABLE: Enable auto-disable on drift (default: true)
- COSTSIM_DRIFT_THRESHOLD: Max acceptable drift score (default: 0.2)
- COSTSIM_CANARY_ENABLED: Enable daily canary runner (default: true)
- ALERTMANAGER_URL: Alertmanager API endpoint for alerts
- INSTANCE_ID: Instance identifier for alerts
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("nova.costsim.config")


@dataclass
class CostSimConfig:
    """Configuration for CostSim V2."""

    # Feature Flags
    v2_sandbox_enabled: bool = False
    auto_disable_enabled: bool = True
    canary_enabled: bool = True

    # Thresholds
    drift_threshold: float = 0.2  # P1 alert threshold
    drift_warning_threshold: float = 0.15  # P2 warning threshold
    schema_error_threshold: int = 5  # P3 schema error count

    # Circuit Breaker
    failure_threshold: int = 3  # Consecutive failures to trip
    auto_recover_enabled: bool = True  # Auto-recover after TTL expires
    default_disable_ttl_hours: int = 24  # Default TTL for disables

    # Provenance
    provenance_enabled: bool = True
    provenance_compress: bool = True  # Compress JSON payloads

    # Paths (legacy, for backward compatibility)
    disable_file_path: str = "/var/lib/aos/costsim_v2_disabled"
    incident_dir: str = "/var/lib/aos/costsim_incidents"
    artifacts_dir: str = "/var/lib/aos/costsim_artifacts"

    # Alertmanager
    alertmanager_url: Optional[str] = None
    alertmanager_timeout_seconds: int = 10
    alertmanager_retry_attempts: int = 3
    alertmanager_retry_delay_seconds: float = 1.0

    # Instance identification
    instance_id: str = "aos-unknown"

    # Versioning
    adapter_version: str = "2.0.0"
    model_version: str = "2.0.0"

    # Database
    v2_table_prefix: str = "costsim_v2_"
    use_db_circuit_breaker: bool = True  # Use DB-backed circuit breaker

    @classmethod
    def from_env(cls) -> "CostSimConfig":
        """Load configuration from environment variables."""
        return cls(
            v2_sandbox_enabled=os.getenv("COSTSIM_V2_SANDBOX", "false").lower() == "true",
            auto_disable_enabled=os.getenv("COSTSIM_V2_AUTO_DISABLE", "true").lower() == "true",
            canary_enabled=os.getenv("COSTSIM_CANARY_ENABLED", "true").lower() == "true",
            drift_threshold=float(os.getenv("COSTSIM_DRIFT_THRESHOLD", "0.2")),
            drift_warning_threshold=float(os.getenv("COSTSIM_DRIFT_WARNING_THRESHOLD", "0.15")),
            schema_error_threshold=int(os.getenv("COSTSIM_SCHEMA_ERROR_THRESHOLD", "5")),
            failure_threshold=int(os.getenv("COSTSIM_FAILURE_THRESHOLD", "3")),
            auto_recover_enabled=os.getenv("COSTSIM_AUTO_RECOVER", "true").lower() == "true",
            default_disable_ttl_hours=int(os.getenv("COSTSIM_DISABLE_TTL_HOURS", "24")),
            provenance_enabled=os.getenv("COSTSIM_PROVENANCE_ENABLED", "true").lower() == "true",
            provenance_compress=os.getenv("COSTSIM_PROVENANCE_COMPRESS", "true").lower() == "true",
            disable_file_path=os.getenv("COSTSIM_DISABLE_FILE", "/var/lib/aos/costsim_v2_disabled"),
            incident_dir=os.getenv("COSTSIM_INCIDENT_DIR", "/var/lib/aos/costsim_incidents"),
            artifacts_dir=os.getenv("COSTSIM_ARTIFACTS_DIR", "/var/lib/aos/costsim_artifacts"),
            alertmanager_url=os.getenv("ALERTMANAGER_URL"),
            alertmanager_timeout_seconds=int(os.getenv("ALERTMANAGER_TIMEOUT", "10")),
            alertmanager_retry_attempts=int(os.getenv("ALERTMANAGER_RETRY_ATTEMPTS", "3")),
            alertmanager_retry_delay_seconds=float(os.getenv("ALERTMANAGER_RETRY_DELAY", "1.0")),
            instance_id=os.getenv("INSTANCE_ID", os.getenv("HOSTNAME", "aos-unknown")),
            adapter_version=os.getenv("COSTSIM_ADAPTER_VERSION", "2.0.0"),
            model_version=os.getenv("COSTSIM_MODEL_VERSION", "2.0.0"),
            use_db_circuit_breaker=os.getenv("COSTSIM_USE_DB_CB", "true").lower() == "true",
        )


# Global config instance
_config: Optional[CostSimConfig] = None


def get_config() -> CostSimConfig:
    """Get the global CostSim configuration."""
    global _config
    if _config is None:
        _config = CostSimConfig.from_env()
    return _config


def is_v2_sandbox_enabled() -> bool:
    """
    Check if V2 sandbox is enabled.

    Returns False if:
    - COSTSIM_V2_SANDBOX != true
    - Disable file exists (auto-disabled due to drift)
    """
    config = get_config()

    if not config.v2_sandbox_enabled:
        return False

    # Check for auto-disable file
    if os.path.exists(config.disable_file_path):
        logger.warning("CostSim V2 disabled via disable file")
        return False

    return True


def is_v2_disabled_by_drift() -> bool:
    """Check if V2 was auto-disabled due to drift."""
    config = get_config()
    return os.path.exists(config.disable_file_path)


def get_commit_sha() -> str:
    """Get current git commit SHA."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except Exception:
        pass
    return os.getenv("GIT_COMMIT_SHA", "unknown")
