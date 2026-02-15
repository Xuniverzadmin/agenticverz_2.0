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

    from stagetest_artifacts import StagetestEmitter
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
    filename = os.path.basename(item.fspath)
    uc_info = _UC_MAP.get(filename)
    if uc_info is None:
        return

    uc_id, stage = uc_info
    case_id = item.nodeid.split("::")[-1]
    status = "PASS" if report.passed else "FAIL"

    # Extract operation name from test docstring if available
    doc = item.obj.__doc__ or ""
    op_match = re.search(r"([\w.]+)\s+is\s+a?\s*registered", doc)
    operation_name = op_match.group(1) if op_match else f"{uc_id.lower().replace('-', '_')}.validation"

    emitter.emit_case(
        case_id=case_id,
        uc_id=uc_id,
        stage=stage,
        operation_name=operation_name,
        status=status,
        synthetic_input={"test_name": item.name},
        observed_output={"passed": report.passed, "duration": report.duration},
        assertions=[{
            "id": f"A-{item.name}",
            "status": status,
            "message": str(report.longrepr) if report.failed else "Assertion passed",
        }],
    )


def pytest_sessionstart(session):
    """Initialize emitter on session object for hook access."""
    if _EMIT_ENABLED:
        from stagetest_artifacts import StagetestEmitter
        session._stagetest_emitter = StagetestEmitter()


def pytest_sessionfinish(session, exitstatus):
    """Finalize emitter at session end."""
    emitter = getattr(session, "_stagetest_emitter", None)
    if emitter and _EMIT_ENABLED:
        emitter.finalize()
