# Layer: L4 — Tests
# AUDIENCE: INTERNAL
# Role: Guard: "wired" dependencies must also be executable via L4 call paths.
# artifact_class: TEST

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_policies_sandbox_execute_operation_runs() -> None:
    from app.hoc.cus.hoc_spine.orchestrator.handlers import register_all_handlers
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        OperationContext,
        get_operation_registry,
        reset_operation_registry,
    )

    reset_operation_registry()
    registry = get_operation_registry()
    register_all_handlers(registry)

    ctx = OperationContext(
        session=MagicMock(),
        tenant_id="tenant-test",
        params={
            "code": "print('sandbox-ok')",
            "language": "python",
            "policy_id": "standard",
        },
    )

    result = await registry.execute("policies.sandbox_execute", ctx)
    assert result.success is True
    assert result.data["status"] == "completed"
    assert "sandbox-ok" in (result.data.get("stdout") or "")


@pytest.mark.asyncio
async def test_governance_audit_job_operation_runs() -> None:
    from app.hoc.cus.hoc_spine.orchestrator.handlers import register_all_handlers
    from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
        OperationContext,
        get_operation_registry,
        reset_operation_registry,
    )

    reset_operation_registry()
    registry = get_operation_registry()
    register_all_handlers(registry)

    now = datetime.now(timezone.utc)
    job_id = uuid4()
    contract_id = uuid4()
    target = "capability_enable:test"

    ctx = OperationContext(
        session=MagicMock(),
        tenant_id="tenant-test",
        params={
            "job_id": str(job_id),
            "contract_id": str(contract_id),
            "job_status": "COMPLETED",
            "contract_scope": [target],
            "proposed_changes": {"capability_name": target},
            "activation_window_start": (now - timedelta(minutes=5)).isoformat(),
            "activation_window_end": (now + timedelta(minutes=5)).isoformat(),
            "execution_result": {
                "step_results": [
                    {
                        "step_index": 0,
                        "status": "COMPLETED",
                        "started_at": now.isoformat(),
                        "completed_at": (now + timedelta(seconds=1)).isoformat(),
                        "output": {
                            "target": target,
                            "rollback_action": "noop",
                        },
                        "error": None,
                    }
                ],
                "health_observations": {
                    "before": {target: "HEALTHY"},
                    "after": {target: "HEALTHY"},
                },
                "timing": {
                    "started_at": now.isoformat(),
                    "completed_at": (now + timedelta(seconds=1)).isoformat(),
                    "duration_seconds": 1.0,
                },
            },
        },
    )

    result = await registry.execute("governance.audit_job", ctx)
    assert result.success is True
    assert result.data["job_id"] == str(job_id)
    assert result.data["contract_id"] == str(contract_id)
    assert result.data["verdict"] == "PASS"

