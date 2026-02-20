# capability_id: CAP-018
# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: L5-safe enum mirrors for customer integration domain
# Callers: cus_schemas.py, cus_health_engine.py
# Allowed Imports: stdlib only
# Forbidden Imports: L1, L2, L3, L7 (app.models)
# Reference: PIN-520 Phase 3 (L5 purity — no runtime app.models imports)
# artifact_class: CODE

"""
Customer integration enum mirrors.

These mirror the canonical enums in app.models.cus_models so that
L5 engines and L5 schemas never need a runtime import of app.models.
Values MUST stay in sync with the L7 originals.

Canonical source: app/models/cus_models.py
"""

from enum import Enum


class CusProviderType(str, Enum):
    """Supported LLM provider types.

    Mirror of app.models.cus_models.CusProviderType.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


class CusIntegrationStatus(str, Enum):
    """Integration lifecycle status.

    Mirror of app.models.cus_models.CusIntegrationStatus.
    """

    CREATED = "created"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class CusHealthState(str, Enum):
    """Integration health state.

    Mirror of app.models.cus_models.CusHealthState.
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"


class CusPolicyResult(str, Enum):
    """Policy enforcement result for LLM calls.

    Mirror of app.models.cus_models.CusPolicyResult.
    """

    ALLOWED = "allowed"
    WARNED = "warned"
    BLOCKED = "blocked"
