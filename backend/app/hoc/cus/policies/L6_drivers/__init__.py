# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policies, limits, rules
#   Writes: policies, limits, rules
# Database:
#   Scope: domain (policies)
#   Models: PolicyRule, Limit, PolicySnapshot
# Role: Data access drivers for customer policies domain
# Callers: L5 engines
# Allowed Imports: L6, L7 (models)
# Reference: PIN-470, PHASE2_EXTRACTION_PROTOCOL.md

"""
policies/drivers

L6 drivers for customer policy data access operations.
All drivers are pure data access - no business logic.

For CUSTOMER policy read operations:
    from app.hoc.cus.policies.L6_drivers import PolicyReadDriver

For INTERNAL policy operations:
    from app.hoc.int.platform.policy.engines import get_policy_driver
"""

from app.hoc.cus.policies.L6_drivers.policy_read_driver import (
    PolicyReadDriver,
    get_policy_read_driver,
    TenantBudgetDataDTO,
    UsageSumDTO,
    GuardrailDTO,
)
from app.hoc.cus.policies.L6_drivers.policy_proposal_read_driver import (
    PolicyProposalReadDriver,
    get_policy_proposal_read_driver,
)
from app.hoc.cus.policies.L6_drivers.policy_proposal_write_driver import (
    PolicyProposalWriteDriver,
    get_policy_proposal_write_driver,
)
from app.hoc.cus.policies.L6_drivers.policy_rules_read_driver import (
    PolicyRulesReadDriver,
    get_policy_rules_read_driver,
)
from app.hoc.cus.policies.L6_drivers.limits_read_driver import (
    LimitsReadDriver,
    get_limits_read_driver,
)
from app.hoc.cus.policies.L6_drivers.proposals_read_driver import (
    ProposalsReadDriver,
    get_proposals_read_driver,
)

__all__ = [
    # Existing
    "PolicyReadDriver",
    "get_policy_read_driver",
    "TenantBudgetDataDTO",
    "UsageSumDTO",
    "GuardrailDTO",
    # Policy Proposal drivers (Phase 3B P3)
    "PolicyProposalReadDriver",
    "get_policy_proposal_read_driver",
    "PolicyProposalWriteDriver",
    "get_policy_proposal_write_driver",
    # Split query engine drivers (Phase 3B P3)
    "PolicyRulesReadDriver",
    "get_policy_rules_read_driver",
    "LimitsReadDriver",
    "get_limits_read_driver",
    "ProposalsReadDriver",
    "get_proposals_read_driver",
]
