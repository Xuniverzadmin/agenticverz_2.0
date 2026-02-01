# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: pytest
#   Execution: sync + async
# Role: Operation Registry invariant tests — colocated under hoc_spine/tests/
# Callers: pytest, CI
# Reference: PIN-491 (L2-L4-L5 Construction Plan)
# artifact_class: TEST
#
# HOC Traceability:
#   Subject under test: backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py
#   HOC Layer: L4 — Orchestrator
#   Literature: literature/hoc_spine/orchestrator/operation_registry.md
#   Construction Plan: docs/architecture/hoc/L2-L4-L5_CONSTRUCTION_PLAN.md (Phase A.0)
#
# Why hoc_spine/tests/ and not hoc_spine/orchestrator/tests/:
#   Historical: orchestrator/__init__.py had broken cross-domain imports.
#   PIN-513 replaced those with Protocol-based interfaces.
#   Tests may now be migrated to hoc_spine/orchestrator/tests/ if desired.
#
# Run:
#   cd backend && PYTHONPATH=. python3 -m pytest app/hoc/cus/hoc_spine/tests/test_operation_registry.py -v

"""
Operation Registry Tests

Tests for the L4 operation dispatch registry.
Subject: backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py

Invariants tested:
- REG-001: Register + execute round-trip works
- REG-002: Unknown operation returns UNKNOWN_OPERATION error
- REG-003: Duplicate registration raises RuntimeError
- REG-004: Frozen registry rejects new registrations
- REG-005: Handler exceptions are caught and wrapped in OperationResult
- REG-006: Introspection (operations list, count, has_operation)
- REG-007: OperationResult.ok() and .fail() factory methods
- REG-008: Registry status reports correct data
"""

from unittest.mock import MagicMock

import pytest

# Direct file import — avoids orchestrator/__init__.py import chain.
# PIN-513 fixed the broken cross-domain imports, but keeping direct import
# for isolation. Can switch to package import if desired:
#   from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (...)
import importlib.util
import sys
from pathlib import Path

