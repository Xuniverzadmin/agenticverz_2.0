# capability_id: CAP-012
# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Product: system-wide (Part-2 CRM Workflow)
# Temporal:
#   Trigger: api (L2 HTTP request via registry dispatch) | internal tools
#   Execution: sync
# Role: L4 handler — triggers L8 audit over frozen execution evidence
# Callers: OperationRegistry (L4) via operation "governance.audit_job"
# Allowed Imports: hoc_spine, account-owned CRM audit engine (lazy)
# Forbidden Imports: L1, L2
# Reference: PART2_CRM_WORKFLOW_CHARTER.md, PIN-292, GOVERNANCE_AUDIT_MODEL.md
# artifact_class: CODE

"""
Governance Audit Handler (Part-2 CRM)

Creates an explicit L4-owned execution call path to the (L8) governance audit
engine: evidence in → verdict out.

This handler does not decide outcomes; it only runs the auditor.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


def _parse_uuid(val: Any, label: str) -> tuple[Optional[UUID], Optional[OperationResult]]:
    if not isinstance(val, str) or not val.strip():
        return None, OperationResult.fail(f"Missing required param: {label}", f"MISSING_{label.upper()}")
    try:
        return UUID(val), None
    except Exception:
        return None, OperationResult.fail(f"Invalid UUID for {label}", f"INVALID_{label.upper()}")


def _parse_dt(val: Any, label: str) -> tuple[Optional[datetime], Optional[OperationResult]]:
    if val is None:
        return None, None
    if not isinstance(val, str) or not val.strip():
        return None, OperationResult.fail(f"Invalid datetime for {label}", f"INVALID_{label.upper()}")
    try:
        # Accept Z-suffixed ISO strings.
        return datetime.fromisoformat(val.replace("Z", "+00:00")), None
    except Exception:
        return None, OperationResult.fail(f"Invalid datetime for {label}", f"INVALID_{label.upper()}")


class GovernanceAuditJobHandler:
    """Handler for governance.audit_job."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        job_id, err = _parse_uuid(ctx.params.get("job_id"), "job_id")
        if err:
            return err
        contract_id, err = _parse_uuid(ctx.params.get("contract_id"), "contract_id")
        if err:
            return err

        job_status = ctx.params.get("job_status")
        if not isinstance(job_status, str) or not job_status.strip():
            return OperationResult.fail("Missing required param: job_status", "MISSING_JOB_STATUS")

        contract_scope = ctx.params.get("contract_scope")
        if not isinstance(contract_scope, list) or not all(isinstance(x, str) for x in contract_scope):
            return OperationResult.fail("Missing/invalid param: contract_scope", "INVALID_CONTRACT_SCOPE")

        proposed_changes = ctx.params.get("proposed_changes")
        if not isinstance(proposed_changes, (dict, list)):
            return OperationResult.fail("Missing/invalid param: proposed_changes", "INVALID_PROPOSED_CHANGES")

        execution_result = ctx.params.get("execution_result")
        if not isinstance(execution_result, dict):
            return OperationResult.fail("Missing/invalid param: execution_result", "INVALID_EXECUTION_RESULT")

        window_start, err = _parse_dt(ctx.params.get("activation_window_start"), "activation_window_start")
        if err:
            return err
        window_end, err = _parse_dt(ctx.params.get("activation_window_end"), "activation_window_end")
        if err:
            return err

        from app.hoc.cus.hoc_spine.orchestrator.governance_orchestrator import (
            get_audit_service,
        )
        from app.hoc.cus.account.logs.CRM.audit.audit_engine import (
            audit_result_to_record,
            create_audit_input_from_evidence,
        )

        audit_input = create_audit_input_from_evidence(
            job_id=job_id,
            contract_id=contract_id,
            job_status=job_status,
            contract_scope=contract_scope,
            proposed_changes=proposed_changes,
            execution_result=execution_result,
            activation_window_start=window_start,
            activation_window_end=window_end,
        )

        auditor = get_audit_service()
        audit_result = auditor.audit(audit_input)
        return OperationResult.ok(audit_result_to_record(audit_result))


def register(registry: OperationRegistry) -> None:
    """Register governance audit operations with the registry."""
    registry.register("governance.audit_job", GovernanceAuditJobHandler())
