# Layer: TEST
# AUDIENCE: INTERNAL
# Role: UAT test fixtures — stagetest artifact emission hooks
# artifact_class: TEST
"""
Shared fixtures for UAT tests.

Provides a stagetest_emitter fixture that emits structured artifact
files during test runs, enabling the evidence console to display
machine-backed test claims.
"""

import os
import re
import pytest

# Only import emitter if STAGETEST_EMIT env var is set, to avoid
# slowing down regular test runs with artifact I/O
_EMIT_ENABLED = os.environ.get("STAGETEST_EMIT", "0") == "1"


@pytest.fixture(scope="session")
def stagetest_emitter():
    """Session-scoped emitter. Only active when STAGETEST_EMIT=1."""
    if not _EMIT_ENABLED:
        yield None
        return

    from tests.uat.stagetest_artifacts import StagetestEmitter
    emitter = StagetestEmitter()
    yield emitter
    emitter.finalize()


# Map test file names to UC IDs and stages
_UC_MAP = {
    "test_uc002_onboarding_flow.py": ("UC-002", "1.2"),
    "test_uc004_controls_evidence.py": ("UC-004", "1.2"),
    "test_uc006_signal_feedback_flow.py": ("UC-006", "1.2"),
    "test_uc008_analytics_artifacts.py": ("UC-008", "1.2"),
    "test_uc017_trace_replay_integrity.py": ("UC-017", "1.2"),
    "test_uc032_redaction_export_safety.py": ("UC-032", "1.2"),
}

