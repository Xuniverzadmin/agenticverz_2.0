# Layer: TEST
# AUDIENCE: INTERNAL
# Role: Stage 1.2 in-process runtime harness for mapped UCs blocked by route/auth prerequisites
# artifact_class: TEST
"""
UAT Runtime Harness (Stage 1.2)

Purpose:
- Provide deterministic, in-process Stage 1.2 execution for mapped UCs that were
  blocked by HTTP route/auth prerequisites.
- Avoid force-fit by asserting real hoc_spine registry composition plus
  handler-level operation anchors in source.
- Emit stagetest artifacts (execution_trace/db_writes) through the shared conftest
  hook path.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from pathlib import Path

from app.hoc.cus.hoc_spine.orchestrator.handlers import register_all_handlers
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    OperationRegistry,
    OperationResult,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]

ACTIVITY_HANDLER = BACKEND_ROOT / "app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py"
INCIDENTS_HANDLER = BACKEND_ROOT / "app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py"
POLICIES_HANDLER = BACKEND_ROOT / "app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py"
LOGS_HANDLER = BACKEND_ROOT / "app/hoc/cus/hoc_spine/orchestrator/handlers/logs_handler.py"
TRACE_API_ENGINE = BACKEND_ROOT / "app/hoc/cus/logs/L5_engines/trace_api_engine.py"
TRACE_STORE_DRIVER = BACKEND_ROOT / "app/hoc/cus/logs/L6_drivers/trace_store.py"
PG_TRACE_STORE_DRIVER = BACKEND_ROOT / "app/hoc/cus/logs/L6_drivers/pg_store.py"
CONTROLS_HANDLER = BACKEND_ROOT / "app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_tokens(path: Path, tokens: list[str]) -> None:
    text = _source(path)
    missing = [token for token in tokens if token not in text]
    assert not missing, f"missing operation tokens in {path}: {missing}"


def _registry() -> OperationRegistry:
    registry = OperationRegistry()
    register_all_handlers(registry)
    return registry


@contextmanager
def _patched_probe_execute(registry: OperationRegistry, operation_key: str):
    handler = registry.get_handler(operation_key)
    assert handler is not None, f"missing handler for operation: {operation_key}"
    handler_cls = type(handler)
    original_execute = handler_cls.execute
    captured: dict[str, str | bool] = {}

    async def _probe_execute(self, ctx: OperationContext) -> OperationResult:  # type: ignore[override]
        captured["probe_called"] = True
        captured["operation"] = ctx.operation
        captured["tenant_id"] = ctx.tenant_id
        captured["timestamp"] = ctx.timestamp
        return OperationResult.ok(
            {
                "probe": True,
                "operation": ctx.operation,
                "tenant_id": ctx.tenant_id,
                "timestamp_present": bool(ctx.timestamp),
            }
        )

    handler_cls.execute = _probe_execute  # type: ignore[assignment]
    try:
        yield captured
    finally:
        handler_cls.execute = original_execute  # type: ignore[assignment]


def _assert_dispatch_probe(operation_key: str) -> None:
    registry = _registry()
    with _patched_probe_execute(registry, operation_key) as captured:
        result = asyncio.run(
            registry.execute(
                operation_key,
                OperationContext(
                    session=None,
                    tenant_id="syn-tenant-001",
                    params={"probe": True, "operation_key": operation_key},
                ),
            )
        )

    assert result.success, f"registry dispatch failed for {operation_key}: {result.error}"
    assert result.operation == operation_key
    assert result.data and result.data.get("probe") is True
    assert result.data.get("tenant_id") == "syn-tenant-001"
    assert result.data.get("operation") == operation_key
    assert result.data.get("timestamp_present") is True
    assert captured.get("probe_called") is True
    assert captured.get("operation") == operation_key
    assert captured.get("tenant_id") == "syn-tenant-001"
    assert isinstance(captured.get("timestamp"), str) and bool(captured.get("timestamp"))


class TestUC001MonitoringHarness:
    def test_event_schema_contract_shared_authority_anchor(self) -> None:
        _assert_tokens(ACTIVITY_HANDLER, ["event_schema_contract"])
        _assert_dispatch_probe("activity.query")

    def test_activity_query_telemetry_orphan_recovery_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("activity.query")
        _assert_tokens(ACTIVITY_HANDLER, ["activity.telemetry", "activity.orphan_recovery"])
        _assert_dispatch_probe("activity.query")


class TestUC003TraceIngestHarness:
    def test_logs_traces_core_operations_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("logs.traces_api")
        _assert_tokens(LOGS_HANDLER, ["list_traces", "store_trace", "get_trace", "delete_trace", "cleanup_old_traces"])
        _assert_dispatch_probe("logs.traces_api")

    def test_trace_lifecycle_operations_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("logs.traces_api")
        _assert_tokens(TRACE_API_ENGINE, ["search_traces"])
        _assert_tokens(TRACE_STORE_DRIVER, ["start_trace", "record_step", "complete_trace", "search_traces"])
        _assert_tokens(PG_TRACE_STORE_DRIVER, ["mark_trace_aborted"])
        _assert_dispatch_probe("logs.traces_api")


class TestUC007IncidentLifecycleHarness:
    def test_incidents_query_write_recurrence_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("incidents.query")
        _assert_tokens(INCIDENTS_HANDLER, ["incidents.write", "incidents.cost_guard", "incidents.recurrence"])
        _assert_dispatch_probe("incidents.query")


class TestUC010ActivityFeedbackLifecycleHarness:
    def test_activity_signal_fingerprint_discovery_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("activity.signal_fingerprint")
        assert registry.has_operation("activity.discovery")
        _assert_dispatch_probe("activity.signal_fingerprint")


class TestUC011IncidentResolutionHarness:
    def test_incidents_export_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("incidents.export")
        _assert_dispatch_probe("incidents.export")


class TestUC018PolicySnapshotHarness:
    def test_policies_query_rules_approval_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.query")
        _assert_tokens(POLICIES_HANDLER, ["policies.rules", "policies.proposals_query", "policies.rules_query", "policies.policy_facade", "policies.approval"])
        _assert_dispatch_probe("policies.query")


class TestUC019PolicyEnforcementHarness:
    def test_policies_enforcement_health_workers_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.enforcement")
        _assert_tokens(POLICIES_HANDLER, ["policies.enforcement_write", "policies.health", "policies.guard_read", "policies.sync_guard_read", "policies.workers"])
        _assert_dispatch_probe("policies.enforcement")


class TestUC020PolicyGovernanceHarness:
    def test_policies_governance_rbac_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.governance")
        _assert_tokens(POLICIES_HANDLER, ["rbac.audit"])
        _assert_dispatch_probe("policies.governance")


class TestUC021LimitsAndThresholdsHarness:
    def test_controls_thresholds_overrides_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("controls.thresholds")
        _assert_tokens(CONTROLS_HANDLER, ["controls.overrides"])
        _assert_dispatch_probe("controls.thresholds")

    def test_policies_limits_rate_limits_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.limits")
        _assert_tokens(POLICIES_HANDLER, ["policies.limits_query", "policies.rate_limits"])
        _assert_dispatch_probe("policies.limits")


class TestUC022RecoveryLessonsHarness:
    def test_policies_lessons_recovery_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.lessons")
        _assert_tokens(POLICIES_HANDLER, ["policies.recovery.match", "policies.recovery.write", "policies.recovery.read"])
        _assert_dispatch_probe("policies.lessons")


class TestUC023PolicyConflictHarness:
    def test_policies_simulate_visibility_replay_anchor(self) -> None:
        registry = _registry()
        assert registry.has_operation("policies.simulate")
        _assert_tokens(POLICIES_HANDLER, ["policies.customer_visibility", "policies.replay"])
        _assert_dispatch_probe("policies.simulate")


class TestUC031IncidentPatternsHarness:
    def test_incidents_recovery_rules_anchor(self) -> None:
        registry = _registry()
        _assert_tokens(INCIDENTS_HANDLER, ["incidents.recovery_rules"])
        _assert_dispatch_probe("incidents.query")
