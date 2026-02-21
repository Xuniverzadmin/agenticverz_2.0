# Layer: L8 — Test
# AUDIENCE: INTERNAL
# Role: Validates BA-04 — invariant_evaluator is wired into operation_registry.py execute path
# artifact_class: TEST

"""
Invariant Registry Wiring Tests (BA-04 Delta)

Proves that the OperationRegistry.execute() path invokes invariant
preconditions and postconditions via _evaluate_invariants_safe().
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = (
    BACKEND_ROOT
    / "app"
    / "hoc"
    / "cus"
    / "hoc_spine"
    / "orchestrator"
    / "operation_registry.py"
)


# =============================================================================
# Static analysis: prove the wiring exists in source
# =============================================================================


def _read_registry_source() -> str:
    return REGISTRY_PATH.read_text(encoding="utf-8")


def _extract_method_body(source: str, method_name: str) -> str:
    """Extract the full body of a method from source, without fixed-size slicing."""
    marker = f"def {method_name}("
    start = source.find(marker)
    assert start != -1, f"{method_name} not found in source"
    # Find the next method at the same indentation level (4-space class method)
    next_def = source.find("\n    def ", start + 1)
    if next_def != -1:
        return source[start:next_def]
    return source[start:]


class TestInvariantWiringStatic:
    """Static analysis tests: prove invariant_evaluator is wired into the registry."""

    def test_evaluate_invariants_safe_method_exists(self):
        """The _evaluate_invariants_safe method must exist in OperationRegistry."""
        source = _read_registry_source()
        assert "def _evaluate_invariants_safe(" in source

    def test_precondition_call_before_handler_execute(self):
        """_evaluate_invariants_safe must be called with phase='pre' before handler.execute."""
        source = _read_registry_source()
        # Find the execute method body
        pre_idx = source.find('phase="pre"')
        handler_idx = source.find("await handler.execute(")
        assert pre_idx != -1, "phase='pre' call not found"
        assert handler_idx != -1, "handler.execute call not found"
        assert pre_idx < handler_idx, (
            "Precondition check must appear BEFORE handler.execute()"
        )

    def test_postcondition_call_after_handler_execute(self):
        """_evaluate_invariants_safe must be called with phase='post' after handler.execute."""
        source = _read_registry_source()
        handler_idx = source.find("await handler.execute(")
        post_idx = source.find('phase="post"')
        assert handler_idx != -1, "handler.execute call not found"
        assert post_idx != -1, "phase='post' call not found"
        assert post_idx > handler_idx, (
            "Postcondition check must appear AFTER handler.execute()"
        )

    def test_invariant_evaluator_import_inside_safe_method(self):
        """The lazy import of invariant_evaluator must be inside _evaluate_invariants_safe."""
        method_body = _extract_method_body(_read_registry_source(), "_evaluate_invariants_safe")
        assert "from app.hoc.cus.hoc_spine.authority.invariant_evaluator import" in method_body

    def test_monitor_mode_used(self):
        """The wiring must use MONITOR mode (log only, never block)."""
        method_body = _extract_method_body(_read_registry_source(), "_evaluate_invariants_safe")
        assert "InvariantMode.MONITOR" in method_body

    def test_exception_handling_never_blocks(self):
        """The method must catch all exceptions to never block dispatch."""
        method_body = _extract_method_body(_read_registry_source(), "_evaluate_invariants_safe")
        assert "except Exception:" in method_body

    def test_invariant_context_includes_tenant_id(self):
        """The invariant context dict must include tenant_id from OperationContext."""
        method_body = _extract_method_body(_read_registry_source(), "_evaluate_invariants_safe")
        assert '"tenant_id"' in method_body


# =============================================================================
# Runtime: prove the wiring works at execution time
# =============================================================================


class TestInvariantWiringRuntime:
    """Runtime tests: prove invariant evaluation fires during dispatch."""

    @pytest.fixture
    def fresh_registry(self):
        """Create a fresh OperationRegistry with a mock handler."""
        from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
            OperationRegistry,
            OperationContext,
            OperationResult,
        )

        registry = OperationRegistry()

        # Create a mock handler
        handler = MagicMock()
        handler.execute = AsyncMock(return_value=OperationResult.ok({"key": "value"}))
        registry.register("test.operation", handler)

        ctx = OperationContext(
            session=None,
            tenant_id="test-tenant",
            params={"method": "test"},
        )

        return registry, ctx, handler

    @pytest.mark.asyncio
    async def test_execute_calls_evaluate_invariants_safe(self, fresh_registry):
        """execute() must call _evaluate_invariants_safe for both pre and post."""
        registry, ctx, handler = fresh_registry

        with patch.object(registry, "_evaluate_invariants_safe") as mock_eval:
            await registry.execute("test.operation", ctx)

            assert mock_eval.call_count == 2
            # First call: pre
            pre_call = mock_eval.call_args_list[0]
            assert pre_call.args[0] == "test.operation"
            assert pre_call.kwargs.get("phase") or pre_call.args[2] == "pre"
            # Second call: post
            post_call = mock_eval.call_args_list[1]
            assert post_call.args[0] == "test.operation"
            assert post_call.kwargs.get("phase") or post_call.args[2] == "post"

    @pytest.mark.asyncio
    async def test_invariant_failure_does_not_block_dispatch(self, fresh_registry):
        """Even if invariant evaluation raises, the handler must still execute."""
        registry, ctx, handler = fresh_registry

        def _side_effect(*args, **kwargs):
            raise RuntimeError("Invariant evaluation exploded")

        with patch.object(registry, "_evaluate_invariants_safe", side_effect=_side_effect):
            # The RuntimeError from the patched method should be caught
            # But since we're patching at the call site, the execute method
            # will see the exception. Let's verify handler still ran.
            # Actually, the try/except is INSIDE _evaluate_invariants_safe,
            # so patching it means the exception propagates. Let's test differently.
            pass

        # Better test: verify that a real exception from invariant_evaluator
        # does NOT propagate — use the actual method with a broken import
        with patch(
            "app.hoc.cus.hoc_spine.authority.invariant_evaluator.evaluate_preconditions",
            side_effect=RuntimeError("broken"),
        ):
            result = await registry.execute("test.operation", ctx)
            # Handler must still have been called despite invariant error
            assert result.success is True
            assert handler.execute.called
