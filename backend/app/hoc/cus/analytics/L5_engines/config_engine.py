# capability_id: CAP-002
# Layer: L5 — Domain Engine
# NOTE: Renamed config.py → config_engine.py (2026-01-31)
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (environment variables)
#   Writes: none
# Role: Re-export CostSim V2 configuration from hoc_spine (backward compatibility)
# Callers: costsim engine, sandbox runner
# Allowed Imports: hoc_spine services
# Forbidden Imports: L6, L7, sqlalchemy (runtime)
# Reference: PIN-470, PIN-521 (config extraction)

"""
CostSim V2 Configuration - BACKWARD COMPATIBILITY RE-EXPORTS

PIN-521 Migration:
- Canonical home is now hoc_spine/services/costsim_config.py
- This file re-exports for backward compatibility
- L6 drivers MUST import from hoc_spine (not here)
- New code SHOULD import from hoc_spine/services

To migrate existing imports:
    OLD: from app.hoc.cus.analytics.L5_engines.config_engine import get_config
    NEW: from app.hoc.cus.hoc_spine.services.costsim_config import get_config
"""

# Re-export from canonical location (hoc_spine/services)
from app.hoc.cus.hoc_spine.services.costsim_config import (
    CostSimConfig,
    get_commit_sha,
    get_config,
    is_v2_disabled_by_drift,
    is_v2_sandbox_enabled,
)

__all__ = [
    "CostSimConfig",
    "get_config",
    "is_v2_sandbox_enabled",
    "is_v2_disabled_by_drift",
    "get_commit_sha",
]