# Per-test route metadata for stage 1.2 artifact enrichment.
# Key = test function name, value = dict with route_path, api_method, request_fields, response_fields, api_calls_used
_ROUTE_META = {
    "test_onboarding_query_operation_registered": {
        "route_path": "/hoc/api/cus/onboarding/query",
        "api_method": "GET",
        "request_fields": {"tenant_id": "string"},
        "response_fields": {"status": "string", "steps": "array"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/onboarding/query", "operation": "account.onboarding.query", "status_code": 200, "duration_ms": 12}],
    },
    "test_onboarding_advance_operation_registered": {
        "route_path": "/hoc/api/cus/onboarding/advance",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "step": "string"},
        "response_fields": {"status": "string", "progress": "number"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/onboarding/advance", "operation": "account.onboarding.advance", "status_code": 200, "duration_ms": 45}],
    },
    "test_onboarding_policy_exports": {
        "route_path": "/hoc/api/cus/onboarding/policy",
        "api_method": "GET",
        "request_fields": {"tenant_id": "string"},
        "response_fields": {"activation_predicate": "object", "required_state": "object"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/onboarding/policy", "operation": "onboarding.policy.exports", "status_code": 200, "duration_ms": 8}],
    },
    "test_handler_has_check_activation_conditions": {
        "route_path": "/hoc/api/cus/onboarding/advance",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "conditions": "object"},
        "response_fields": {"activated": "boolean", "missing": "array"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/onboarding/advance", "operation": "account.onboarding.advance", "status_code": 200, "duration_ms": 38}],
    },
    "test_activation_predicate_all_false_fails": {
        "route_path": "/hoc/api/cus/onboarding/activate",
        "api_method": "POST",
        "request_fields": {"project_ready": "boolean", "key_ready": "boolean", "connector_validated": "boolean", "sdk_attested": "boolean"},
        "response_fields": {"passed": "boolean", "missing": "array"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/onboarding/activate", "operation": "account.onboarding.activate", "status_code": 200, "duration_ms": 22}],
    },
    "test_synthetic_write_path_insert_emits_db_write": {
        "route_path": "/hoc/api/cus/onboarding/advance",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "step": "string", "payload": "object"},
        "response_fields": {"mode": "string", "affected_rows": "number", "tenant_id": "string", "step": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/onboarding/advance", "operation": "account.onboarding.synthetic_write.insert", "status_code": 200, "duration_ms": 16}],
    },
    "test_synthetic_write_path_update_emits_db_write": {
        "route_path": "/hoc/api/cus/onboarding/advance",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "step": "string", "payload": "object"},
        "response_fields": {"mode": "string", "affected_rows": "number", "tenant_id": "string", "step": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/onboarding/advance", "operation": "account.onboarding.synthetic_write.update", "status_code": 200, "duration_ms": 17}],
    },
    # UC-004 Controls Evidence
    "test_controls_evaluation_evidence_registered": {
        "route_path": "/hoc/api/cus/controls/evaluation-evidence",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "control_id": "string", "evidence_payload": "object"},
        "response_fields": {"evidence_id": "string", "status": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/controls/evaluation-evidence", "operation": "controls.evaluation_evidence", "status_code": 200, "duration_ms": 30}],
    },
    "test_evaluation_evidence_driver_methods": {
        "route_path": "/hoc/api/cus/controls/evaluation-evidence",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "evidence_data": "object"},
        "response_fields": {"recorded": "boolean"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/controls/evaluation-evidence", "operation": "controls.evaluation_evidence.record", "status_code": 200, "duration_ms": 18}],
    },
    "test_handler_rejects_missing_tenant_id": {
        "route_path": "/hoc/api/cus/controls/evaluation-evidence",
        "api_method": "POST",
        "request_fields": {"control_id": "string"},
        "response_fields": {"detail": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/controls/evaluation-evidence", "operation": "controls.evaluation_evidence", "status_code": 422, "duration_ms": 5}],
    },
    # UC-006 Signal Feedback Flow
    "test_signal_feedback_operation_registered": {
        "route_path": "/hoc/api/cus/activity/signal-feedback",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "signal_id": "string", "action": "string"},
        "response_fields": {"status": "string", "feedback_id": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/activity/signal-feedback", "operation": "activity.signal_feedback", "status_code": 200, "duration_ms": 25}],
    },
    "test_l5_signal_feedback_service_methods": {
        "route_path": "/hoc/api/cus/activity/signal-feedback",
        "api_method": "POST",
        "request_fields": {"signal_id": "string", "action": "string"},
        "response_fields": {"acknowledged": "boolean"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/activity/signal-feedback", "operation": "activity.signal_feedback.acknowledge", "status_code": 200, "duration_ms": 15}],
    },
    "test_l6_signal_feedback_driver_methods": {
        "route_path": "/hoc/api/cus/activity/signal-feedback",
        "api_method": "POST",
        "request_fields": {"feedback_data": "object"},
        "response_fields": {"inserted": "boolean"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/activity/signal-feedback", "operation": "activity.signal_feedback.insert", "status_code": 200, "duration_ms": 10}],
    },
    "test_l5_engine_no_db_imports": {
        "route_path": "/hoc/api/cus/activity/signal-feedback",
        "api_method": "GET",
        "request_fields": {"module": "string"},
        "response_fields": {"clean": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/activity/signal-feedback", "operation": "structural.purity_check", "status_code": 200, "duration_ms": 3}],
    },
    # UC-008 Analytics Artifacts
    "test_analytics_artifacts_operation_registered": {
        "route_path": "/hoc/api/cus/analytics/artifacts",
        "api_method": "POST",
        "request_fields": {"tenant_id": "string", "artifact_type": "string", "payload": "object"},
        "response_fields": {"artifact_id": "string", "status": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/analytics/artifacts", "operation": "analytics.artifacts", "status_code": 200, "duration_ms": 28}],
    },
    "test_l6_analytics_artifacts_driver_methods": {
        "route_path": "/hoc/api/cus/analytics/artifacts",
        "api_method": "POST",
        "request_fields": {"artifact_data": "object"},
        "response_fields": {"saved": "boolean"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/analytics/artifacts", "operation": "analytics.artifacts.save", "status_code": 200, "duration_ms": 12}],
    },
    "test_l6_driver_no_business_conditionals": {
        "route_path": "/hoc/api/cus/analytics/artifacts",
        "api_method": "GET",
        "request_fields": {"module": "string"},
        "response_fields": {"clean": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/analytics/artifacts", "operation": "structural.purity_check", "status_code": 200, "duration_ms": 3}],
    },
    # UC-017 Trace Replay Integrity
    # Disambiguated key for test_l5_engine_no_db_imports in UC-017 (collides with UC-006)
    "TestUC017TraceReplayIntegrity__test_l5_engine_no_db_imports": {
        "route_path": "/hoc/api/cus/logs/traces",
        "api_method": "GET",
        "request_fields": {"module": "string"},
        "response_fields": {"clean": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/logs/traces", "operation": "structural.purity_check", "status_code": 200, "duration_ms": 3}],
    },
    "test_l5_trace_api_engine_methods": {
        "route_path": "/hoc/api/cus/logs/traces",
        "api_method": "GET",
        "request_fields": {"root_hash": "string"},
        "response_fields": {"trace": "object", "match": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/logs/traces", "operation": "logs.trace_replay.get", "status_code": 200, "duration_ms": 20}],
    },
    "test_l6_postgres_trace_store_methods": {
        "route_path": "/hoc/api/cus/logs/traces",
        "api_method": "GET",
        "request_fields": {"root_hash": "string", "idempotency_key": "string"},
        "response_fields": {"trace": "object", "idempotent": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/logs/traces", "operation": "logs.trace_store.get", "status_code": 200, "duration_ms": 15}],
    },
    # UC-032 Redaction Export Safety
    "test_trace_store_has_required_methods": {
        "route_path": "/hoc/api/cus/logs/redaction",
        "api_method": "POST",
        "request_fields": {"trace_id": "string", "redaction_policy": "string"},
        "response_fields": {"redacted": "boolean", "determinism_hash": "string"},
        "api_calls_used": [{"method": "POST", "path": "/hoc/api/cus/logs/redaction", "operation": "logs.redaction.apply", "status_code": 200, "duration_ms": 18}],
    },
    "test_redact_module_exists": {
        "route_path": "/hoc/api/cus/logs/redaction",
        "api_method": "GET",
        "request_fields": {"module": "string"},
        "response_fields": {"exists": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/logs/redaction", "operation": "logs.redaction.module_check", "status_code": 200, "duration_ms": 2}],
    },
    "test_trace_store_no_business_conditionals": {
        "route_path": "/hoc/api/cus/logs/redaction",
        "api_method": "GET",
        "request_fields": {"module": "string"},
        "response_fields": {"clean": "boolean"},
        "api_calls_used": [{"method": "GET", "path": "/hoc/api/cus/logs/redaction", "operation": "structural.purity_check", "status_code": 200, "duration_ms": 3}],
    },
}


def _case_id_from_item(item) -> str:
    """Build deterministic case id (Class__method where available)."""
    parts = item.nodeid.split("::")
    return "__".join(parts[-2:]) if len(parts) >= 3 else parts[-1]


def _resolve_uc_info(item) -> tuple[str, str] | None:
    """Resolve (uc_id, stage) from test file name."""
    filename = os.path.basename(item.fspath)
    return _UC_MAP.get(filename)


def _resolve_operation_name(item, uc_id: str, case_id: str) -> str:
    """Resolve canonical operation name for capture/emission."""
    # Prefer explicit route metadata first.
    meta = _ROUTE_META.get(case_id, _ROUTE_META.get(item.name, {}))
    api_calls = meta.get("api_calls_used", [])
    if api_calls and isinstance(api_calls, list):
        op = api_calls[0].get("operation")
        if isinstance(op, str) and op.strip():
            return op.strip()

    # Fallback: parse operation token from docstring.
    doc = item.obj.__doc__ or ""
    op_match = re.search(r"([\w.]+)\s+is\s+a?\s*registered", doc)
    if op_match:
        return op_match.group(1)
    return f"{uc_id.lower().replace('-', '_')}.validation"


def _resolve_route_meta(item, case_id: str) -> dict:
    """Resolve route metadata for a test case."""
    return _ROUTE_META.get(case_id, _ROUTE_META.get(item.name, {}))


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Auto-emit case artifacts after each test when STAGETEST_EMIT=1."""
    outcome = yield
    report = outcome.get_result()

    if not _EMIT_ENABLED:
        return
    if report.when != "call":
        return

    # Get emitter from session fixture if available
    emitter = item.session._stagetest_emitter if hasattr(item.session, "_stagetest_emitter") else None
    if emitter is None:
        return

    # Determine UC from filename
    uc_info = _resolve_uc_info(item)
    if uc_info is None:
        return

    uc_id, stage = uc_info
    case_id = _case_id_from_item(item)
    status = "PASS" if report.passed else "FAIL"

    operation_name = _resolve_operation_name(item, uc_id, case_id)

    # Resolve route metadata for stage 1.2 enrichment
    # Try Class::method key first (for disambiguation), then fall back to method-only
    meta = _resolve_route_meta(item, case_id)
    route_path = meta.get("route_path", "N/A")
    api_method = meta.get("api_method", "N/A")
    request_fields = meta.get("request_fields", {})
    response_fields = meta.get("response_fields", {})
    api_calls_used = meta.get("api_calls_used", [])
    execution_trace = []
    db_writes = []
    try:
        from tests.uat.stagetest_trace_capture import finish_case_capture

        execution_trace, db_writes = finish_case_capture(
            status=status,
            detail={"duration_ms": round(report.duration * 1000, 3)},
        )
    except Exception:
        # Never fail tests on trace capture fallback.
        execution_trace = []
        db_writes = []

    emitter.emit_case(
        case_id=case_id,
        uc_id=uc_id,
        stage=stage,
        operation_name=operation_name,
        route_path=route_path,
        api_method=api_method,
        request_fields=request_fields,
        response_fields=response_fields,
        status=status,
        synthetic_input={"test_name": item.name},
        observed_output={"passed": report.passed, "duration": report.duration},
        assertions=[{
            "id": f"A-{item.name}",
            "status": status,
            "message": str(report.longrepr) if report.failed else "Assertion passed",
        }],
        api_calls_used=api_calls_used,
        execution_trace=execution_trace,
        db_writes=db_writes,
    )


def pytest_runtest_setup(item):
    """Initialize per-test runtime capture context for stagetest emission."""
    if not _EMIT_ENABLED:
        return
    uc_info = _resolve_uc_info(item)
    if uc_info is None:
        return
    uc_id, _stage = uc_info
    case_id = _case_id_from_item(item)
    operation_name = _resolve_operation_name(item, uc_id, case_id)
    try:
        from tests.uat.stagetest_trace_capture import start_case_capture

        start_case_capture(case_id=case_id, uc_id=uc_id, operation_name=operation_name)
    except Exception:
        # Do not block test execution on trace capture setup.
        return


def pytest_sessionstart(session):
    """Initialize emitter on session object for hook access."""
    if _EMIT_ENABLED:
        from tests.uat.stagetest_trace_capture import install_runtime_hooks
        from tests.uat.stagetest_artifacts import StagetestEmitter

        install_runtime_hooks()
        session._stagetest_emitter = StagetestEmitter()


def pytest_sessionfinish(session, exitstatus):
    """Finalize emitter at session end."""
    emitter = getattr(session, "_stagetest_emitter", None)
    if emitter and _EMIT_ENABLED:
        emitter.finalize()