_mod_path = Path(__file__).resolve().parent.parent / "orchestrator" / "operation_registry.py"
_spec = importlib.util.spec_from_file_location("operation_registry", _mod_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["operation_registry"] = _mod
_spec.loader.exec_module(_mod)

OperationContext = _mod.OperationContext
OperationResult = _mod.OperationResult
OperationRegistry = _mod.OperationRegistry
get_operation_registry = _mod.get_operation_registry
reset_operation_registry = _mod.reset_operation_registry


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def registry():
    """Fresh registry for each test."""
    return OperationRegistry()


@pytest.fixture
def mock_session():
    """Mock AsyncSession."""
    return MagicMock()


@pytest.fixture
def ctx(mock_session):
    """Basic operation context."""
    return OperationContext(
        session=mock_session,
        tenant_id="tenant-001",
        params={"key": "value"},
    )


class StubHandler:
    """Test handler that returns fixed data."""

    def __init__(self, data=None):
        self._data = data or {"status": "ok"}

    async def execute(self, ctx: OperationContext) -> OperationResult:
        return OperationResult.ok(self._data)


class FailingStubHandler:
    """Test handler that raises an exception."""

    async def execute(self, ctx: OperationContext) -> OperationResult:
        raise ValueError("Something went wrong in L5")


# =============================================================================
# REG-001: Register + execute round-trip
# =============================================================================


@pytest.mark.asyncio
async def test_register_and_execute(registry, ctx):
    """REG-001: Registered handler is found and executed."""
    handler = StubHandler(data={"count": 42})
    registry.register("test.query", handler)

    result = await registry.execute("test.query", ctx)

    assert result.success is True
    assert result.data == {"count": 42}
    assert result.operation == "test.query"
    assert result.duration_ms > 0


# =============================================================================
# REG-002: Unknown operation
# =============================================================================


@pytest.mark.asyncio
async def test_unknown_operation(registry, ctx):
    """REG-002: Unknown operation returns error, not exception."""
    result = await registry.execute("nonexistent.op", ctx)

    assert result.success is False
    assert result.error_code == "UNKNOWN_OPERATION"
    assert "nonexistent.op" in result.error


# =============================================================================
# REG-003: Duplicate registration
# =============================================================================


def test_duplicate_registration_raises(registry):
    """REG-003: Cannot register same operation name twice."""
    registry.register("dup.op", StubHandler())

    with pytest.raises(RuntimeError, match="already registered"):
        registry.register("dup.op", StubHandler())


# =============================================================================
# REG-004: Frozen registry
# =============================================================================


def test_frozen_registry_rejects(registry):
    """REG-004: Frozen registry refuses new registrations."""
    registry.register("first.op", StubHandler())
    registry.freeze()

    with pytest.raises(RuntimeError, match="frozen"):
        registry.register("second.op", StubHandler())


def test_freeze_sets_flag(registry):
    """REG-004: freeze() sets is_frozen flag."""
    assert registry.is_frozen is False
    registry.freeze()
    assert registry.is_frozen is True


# =============================================================================
# REG-005: Handler exception wrapping
# =============================================================================


@pytest.mark.asyncio
async def test_handler_exception_wrapped(registry, ctx):
    """REG-005: Handler exceptions become OperationResult.fail()."""
    registry.register("fail.op", FailingStubHandler())

    result = await registry.execute("fail.op", ctx)

    assert result.success is False
    assert "Something went wrong in L5" in result.error
    assert "HANDLER_EXCEPTION:ValueError" in result.error_code


# =============================================================================
# REG-006: Introspection
# =============================================================================


def test_operations_list(registry):
    """REG-006: operations returns sorted list."""
    registry.register("b.op", StubHandler())
    registry.register("a.op", StubHandler())

    assert registry.operations == ["a.op", "b.op"]


def test_operation_count(registry):
    """REG-006: operation_count is accurate."""
    assert registry.operation_count == 0
    registry.register("x.op", StubHandler())
    assert registry.operation_count == 1


def test_has_operation(registry):
    """REG-006: has_operation checks correctly."""
    registry.register("yes.op", StubHandler())

    assert registry.has_operation("yes.op") is True
    assert registry.has_operation("no.op") is False


def test_get_handler(registry):
    """REG-006: get_handler returns handler or None."""
    handler = StubHandler()
    registry.register("get.op", handler)

    assert registry.get_handler("get.op") is handler
    assert registry.get_handler("nope") is None


# =============================================================================
# REG-007: Result factories
# =============================================================================


def test_result_ok():
    """REG-007: OperationResult.ok() creates success result."""
    result = OperationResult.ok({"data": 1})
    assert result.success is True
    assert result.data == {"data": 1}
    assert result.error is None


def test_result_fail():
    """REG-007: OperationResult.fail() creates failure result."""
    result = OperationResult.fail("bad input", "VALIDATION_ERROR")
    assert result.success is False
    assert result.error == "bad input"
    assert result.error_code == "VALIDATION_ERROR"
    assert result.data is None


# =============================================================================
# REG-008: Status
# =============================================================================


def test_status(registry):
    """REG-008: status() returns correct diagnostics."""
    registry.register("a.op", StubHandler())
    registry.register("b.op", StubHandler())

    s = registry.status()
    assert s["version"] == "1.0.0"
    assert s["operation_count"] == 2
    assert s["frozen"] is False
    assert s["operations"] == ["a.op", "b.op"]


# =============================================================================
# Singleton tests
# =============================================================================


def test_singleton():
    """Singleton returns same instance."""
    reset_operation_registry()
    r1 = get_operation_registry()
    r2 = get_operation_registry()
    assert r1 is r2
    reset_operation_registry()


def test_reset_singleton():
    """Reset creates new instance."""
    reset_operation_registry()
    r1 = get_operation_registry()
    reset_operation_registry()
    r2 = get_operation_registry()
    assert r1 is not r2
    reset_operation_registry()


# =============================================================================
# Handler protocol enforcement
# =============================================================================


def test_invalid_handler_rejected(registry):
    """Handler without execute() method is rejected."""
    with pytest.raises(TypeError, match="OperationHandler protocol"):
        registry.register("bad.op", "not a handler")
