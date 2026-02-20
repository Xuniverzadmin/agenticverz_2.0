# capability_id: CAP-018
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api|worker
#   Execution: async|sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (module exports)
#   Writes: none
# Role: integrations domain - engines (business logic, decisions)
# Callers: L2 APIs, L3 adapters
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
integrations / engines

L5 Engine exports for the integrations domain.
"""

from .prevention_contract import (
    PREVENTION_CONTRACT_FROZEN_AT,
    PREVENTION_CONTRACT_VERSION,
    PreventionCandidate,
    PreventionContractViolation,
    assert_no_deletion,
    assert_prevention_immutable,
    validate_prevention_candidate,
    validate_prevention_for_graduation,
)
# NOTE: learning_proof_engine was moved to policies/L5_engines/ during domain
# consolidation (PIN-498). Stale re-export removed per PIN-507 Law 0.
# NOTE: cost_bridges_engine deleted — orphaned entry module (PIN-520 Phase 4).
# MCP Server Engine (PIN-516 Phase 2)
from .mcp_server_engine import (
    McpDiscoveryResult,
    McpHealthResult,
    McpRegistrationResult,
    McpServerEngine,
    McpServerStatus,
)
# MCP Tool Invocation Engine (PIN-516 Phase 4)
from .mcp_tool_invocation_engine import (
    McpInvocationResult,
    McpPolicyChecker,
    McpToolInvocationEngine,
    PolicyCheckResult,
)

__all__ = [
    # prevention_contract
    "PREVENTION_CONTRACT_FROZEN_AT",
    "PREVENTION_CONTRACT_VERSION",
    "PreventionCandidate",
    "PreventionContractViolation",
    "assert_no_deletion",
    "assert_prevention_immutable",
    "validate_prevention_candidate",
    "validate_prevention_for_graduation",
    # mcp_server_engine (PIN-516 Phase 2)
    "McpServerEngine",
    "McpServerStatus",
    "McpRegistrationResult",
    "McpDiscoveryResult",
    "McpHealthResult",
    # mcp_tool_invocation_engine (PIN-516 Phase 4)
    "McpToolInvocationEngine",
    "McpInvocationResult",
    "McpPolicyChecker",
    "PolicyCheckResult",
]
