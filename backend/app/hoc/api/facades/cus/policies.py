# Layer: L2.1 — Facade (CUS: policies)

from __future__ import annotations

from fastapi import APIRouter

from app.hoc.api.cus.policies.M25_integrations import router as m25_integration_router
from app.hoc.api.cus.policies.alerts import router as alerts_router
from app.hoc.api.cus.policies.compliance import router as compliance_router
from app.hoc.api.cus.policies.connectors import router as connectors_router
from app.hoc.api.cus.policies.cus_enforcement import router as cus_enforcement_router
from app.hoc.api.cus.policies.customer_visibility import router as customer_visibility_router
from app.hoc.api.cus.policies.datasources import router as datasources_router
from app.hoc.api.cus.policies.detection import router as detection_router
from app.hoc.api.cus.policies.evidence import router as evidence_router
from app.hoc.api.cus.policies.governance import router as governance_router
from app.hoc.api.cus.policies.guard import router as guard_router
from app.hoc.api.cus.policies.guard_policies import router as guard_policies_router
from app.hoc.api.cus.policies.lifecycle import router as lifecycle_router
from app.hoc.api.cus.policies.logs import router as logs_router
from app.hoc.api.cus.policies.monitors import router as monitors_router
from app.hoc.api.cus.policies.notifications import router as notifications_router
from app.hoc.api.cus.policies.override import router as limits_override_router
from app.hoc.api.cus.policies.policies import router as policies_router
from app.hoc.api.cus.policies.policy import router as policy_router
from app.hoc.api.cus.policies.policy_layer import router as policy_layer_router
from app.hoc.api.cus.policies.policy_limits_crud import router as policy_limits_crud_router
from app.hoc.api.cus.policies.policy_proposals import router as policy_proposals_router
from app.hoc.api.cus.policies.policies_public import router as policies_public_router
from app.hoc.api.cus.policies.policy_rules_crud import router as policy_rules_crud_router
from app.hoc.api.cus.policies.rate_limits import router as rate_limits_router
from app.hoc.api.cus.policies.rbac_api import router as rbac_router
from app.hoc.api.cus.policies.replay import router as replay_router
from app.hoc.api.cus.policies.retrieval import router as retrieval_router
from app.hoc.api.cus.policies.runtime import router as runtime_router
from app.hoc.api.cus.policies.scheduler import router as scheduler_router
from app.hoc.api.cus.policies.simulate import router as limits_simulate_router
from app.hoc.api.cus.policies.status_history import router as status_history_router
from app.hoc.api.cus.policies.v1_killswitch import router as v1_killswitch_router
from app.hoc.api.cus.policies.workers import router as workers_router

DOMAIN = "policies"
ROUTERS: list[APIRouter] = [
    # Core / policy CRUD
    policy_router,
    policies_router,
    policy_layer_router,
    policy_limits_crud_router,
    policy_rules_crud_router,
    policy_proposals_router,
    policies_public_router,
    status_history_router,
    rbac_router,
    runtime_router,
    workers_router,
    # Guard surface
    guard_router,
    guard_policies_router,
    v1_killswitch_router,
    # Capability surfaces
    retrieval_router,
    detection_router,
    compliance_router,
    evidence_router,
    notifications_router,
    alerts_router,
    scheduler_router,
    datasources_router,
    monitors_router,
    rate_limits_router,
    lifecycle_router,
    logs_router,
    connectors_router,
    governance_router,
    cus_enforcement_router,
    customer_visibility_router,
    # Limits
    limits_simulate_router,
    limits_override_router,
    # Internal/phase workstreams
    replay_router,
    m25_integration_router,
]
