# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Limits domain schemas (PIN-LIM)
# Callers: api/limits/*, services/limits/*
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: LIMITS_MANAGEMENT_AUDIT.md

"""
Limits Domain Schemas

Provides request/response models for:
- Policy limits CRUD
- Policy rules CRUD
- Limit simulation (pre-execution check)
- Limit overrides (temporary increases)
"""

from app.schemas.limits.policy_limits import (
    CreatePolicyLimitRequest,
    UpdatePolicyLimitRequest,
    PolicyLimitResponse,
)
from app.schemas.limits.policy_rules import (
    CreatePolicyRuleRequest,
    UpdatePolicyRuleRequest,
    PolicyRuleResponse,
)
from app.schemas.limits.simulation import (
    LimitSimulationRequest,
    LimitSimulationResponse,
    LimitCheckResult,
    HeadroomInfo,
)
from app.schemas.limits.overrides import (
    LimitOverrideRequest,
    LimitOverrideResponse,
    OverrideStatus,
)

__all__ = [
    # Policy Limits
    "CreatePolicyLimitRequest",
    "UpdatePolicyLimitRequest",
    "PolicyLimitResponse",
    # Policy Rules
    "CreatePolicyRuleRequest",
    "UpdatePolicyRuleRequest",
    "PolicyRuleResponse",
    # Simulation
    "LimitSimulationRequest",
    "LimitSimulationResponse",
    "LimitCheckResult",
    "HeadroomInfo",
    # Overrides
    "LimitOverrideRequest",
    "LimitOverrideResponse",
    "OverrideStatus",
]
