# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policies, limits, rules, policy_enforcements
#   Writes: policies, limits, rules, policy_enforcements
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
from app.hoc.cus.policies.L6_drivers.proposals_read_driver import (
    ProposalsReadDriver,
    get_proposals_read_driver,
)
from app.hoc.cus.policies.L6_drivers.policy_enforcement_write_driver import (
    PolicyEnforcementWriteDriver,
    get_policy_enforcement_write_driver,
)
from app.hoc.cus.policies.L6_drivers.replay_read_driver import (
    ReplayReadDriver,
    get_replay_read_driver,
)
from app.hoc.cus.policies.L6_drivers.m25_integration_read_driver import (
    M25IntegrationReadDriver,
    get_m25_integration_read_driver,
    LoopStageRow,
    CheckpointRow,
    LoopStatsRow,
    PatternStatsRow,
    RecoveryStatsRow,
    PolicyStatsRow,
    RoutingStatsRow,
    CheckpointStatsRow,
    SimulationStateRow,
    IncidentRow,
    PreventionRow,
    RegretRow,
)
from app.hoc.cus.policies.L6_drivers.m25_integration_write_driver import (
    M25IntegrationWriteDriver,
    get_m25_integration_write_driver,
    PreventionRecordInput,
    RegretEventInput,
    TimelineViewInput,
    GraduationHistoryInput,
    GraduationStatusUpdateInput,
)
from app.hoc.cus.policies.L6_drivers.guard_read_driver import (
    GuardReadDriver,
    SyncGuardReadDriver,
    get_sync_guard_read_driver,
)
from app.hoc.cus.policies.L6_drivers.policy_approval_driver import (
    PolicyApprovalDriver,
    get_policy_approval_driver,
)
from app.hoc.cus.policies.L6_drivers.workers_read_driver import (
    WorkersReadDriver,
    get_workers_read_driver,
)
from app.hoc.cus.policies.L6_drivers.rbac_audit_driver import (
    RbacAuditDriver,
    get_rbac_audit_driver,
    AuditEntryDTO,
    AuditQueryResultDTO,
    AuditCleanupResultDTO,
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
    "ProposalsReadDriver",
    "get_proposals_read_driver",
    # Policy Enforcement write driver (PIN-524)
    "PolicyEnforcementWriteDriver",
    "get_policy_enforcement_write_driver",
    # Replay read driver (Replay UX H1)
    "ReplayReadDriver",
    "get_replay_read_driver",
    # M25 Integration drivers (L2 first-principles purity)
    "M25IntegrationReadDriver",
    "get_m25_integration_read_driver",
    "LoopStageRow",
    "CheckpointRow",
    "LoopStatsRow",
    "PatternStatsRow",
    "RecoveryStatsRow",
    "PolicyStatsRow",
    "RoutingStatsRow",
    "CheckpointStatsRow",
    "SimulationStateRow",
    "IncidentRow",
    "PreventionRow",
    "RegretRow",
    "M25IntegrationWriteDriver",
    "get_m25_integration_write_driver",
    "PreventionRecordInput",
    "RegretEventInput",
    "TimelineViewInput",
    "GraduationHistoryInput",
    "GraduationStatusUpdateInput",
    # Guard read drivers (L2 first-principles purity)
    "GuardReadDriver",
    "SyncGuardReadDriver",
    "get_sync_guard_read_driver",
    # Approval workflow driver (Goal B: eliminate session.execute from policy.py)
    "PolicyApprovalDriver",
    "get_policy_approval_driver",
    # Workers read driver (L2 first-principles purity for workers.py)
    "WorkersReadDriver",
    "get_workers_read_driver",
    # RBAC Audit driver (L2 first-principles purity for rbac_api.py)
    "RbacAuditDriver",
    "get_rbac_audit_driver",
    "AuditEntryDTO",
    "AuditQueryResultDTO",
    "AuditCleanupResultDTO",
]
