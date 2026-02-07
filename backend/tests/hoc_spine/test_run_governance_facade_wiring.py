# Layer: L4 — Tests
# AUDIENCE: INTERNAL
# Role: Guard: RunGovernanceFacade must be wired with real engines, never null.
# artifact_class: TEST

"""
RunGovernanceFacade Wiring Guards (Batch 1 — G1 Gap Closure)

These tests verify that:
1. wire_run_governance_facade() injects real engines (not None)
2. get_run_governance_facade() raises RuntimeError if unwired
3. The wired facade satisfies LessonsEnginePort and PolicyEvaluationPort protocols
"""

from __future__ import annotations

import importlib

import pytest


def _reset_facade_singleton() -> None:
    """Reset the module-level _facade_instance to None for test isolation."""
    mod = importlib.import_module(
        "app.hoc.cus.hoc_spine.orchestrator.run_governance_facade"
    )
    mod._facade_instance = None


@pytest.fixture(autouse=True)
def _isolate_facade():
    """Reset facade singleton before and after each test."""
    _reset_facade_singleton()
    yield
    _reset_facade_singleton()


def test_get_run_governance_facade_raises_when_unwired() -> None:
    """get_run_governance_facade() must raise RuntimeError before wiring."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        get_run_governance_facade,
    )

    with pytest.raises(RuntimeError, match="not wired"):
        get_run_governance_facade()


def test_wire_injects_real_engines() -> None:
    """wire_run_governance_facade() must populate both engine slots."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        wire_run_governance_facade,
    )

    facade = wire_run_governance_facade()

    assert facade._lessons_engine is not None, "lessons_engine must not be None after wiring"
    assert facade._policy_evaluator is not None, "policy_evaluator must not be None after wiring"


def test_wired_facade_returned_by_getter() -> None:
    """After wiring, get_run_governance_facade() must return the wired instance."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        get_run_governance_facade,
        wire_run_governance_facade,
    )

    wired = wire_run_governance_facade()
    fetched = get_run_governance_facade()

    assert fetched is wired, "getter must return the exact instance from wiring"


def test_lessons_engine_satisfies_protocol() -> None:
    """Injected lessons_engine must satisfy LessonsEnginePort."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        wire_run_governance_facade,
    )
    from app.hoc.cus.hoc_spine.schemas.protocols import LessonsEnginePort

    facade = wire_run_governance_facade()

    assert isinstance(facade._lessons_engine, LessonsEnginePort), (
        f"lessons_engine ({type(facade._lessons_engine).__name__}) "
        f"must satisfy LessonsEnginePort protocol"
    )


def test_policy_evaluator_is_callable() -> None:
    """Injected policy_evaluator must be callable (matches PolicyEvaluationPort.__call__)."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        wire_run_governance_facade,
    )

    facade = wire_run_governance_facade()

    assert callable(facade._policy_evaluator), "policy_evaluator must be callable"
