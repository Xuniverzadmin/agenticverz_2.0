# Layer: L5 — Domain Engine (DEPRECATED REDIRECT)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: DEPRECATED - Redirect to drivers/cus_health_driver.py
# Callers: Legacy imports
# Allowed Imports: L6 (drivers)
# Forbidden Imports: L1, L2, L3, L4
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md
#
# =============================================================================
# DEPRECATION NOTICE (2026-01-24)
# =============================================================================
# This file has been moved to:
#   app.houseofcards.customer.general.drivers.cus_health_driver
#
# Reason: The original file had DB Session imports (sqlmodel Session, select)
# which makes it L6 Driver layer work, not L5 Engine layer work.
#
# This file now serves as a backward-compatibility redirect.
# Please update imports to use the new location.
#
# Old: from app.houseofcards.customer.general.engines.cus_health_service import CusHealthService
# New: from app.houseofcards.customer.general.drivers.cus_health_driver import CusHealthDriver
#
# =============================================================================

"""DEPRECATED: Customer Health Service

This module has been moved to drivers/cus_health_driver.py.

The service was reclassified from L4 Engine to L6 Driver because it contains
direct database operations (sqlmodel Session imports).

For backward compatibility, this module re-exports the class from its new location.
Please update your imports to use the new location directly.
"""

import warnings

# Re-export from new location for backward compatibility
from app.houseofcards.customer.general.drivers.cus_health_driver import (
    CusHealthDriver,
    CusHealthService,  # Alias for backward compatibility
)

# Emit deprecation warning on import
warnings.warn(
    "cus_health_service has been moved to drivers/cus_health_driver. "
    "Please update imports to: "
    "from app.houseofcards.customer.general.drivers.cus_health_driver import CusHealthDriver",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["CusHealthService", "CusHealthDriver"]
